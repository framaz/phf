import threading
import time
import tracemalloc

from abstracthook import BasicPrintHook
from phfsystem import PHFSystem
from provider import ComplexContentProvider

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
    phfsys = PHFSystem()
    phfsys.import_hook_sources("hooks")
    phfsys.import_provider_sources("providers")

    hook1, hook2 = BasicPrintHook(), BasicPrintHook()
    provider = ComplexContentProvider()
    message_sys = provider.get_message_system()
    threading.Thread(target=_thread_func, args=[message_sys]).start()
    provider.add_hook(hook1)
    provider.add_hook(hook2)
    phfsys.add_content_provider(provider)
    phfsys.start()
