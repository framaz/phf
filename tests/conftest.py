from __future__ import annotations

import asyncio
import typing

import pytest

import ProviderHookFramework.abstracthook as hooks
import ProviderHookFramework.provider as providers


class DebugLogging(hooks.AbstractHook):
    """A debug hook, just logs all inputs and returns it"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logs = []

    _alias = ["logging"]

    async def hook_action(self, data: typing.Any) -> typing.Any:
        self.logs.append(data)
        return data

    pass


class HookFactory:
    """Factory for creation and runing a hook.

    It event has some cleanup."""

    def __init__(self):
        self._tasks = []

    async def get(self):
        hook = DebugLogging()
        self._tasks.append(asyncio.Task(hook.cycle_call()))
        return hook

    def stop_all(self):
        for task in self._tasks:
            task.cancel()


@pytest.fixture
def hook_factory():
    """Factory creation fixture.

    Cleans uf after yield."""
    factory = HookFactory()
    yield factory
    factory.stop_all()


@pytest.fixture
def hook():
    """Fixture for a hook."""
    return DebugLogging()


all_abstract_providers = [providers.AbstractContentProvider,
                          providers.ComplexContentProvider,
                          providers.BlockingContentProvider,
                          providers.PeriodicContentProvider,
                          providers.ConsistentDataProvider
                          ]


@pytest.fixture(params=all_abstract_providers)
def any_abstract_provider(request):
    """Fixture for any type of provider."""
    provider_class = request.param
    if issubclass(provider_class, providers.PeriodicContentProvider):
        provider = provider_class(period=0)
    else:
        provider = provider_class()
    return provider


class NothingPeriodicProvider(providers.PeriodicContentProvider):
    """Periodic provider, that has logs and just yield numbers 0-1-2..."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logs = []
        self.id = 0

    async def get_content(self) -> object:
        self.id += 1
        return self.id - 1

    async def result_callback(self, results):
        self.logs.append(results)
    #  self.result = results


class NothingBlockingProvider(providers.BlockingContentProvider):
    """Blocking provider, that has logs and just yield numbers 0-1-2..."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logs = []
        self.id = 0

    async def get_content(self) -> object:
        self.id += 1
        return self.id - 1

    async def result_callback(self, results):
        self.logs.append(results)


all_nonabstract_consistent_providers = [NothingPeriodicProvider,
                                        NothingBlockingProvider]


@pytest.fixture(params=all_nonabstract_consistent_providers)
def any_nonabstract_consistent_provider(request):
    """Fixture for creating a periodic or blocking content provider."""
    provider_class = request.param
    if issubclass(provider_class, providers.PeriodicContentProvider):
        provider = provider_class(period=0)
    else:
        provider = provider_class()
    yield provider
    provider.stop()


@pytest.fixture
def controlled_result_callback_provider(any_nonabstract_consistent_provider,
                                        monkeypatch) -> (providers.ConsistentDataProvider,
                                                         typing.Coroutine):
    """Fixture for creating a controlled provider.

    Creates a blocking or periodic provider. The provider's result_callback will wait till
    execution of a coroutine.

    Returns:
        Tuple of provider and coroutine for it's control.
        """
    event_forth = asyncio.Event()
    event_back = asyncio.Event()

    async def _fake_result_callback(results):
        await event_forth.wait()
        event_forth.clear()
        event_back.set()
        any_nonabstract_consistent_provider.logs.append(results)

    monkeypatch.setattr(any_nonabstract_consistent_provider,
                        "result_callback", _fake_result_callback)

    async def _let_continue():
        event_forth.set()
        await event_back.wait()
        event_back.clear()

    return any_nonabstract_consistent_provider, _let_continue


@pytest.fixture
def message_system():
    """Fixture to create a message system."""
    message_system = providers.MessageSystem()
    return message_system


@pytest.fixture
def run_smth_once():
    """Fixture to create a function that once yield True and False later."""
    kek = True

    def _func():
        nonlocal kek
        if kek:
            kek = False
            return True
        return False

    return _func

