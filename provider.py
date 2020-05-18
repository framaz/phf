import asyncio
import copy


class AbstractContentProvider:
    _alias = []

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._asynio_hooks = []
        obj._asyncio_tasks = []
        obj._asyncio_queues = []
        obj._asyncio_task = None
        obj._asyncio_running = False
        obj._asyncio_loop = None
        return obj

    def __init__(self, *args, **kwargs):
        self._asynio_hooks = []
        self._asyncio_tasks = []
        self._asyncio_queues = []
        self._asyncio_task = None
        self._asyncio_running = False
        pass

    async def get_content(self):
        raise NotImplementedError(f"Get_site of {self.__class__} not overridden")

    async def cycle(self):
        raise NotImplementedError(f"Cycle of {self.__class__} not overridden")

    def _start_hook(self, hook):
        self._asyncio_queues.append(hook._AbstractHook__queue)
        self._asyncio_tasks.append(asyncio.create_task(hook.cycle_call()))

    def _get_hooks(self):
        return self._asynio_hooks

    def add_hook(self, hook):
        self._asynio_hooks.append(hook)
        if self._asyncio_running:
            self._start_hook(hook)

    async def __aenter__(self):
        for hook in self._asynio_hooks:
            self._start_hook(hook)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is asyncio.CancelledError:
            for hook in self._asynio_hooks:
                hook.cancel()
            return True

    @classmethod
    def get_aliases(cls):
        return copy.deepcopy(cls._alias)


class PeriodicContentProvider(AbstractContentProvider):
    def __new__(cls, *args, **kwargs):
        obj = AbstractContentProvider.__new__(cls, *args, **kwargs)
        obj.period = 5
        return obj

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.period = 5

    async def cycle(self):
        self._asyncio_running = True
        async with self:
            while True:
                await asyncio.sleep(self.period)
                string = await self.get_content()
                for queue in self._asyncio_queues:
                    queue.put_nowait(string)
