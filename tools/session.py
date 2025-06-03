import requests
import sys

from tools.default_http_headers import default_http_headers


def init_session():
    session = requests.Session()
    session.headers.update(default_http_headers)
    session.headers["referer"] = "https://bbs.nga.cn/thread.php?fid=-362960"
    try:
        with open("cookie_file.txt", "r") as f:
            ck = f.read().strip()
            session.headers["cookie"] = ck
    except:
        print("未找到cookie_file文件！将退出运行")
        sys.exit(1)

    return session
