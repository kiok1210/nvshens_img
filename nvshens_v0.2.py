# -*- coding: UTF-8 -*-
import requests
from soup_tool import Soup
from soup_tool import MyThread
from time import sleep, ctime

'''
抓取nvshens.com下高清图片
目标网站：nvshens.com
依赖工具类：soup_tool
version:0.1 单个网址链接抓取所有相关图片
version:0.2 通过标签搜索的方式获取整个标签下所有图片，只获取第一页，翻页V0.3再做
author:yaowei
date:2018-04-20
'''


class Capture:

    def __init__(self):
        # referer
        self.index_page_url = 'http://www.nvshens.com'
        # 搜索页面
        self.search_page_url = 'https://www.nvshens.com/gallery/:key/'
        # 作品内容主页
        self.one_page_url = 'https://www.nvshens.com/g/:key/'
        # root folder
        self.folder_path = 'nvshens/'
        # 每个线程的沉睡时间，防止反爬
        self.sleep_time = 2

    def readPageSearch(self, search_key):
        """
       根据输入key读取搜索页面,找寻所有的galleryli_link
       :param search_key: jiemeihua (代表https://www.nvshens.com/gallery/jiemeihua/)
       :return:
       """
        root_folder = self.folder_path + search_key
        Soup.create_folder(root_folder)

        page_url = self.search_page_url.replace(':key', search_key)
        print(page_url)
        soup_html = Soup.get_soup(page_url)

        a_lists = soup_html.find_all("a", {'class': 'galleryli_link'})

        threads = []
        # n = 0
        for a in a_lists:
            page_one_key = a.get('href').split('/')[2]
            print('page_one_key', page_one_key)
            # self.readPageOne(page_one_key, root_folder)
            t = MyThread(self.readPageOne, (page_one_key, root_folder), self.readPageOne.__name__)
            threads.append(t)

            '''
             # 测试用代码，多线程以下跑太多了
            n = n + 1
            if n > 2:
                break
            '''

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        print('all end', ctime())

    def readPageOne(self, page_one_key, root_folder=None):
        """
       根据输入key读取搜索页面
       :param page_one_key: 24816 (代表https://www.nvshens.com/g/24816/)
       :param root_folder: 根目录
       :return:
       """
        sleep(self.sleep_time)

        if root_folder is None:
            root_folder = self.folder_path

        # 创建文件夹 /magnet/search_key
        # path = root_folder + page_one_key


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
        image_one = soup_html.find("ul", {'id': 'hgallery'}).find('img')
        image_one_url = image_one.get('src')
        print('image_one_url', image_one_url)

        # 第2张图片链接作为模版
        image_two = image_one.find_next_sibling()
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
        self.readPagetoTxt(image_one_url, path + '/0.' + file_hz, self.sleep_time)
        # 接下去，从第1张开始
        self.readPageByThread(item_size, path, img_mod_url, file_hz)

    # 多线程读取，每个图片下载都是一个线程
    def readPageByThread(self, item_size, path, img_mod_url, file_hz):

        threads = []
        # 循环打开图片链接
        for item in range(1, item_size):
            # 左侧补零 1->001,2->002,……,114->114
            page = str(item + 1).zfill(3)
            new_page_url = img_mod_url + page + '.' + file_hz
            new_path = path + '/' + page + '.' + file_hz
            print(new_path, '---', new_page_url)

            t = MyThread(self.readPagetoTxt, (new_page_url, new_path, self.sleep_time), self.readPagetoTxt.__name__)
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        print('all end', ctime())

    # 读取单章内容并写入
    def readPagetoTxt(self, page_url, path, _time):

        # 先等待几秒，防反爬
        sleep(_time)

        # 使用此方法，下载图片为盗链
        # urllib.request.urlretrieve(page_url, path)

        # 使用Request添加头部的方法，读取图片链接再写入，最重要的是加上Referer
        Soup.write_img(page_url, path, referer=self.index_page_url)

        '''
        img_content = requests.get(page_url, ).content
        with open(path, 'wb') as f:
            f.write(img_content)
        '''

    def run(self):
        try:
            # 单独抓取一个页面 url = https://www.nvshens.com/g/24816/
            # self.readPageOne('25412')
            self.readPageSearch('jiemeihua')

        except BaseException as msg:
            print(msg)

    if __name__ == '__main__':
        n = '24'
        s = n.zfill(3)
        print(s)


Capture().run()
