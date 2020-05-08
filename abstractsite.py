import asyncio


class AbstractSiteContentDownloader:
    def __init__(self, *args, **kwargs):
        self.hooks = []
        self.tasks = []
        self.queues = []
        self.initialize(*args, **kwargs)

    def initialize(self):
        raise NotImplementedError(f"Initialise of {self.__class__} not overridden")

    def get_site(self):
        raise NotImplementedError(f"Get_site of {self.__class__} not overridden")

    async def cycle(self, period=5):
        while True:
            await asyncio.sleep(period)
            str = self.get_site()
            for queue in self.queues:
                queue.put_nowait(str)

    def add_hook(self, hook):
        self.hooks.append(hook)
        self.queues.append(hook.queue)
        self.tasks.append(asyncio.create_task(hook.cycle_call()))
