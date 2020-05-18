from asyncparser import AsyncParser
from inputs.consoleinput import ConsoleDebugInput

if __name__ == "__main__":
    parser = AsyncParser()
    parser.import_hook_sources("hooks")
    parser.import_provider_sources("providers")

    parser.add_input_source(ConsoleDebugInput())
    parser.start()
