from abc import ABC

from ProviderHookFramework.abstracthook import AbstractHook


class Hook2(AbstractHook, ABC):
    pass


class HookNoPass(AbstractHook, ABC):
    pass


class HookCopyAlias(AbstractHook, ABC):
    _alias = ["hook"]
