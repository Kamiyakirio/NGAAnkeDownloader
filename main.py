import requests
import re
import random
import time
import datetime
import pickle
import os
import sys
from bs4 import BeautifulSoup
import bs4.element
from typing import List, Tuple, Optional

from tools.content import nga_content_convert_to_markdown, extract_user_info
from tools.session import init_session
from tools.utils import sanitize_filename, check_folders, check_user_type_uid


def get_author_info(session: requests.Session, tid: str) -> Tuple[str, str]:
    """获取作者信息和帖子标题"""
    response = session.get(f"https://bbs.nga.cn/read.php?tid={tid}")
    if response.status_code != 200 or "msgcodestart" in response.text:
        print(
            """访问失败，请检查:\n  1. cookie是否失效\n  2. tid是否合法\n  3. 目前只支持查看ff14板的帖子"""
        )
        sys.exit(0)

    soup = BeautifulSoup(response.text, "lxml")
    author_uid = re.search(
        r"uid=(\d+)", soup.find("a", attrs={"id": "postauthor0"}).attrs["href"]
    ).group(1)
    title = soup.find("h3", attrs={"id": "postsubject0"}).text
    return author_uid, title


def get_max_page(
    session: requests.Session, tid: str, target_uid: Optional[str] = None
) -> int:
    """获取最大页数"""
    params = {"tid": tid, "page": 114514}
    if target_uid and target_uid != "all":
        params["authorid"] = target_uid
    response = session.get("https://bbs.nga.cn/read.php", params=params)
    soup = BeautifulSoup(response.text, "lxml")
    pagebtns = soup.find_all("a", attrs={"class": "pager_spacer"})
    maxpage = 1

    if pagebtns:
        for i in pagebtns:
            if "上一页" in i.text:
                maxpage = int(re.search(r"上一页\((\d+)\)", i.text).group(1)) + 1
                break
    return maxpage


def parse_post_content(
    post_content: bs4.element.Tag, post_uid: str, tid: str, pid: str
) -> str:
    """解析帖子内容"""
    joined_content = ""

    for s in post_content.contents:
        if isinstance(s, bs4.element.NavigableString):
            joined_content += str(s).replace("*", "\*").replace("_", "\_")
        elif s.name == "br":
            joined_content += "\n"

    return nga_content_convert_to_markdown(
        joined_content, int(post_uid), int(tid), int(pid)
    )


def crawl_page(
    session: requests.Session, tid: str, target_uid: Optional[str], page: int
) -> List[Tuple[str, str, str]]:
    """爬取单页内容"""
    params = {"tid": tid}
    if target_uid and target_uid != "all":
        params["authorid"] = target_uid
    if page > 1:
        params["page"] = page
    print(f"Crawling page {page} of tid {tid}...")

    response = session.get("https://bbs.nga.cn/read.php", params=params)
    soup = BeautifulSoup(response.text, "lxml")
    items = soup.find_all("table", attrs={"class": "forumbox postbox"})
    userinfo_dict = extract_user_info(response.text)
    results = []

    for i in items:
        post_content = i.find(
            attrs={
                "id": re.compile(r"^postcontent"),
                "class": "postcontent ubbcode",
            }
        )

        post_uid = "-1"
        match_postuid = re.search(
            r"uid=(\d+)", i.find(attrs={"class": "author b"}).attrs["href"]
        )
        if match_postuid:
            post_uid = match_postuid.group(1)

        if target_uid and target_uid != "all" and post_uid != target_uid:
            continue

        pid = re.search(
            r"pid(\d+)Anchor",
            i.find_all("a", attrs={"name": re.compile(r"^l\d+$")})[0].previous.attrs[
                "id"
            ],
        ).group(1)

        post_time = i.find("span", attrs={"id": re.compile(r"^postdate")}).text
        content = parse_post_content(post_content, post_uid, tid, pid)

        username = ""
        if target_uid == "all" and post_uid in userinfo_dict:
            username = f"【{userinfo_dict[post_uid]['username']}】\n"

        results.append((post_time, username + content, post_uid))

    return results


def save_results(
    title: str,
    results: List[str],
    tid: str,
    last_post_time: str,
    target_uid: str,
    mode: str = "w",
):
    """保存结果到文件"""
    print("Saving files...")
    with open(
        os.path.join(os.getcwd(), "data", f"{sanitize_filename(title,'')}.md"),
        mode,
        encoding="utf8",
    ) as f:
        f.write("\n\n------\n\n".join(results))
    print(f"Last update time of post {tid}: {last_post_time}")
    print("")
    with open(os.path.join(os.getcwd(), "data", tid), "wb") as f:
        pickle.dump(
            (datetime.datetime.strptime(last_post_time, "%Y-%m-%d %H:%M"), target_uid),
            f,
        )
    print("Done!")


def first_work(tid: str, target_uid: Optional[str] = None):
    session = init_session()
    author_uid, title = get_author_info(session, tid)
    if not target_uid:
        target_uid = author_uid
    maxpage = get_max_page(session, tid, target_uid)

    print(f"Title: {title}")
    print(f"Get {maxpage} pages of contents")

    all_results = []
    for page in range(1, maxpage + 1):
        page_results = crawl_page(session, tid, target_uid, page)
        all_results.extend([content for _, content, _ in page_results])
        time.sleep(random.uniform(1.0, 2.0))

    save_results(
        title,
        all_results,
        tid,
        page_results[-1][0] if page_results else "1970-01-01 08:00",
        target_uid,
    )


def regain_work(tid: str, target_uid: Optional[str] = None):
    session = init_session()
    author_uid, title = get_author_info(session, tid)
    if not target_uid:
        target_uid = author_uid
    maxpage = get_max_page(session, tid, target_uid)

    last_post_time = "1970-01-01 08:00"
    saved_target_uid = None
    with open(os.path.join(os.getcwd(), "data", tid), "rb") as f:
        last_post_time, saved_target_uid = pickle.load(f)
        last_post_time = last_post_time.strftime("%Y-%m-%d %H:%M")

    if saved_target_uid != target_uid:
        print(
            f"Warning: current input uid ({target_uid}) is different from the saved uid ({saved_target_uid}) and we need to get all contents again."
        )
        print("Do continue? (y/n)")
        if input() == "y":
            first_work(tid, target_uid)
            return
        else:
            sys.exit(0)

    print(f"Title: {title}")
    print(f"Get {maxpage} pages of contents")

    all_results = []
    printed_update_message = False

    for page in range(maxpage, 0, -1):
        page_results = crawl_page(session, tid, target_uid, page)
        found_old_post = False

        for post_time, content, _ in page_results:
            if datetime.datetime.strptime(
                post_time, "%Y-%m-%d %H:%M"
            ) <= datetime.datetime.strptime(last_post_time, "%Y-%m-%d %H:%M"):
                found_old_post = True
                break
            else:
                if not printed_update_message:
                    printed_update_message = True
                    print("Detected update from last save time!")
                all_results.append(content)

        if found_old_post:
            break

        time.sleep(random.uniform(1.0, 2.0))

    if not printed_update_message:
        print("Not detecting any updates, program will exit.")
        sys.exit(0)

    save_results(
        title, list(reversed(all_results)), tid, last_post_time, target_uid, "a"
    )


def main():
    check_folders()
    tid = input("Enter tid: ")
    target_uid = "PLACEHOLDER"
    while not check_user_type_uid(target_uid):
        target_uid = input(
            "Enter target uid (press Enter for author, 'all' for all replies): "
        ).strip()
    if not target_uid:
        target_uid = None
    if not os.path.exists(os.path.join(os.getcwd(), "data", tid)):
        first_work(tid, target_uid)
    else:
        regain_work(tid, target_uid)


if __name__ == "__main__":
    main()
