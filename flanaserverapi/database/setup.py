from config import config
from database.client import database


async def check_collection_exists(name: str) -> bool:
    async for collection in await database.list_collections():
        if collection['type'] == 'collection' and collection['name'] == name:
            return True

    return False


async def ensure_collections_exist() -> None:
    for name, options in config.collections.items():
        if not await check_collection_exists(name):
            await database.create_collection(name, **options)
