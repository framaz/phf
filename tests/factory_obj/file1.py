from ProviderHookFramework.abstracthook import AbstractHook
from ProviderHookFramework.provider import BlockingContentProvider


class Hook1(AbstractHook):
    _alias = ["hook"]

    def __init__(self, a, b=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.a = a
        self.b = b


class NonHook1:
    pass


class Provider1(BlockingContentProvider):
    def __init__(self, a, b=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.a = a
        self.b = b

    pass


NonHook2 = 0
