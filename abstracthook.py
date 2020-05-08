import asyncio


class AbstractHook:
    def __new__(cls, IOLock=None, *args, **kwargs):
        obj = object.__new__(cls)
        obj.__IOLock = asyncio.Lock()
        obj.__IOLock = IOLock
        obj.__queue = asyncio.Queue()
        return obj

    def __init__(self, *args, **kwargs):
        pass

    def initialize(self, *args, **kwargs):
        raise NotImplementedError(f"Initialise component of {self.__class__} not overridden")

    async def cycle_call(self):
        while True:
            target = await self.__queue.get()
            await self.__IOLock.acquire()
            self.hook_action(target)
            self.__IOLock.release()
        pass

    def hook_action(self, output):
        raise NotImplementedError(f"hook_action of {self.__class__} not overridden")