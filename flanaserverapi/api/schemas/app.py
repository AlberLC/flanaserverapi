import datetime

from pydantic import BaseModel, Field


class App(BaseModel):
    id: str
    version: str = Field(pattern='^\d+\.\d+\.\d+$')
    online: bool
    delete_app_installations: bool
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    expires_at: datetime.datetime
