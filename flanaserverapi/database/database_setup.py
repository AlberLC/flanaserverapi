from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from pymongo.asynchronous.database import AsyncDatabase

from config import config
from database import database_client


async def ensure_collections_exist(database: AsyncDatabase) -> None:
    existing_collections = {
        collection['name']
        async for collection in await database.list_collections()
        if collection['type'] == 'collection'
    }

    for collection_name, options in config.collections.items():
        if collection_name not in existing_collections:
            await database.create_collection(collection_name, **options)
            existing_collections.add(collection_name)


async def ensure_indexes_exist(database: AsyncDatabase) -> None:
    for collection_name, index_configs in config.indexes.items():
        collection = database[collection_name]
        index_names = {index['name'] async for index in await collection.list_indexes()}

        for index_config in index_configs:
            index_name = index_config['name']

            if index_name not in index_names:
                await collection.create_index(**index_config)
                index_names.add(index_name)


async def ensure_schema() -> None:
    try:
        database_client.initialize_database_client()

        database = database_client.get_database()
        await ensure_collections_exist(database)
        await ensure_indexes_exist(database)
    finally:
        await database_client.close_database_client()


@asynccontextmanager
async def initialize_database() -> AsyncGenerator[None]:
    try:
        database_client.initialize_database_client()

        yield
    finally:
        await database_client.close_database_client()
