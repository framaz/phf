import json
import re

import requests


class Dvach:
    def __init__(self, link):
        res = re.search(r"2ch\.(hk|pm|re|tf|wf|yt)\/[a-zA-Z0-9]+\/res\/[0-9]+", link)
        self.link = "https://" + res[0] + ".json"
        self.site = "Dvach"
        formatted_json = self._get_json_data()
        self.board = r"/" + formatted_json["Board"] + r"/"
        self.thread_num = formatted_json["current_thread"]
        self.last_posts = set()

    def _get_content(self):
        r = requests.get(self.link)
        return r.text

    def _get_json_data(self):
        unformatted_json = self._get_content()
        formatted_json = json.loads(unformatted_json)
        return formatted_json

    @staticmethod
    def _decode_post(post_string):
        res = re.sub(r'<a [a-zA-Z0-9="\/.# ->]*(>>[0-9]+( \(OP\))?)<\/a>', r'\1', post_string)
        res = re.sub(r"<br>", "\n", res)
        return res

    @staticmethod
    def _full_post_to_short_form(post_json):
        short_post = dict()
        short_post["date"] = post_json["date"]
        short_post["num"] = post_json["num"]
        short_post["comment"] = Dvach._decode_post(post_json["comment"])
        return short_post

    def _get_posts(self):
        formatted_json = self._get_json_data()
        posts = formatted_json["threads"][0]['posts']
        res = []
        for post in posts:
            res.append(Dvach._full_post_to_short_form(post))
        return res

    def get_updated_text(self):
        posts = self._get_posts()
        res = []
        for post in posts:
            if post['num'] not in self.last_posts:
                self.last_posts.add(post['num'])
                res.append(post)
        return res