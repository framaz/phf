from __future__ import annotations

import asyncio
import os
import threading
import typing

import pytest

import phf.abstracthook as hooks
import phf.commandinput as commandinput
import phf.factory as factory
import phf.provider as providers
from phf.phfsystem import PHFSystem


@pytest.fixture(autouse=True, scope="session")
def working_dir():
    directory = os.getcwd()
    if not directory.endswith("tests"):
        os.chdir(os.path.join(directory, "tests"))
    yield
    os.chdir(directory)


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

    Be aware that get is not a method but a coroutine.
    It event has some cleanup."""

    def __init__(self):
        self._tasks = []
        self._hooks = []

    async def get_started_hook(self) -> DebugLogging:
        hook = DebugLogging()
        self._hooks.append(hook)
        self._tasks.append(asyncio.Task(hook.cycle_call()))
        return hook

    async def get_hook(self) -> DebugLogging:
        hook = DebugLogging()
        self._hooks.append(hook)
        return hook

    def stop_all(self):
        for task in self._tasks:
            task.cancel()
        for hook in self._hooks:
            hook.stop()


@pytest.fixture
async def hook_factory() -> HookFactory:
    """Factory creation fixture.

    Cleans uf after yield."""
    cur_factory = HookFactory()
    yield cur_factory
    cur_factory.stop_all()
    await asyncio.sleep(0.01)


@pytest.fixture
async def hook() -> DebugLogging:
    """Fixture for a hook."""
    hook = DebugLogging()
    yield hook
    hook.stop()
    await asyncio.sleep(0.01)


all_abstract_providers = [providers.AbstractContentProvider,
                          providers.ComplexContentProvider,
                          providers.BlockingContentProvider,
                          providers.PeriodicContentProvider,
                          providers.ConsistentDataProvider
                          ]


@pytest.fixture(params=all_abstract_providers)
async def any_abstract_provider(request, monkeypatch) -> providers.AbstractContentProvider:
    """Fixture for any type of provider."""
    provider_class = request.param
    if issubclass(provider_class, providers.PeriodicContentProvider):
        provider = provider_class(period=0)
    else:
        provider = provider_class()

    async def _coro():
        return "1"

    if issubclass(provider_class, providers.ConsistentDataProvider):
        monkeypatch.setattr(provider, "get_content", _coro)

    yield provider
    await asyncio.sleep(0.01)
    provider.stop()


class NothingPeriodicProvider(providers.PeriodicContentProvider):
    """Periodic provider, that has logs and just yield numbers 0-1-2..."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logs = []
        self.id = 0

    async def get_content(self) -> object:
        self.id += 1
        return self.id - 1

    async def result_callback(self, results) -> None:
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

    async def result_callback(self, results) -> None:
        self.logs.append(results)


class PeriodicProviderFactory:
    """Creates periodic providers."""

    def get_provider(self) -> NothingPeriodicProvider:
        """Create periodic provider."""
        return NothingPeriodicProvider()


@pytest.fixture
def periodic_provider_factory() -> PeriodicProviderFactory:
    """Fixture to create PeriodicProviderFactory."""
    return PeriodicProviderFactory()


all_nonabstract_consistent_providers = [NothingPeriodicProvider,
                                        NothingBlockingProvider]


@pytest.fixture(params=all_nonabstract_consistent_providers)
def any_nonabstract_consistent_provider(request) -> providers.ConsistentDataProvider:
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
        # noinspection PyUnresolvedReferences
        any_nonabstract_consistent_provider.logs.append(results)

    monkeypatch.setattr(any_nonabstract_consistent_provider,
                        "result_callback", _fake_result_callback)

    async def _let_continue():
        event_forth.set()
        await event_back.wait()
        event_back.clear()

    return any_nonabstract_consistent_provider, _let_continue


@pytest.fixture
def message_system() -> providers.MessageSystem:
    """Fixture to create a message system."""
    message_system = providers.MessageSystem()
    return message_system


@pytest.fixture
def run_smth_once() -> typing.Callable:
    """Fixture to create a function that once yield True and False later."""
    kek = True

    def _func():
        nonlocal kek
        if kek:
            kek = False
            return True
        return False

    return _func


@pytest.fixture
def complex_provider_nonstarted() -> providers.ComplexContentProvider:
    """Fixture to create a complex provider."""
    return providers.ComplexContentProvider()


@pytest.fixture
def complex_provider() -> providers.ComplexContentProvider:
    """Fixture to create a complex provider and run it in a different thread."""
    provider = providers.ComplexContentProvider()

    def _thread_func(cycle_coroutine):
        asyncio.run(cycle_coroutine)

    thread = threading.Thread(target=_thread_func, args=[provider.cycle()])
    thread.start()
    yield provider
    provider.stop()


@pytest.fixture(scope="session")
def hook_provider_factory() -> factory.HookAndProviderFactory:
    """Creates a ready to use HookAndProviderFactory.

    The factory has already read all needed providers and hooks."""
    return factory.HookAndProviderFactory(["factory_obj"], ["factory_obj"])

@pytest.fixture
def non_started_phfsys() -> PHFSystem:
    """Create a non-started PHFSystem."""
    phfsys = PHFSystem()
    phfsys.import_hook_sources("factory_obj")
    phfsys.import_provider_sources("factory_obj")
    return phfsys

@pytest.fixture
def fake_started_phfsys() -> PHFSystem:
    """Create PHFSystem that's not running, but running flag is True.

    As it isn't running, commands cannot be run from the inside."""
    phfsys = PHFSystem()
    phfsys._running_state = True
    phfsys.import_hook_sources("factory_obj")
    phfsys.import_provider_sources("factory_obj")
    return phfsys


class FakeCommandTranslator:
    """Class to yield Command to PHFSystem without usage of command inputs.

    This class should be send to PHFSystem instead of command input class
    command input's set_command_result is ducktyped here.

    Attributes:
        _to_phfsys_queue: asyncio.Queue, queue where to put commands(matches
            PHFSystem._command_queue).
        _loop: asyncio.loop, at which PHFSystem runs.
        logs: logs of all commands results.
        """

    def __init__(self):
        self._to_phfsys_queue = None
        self._loop = None
        self.logs = []

    async def set_command_result(self, output) -> None:
        """Mocks AbstractCommandInput.set_command_result.

        Shouldn't be called by user.
        """
        self.logs.append(output)

    def initialize(self,
                   event_loop: asyncio.AbstractEventLoop,
                   queue: asyncio.Queue) -> None:
        """Initialize object with PHFSystem's event loop and command input queue.
        Args:
            event_loop: targeted PHFSystem's event loop.
            queue: targeted PHFSystem's command input queue.
        """
        self._loop = event_loop
        self._to_phfsys_queue = queue

    def send_command_to_phfsys(self, command: commandinput.Command) -> None:
        """Send command to targeted PHFSystem's command queue."""
        asyncio.run_coroutine_threadsafe(self._to_phfsys_queue.put((command, self)),
                                         self._loop)


@pytest.fixture
async def started_phfsys() -> (PHFSystem, FakeCommandTranslator):
    """Fixture to get a running PHFSystem and command input source."""
    phfsys = PHFSystem()
    fake_command_translator = FakeCommandTranslator()

    def _start_sys():
        phfsys.start()

    phfsys.import_hook_sources("factory_obj")
    phfsys.import_provider_sources("factory_obj")

    loop = None

    threading.Thread(target=_start_sys).start()
    await asyncio.sleep(0.1)

    fake_command_translator.initialize(phfsys._asyncio_loop, phfsys._command_queue)

    return phfsys, fake_command_translator

