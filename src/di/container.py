from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import FastapiProvider

from .providers.auth import AuthProvider
from .providers.core import CoreProvider
from .providers.repos import RepositoryProvider
from .providers.services import ServiceProvider


def get_container() -> AsyncContainer:
    return make_async_container(
        FastapiProvider(),
        CoreProvider(),
        RepositoryProvider(),
        ServiceProvider(),
        AuthProvider(),
    )
