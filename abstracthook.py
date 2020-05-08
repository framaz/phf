import asyncio


class AbstractHook:
    def __init__(self, IOLock=None, *args, **kwargs):
        self.IOLock = asyncio.Lock()
        if IOLock is not None:
            self.IOLock = IOLock
        self.queue = asyncio.Queue()
        self.initialize(*args, **kwargs)

    def initialize(self, *args, **kwargs):
        raise NotImplementedError(f"Initialise component of {self.__class__} not overridden")

    async def cycle_call(self):
        while True:
            target = await self.queue.get()
            await self.IOLock.acquire()
            self.hook_action(target)
            self.IOLock.release()
        pass

    def hook_action(self, output):
        raise NotImplementedError(f"hook_action of {self.__class__} not overridden")