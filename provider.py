import asyncio
import copy
import queue
import threading
import time
from abc import ABC


class AbstractContentProvider:
    _alias = []

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._asynio_hooks = []
        obj._asyncio_tasks = []
        obj._asyncio_queues = []
        obj._asyncio_callback_queues = []
        obj._asyncio_task = None
        obj._asyncio_running = False
        obj._asyncio_loop = None
        obj._is_with_callback = False
        if AbstractContentProvider.result_callback != cls.result_callback:
            obj._is_with_callback = True
        return obj

    def __init__(self, *args, **kwargs):
        self._asynio_hooks = []
        self._asyncio_tasks = []
        self._asyncio_queues = []
        self._asyncio_callback_queues = []
        self._asyncio_task = None
        self._asyncio_running = False
        self._asyncio_loop = None
        self._is_with_callback = False
        if AbstractContentProvider.result_callback != self.__class__.result_callback:
            self._is_with_callback = True

    async def get_content(self):
        raise NotImplementedError(f"Get_site of {self.__class__} not overridden")

    async def cycle(self):
        raise NotImplementedError(f"Cycle of {self.__class__} not overridden")

    async def result_callback(self, results):
        pass

    async def _run_result_callback(self):
        if self._is_with_callback:
            results = await asyncio.gather(*[queue.get() for queue in self._asyncio_callback_queues])
            return results
        else:
            for queue in self._asyncio_callback_queues:
                while not queue.empty():
                    await queue.get()

    def _start_hook(self, hook):
        self._asyncio_queues.append(hook.get_straight_queue())
        self._asyncio_callback_queues.append(hook.get_callback_queue())
        self._asyncio_tasks.append(asyncio.create_task(hook.cycle_call()))

    def _get_hooks(self):
        return self._asynio_hooks

    def add_hook(self, hook):
        self._asynio_hooks.append(hook)
        if self._asyncio_running:
            self._start_hook(hook)

    async def __aenter__(self):
        self._asyncio_loop = asyncio.get_event_loop()
        self._asyncio_running = True
        for hook in self._asynio_hooks:
            self._start_hook(hook)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._asyncio_running = False
        if exc_type is asyncio.CancelledError:
            for hook in self._asynio_hooks:
                hook.cancel()
            return True

    @classmethod
    def get_aliases(cls):
        return copy.deepcopy(cls._alias)

    async def _notify_all_hooks(self, string):
        for queue in self._asyncio_queues:
            queue.put_nowait(string)


class PeriodicContentProvider(AbstractContentProvider, ABC):
    def __new__(cls, *args, **kwargs):
        obj = AbstractContentProvider.__new__(cls, *args, **kwargs)
        obj.period = 5
        return obj

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.period = 5

    async def cycle(self):
        async with self:
            while True:
                await asyncio.sleep(self.period)
                string = await self.get_content()
                await self._notify_all_hooks(string)
                result = await self._run_result_callback()
                await self.result_callback(result)


class BlockingContentProvider(AbstractContentProvider, ABC):
    def __new__(cls, *args, **kwargs):
        obj = AbstractContentProvider.__new__(cls, *args, **kwargs)
        obj._content_queue = asyncio.Queue()
        return obj

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content_queue = asyncio.Queue()

    def _thread_func(self):
        async def _coro():
            while self._asyncio_running:
                content = await self.get_content()
                asyncio.run_coroutine_threadsafe(self._content_queue.put(content), self._asyncio_loop)
                res = asyncio.run_coroutine_threadsafe(self._run_result_callback(), self._asyncio_loop).result()
                await self.result_callback(res)

        asyncio.run(_coro())

    async def __aenter__(self):
        kek = await super().__aenter__()
        self._content_queue = asyncio.Queue()
        return kek

    async def cycle(self):
        async with self:
            threading.Thread(target=self._thread_func).start()
            while True:
                string = await self._content_queue.get()
                await self._notify_all_hooks(string)


class ComplexDataProvider(AbstractContentProvider):
    def __new__(cls, *args, **kwargs):
        obj = PeriodicContentProvider.__new__(cls, *args, **kwargs)
        obj._input_queue = None
        obj._output_queue = None
        obj._message_system = MessageSystem()

        return obj

    async def __aenter__(self):
        kek = await super().__aenter__()
        self._input_queue, self._output_queue = await self._message_system.initialize()
        return kek

    def get_message_system(self):
        return self._message_system

    async def cycle(self):
        async with self:
            while True:
                content, msg_id = await ComplexDataProvider.get_content(self)
                await self._notify_all_hooks(content)
                result = await self._run_result_callback()
                await ComplexDataProvider.result_callback(self, (result, msg_id))

    async def get_content(self):
        return await self._input_queue.get()

    async def result_callback(self, results):
        await self._output_queue.put(results)


class MessageSystem:
    def __init__(self):
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
        input_queue = asyncio.Queue()
        self._output_queue = asyncio.Queue()
        self._asyncio_loop = asyncio.get_event_loop()
        with self._lock:
            while not self._tmp_queue.empty():
                msg = self._tmp_queue.get()
                input_queue.put_nowait(msg)
            self._input_queue = input_queue
        self._task = asyncio.create_task(self.cycle())
        return self._input_queue, self._output_queue

    def send_to_provider(self, message):
        if self._input_queue is None:
            self._tmp_queue.put_nowait((message, self._message_id))
        else:
            asyncio.run_coroutine_threadsafe(self._input_queue.put((message, self._message_id)),
                                             self._asyncio_loop)
        self._message_id += 1
        return self._message_id - 1

    async def cycle(self):
        while True:
            result, msg_id = await self._output_queue.get()
            with self._lock:
                self._result_to_mID_mapping[msg_id] = result
                if msg_id in self._needed_output_events:
                    self._needed_output_events[msg_id].set()

    def retrieve_result(self, message_id):
        cur_event = threading.Event()
        with self._lock:
            if message_id in self._result_to_mID_mapping:
                return self._result_to_mID_mapping[message_id]
            self._needed_output_events[message_id] = cur_event
        cur_event.wait()
        del self._needed_output_events[message_id]
        return self._result_to_mID_mapping[message_id]


class DummyBlocking(BlockingContentProvider):
    async def get_content(self):
        time.sleep(5)
        return "keki"
