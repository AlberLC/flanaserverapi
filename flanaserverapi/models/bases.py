from typing import Annotated

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

from utils import crypto_utils


class MongoModel[T](BaseModel):
    mongo_id: T = Field(alias='_id')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ObjectIdModel(MongoModel[ObjectId]):
    mongo_id: Annotated[ObjectId, PlainSerializer(str, when_used='json')] = Field(alias='_id', default_factory=ObjectId)


class SecretIdModel(MongoModel[str]):
    mongo_id: str = Field(alias='_id', default_factory=crypto_utils.create_id)
