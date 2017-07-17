import re, requests
import traceback
import os
import os.path as Path
from queue import Queue
import uuid
import threading
from lxml import etree


# 抓取网站图片，针对html递归抓取



class SpiderCernPic:
    unProcessUrl = Queue()
    picSavePath = "d:/pic"
    processedUrl = set()
    thread_size = 10

    # 启动抓取线程，将种子链接放入队列
    def start(self, url):
        if not Path.exists(self.picSavePath):
            os.mkdir(self.picSavePath)
        self.unProcessUrl.put(url)
        for i in range(self.thread_size):
            spiderThread = threading.Thread(target=self.spider)
            spiderThread.setDaemon(False)
            spiderThread.start()

    def spider(self):
        print("thread:%s started" % (threading.current_thread().getName()))
        while True:
            url = self.unProcessUrl.get()
            try:
                if self.isPic(url):
                    self.downLoadPic(url)
                elif self.isLink(url) and self.isCernLink(url):
                    links = self.parseLink(url)
                    self.putInQue(url, links)
            except Exception:
                # self.unProcessUrl.put(url)
                print(traceback.format_exc())

    def isPic(self, url):
        return None != re.match(r'^\S*\.(?:png|jpg|bmp|gif)$', url, re.IGNORECASE)

    def downLoadPic(self, url):
        ir = self.getUrlContent(url)
        if ir.status_code == 200:
            fileName = Path.join(self.picSavePath,
                                 "%s%s" % (url.replace("/", "_").replace(".", "_").replace(":", "_"), ".jpg"))
            print(fileName)
            open(fileName, 'wb').write(ir.content)

    def getUrlContent(self, url):
        return requests.get(url, timeout=1)

    # 去除css,js,woff
    def isLink(self, url):
        return None == re.match(r'^\S*\.(?:js|css|woff)', url, re.IGNORECASE)

    # 分析链接
    def parseLink(self, url):
        links = []
        ir = self.getUrlContent(url)
        if ir.status_code == 200:
            html = etree.HTML(ir.text)
            links = self.parseHtmlLink(html)
        return links

    # 分析链接
    def parseHtmlLink(self, html):
        links = []
        links.extend(html.xpath('//a/@href'))
        links.extend(html.xpath("//img//@src"))
        return links

    # 将所有链接放入队列
    def putInQue(self, url, links):
        for link in links:
            self.putOneInQue(url, link)

    # 将一个链接放入队列
    def putOneInQue(self, url, link):
        newLink = self.preProcessLink(url, link)
        if not newLink in self.processedUrl:
            self.unProcessUrl.put(newLink)
            self.processedUrl.add(newLink)
            print("%s,%s,%s,%d" % (url, link, newLink, self.unProcessUrl.qsize()))

    # 预处理格式化链接
    def preProcessLink(self, url, link):
        if not link.startswith("http"):
            if link.startswith("//"):
                link = "%s%s" % (url[0:url.find("//")], link)
            elif link.startswith("/"):
                if url[url.find("//") + 2:].find("/") > 0:
                    link = "%s%s%s" % (
                        url[0:url.find("//")],
                        url[url.find("//"):(url[url.find("//") + 2:].find("/") + url.find("//") + 2)], link)
                else:
                    link = "%s%s" % (url, link)

        return link

    def isCernLink(self, url):
        return url.find("crfeb") >= 0


if __name__ == '__main__':
    SpiderCernPic().start("http://www.crfeb.cn/")
