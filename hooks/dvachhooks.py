from abstracthook import AbstractHook


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

    def hook_action(self, output):
        to_print = str(self.get_updated_text(output))
        if to_print == "[]":
            return
        print("                                                          ", end="\r")
        print("\n" + to_print)
        print("\rPress any button to add new stuff", end="\r")
