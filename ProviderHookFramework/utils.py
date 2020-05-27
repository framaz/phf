import asyncio
from pathlib import Path

import aiofiles
import aiohttp


async def download_one_file(site, path, session, semaphore):
    await semaphore.acquire()
    async with session.get(site) as resp:
        if resp.status == 200:
            start_path = path
            i = 1
            while Path(path).exists():
                dot_pos = start_path.rindex(".")
                path = start_path[:dot_pos] + f"({i})" + start_path[dot_pos:]
                i += 1
            try:
                f = await aiofiles.open(path, mode='wb')
            except FileNotFoundError:
                import os
                dirs = path.split("/")
                dirs = "/".join(dirs[:-1])
                os.makedirs(dirs)
                f = await aiofiles.open(path, mode='wb')
            await f.write(await resp.read())
            await f.close()
    semaphore.release()
    return


async def download_files(site_paths, file_paths=None, max_objects_at_once=5):
    if file_paths is None:
        file_paths = list(map(lambda x: x[1], site_paths))
        site_paths = list(map(lambda x: x[0], site_paths))
    all_downloads = []
    semaphore = asyncio.Semaphore(value=max_objects_at_once)
    async with aiohttp.ClientSession() as session:
        for site, path in zip(site_paths, file_paths):
            if site.find(r"https://") == -1 and site.find(r"http://"):
                site = r"https://" + site
            cur_coru = download_one_file(site, path, session, semaphore)
            all_downloads.append(cur_coru)
        await asyncio.gather(*all_downloads)


if __name__ == "__main__":
    async def test():
        async with aiohttp.ClientSession() as session:
            await download_files(["http://2ch.hk/po/src/37636569/15889617915020.png",
                                  "http://2ch.hk/po/src/37636569/15889618552310.jpg"],
                                 ["downloads/azaza/kek.png", "downloads/azaza/keks.png"])


    asyncio.run(test())
