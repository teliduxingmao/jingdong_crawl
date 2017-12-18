from pyquery import PyQuery as pq
from multiprocessing import Pool,Process
import requests
import re
import redis
import pymongo
import json
# import gevent
from settings import *
from gevent import monkey

# monkey.patch_all()
redis_pool = redis.ConnectionPool(host=REDIS_URI, port=REDIS_PORT,password = REDIS_PASSWD)

#这部分主要用于从主页面获取商品的id，并通过redis的set去重，最后把id保存到redis的list中
class jingdong_spider:
    def __init__(self):
        self.headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'zh-CN,zh;q=0.9',
        'Cache-Control':'max-age=0',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        }

    #用于获取页面内容，小小地封装一下，如果需要代理、cookie之类的同理
    def get_page(self,url):
        return requests.get(url,headers = self.headers).text

    #获取商品的页面总数
    def get_page_count(self,url):
        print('get_page_count',url)
        doc = pq(self.get_page(url))
        page_count = doc('#J_bottomPage  span.p-skip > em > b').text()
        print(page_count)
        print(type(page_count))
        return int(page_count)

    #把每页的所有id保存到一个list返回
    def get_idList(self,url):
        doc = pq(self.get_page(url))
        idList = []
        items = doc('.gl-warp .gl-item').items()
        for item in items:
            id = item('.gl-i-wrap').attr('data-sku')
            print('get id:',id)
            idList.append(id)
        return idList

    #保存到redis
    def save_to_redis(self,idList):
        conn = redis.Redis(connection_pool = redis_pool)
        for id in idList:
            #去重
            if conn.sadd(SET_KEY,id):
                #从左边保存到redis的list，将list作为一个队列来使用，方便进行分布式
                conn.lpush(LIST_KEY,id)
                print('save to redis list',id)
    #每一个起始url的处理逻辑
    def deal(self,url):
        print(url)
        count = 0
        url1 = url
        page_count = self.get_page_count(url.format(1))
        for page in range(page_count):
            count +=1
            print(page)
            url = url1.format(page)
            print(url)
            idList = self.get_idList(url)
            self.save_to_redis(idList)
        print('count',count)

    #多进程爬取
    def run(self):
        pool = Pool()
        pool.map(self.deal,URL_LIST)
        pool.close()
        pool.join()

if __name__ =='__main__':
    spider = jingdong_spider()
    spider.run()





