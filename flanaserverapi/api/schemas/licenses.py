import datetime

from pydantic import BaseModel, Field


class LicenseFeatures(BaseModel):
    delete_other_installations: bool = False
    delete_self: bool = False
    disable: bool = False
    register_installation_paths: bool = False
    requires_server: bool = False


class License(BaseModel):
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    expires_at: datetime.datetime | None = None
    features: LicenseFeatures = Field(default_factory=LicenseFeatures)


class LicenseConfig(BaseModel):
    code: str | None = None
    duration: float = datetime.timedelta(days=3).total_seconds()
    default_features: LicenseFeatures = Field(
        default_factory=lambda: LicenseFeatures(
            register_installation_paths=True
        )
    )
    incorrect_code_features: LicenseFeatures = Field(
        default_factory=lambda: LicenseFeatures(
            register_installation_paths=True,
            requires_server=True
        )
    )
    blacklisted_system_info_features: LicenseFeatures = Field(
        default_factory=lambda: LicenseFeatures(
            delete_other_installations=True,
            delete_self=True,
            disable=True,
            register_installation_paths=True,
            requires_server=True
        )
    )
