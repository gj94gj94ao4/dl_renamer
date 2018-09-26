import os
import sys
import re
import configparser

import requests
from bs4 import BeautifulSoup

DOMAIN = "http://www.dlsite.com"
_REQ_LINK = DOMAIN + "/maniax/work/=/product_id/{}.html"
RENAME_PATTERN = "[{rjnumber}][{maker_name}] {name} {genre}"


def main():
    req_list = _parse_file(os.listdir("."))
    print("識別檔案:{}\n需要創建 hard Link 分類嗎(y)?".format(req_list), end="")
    HL = input()

    for req in req_list:
        find = re.search(r"([rjRJ]{2}[0-9]+)", req)
        target = find.group(1).upper()
        print("找尋{}.....".format(target), end="")

        try:
            work = Work(target)
            # change name
            file_name = _combine_name(work)
            if not os.path.isdir(req):
                file_name += "." + req.split(".")[-1]
            jpg_name = _combine_name(work) + ".jpg"
            os.rename(req, file_name)
            print("\t完成! 更名為 {}".format(file_name))
            # download img
            print("下載{}img中...".format(target), end="")
            with requests.get(work.image_link, stream=True) as req:
                with open(jpg_name, "wb") as f:
                    for chunk in req.iter_content(chunk_size=1024):
                        f.write(chunk)
            print("\t完成")

            # hard link
            if HL == 'y':
                print("創建 hard link 連結...", end="")
                for link_target in work.get_category_list():
                    destination = "{type}{sep}".format(type=_safe_name(link_target[0]), sep=os.sep)
                    if isinstance(link_target[1], list):
                        for sub_link_target in link_target[1]:
                            sub_destination = destination + "{sub_type}{sep}".format(sub_type=_safe_name(sub_link_target), sep=os.sep)
                            os.makedirs(sub_destination, exist_ok=True)
                            os.link(jpg_name, sub_destination + jpg_name)
                            _hardlink_allow_floder(file_name, sub_destination + file_name)
                    else:
                        sub_destination = destination + "{sub_type}{sep}".format(sub_type=_safe_name(link_target[1]), sep=os.sep)
                        os.makedirs(sub_destination, exist_ok=True)
                        os.link(jpg_name, sub_destination + jpg_name)
                        _hardlink_allow_floder(file_name, sub_destination + file_name)
                print('\t完成')
                # os.link(change_name, maker_location + change_name)

        except Exception as e:
            with open("fail.txt", 'a', encoding='utf-8') as f:
                f.write("{} 失敗..".format(target))
                f.write("cause: {}\n".format(str(e)))
            print("失敗{} 原因:{}".format(target, e))
    print("等待確認~~", end="")
    input()


def fuck(work, genre=None):
    change_name = _combine_name(work)
    picture = "".join(change_name.split(".")[0::-1]) + ".jpg"
    if genre is not None:
        name = "製作"
        fuck_str = genre
    else:
        name = "分類"
        fuck_str = work.maker
    location = "{name}{sep}{fuck_str}{sep}".format(
        name=name, sep=os.sep, fuck_str=fuck_str)
    os.makedirs(location, exist_ok=True)
    os.link(picture, location + picture)
    _hardlink_allow_floder(
        change_name, location + change_name)


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
        if tag.attrs["content"] == "/images/web/home/no_img_main.gif":
            return DOMAIN + tag.attrs["content"]
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

    def get_category_list(self):
        return [
            ("種類", self.get_genre()),
            ("製作社團", self.get_maker())
        ]


# @user_interface
def loading_config():
    global RENAME_PATTERN
    config = configparser.ConfigParser()
    if os.path.isfile("config.ini"):
        try:
            config.read("config.ini", encoding='utf-8')
            RENAME_PATTERN = config["DEFAULT"]["rename_pattern"]
        except Exception:
            print("config.ini dead.  Relive it or del it.")
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


def _parse_file(file_list):
    parsed_file_list = [req for req in file_list if re.search(
        r"([Rr][Jj][0-9]+)", req) is not None and req.split(".")[-1] != "jpg"]
    return parsed_file_list


def _combine_name(work: Work):
    return _safe_name(
        RENAME_PATTERN.format(
            rjnumber=work.rjnumber,
            maker_name=work.maker,
            name=work.name,
            genre=work.genre))


def _hardlink_allow_floder(src, loc):
    if os.path.isdir(src):
        os.makedirs(loc, exist_ok=True)
        hardlink_targets = os.listdir(src)
        for hardlink_target in hardlink_targets:
            _hardlink_allow_floder(
                src + os.sep + hardlink_target, loc + os.sep + hardlink_target)
    else:
        try:
            os.link(src, loc)
        except FileExistsError:
            pass

# 這是給其他專案用的
def parse_filename_to_infodict(filename):
    pattern = re.escape(RENAME_PATTERN)\
        .replace(r"\{rjnumber\}", r"(?P<rjnumber>RJ\d+)")\
        .replace(r"\{maker_name\}", r"(?P<maker_name>.+)")\
        .replace(r"\{name\}", r"(?P<name>.+)")\
        .replace(r"\{genre\}", r"\[(?P<genre>'.+')\]")
    ret = re.search(pattern, filename)
    genre = ret.group("genre").replace("'", "").split(", ")
    rem = ret.groupdict()
    rem.update({"genre": genre})
    return rem


loading_config()
if __name__ == "__main__":
    main()
