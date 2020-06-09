from ProviderHookFramework.abstracthook import AbstractHook
from ProviderHookFramework.provider import BlockingContentProvider


class Hook1(AbstractHook):
    _alias = ["hook"]
    pass


class NonHook1:
    pass


class Provider1(BlockingContentProvider):
    pass


NonHook2 = 0
