from dishka import AsyncContainer, make_async_container

from .providers.core import CoreProvider, RequestProvider
from .providers.repos import RepositoryProvider
from .providers.services import ServiceProvider


def get_container() -> AsyncContainer:
    return make_async_container(
        CoreProvider(),
        RequestProvider(),
        RepositoryProvider(),
        ServiceProvider(),
    )