import asyncio
import copy


class AbstractContentProvider:
    _alias = []

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj.__hooks = []
        obj.__tasks = []
        obj.__queues = []
        obj._asyncio_task = None
        obj._asyncio_running = False
        return obj

    def __init__(self, *args, **kwargs):
        self.__hooks = []
        self.__tasks = []
        self.__queues = []
        self._asyncio_task = None
        self._asyncio_running = False
        pass

    def get_site(self):
        raise NotImplementedError(f"Get_site of {self.__class__} not overridden")

    async def cycle(self, period=5):
        self._asyncio_running = True
        async with self:
            while True:
                await asyncio.sleep(period)
                string = self.get_site()
                for queue in self.__queues:
                    queue.put_nowait(string)

    def _start_hook(self, hook):
        self.__queues.append(hook._AbstractHook__queue)
        self.__tasks.append(asyncio.create_task(hook.cycle_call()))

    def add_hook(self, hook):
        self.__hooks.append(hook)
        if self._asyncio_running:
            self._start_hook(hook)

    async def __aenter__(self):
        for hook in self.__hooks:
            self._start_hook(hook)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is asyncio.CancelledError:
            for hook in self.__hooks:
                hook.cancel()
            return True

    @classmethod
    def get_aliases(cls):
        return copy.deepcopy(cls._alias)
