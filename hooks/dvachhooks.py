import time

from abstracthook import AbstractHook
from unils import download_files


class DvachShowHook(AbstractHook):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_posts = set()

    def get_updated_text(self, posts):
        res = []
        for post in posts:
            if post['num'] not in self.last_posts:
                self.last_posts.add(post['num'])
                res.append(post)
        return res

    async def hook_action(self, output):
        to_print = str(self.get_updated_text(output))
        if to_print == "[]":
            return
        print("                                                          ", end="\r")
        print("\n" + to_print)
        print("\rPress any button to add new stuff", end="\r")


class DvachFileDownloader(DvachShowHook):
    async def hook_action(self, output):
        posts = self.get_updated_text(output)
        download_list = []
        for post in posts:
            for file in post["files"]:
                download_path = "2ch.hk" + file["path"]
                download_to = download_path.split("/")
                download_to = "downloads/" + download_to[3] + "/" + file["fullname"]
                download_list.append((download_path, download_to))
        if len(download_list) == 0:
            return
        await download_files(download_list)
