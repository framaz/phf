from ProviderHookFramework.abstracthook import AbstractHook


class Hook2(AbstractHook):
    pass


class HookNoPass(AbstractHook):
    pass


class HookCopyAlias(AbstractHook):
    _alias = ["hook"]
