import threading
import time
import tracemalloc

from abstracthook import BasicPrintHook
from asyncparser import AsyncParser
from provider import ComplexDataProvider

tracemalloc.start()


def _thread_func(message_sys):
    kek = 0
    id = message_sys.send_to_provider(kek)
    while True:
        kek += 1
        time.sleep(1)
        print(f"send {kek}")
        res = message_sys.send_wait_answer(kek)
        print(f"got {res}")


if __name__ == "__main__":
    parser = AsyncParser()
    parser.import_hook_sources("hooks")
    parser.import_provider_sources("providers")

    hook1, hook2 = BasicPrintHook(), BasicPrintHook()
    provider = ComplexDataProvider()
    message_sys = provider.get_message_system()
    threading.Thread(target=_thread_func, args=[message_sys]).start()
    provider.add_hook(hook1)
    provider.add_hook(hook2)
    parser.add_content_provider(provider)
    parser.start()
