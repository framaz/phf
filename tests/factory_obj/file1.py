from ProviderHookFramework.abstracthook import AbstractHook
from ProviderHookFramework.provider import BlockingContentProvider


class Hook1(AbstractHook):
    _alias = ["hook"]

    def __init__(self, a, b=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.a = a
        self.b = b

    async def hook_action(self, data):
        return data


class NonHook1:
    pass


class Provider1(BlockingContentProvider):
    def __init__(self, a, b=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.a = a
        self.b = b

    async def get_content(self) -> object:
        return "a"

    pass


NonHook2 = 0
