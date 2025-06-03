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

from tools.content import nga_content_convert_to_markdown
from tools.session import init_session
from tools.utils import sanitize_filename, check_folders


def first_work(tid: str):
    session = init_session()

    results = []

    response = session.get(f"https://bbs.nga.cn/read.php?tid={tid}")
    if response.status_code != 200 or "msgcodestart" in response.text:
        print(
            """访问失败，请检查:\n  1. cookie是否失效\n  2. tid是否合法\n  3. 目前只支持查看ff14板的帖子"""
        )
        return

    soup = BeautifulSoup(response.text, "lxml")
    author_uid = re.search(
        r"uid=(\d+)", soup.find("a", attrs={"id": "postauthor0"}).attrs["href"]
    ).group(1)
    title = soup.find("h3", attrs={"id": "postsubject0"}).text

    response = session.get(
        f"https://bbs.nga.cn/read.php",
        params={"tid": tid, "authorid": author_uid, "page": 114514},
    )
    soup = BeautifulSoup(response.text, "lxml")
    pagebtns = soup.find_all("a", attrs={"class": "pager_spacer"})
    maxpage = 1

    last_post_time = "1970-01-01 08:00"

    if pagebtns:
        for i in pagebtns:
            if "上一页" in i.text:
                maxpage = int(re.search(r"上一页\((\d+)\)", i.text).group(1)) + 1
                break

    print(f"Title: {title}")
    print(f"Get {maxpage} pages of contents (author-only)")

    for page in range(1, maxpage + 1):
        params = {"tid": tid, "authorid": author_uid}
        if page > 1:
            params["page"] = page
        print(f"Crawling page {page} of tid {tid}...")

        response = session.get("https://bbs.nga.cn/read.php", params=params)
        soup = BeautifulSoup(response.text, "lxml")

        items = soup.find_all("table", attrs={"class": "forumbox postbox"})

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

            pid = re.search(
                r"pid(\d+)Anchor",
                i.find_all("a", attrs={"name": re.compile(r"^l\d+$")})[
                    0
                ].previous.attrs["id"],
            ).group(1)

            post_time = i.find(
                "span", attrs={"id": re.compile(r"^postdate")}).text
            last_post_time = post_time

            joined_content = ""

            for s in post_content.contents:
                if isinstance(s, bs4.element.NavigableString):
                    joined_content += str(s)
                elif s.name == "br":
                    joined_content += "\n"

            content_s = nga_content_convert_to_markdown(
                joined_content, int(post_uid), int(tid), int(pid)
            )

            results.append(content_s)

        time.sleep(random.uniform(1.0, 2.0))
        page += 1

    print("Saving files...")
    with open(
        os.path.join(os.getcwd(), "data", f"{sanitize_filename(title,'')}.md"),
        "w",
        encoding="utf8",
    ) as f:
        f.write("\n\n------\n\n".join(results))
    print(f"Last update time of post {tid}: {last_post_time}")
    with open(os.path.join(os.getcwd(), "data", tid), "wb") as f:
        pickle.dump(datetime.datetime.strptime(
            last_post_time, "%Y-%m-%d %H:%M"), f)
    print("Done!")


def regain_work(tid: str):
    session = init_session()

    results = []

    response = session.get(f"https://bbs.nga.cn/read.php?tid={tid}")
    if response.status_code != 200 or "msgcodestart" in response.text:
        print(
            """访问失败，请检查:\n  1. cookie是否失效\n  2. tid是否合法\n  3. 目前只支持查看ff14板的帖子"""
        )
        return

    soup = BeautifulSoup(response.text, "lxml")
    author_uid = re.search(
        r"uid=(\d+)", soup.find("a", attrs={"id": "postauthor0"}).attrs["href"]
    ).group(1)
    title = soup.find("h3", attrs={"id": "postsubject0"}).text

    response = session.get(
        f"https://bbs.nga.cn/read.php",
        params={"tid": tid, "authorid": author_uid, "page": 114514},
    )
    soup = BeautifulSoup(response.text, "lxml")
    pagebtns = soup.find_all("a", attrs={"class": "pager_spacer"})
    maxpage = 1

    last_post_time = "1970-01-01 08:00"
    with open(os.path.join(os.getcwd(), "data", tid), "rb") as f:
        last_post_time = pickle.load(f).strftime("%Y-%m-%d %H:%M")
    if pagebtns:
        for i in pagebtns:
            if "上一页" in i.text:
                maxpage = int(re.search(r"上一页\((\d+)\)", i.text).group(1)) + 1
                break

    printed_update_message = False

    print(f"Title: {title}")
    print(f"Get {maxpage} pages of contents (author-only)")

    for page in range(maxpage, 0, -1):
        flag = False
        params = {"tid": tid, "authorid": author_uid}
        if page > 1:
            params["page"] = page
        print(f"Crawling page {page} of tid {tid}...")

        response = session.get("https://bbs.nga.cn/read.php", params=params)
        soup = BeautifulSoup(response.text, "lxml")

        items = soup.find_all("table", attrs={"class": "forumbox postbox"})

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

            pid = re.search(
                r"pid(\d+)Anchor",
                i.find_all("a", attrs={"name": re.compile(r"^l\d+$")})[
                    0
                ].previous.attrs["id"],
            ).group(1)

            post_time = i.find(
                "span", attrs={"id": re.compile(r"^postdate")}).text
            if datetime.datetime.strptime(
                post_time, "%Y-%m-%d %H:%M"
            ) <= datetime.datetime.strptime(last_post_time, "%Y-%m-%d %H:%M"):
                flag = True
                break
            else:
                if not printed_update_message:
                    printed_update_message = True
                    print("Detected update from last save time!")

            joined_content = ""

            for s in post_content.contents:
                if isinstance(s, bs4.element.NavigableString):
                    joined_content += str(s)
                elif s.name == "br":
                    joined_content += "\n"

            content_s = nga_content_convert_to_markdown(
                joined_content, int(post_uid), int(tid), int(pid)
            )

            results.append(content_s)

        if flag:
            break

        time.sleep(random.uniform(1.0, 2.0))
        page += 1

    if not printed_update_message:
        print("Not detected updates, program will exit.")
        sys.exit(0)

    print("Saving files...")
    with open(
        os.path.join(os.getcwd(), "data", f"{sanitize_filename(title,'')}.md"),
        "a",
        encoding="utf8",
    ) as f:
        f.write("\n\n------\n\n".join(reversed(results)))
    print(f"Last update time of post {tid}: {last_post_time}")
    with open(os.path.join(os.getcwd(), "data", tid), "wb") as f:
        pickle.dump(datetime.datetime.strptime(
            last_post_time, "%Y-%m-%d %H:%M"), f)
    print("Done!")


def main():
    check_folders()
    tid = input("Enter tid: ")
    # uid = input(
    #     "Enter the uid of author (or the user you want); leave blank to automatically get the author's uid; enter 'all' to get everyone's reply."
    # )
    if not os.path.exists(os.path.join(os.getcwd(), "data", tid)):
        first_work(tid)
    else:
        regain_work(tid)


if __name__ == "__main__":
    main()
