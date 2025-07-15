#!/usr/bin/env python3
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

__license__ = "GPL v3"
__copyright__ = "2014, Rex<talebook@foxmail.com>"
__docformat__ = "restructuredtext en"

import datetime
import json
import logging
import re
import sys
from gettext import gettext as _

import requests

CHROME_HEADERS = {
    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.6",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)"
    + "Chrome/66.0.3359.139 Safari/537.36",
}

KEY = "douban"
REMOVES = [
    re.compile(r"^\([^)]*\)\s*"),
    re.compile(r"^\[[^\]]*\]\s*"),
    re.compile(r"^【[^】]*】\s*"),
    re.compile(r"^（[^）]*）\s*"),
]


def str2date(s):
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", _("%Y年"), _("%Y年%m月"), _("%Y年%m月%d日"), "%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).replace(tzinfo=datetime.timezone.utc)
        except:
            continue
    return None


class DoubanBookApi(object):
    def __init__(self, apikey, baseUrl, copy_image=True, manual_select=False, maxCount=2):
        self.apikey = apikey
        self.baseUrl = baseUrl
        self.maxCount = maxCount
        self.copy_image = copy_image
        self.manual_select = manual_select

    def author(self, book):
        author = book["author"]
        if not author:
            return None
        if isinstance(author, list):
            return author[0]
        return author

    def request(self, url, params={}):
        if self.apikey:
            params["apikey"] = self.apikey

        try:
            rsp = requests.get(url, timeout=10, headers=CHROME_HEADERS, params=params)
        except Exception as e:
            logging.error("豆瓣接口异常1: request fail, err=%s", str(e))
            return None

        if rsp.status_code != 200:
            logging.error("豆瓣接口异常2: status_code[%s] != 200 OK", rsp.status_code)
            return None
        else:  # 新增调试日志
            logging.debug("豆瓣接口请求成功: url=%s params=%s", url, params)

        try:
            data = rsp.json()
        except json.JSONDecodeError:
            logging.error("豆瓣接口异常3: json decode fail, content:\n%s", rsp.content)
            return None

        if "code" in data and data["code"] != 0:
            logging.error("豆瓣接口异常4: code=%d, msg=%s", rsp["code"], rsp["msg"])
            return None

        # 使用 %r 格式化字符串，以显示原始数据
        logging.debug("豆瓣接口返回数据: %r", data)
        return data

    def get_book_by_isbn(self, isbn):
        logging.debug("搜索ISBN开始: isbn=%s", isbn)
        if not isbn or '00000000' in isbn:
            logging.debug("isbn异常")
            return None
        url = "%s/v2/book/isbn/%s" % (self.baseUrl, isbn)
        logging.debug("正在请求豆瓣API: %s", url)
        return self.request(url)

    def get_book_by_id(self, id):
        logging.debug("搜索id开始: id=%s", id)
        url = "%s/v2/book/%s" % (self.baseUrl, id)
        logging.debug("正在请求豆瓣API: %s", url)
        return self.request(url)

    def search_books(self, title, author=None):
        logging.debug("搜索title开始: title=%s", title)
        url = "%s/v2/book/search" % self.baseUrl
        q = (title + " " + author) if author else title
        args = {"q": q.encode("UTF-8"), "count": self.maxCount}
        logging.debug("正在请求豆瓣API: %s", url)
        r = self.request(url, params=args)
        return r["books"] if r else None

    def get_book_by_title(self, title, author=None):
        books = self.search_books(title, author)
        if not books:
            return None
        for b in books:
            if not b["author"]:
                b["author"] = b["translator"]
            if b["title"] != title and b["title"] + ":" + b["subtitle"] != title:
                continue
            if not author or self.author(b) == author:
                return b
        return None

    def get_book(self, md):
        logging.debug("get_book 66666")
        return self.get_metadata(md)

    def get_book_detail(self, md):
        logging.debug("get_book_detail function::%r", md)
        #拿到书籍信息，又找到douban_id，再调用get_book_by_id获取书籍信息，最后返回元数据
        # 这里的md是一个元数据对象，包含了书籍的信息，比如title, author, isbn, douban_id等
        # 字典结构体，转化格式
        douban_id = md['id'] if isinstance(md, dict) else md.douban_id
        logging.debug("get_book_detail function::%s", douban_id)
        info = self.get_book_by_id(douban_id)
        return self._metadata(info, 'get_book_detail')

    def get_metadata(self, md):
        logging.debug("开始获取元数据，豆瓣ID=%s，ISBN=%s", md.douban_id, md.isbn)
        book = None
        # if md.douban_id:
        #     book = self.get_book_by_id(md.douban_id)
        # elif md.isbn:
        #     book = self.get_book_by_isbn(md.isbn)
        # if not book:
        #     book = self.get_book_by_title(md.title, md.author_sort)
        
        # if not book:
        #     return None
        # return self._metadata(book)

        # 优先使用豆瓣ID获取
        if md.douban_id:
            if book := self.get_book_by_id(md.douban_id):
                logging.debug("通过豆瓣ID获取到数据")
                return self._metadata(book, 'get_book_by_id')
        
        # 其次尝试ISBN查询
        if md.isbn and '00000000' not in md.isbn:
            if book := self.get_book_by_isbn(md.isbn):
                logging.debug("通过ISBN获取到数据")
                return self._metadata(book, 'get_book_by_isbn')
        
        # 最后使用标题搜索
        if book := self.get_book_by_title(md.title, md.author_sort):
            logging.debug("通过标题搜索获取到数据")
            return self._metadata(book, 'get_book_by_title')
        
        logging.warning("未找到匹配的豆瓣书籍信息")
        return None

        # if book:
        #   logging.debug("成功获取豆瓣数据，准备转换元数据")
        #   return self._metadata(book)
        # else:
        #   logging.warning("未找到匹配的豆瓣书籍信息")

    def get_cover(self, cover_url):
        if not self.copy_image:
            return None
        img = requests.get(cover_url, headers=CHROME_HEADERS).content
        img_fmt = cover_url.split(".")[-1]
        return (img_fmt, img)
        # if not self.copy_image:
        #   return None
        # try:
        #   rsp = requests.get(cover_url, headers=CHROME_HEADERS, timeout=5)
        #   rsp.raise_for_status()
        #   return (cover_url.split(".")[-1], rsp.content)
        # except Exception as e:
        #   logging.error("封面下载失败：%s", str(e))
        #   return None

    def _metadata(self, book, source_method):
        logging.debug("_metadata function from::%s", source_method)
        if not book:
            logging.debug("_metadata function get none book")
            return None
        
        # authors = []
        # if book["author"]:
        #     for author in book["author"]:
        #         for r in REMOVES:
        #             author = r.sub("", author)
        #         authors.append(author)
        # if not authors:
        #     authors = [u"佚名"]
        logging.debug("_metadata11::")
        from calibre.ebooks.metadata.book.base import Metadata
        from calibre.utils.date import utcnow
        logging.debug("_metadata22::")
        logging.debug(book)

        # 获取原始标题，若无则标记为未知
        raw_title = book["title"]
        if not raw_title:
            logging.warning("书籍标题缺失，使用默认标题")
            raw_title = _("未知标题")
        
        mi = Metadata(raw_title)

        logging.debug("_metadata31::")
        logging.debug(book.get("publisher"))
        # mi.authors = authors
        # mi.author = mi.authors[0]
        # mi.author_sort = mi.authors[0]
        mi.publisher = book.get("publisher") or _("")
        logging.debug("_metadata33::")
        mi.comments = book.get("summary", "")  # 确保即使无summary也不会报错
        if not mi.comments or '暂无简介' in mi.comments:  # 新增空值判断
          mi.comments = book.get("author_intro", _("暂无简介"))
        logging.debug("_metadata34::")
        if not mi.isbn or '00000000' in mi.isbn:
          mi.isbn = book.get("isbn13", None)
          logging.debug("_metadata function 更新了isbn::%ss", mi.isbn)
        mi.series = book.get("serials", None)
        # mi.tags = [t["name"] for t in book["tags"]][:8]
        mi.rating = int(float(book["rating"]["average"]))
        mi.pubdate = str2date(book.get("pubdate", _("2000-01-01")))
        mi.timestamp = utcnow()
        mi.douban_author_intro = book.get("author_intro", _("暂无简介"))
        mi.douban_subtitle = book.get("subtitle", None)
        mi.website = "https://book.douban.com/subject/%s/" % book["id"]
        mi.source = u"豆瓣"
        logging.debug("_metadata35::")
        mi.provider_key = KEY
        logging.debug("_metadata36::")
        mi.provider_value = book["id"]

        # mi.cover_url = book["images"]["large"]
        # mi.cover_data = self.get_cover(mi.cover_url)

        # 添加封面下载保护
        try:
            mi.cover_data = self.get_cover(mi.cover_url)
        except Exception as e:
            logging.error("封面下载失败: %s", str(e))
            mi.cover_data = None

        logging.debug("_metadata44::")
        logging.debug("\n输出的douban metadata:\n%r", mi)
        return mi


def get_douban_metadata(mi):
    api = DoubanBookApi()
    try:
        return api.get_metadata(mi, False)
    except Exception as err:
        logging.error(f"豆瓣接口异常5: {err}")
        return None


def select_douban_metadata(mi):
    api = DoubanBookApi()
    try:
        return api.get_metadata(mi, True)
    except Exception as err:
        logging.error(f"豆瓣接口异常6: {err}")
        return None


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("%s BOOK-TITLE BASE-URL" % sys.argv[0])
        exit(0)

    from pprint import pprint

    logging.basicConfig(level=logging.DEBUG)
    api = DoubanBookApi("fake-api-key", sys.argv[2])
    books = api.get_books_by_title(sys.argv[1])
    pprint(books)
    metas = [str2date(b["pubdate"]) for b in books]
    pprint(metas)
