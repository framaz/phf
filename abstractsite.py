import asyncio


class AbstractSiteContentDownloader:
    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj.__hooks = []
        obj.__tasks = []
        obj.__queues = []
        return obj

    def __init__(self, *args, **kwargs):
        pass

    def get_site(self):
        raise NotImplementedError(f"Get_site of {self.__class__} not overridden")

    async def cycle(self, period=5):
        while True:
            await asyncio.sleep(period)
            string = self.get_site()
            for queue in self.__queues:
                queue.put_nowait(string)

    def add_hook(self, hook):
        self.__hooks.append(hook)
        self.__queues.append(hook._AbstractHook__queue)
        self.__tasks.append(asyncio.create_task(hook.cycle_call()))

