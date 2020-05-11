import asyncio
from Inputs.consoleinput import ConsoleDebugInput
from Sites.dvach import Dvach
from hooks.dvachhooks import DvachShowHook, DvachFileDownloader
from asyncparser import AsyncParser
from Inputs.consoleinput import ConsoleDebugInput


parser = AsyncParser()
parser.import_hook_sources("hooks")
parser.import_provider_sources("Sites")

parser.add_input_source(ConsoleDebugInput())
parser.start()
