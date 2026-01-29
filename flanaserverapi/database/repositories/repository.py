import typing
from collections.abc import Iterable, Sequence
from typing import Any

import pymongo.errors
from bson import ObjectId
from pydantic import BaseModel
from pymongo.asynchronous.collection import AsyncCollection, ReturnDocument


class Repository[T: BaseModel]:
    def __init__(self, collection: AsyncCollection[T]) -> None:
        self._collection = collection
        # noinspection PyUnresolvedReferences
        self._T = typing.get_args(self.__orig_bases__[0])[0]

    async def delete(self, id: str | ObjectId) -> None:
        await self._collection.delete_one({'_id': id})

    async def delete_many(self, filter: dict[str, Any]) -> None:
        await self._collection.delete_many(filter)

    async def enforce_limit(self, limit: int) -> None:
        if (excess := await self._collection.count_documents({}) - limit) <= 0:
            return

        cursor = self._collection.find(projection={'_id': True}, sort=('date',), limit=excess)
        await self._collection.delete_many({'_id': {'$in': [document['_id'] async for document in cursor]}})

    async def get_all(self, sort_keys: str | Sequence[str | tuple[str, int]] = ()) -> list[T]:
        cursor = self._collection.find()

        if sort_keys:
            cursor.sort(sort_keys)

        return [self._T(**document) async for document in cursor]

    async def get_by_id(self, id: str | ObjectId) -> T | None:
        if document := await self._collection.find_one({'_id': id}):
            return self._T(**document)

    async def insert(self, item: T, limit: int | None = None) -> T:
        insert_result = await self._collection.insert_one(item.model_dump(by_alias=True))
        item.id = insert_result.inserted_id

        if limit is not None and await self._collection.count_documents({}) > limit:
            await self._collection.find_one_and_delete({}, sort=('date',))

        return item

    async def insert_many(self, items: Iterable[T], limit: int | None = None) -> None:
        try:
            await self._collection.insert_many((item.model_dump(by_alias=True) for item in items))
        except pymongo.errors.InvalidOperation:
            pass

        if limit is not None:
            await self.enforce_limit(limit)

    async def update(self, item: T) -> T | None:
        if document := await self._collection.find_one_and_update(
            {'_id': item.id},
            {'$set': item.model_dump(by_alias=True)},
            upsert=True,
            return_document=ReturnDocument.AFTER
        ):
            return self._T(**document)
