from config import config
from database.client import database


async def check_collection_exists(name: str) -> bool:
    async for collection in await database.list_collections():
        if collection['type'] == 'collection' and collection['name'] == name:
            return True

    return False


async def ensure_collections_exist() -> None:
    for collection_name, options in config.collections.items():
        if not await check_collection_exists(collection_name):
            await database.create_collection(collection_name, **options)


async def ensure_indexes_exist() -> None:
    for collection_name, index_configs in config.indexes.items():
        collection = database[collection_name]
        index_names = [index['name'] async for index in await collection.list_indexes()]

        for index_config in index_configs:
            if index_config['name'] in index_names:
                continue

            await collection.create_index(**index_config)


async def initialize_database() -> None:
    await ensure_collections_exist()
    await ensure_indexes_exist()
