import os
import sys
import re
import configparser

import requests
from bs4 import BeautifulSoup

_REQ_LINK = "http://www.dlsite.com/maniax/work/=/product_id/{}.html"
RENAME_PATTERN = "[{rjnumber}][{maker_name}] {name} {genre}"


def main():
    req_list = [req for req in os.listdir(".") if re.search(
        r"([Rr][Jj][0-9]+)", req) is not None]
    print("識別檔案:{}\n確定要執行嗎(y)?".format(req_list), end="")
    if input() != 'y':
        return
    
    for req in req_list:
        find = re.search(r"([rjRJ]{2}[0-9]+)", req)
        target = find.group(1).upper()
        print("找尋{}...".format(target), end="")
        
        try:
            work = Work(target)
            # change name
            if os.path.isdir(req):
                change_name = _combine_name(work)
            else:
                change_name = _combine_name(work) + "." + req.split(".")[-1]
            os.rename(req, change_name)
            print("成功! 更名為 {}".format(change_name))
            # download img
            print("下載{}img中...".format(target), end="")
            with requests.get(work.image_link, stream=True) as req:
                with open(_combine_name(work) + ".jpg", "wb") as f:
                    for chunk in req.iter_content(chunk_size=1024):
                        f.write(chunk)
            print("完成")
        except Exception as e:
            print("失敗{} 原因:{}".format(target, e))
    print("等待確認~~", end="")
    input()


class Work():
    def __init__(self, rjnumber):
        req = requests.get(_REQ_LINK.format(rjnumber))
        self.rjnumber = rjnumber
        self.bf = BeautifulSoup(req.text, 'html.parser')
        self.image_link = self.get_image_link()
        self.maker = self.get_maker()
        self.genre = self.get_genre()
        self.name = self.get_name()

    def get_image_link(self):
        tag = self.bf.find("meta", {"name": "twitter:image:src"})
        return tag.attrs["content"]

    def get_maker(self):
        tag = self.bf.find("span", {"class": "maker_name"}).find("a")
        return tag.text

    def get_genre(self):
        tags = self.bf.findAll("div", {"class": "main_genre"})
        genre = [a.text for a in tags[0].contents]
        return genre

    def get_name(self):
        tag = self.bf.find("h1", {"id": "work_name"}).find("a")
        return tag.text

    def get_rjnumber(self):
        return self.rjnumber


# @user_interface
def loading_config():
    global RENAME_PATTERN
    config = configparser.ConfigParser()
    if os.path.isfile("config.ini"):
        config.read("config.ini", encoding='utf-8')
        RENAME_PATTERN = config["DEFAULT"]["rename_pattern"]
    else:
        config["DEFAULT"] = {"rename_pattern": RENAME_PATTERN}
        with open("config.ini", 'w', encoding='utf-8') as configfile:
            configfile.write(
                "# rjnumber: RJ號的位置\n# maker_name: 製作社團\n# name: 品名\n# genre: 種類標籤\n# 可以自定義要甚麼位置喔~~\n# example:\n# rename_pattern = {maker_name}_{rjnumber} {name}\n")
            config.write(configfile)
        print("config.ini Not Found.  Creating new one....")


def _safe_name(name: str()):
    replacement = {"?": "(問號)", "<": "(小於)", ">": "(大於)", ":": "(冒號)",
                   "\"": "(雙引號)", "/": "(正斜線)", "\\": "(反斜線)", "|": "(管號)", "*": "(星號)"}
    for old, new in replacement.items():
        name = name.replace(old, new)
    return name


def _combine_name(work: Work):
    return _safe_name(
        RENAME_PATTERN.format(
            rjnumber=work.rjnumber,
            maker_name=work.maker,
            name=work.name,
            genre=work.genre))

loading_config()
main()