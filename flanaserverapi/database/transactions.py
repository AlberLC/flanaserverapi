import functools

from pymongo.asynchronous.client_session import AsyncClientSession

from database.database_client import database_client
from database.repositories.repository import Repository


def mongo_transaction(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with database_client.start_session() as database_session:
            async def callback(_: AsyncClientSession):
                new_args = tuple(
                    arg.with_session(database_session) if isinstance(arg, Repository) else arg for arg in args
                )
                new_kwargs = {
                    key: value.with_session(database_session) if isinstance(value, Repository) else value
                    for key, value in kwargs.items()
                }

                return await func(*new_args, **new_kwargs)

            return await database_session.with_transaction(callback)

    return wrapper
