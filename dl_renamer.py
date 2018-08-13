import os
import sys
import re

import requests
from bs4 import BeautifulSoup
from mir.dlsite import api
from mir.dlsite import workinfo


def main():
    req_list = parse_id_list(os.listdir())
    print("識別檔案:{}\n確定要執行嗎(y)?".format(req_list), end="")
    if input() != 'y':
        exit()
    print("是否下載封面圖片?(y)", end="")
    dow_img = True if str(input()) is "y" else False
    for req in req_list:
        find = re.search(r"([rjRJ]{2}[0-9]+)", req)
        target = find.group(1).upper()
        print("找尋{}...".format(target), end="")
        try:
            t_finish = api.fetch_work(target)
            t_finish.maker = _safe_name(t_finish.maker)
            t_finish.name = _safe_name(t_finish.name)
            if os.path.isdir(req):
                os.rename(req, "[{}][{}] {}".format(
                    t_finish.rjcode, t_finish.maker, t_finish.name))
            else:
                os.rename(req, "[{}][{}] {}.{}".format(
                    t_finish.rjcode, t_finish.maker, t_finish.name, req.split(".")[1]))
            print("成功~ 改名為[{}][{}] {}".format(
                t_finish.rjcode, t_finish.maker, t_finish.name))
        except Exception as e:
            print("失敗: {}".format(e))
            # download img
        try:
            if dow_img:
                img_link = get_image_link(target)
                print("下載{}img中...".format(t_finish.rjcode), end="")
                with requests.get(img_link, stream=True) as req:
                    with open("[{}][{}] {}.jpg".format(t_finish.rjcode, t_finish.maker, t_finish.name), "wb") as f:
                        for chunk in req.iter_content(chunk_size=1024):
                            f.write(chunk)
                print("完成")
        except Exception as e:
            print("失敗: {}".format(e))

    print("等待確認~~", end="")
    input()


def get_image_link(rjnumber):
    req = requests.get(
        "http://www.dlsite.com/maniax/work/=/product_id/{}.html".format(rjnumber))
    bf = BeautifulSoup(req.text, 'html.parser')
    tags = bf.find_all("meta")
    for tag in tags:
        if tag["content"] is not None:
            pre = re.escape("http://img.dlsite.jp/modpub/images2/work/doujin/")
            end = re.escape("_img_main.jpg")
            target = re.match(
                pre + r"RJ[0-9]+\/RJ[0-9]+" + end, str(tag["content"]))
            if target is not None:
                img_link = target.group(0)
    return img_link


def parse_id_list(dir_list):
    id_list = list()
    for req in dir_list:
        if re.search(r"([rjRJ]{2}[0-9]+)", req) is not None:
            if re.match(r"\[[RJrj]{2}[0-9]+\]\[.+\] .+", req.split(".")[0]) is None:
                id_list.append(req)
    return id_list


def _safe_name(name: str()):
    replacement = {"?": "(問號)", "<": "(小於)", ">": "(大於)", ":": "(冒號)",
                   "\"": "(雙引號)", "/": "(正斜線)", "\\": "(反斜線)", "|": "(管號", "*": "(星號)"}
    for old, new in replacement.items():
        name = name.replace(old, new)
    return name


main()
