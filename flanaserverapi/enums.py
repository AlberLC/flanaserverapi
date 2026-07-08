from enum import Enum


class Environment(Enum):
    DEVELOPMENT = 'development'
    PRODUCTION = 'production'


class ReleaseType(Enum):
    LATEST = 'latest'
    OLD = 'old'
