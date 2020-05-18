from abstracthook import BasicPrintHook
from asyncparser import AsyncParser
from inputs.consoleinput import ConsoleDebugInput
from provider import DummyBlocking

if __name__ == "__main__":
    parser = AsyncParser()
    parser.import_hook_sources("hooks")
    parser.import_provider_sources("providers")

    hook = BasicPrintHook()
    provider = DummyBlocking()
    provider.add_hook(hook)
    parser.add_content_provider(provider)

    parser.add_input_source(ConsoleDebugInput())
    parser.start()
