import asyncio


class AbstractHook:
    def __new__(cls, IOLock=None, *args, **kwargs):
        obj = object.__new__(cls)
        obj.__IOLock = None
        if IOLock is not None:
            obj.__IOLock = IOLock
        obj._asyncio_queue = None
        return obj

    def __init__(self, *args, **kwargs):
        pass

    @property
    def _AbstractHook__queue(self):
        if self._asyncio_queue is None:
            self._asyncio_queue = asyncio.Queue()
        return self._asyncio_queue

    async def cycle_call(self):
        while True:
            target = await self._AbstractHook__queue.get()
            await self.hook_action(target)
        pass

    async def hook_action(self, output):
        raise NotImplementedError(f"hook_action of {self.__class__} not overridden")
