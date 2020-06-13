"""Module for data sources.

Now there 3 types of content providers for external usage: PeriodicContentProvider,
BlockingContentProvider and ComplexContentProvider.

PeriodicContentProvider and BlockingContentProvider are subclasses of ConsistentDataProvider.
ConsistentDataProvider is a provider that can work in the following style:

    while True:
        data = get_content()
        results = []
        for hook in hooks:
            results.append(hook.hook_action(data))
        result_callback(results)

PeriodicContentProvider is executed every period seconds. It is supposed to be used with fast,
non-blocking or async data retrieval.

BlockingContentProvider is executed in cycle lice periodic one, but all waiting should be handled by
the user. As get_content is executed in a different thread, you should not be afraid of doing some
blocking IO as it won't block the whole system.

As being subclasses of ConsistentDataProvider, both of them can be easily created by inheriting and
overriding following methods:

- async get_content(self) - function for receiving content, has to be overridden. Returns the data in
any data form(ie object, dict, str etc). The function's result value is sent to all the hooks. You should
just form the data in a usable way

- async def result_callback(self, results) - function for handling result of all hooks execution.
If it's not overridden, then no actions to capture hook execution results is done.


General idea is that get_content just retrieves and transform data to usable form, hook.hook_action
does the data processing, all needed actions, remote requests etc and result_callback sums up the
result of hook execution

Work with ComplexContentProvider is much a bit different, it will be described later.
"""
from __future__ import annotations

import asyncio
import copy
import queue
import threading
import typing
from abc import ABC

from abstracthook import AbstractHook


class AbstractContentProvider:
    """Basic class for all content providers.

    Should not be directly inherited.

    Attributes:
        _asynio_hooks: list of all linked hooks.
        _asyncio_hook_tasks: list of all asyncio.Task for running hooks.
        _asyncio_straight_queues: list of all asyncio.queues for provider -> hook data .
        _asyncio_callback_queues: list of all asyncio.queues for hook -> provider data transfer.
        _asyncio_task: asyncio.Task for provider rinning.
        _asyncio_running: bool, shows whether the provider is running.
        _asyncio_loop: tracks in what asyncio.Loop provider is running.
        _is_with_callback: tracks whether callbacks should be done.
    """
    _alias = []

    def __new__(cls, *args, **kwargs):
        """Initialize even if user forgets about calling super's __init__."""
        obj = object.__new__(cls)
        obj._asynio_hooks = []
        obj._asyncio_hook_tasks = []
        obj._asyncio_straight_queues = []
        obj._asyncio_callback_queues = []
        obj._asyncio_task = None
        obj._asyncio_running = False
        obj._asyncio_loop = None
        obj._is_with_callback = False

        # Checking if callbacks are needed.
        return obj

    def __init__(self, *args, **kwargs):
        """Construct object."""

    async def cycle(self) -> None:
        """Main working cycle of provider, not implemented.

        In general, it is executed till stop() is called.
        """
        raise NotImplementedError(f"Cycle of {self.__class__} not overridden")

    async def _run_result_callback(self) -> typing.List:
        """Gather all results from all queues


        If provider is without callback, then just empty the queues."""
        if self._is_with_callback:
            results = await asyncio.gather(*[queue.get() for queue in self._asyncio_callback_queues])
            return results
        else:
            for queue in self._asyncio_callback_queues:
                while not queue.empty():
                    await queue.get()

    def _start_hook(self, hook: AbstractHook) -> None:
        """Start hook and remember it's queues.

        Has to be called inside an event loop.

        Args:
            hook: Hook to start(has to be in list of linked hooks)
        """
        if self._asyncio_loop == asyncio.get_event_loop():
            self._asyncio_straight_queues.append(hook.get_straight_queue())
            self._asyncio_callback_queues.append(hook.get_callback_queue())
            self._asyncio_hook_tasks.append(asyncio.create_task(hook.cycle_call()))
        else:
            async def _coro():
                self._asyncio_straight_queues.append(hook.get_straight_queue())
                self._asyncio_callback_queues.append(hook.get_callback_queue())
                self._asyncio_hook_tasks.append(asyncio.create_task(hook.cycle_call()))

            asyncio.run_coroutine_threadsafe(_coro(), self._asyncio_loop)

    def get_hooks(self) -> typing.List[AbstractHook]:
        """Return list of all hooks.

        Returns:
            List of all hooks.
        """
        return self._asynio_hooks

    def add_hook(self, hook: AbstractHook) -> None:
        """Link hook to provider and start it if provider is started.

        Args:
            hook: To be added.
        """
        self._asynio_hooks.append(hook)
        if self._asyncio_running:
            self._start_hook(hook)

    def _is_running(self) -> bool:
        """Return whether provider is running now"""
        return self._asyncio_running

    def start(self) -> None:
        """Start the provider."""
        self._asyncio_running = True
        self._asyncio_task = asyncio.create_task(self.cycle())

    # TODO better stop
    def stop(self):
        """Stop hook from running"""
        if self._asyncio_task is not None:
            self._asyncio_task.cancel()

    async def __aenter__(self) -> None:
        """Initialise all in-loop attributes of class."""
        self._asyncio_loop = asyncio.get_event_loop()
        self._asyncio_running = True
        for hook in self._asynio_hooks:
            self._start_hook(hook)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """At the end the decorator stops all hooks.

        If provider raises non asyncio.CancelledError, then everything crashes."""
        self._asyncio_running = False
        if exc_type is asyncio.CancelledError:
            for hook in self._asynio_hooks:
                hook.stop()
            return True

    @classmethod
    def get_aliases(cls) -> typing.List[str]:
        """Return copy of all class's aliases.

        Returns:
            List of all aliases of the class.
        """
        return copy.deepcopy(cls._alias)

    async def _notify_all_hooks(self, data: object) -> None:
        """Send data to all hooks.

        Args:
            data: what to send to hooks.
        """
        for queue in self._asyncio_straight_queues:
            queue.put_nowait(data)


class ConsistentDataProvider(AbstractContentProvider, ABC):
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls, *args, kwargs)
        if ConsistentDataProvider.result_callback != cls.result_callback:
            obj._is_with_callback = True
        return obj

    async def get_content(self) -> object:
        """Get content, not implemented.

        Returns:
            Data in any format.
            """
        raise NotImplementedError(f"Get_site of {self.__class__} not overridden")

    async def result_callback(self, results: typing.List) -> None:
        """Do something after all hooks are executed.

        By default it does nothing."""
        pass


class PeriodicContentProvider(ConsistentDataProvider, ABC):
    """Periodically executes get_content every period seconds.

    Attributes:
        period: period in seconds.
        """

    def __new__(cls, period=5, *args, **kwargs):
        """Create new object, defined to let people forget to call super().__init__().

        Args:
            period: period in seconds.
        """
        obj = ConsistentDataProvider.__new__(cls, *args, **kwargs)
        obj.period = period
        return obj

    def __init__(self, period=5, *args, **kwargs):
        """Create new object.

        Args:
            period: period in seconds.
        """
        super().__init__(*args, **kwargs)
        self.period = period

    async def cycle(self) -> None:
        """Do provider's work in cycle.

        Can be stopped by self.stop()"""
        async with self:
            while self._is_running():
                data = await self.get_content()
                await self._notify_all_hooks(data)
                result = await self._run_result_callback()
                await self.result_callback(result)
                await asyncio.sleep(self.period)


class BlockingContentProvider(ConsistentDataProvider, ABC):
    """Class for providers that are too slow or have unavoidable blocking IO.

    Get_content and result_callback are executed in different thread to let it block.
    Hook is still executed in the main thread.

    Attributes:
        _content_queue: queue from provider's thread to PHFSystem's thread.
        """

    def __new__(cls, *args, **kwargs):
        obj = ConsistentDataProvider.__new__(cls, *args, **kwargs)
        obj._content_queue = asyncio.Queue()
        return obj

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content_queue = asyncio.Queue()

    def _thread_func(self) -> None:
        """Do all provider's work."""

        async def _coro() -> None:
            while self._asyncio_running:
                content = await self.get_content()
                asyncio.run_coroutine_threadsafe(self._content_queue.put(content), self._asyncio_loop)
                res = asyncio.run_coroutine_threadsafe(self._run_result_callback(), self._asyncio_loop).result()
                await self.result_callback(res)

        asyncio.run(_coro())

    async def __aenter__(self):
        """Initialise all in-loop attributes of class."""
        kek = await super().__aenter__()
        self._content_queue = asyncio.Queue()
        return kek

    async def cycle(self) -> None:
        """Main work of provider.

        Here it just creates the new thread and gets info from queue.
        Can be stopped by self.stop()"""
        async with self:
            threading.Thread(target=self._thread_func).start()
            while self._is_running():
                string = await self._content_queue.get()
                await self._notify_all_hooks(string)


class ComplexContentProvider(AbstractContentProvider):
    """Class for complex data providers like servers etc.

    The idea behind this provider is that to send and receive data to provider form some
    external source with a help of message queue system.

    To get the message system after object creation, call get_message_system BEFORE RUNNING
    PHFSystem.

    The class should not be created in the runtime as there is no way to get the message system
    inside PHFSystem.

    If you want to somehow preprocess data, sent to provider by message system, you should
    override method preprocess_data(self, content).

    If you want to somehow postrpocess results of hooks before sending to message system,
    you should override method postprocess_result(self, results).

    Attributes:
        _input_queue: queue from external system to provider(from message system to provider).
        _output_queue: queue from provider to external system(from provider to message system).
        _message_system: instance of MessageSystem to handle all external system-provider
            data transfer.
    """

    def __new__(cls, *args, **kwargs):
        obj = AbstractContentProvider.__new__(cls, *args, **kwargs)
        obj._input_queue = None
        obj._output_queue = None
        obj._message_system = MessageSystem()
        obj._is_with_callback = True
        return obj

    async def __aenter__(self):
        """Initialise all in-loop attributes of class.

        Message system is also fully initialized for the use here.
        """
        await super().__aenter__()
        self._input_queue, self._output_queue = await self._message_system.initialize()

    def get_message_system(self) -> MessageSystem:
        """Return the message system."""
        return self._message_system

    async def cycle(self) -> None:
        """In endless cycle get content, preprocess, send to hook, receive res, postprocess and send.

        Can be stopped by self.stop()."""
        async with self:
            while self._is_running():
                content, msg_id = await self._input_queue.get()
                content = await self.preprocess_data(content)
                await self._notify_all_hooks(content)

                result = await self._run_result_callback()
                result = await self.postprocess_result(result)
                await self._output_queue.put((result, msg_id))

    async def preprocess_data(self, content: object) -> object:
        """Preprocess data.

        Executed every time there's new info received from message system.

        Args:
            content: data, sent to provider by message system.

        Returns:
            Preprocessed data in any form.
        """
        return content

    async def postprocess_result(self, results: typing.List[object]) -> object:
        """Postprocess hooks results.

        Executed every time results from all hooks are gathered before sending to message system.

        Args:
            results: list of results from all hooks.

        Returns:
            Postprocessed results to send to message system.
        """
        return results


class MessageSystem:
    """Message system to transfer data between complex system and ComplexContentProvider.

    Each message in message system has it's own id. The id is given to message when message to
    provider is created. Later you can get provider's answer to that message by it's id.

    It is thread-safe.

    It's purpose is to transfer data between ComplexContentProvider and complex system.

    Attributes:
        _input_queue: asyncio.Queue from message system to provider.
        _output_queue: asyncio.Queue from provider to message system.
        _tmp_queue: queue.Queue object for temporal data transfer before PHFSystem starts.
        _message_id: amount of sent messages, also serves as id to next message.
        _asyncio_loop: asyncio.Loop, in which the MessageSystem works.
        _result_to_mID_mapping: dict, used to store answers to messages by their id.
        _needed_output_events: dict of threading.Event, stores events for needing answers for
        messages that hasn't been yet.
         _lock: threading.Lock for thread safe message sends.
         _task: asyncio.Task for message's system work(cycle() coroutine).
        """

    def __init__(self):
        """Construct the object.

        Almost nothing is initialized as almost all initialisations need to be done in event loop.
        """
        self._input_queue = None
        self._output_queue = None
        self._tmp_queue = queue.Queue()
        self._message_id = 0
        self._asyncio_loop = None
        self._result_to_mID_mapping = {}
        self._needed_output_events = {}
        self._lock = threading.Lock()
        self._task = None

    async def initialize(self):
        """Initialize everything when in event loop and start the message system.

        All messages that were sent to system before it are not lost.
        """
        input_queue = asyncio.Queue()
        self._output_queue = asyncio.Queue()
        self._asyncio_loop = asyncio.get_event_loop()

        with self._lock:
            while not self._tmp_queue.empty():
                msg = self._tmp_queue.get()
                input_queue.put_nowait(msg)
            self._input_queue = input_queue

        self._task = asyncio.create_task(self._serve_provider_results())
        return self._input_queue, self._output_queue

    def stop(self):
        self.__init__()

    def send_to_provider(self, data: object) -> int:
        """Send message from system to provider.

        Don't be afraid of sending messages before start of PHFSystem's work,
        the messages will be remembered anyways.

        Args:
            data: data to send to provider, any type.

        Returns:
            Message's id.
        """
        if self._input_queue is None:
            self._tmp_queue.put_nowait((data, self._message_id))
        else:
            asyncio.run_coroutine_threadsafe(self._input_queue.put((data, self._message_id)),
                                             self._asyncio_loop)
        self._message_id += 1
        return self._message_id - 1

    async def _serve_provider_results(self) -> None:
        """Serve provider results in endless cycle."""
        while True:
            result, msg_id = await self._output_queue.get()
            with self._lock:
                self._result_to_mID_mapping[msg_id] = result
                if msg_id in self._needed_output_events:
                    self._needed_output_events[msg_id].set()

    def retrieve_result(self, message_id: int) -> object:
        """Get results from ComplexContentProvider.

        Args:
            message_id: Id of message, for which answer is needed.

        Returns:
            Answer with on message message_id.
        """
        cur_event = threading.Event()

        with self._lock:
            if message_id in self._result_to_mID_mapping:
                return self._result_to_mID_mapping[message_id]

            self._needed_output_events[message_id] = cur_event
        cur_event.wait()

        del self._needed_output_events[message_id]
        return self._result_to_mID_mapping[message_id]

    def send_wait_answer(self, data: object) -> object:
        """Send message to provider and wait till result is sent back.

        Args:
            data: data to send.

        Returns:
            Result from provider.
        """
        msg_id = self.send_to_provider(data)
        return self.retrieve_result(msg_id)
