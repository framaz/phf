from abc import ABC

from phf.abstracthook import AbstractHook
from phf.provider import AbstractContentProvider


class Hook3(AbstractHook, ABC):
    pass


class Provider3(AbstractContentProvider, ABC):
    pass
