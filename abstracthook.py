import asyncio
import copy


class AbstractHook:
    _alias = []

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._asyncio_queue = None
        obj._callback_queue = None
        obj._provider = None
        return obj

    def __init__(self, *args, **kwargs):
        pass

    def get_straight_queue(self):
        if self._asyncio_queue is None:
            self._asyncio_queue = asyncio.Queue()
        return self._asyncio_queue

    def get_callback_queue(self):
        if self._callback_queue is None:
            self._callback_queue = asyncio.Queue()
        return self._callback_queue

    async def cycle_call(self):
        while True:
            target = await self.get_straight_queue().get()
            result = await self.hook_action(target)
            self.get_callback_queue().put_nowait(result)
        pass

    async def hook_action(self, output):
        raise NotImplementedError(f"hook_action of {self.__class__} not overridden")

    @classmethod
    def get_aliases(cls):
        return copy.deepcopy(cls._alias)


class BasicPrintHook(AbstractHook):
    async def hook_action(self, output):
        print(output)
        return output
