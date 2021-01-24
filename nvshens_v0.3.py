# -*- coding: UTF-8 -*-
from soup_tool import Soup
from soup_tool import MyThread
from time import sleep, ctime

'''
抓取nvshens.org下高清图片
目标网站：nvshens.org
依赖工具类：soup_tool
version:0.1 单个网址链接抓取所有相关图片
version:0.2 通过标签搜索的方式获取整个标签下所有图片，只获取第一页，翻页V0.3再做
version:0.3 通过标签搜索的方式获取整个标签下所有图片，分页获取
1.由于取不到最大页数，假定100页，取不到直接over
2.或者递归查找，直到提示页面找不到，over
本次最后采用了第二种
author:yaowei
date:2018-04-20
'''


class Capture:

    def __init__(self):
        # referer 防盗链
        # self.index_page_url = 'http://www.zngrils.com/'
        self.index_page_url = 'http://www.nvshens.org/'
        # 搜索页面
        self.search_page_url = 'https://www.nvshens.org/gallery/:key/'
        # 作品内容主页
        self.one_page_url = 'https://www.nvshens.org/g/:key/'
        # root folder
        self.folder_path = 'nvshens/'
        # 每个线程的沉睡时间，防止反爬
        self.sleep_time = 2

    def readPageGallery(self, search_key, page=0):
        """
        :param page: 初始化翻页数，递归用
        :param search_key: 查询关键字
        :return:
        """
        root_folder = self.folder_path + search_key
        Soup.create_folder(root_folder)

        print('max_page=', page)

        if page <= 1:
            page_url = self.search_page_url.replace(':key', search_key)
        else:
            page_url = self.search_page_url.replace(':key', search_key) + str(page) + '.html'

        print('max_page', page, 'page_url', page_url)
        soup_html = Soup.get_soup(page_url)

        is_404 = soup_html.find('div', 'listdiv').get_text()
        print(is_404)

        if '页面不存在' in is_404:
            print('没有了，over')
            return
        else:
            self.readPageSearchThread(soup_html, root_folder)
            page = page + 1
            print(page)
            self.readPageGallery(search_key, page)

    def readPageSearch(self, search_key):
        """
       单页读取，根据输入key读取搜索页面,找寻所有的galleryli_link
       :param search_key: jiemeihua (代表https://www.nvshens.org/gallery/jiemeihua/)
       :return:
       """
        root_folder = self.folder_path + search_key
        Soup.create_folder(root_folder)

        page_url = self.search_page_url.replace(':key', search_key)
        print(page_url)
        soup_html = Soup.get_soup(page_url)
        self.readPageSearchThread(soup_html, root_folder)

    def readPageSearchThread(self, soup_html, root_folder):
        """
        找寻所有的galleryli_link
        :param root_folder: 根目录
        :param soup_html: 使用soup获取到到html页面
        :return:
        """
        a_lists = soup_html.find_all("a", {'class': 'galleryli_link'})

        threads = []
        for a in a_lists:
            page_one_key = a.get('href').split('/')[2]
            print('page_one_key', page_one_key)
            self.readPageOne(page_one_key, root_folder)
            t = MyThread(self.readPageOne, (page_one_key, root_folder), self.readPageOne.__name__)
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        print(' readPageSearchThread all end', ctime())

    def readPageOne(self, page_one_key, root_folder=None):
        """
       根据输入key读取搜索页面
       :param page_one_key: 24816 (代表https://www.nvshens.org/g/24816/)
       :param root_folder: 根目录
       :return:
       """
        sleep(self.sleep_time)

        if root_folder is None:
            root_folder = self.folder_path

        # 打开搜索页面第1页
        page_url = self.one_page_url.replace(':key', page_one_key)
        print(page_url)
        soup_html = Soup.get_soup(page_url)

        htitle = soup_html.find("h1", {'id': 'htilte'}).get_text()
        path = root_folder + '/(' + page_one_key + ')' + htitle
        print(path)
        Soup.create_folder(path)

        text_page = soup_html.find("div", {'id': 'dinfo'}).find('span').get_text()
        print('text_page', text_page)
        last = text_page.replace('张照片', '')
        item_size = int(last)

        # 第1张图片
        imgs = soup_html.find("ul", {'id': 'hgallery'}).find_all('img')
        image_one = imgs[0]
        image_one_url = image_one.get('src')
        print('image_one_url', image_one_url)

        # 第2张图片链接作为模版
        image_two = imgs[1]
        image_two_url = image_two.get('src')
        print('image_two_url', image_two_url)
        # 第1张 <img src="https://img.onvshen.com:85/gallery/25366/24816/0.jpg">
        # 第2张 <img src="https://img.onvshen.com:85/gallery/25366/24816/001.jpg">
        # 第3张 <img src="https://img.onvshen.com:85/gallery/25366/24816/002.jpg">

        print('item_size=====', item_size)

        img_hz = image_two_url.split("/")[-1]
        file_hz = img_hz.split('.')[1]
        img_mod_url = image_two_url.replace(img_hz, '')

        print('img_hz', img_hz, 'file_hz', file_hz, 'img_mod_url', img_mod_url)

        # 直接写0张
        self.write_img(image_one_url, path + '/0.' + file_hz, self.sleep_time)
        # 接下去，从第1张开始
        self.readPageByThread(item_size, path, img_mod_url, file_hz)

    # 多线程读取，每个图片下载都是一个线程
    def readPageByThread(self, item_size, path, img_mod_url, file_hz):

        threads = []
        # 循环打开图片链接,从1开始
        for item in range(1, item_size - 1):
            # 左侧补零 1->001,2->002,……,114->114
            page = str(item).zfill(3)
            new_page_url = img_mod_url + page + '.' + file_hz
            new_path = path + '/' + page + '.' + file_hz
            print(new_path, '---', new_page_url)

            t = MyThread(self.write_img, (new_page_url, new_path, self.sleep_time), self.write_img.__name__)
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        print('all end', ctime())

    # 读取单章内容并写入
    def write_img(self, page_url, path, _time):

        # 先等待几秒，防反爬
        sleep(_time)

        try:
            # 使用Request添加头部的方法，读取图片链接再写入，最重要的是加上Referer
            Soup.write_img(page_url, path, referer=self.index_page_url)
        except BaseException as msg:
            print(msg)

    def run(self):
            # 单独抓取一个页面 url = https://www.nvshens.org/g/24816/
            # self.readPageOne('23025')
            # self.readPageSearch('jiemeihua')
            tags=input('请输入标签：(网址中/gallery/后面的部分)')
            self.readPageGallery(tags)

Capture().run()
