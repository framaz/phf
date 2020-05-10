import asyncio
from Inputs.consoleinput import ConsoleInput, ConsoleDebugInput
from Sites.dvach import Dvach
from hooks.dvachhooks import DvachShowHook, DvachFileDownloader
from asyncparser import AsyncParser

site = Dvach("https://2ch.hk/b/res/219809995.html")
hook = DvachFileDownloader()
site.add_hook(hook)
parser = AsyncParser()
parser.add_content_provider(site)
parser.start()