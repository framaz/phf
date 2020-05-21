import tracemalloc

from abstracthook import BasicPrintHook
from asyncparser import AsyncParser
from provider import DummyBlocking

tracemalloc.start()


class Kek(DummyBlocking):
    def __init__(self):
        self.count = 1

    async def result_callback(self, results):
        print(str(results) + "azaza")


if __name__ == "__main__":
    parser = AsyncParser()
    parser.import_hook_sources("hooks")
    parser.import_provider_sources("providers")

    hook1, hook2 = BasicPrintHook(), BasicPrintHook()
    provider = Kek()
    provider.add_hook(hook1)
    provider.add_hook(hook2)
    parser.add_content_provider(provider)

    parser.start()
