import os
import shutil
import re

def _parse_file(file_list):
    parsed_file_list = [req for req in file_list if re.search(
        r"([Rr][Jj][0-9]+)", req) is not None and req.split(".")[-1] != "jpg"]
    return parsed_file_list

def cetern_path(destination):
    if os.path.isdir(destination):
        this_dir = os.listdir(destination)
        if len(this_dir) is 0:
            print(destination + "是空的")
        elif len(this_dir) is 1:
            return cetern_path(destination + "\\" + this_dir[0])
        return destination
    print(destination + "是檔案")

req_list = _parse_file(os.listdir('.'))
for req in req_list:
    target = cetern_path(req)
    if target and target != req:
        move_files = os.listdir(target)
        for m_file in move_files:
            shutil.move(target + "\\" + m_file, req)
        os.remove(target)


