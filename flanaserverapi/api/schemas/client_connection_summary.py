from typing import Self

from pydantic import BaseModel

from custom_types import AppId
from models.client_connections import ClientConnection


class ClientConnectionSummary(BaseModel):
    id: str
    app_id: AppId
    username: str | None = None
    hostname: str | None = None
    mac_address: str | None = None
    ip: str
    geojs: dict[str, str | None] | None = None
    ip_geolocation: dict[str, str | None] | None = None

    @classmethod
    def from_client_connection(cls, client_connection: ClientConnection) -> Self:
        if geojs_data := client_connection.system_info.ip_geolocation.geojs_data:
            geojs = {
                'country': geojs_data.get('country'),
                'region': geojs_data.get('region'),
                'city': geojs_data.get('city')
            }
        else:
            geojs = None

        if (
            (ip_geolocation_data := client_connection.system_info.ip_geolocation.ip_geolocation_data)
            and
            (ip_geolocation_location_data := ip_geolocation_data.get('location'))
        ):
            ip_geolocation = {
                'country': ip_geolocation_location_data.get('country_name'),
                'state_province': ip_geolocation_location_data.get('state_prov'),
                'district': ip_geolocation_location_data.get('district'),
                'city': ip_geolocation_location_data.get('city')
            }
        else:
            ip_geolocation = None

        return cls(
            id=str(client_connection.mongo_id),
            app_id=client_connection.app_id,
            username=client_connection.system_info.username,
            hostname=client_connection.system_info.hostname,
            mac_address=client_connection.system_info.mac_address,
            ip=client_connection.system_info.ip_geolocation.ip,
            geojs=geojs,
            ip_geolocation=ip_geolocation
        )
