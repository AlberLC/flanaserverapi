import datetime

from api.schemas.app import App
from api.schemas.client_context import ClientContext
from api.schemas.licenses import License


def generate_license(app: App, client_context: ClientContext) -> License:
    kwargs = {}

    license_config = app.license_config

    if client_context.system_info in app.blacklisted_system_infos:
        kwargs['features'] = license_config.blacklisted_system_info_features
    elif client_context.system_info in app.whitelisted_system_infos:
        kwargs['features'] = license_config.whitelisted_system_info_features
    elif not license_config.code or client_context.client_code == license_config.code:
        kwargs['features'] = license_config.default_features
    else:
        kwargs['features'] = license_config.incorrect_code_features

    if license_config.duration:
        kwargs['expires_at'] = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=license_config.duration)

    return License(**kwargs)
