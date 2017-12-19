from pyquery import PyQuery as pq
from multiprocessing import Pool,Process
import requests
import re
import time
from gevent import monkey
import gevent
from json.decoder import JSONDecodeError
import redis
import pymongo
import json
from settings import *
from crawl import jingdong_spider


monkey.patch_all()
redis_pool = redis.ConnectionPool(host=REDIS_URI, port=REDIS_PORT,password = REDIS_PASSWD)
#用于爬取商品的评论数、
url1 = 'https://club.jd.com/comment/productCommentSummaries.action?referenceIds={}'
#用于获取商品价格
#pduid是京东用来检查的时间戳，可自己增大数字，保证在爬取时间内不会过期
url2 = 'https://p.3.cn/prices/mgets?type=1&skuIds=J_{id}&pduid={time}'
#用于获取商品名称
url3 = 'https://item.jd.com/{}.html'
#用于获取商品店铺
url4 = 'https://chat1.jd.com/api/checkChat?&pid={}'
#用于爬取商品热评
url5 = 'https://sclub.jd.com/comment/productPageComments.action?productId={}&score=0&sortType=5&page=0&pageSize=10'
#用于爬取所有评论
url6 = 'https://sclub.jd.com/comment/productPageComments.action?productId={id}&score=0&sortType=5&page={page}&pageSize=10'
class jingdong_parser(jingdong_spider):
    def parse_product(self):
        item = {}
        conn = redis.Redis(connection_pool=redis_pool)
        #从redis中获取商品id，如果出现ValueError，TypeError，说明redis为空，则不断重试
        try:
            id = int(conn.rpop(LIST_KEY))
        except ValueError:
            self.parse_product()
        except TypeError:
            self.parse_product()
        print('get id from redis: ',id)
        url2 = url1.format(id)

        #从url2为起始页能获取商品的评论数，好评，中评等信息
        res = self.get_page(url2)
        res = json.loads(res)['CommentsCount'][0]
        item['id'] = id
        item['CommentCount'] = res['CommentCount']
        item['AverageScore'] = res['AverageScore']
        item['DefaultGoodCount'] = res['DefaultGoodCount']
        item['GoodCount'] = res['GoodCount']
        item['AfterCount'] = res['AfterCount']
        item['GoodRate'] = res['GoodRate']
        item['GeneralCount'] = res['GeneralCount']
        item['GeneralRate'] = res['GeneralRate']
        item['PoorCount'] = res['PoorCount']
        item['PoorRate'] = res['PoorRate']
        item['name'] = self.get_name(id)

        #通过其他函数获取其他信息
        item1 = self.get_price(id)
        item.update(item1)
        item['shop'] = self.get_shop(id)
        item['hot_comment'] = self.get_hot_comment(id)
        item['comment'] = [comment for comment in self.get_comment(id)]
        return item

    #获取商品价格，在另一个页面的json中，获取了原价和打折价
    def get_price(self,id):
        item = {}
        time1 = str(int(time.time()))
        url = url2.format(id = id,time = time1)
        res = self.get_page(url)
        res = json.loads(res)[0]
        item['price'] = res['p']
        item['original_price'] = res['op']
        return item

    #获取商品名称
    def get_name(self,id):
        url = url3.format(id)
        res = self.get_page(url)
        doc = pq(res)
        name = doc('.itemInfo-wrap .sku-name').text()
        return name
    #获取店铺名称，如果json里没写，说明是京东自营
    def get_shop(self,id):
        url = url4.format(id)
        res = self.get_page(url)[5:-2]
        res = json.loads(res)
        shop = res.get('seller', '京东自营')
        return shop

    #获取热评信息
    def get_hot_comment(self,id):
        hot_comment = {}
        url = url5.format(id)
        res = self.get_page(url)
        res = json.loads(res)
        for item in res['hotCommentTagStatistics']:
            name = item['name']
            count = item['count']
            hot_comment[name] = count
        return hot_comment

    #爬取商品所有的评论信息，我发现最多能看100页，所以就循环100次，如果页数小于100，会出现JSONDecodeError，则提前结束
    def get_comment(self,id):
        try:
            for page in range(100):
                url = url6.format(id = id,page = page)
                res = json.loads(self.get_page(url))['comments']
                if res:
                    for i in res:
                        comment = i['content']
                        yield comment
                else:
                    break
        except JSONDecodeError:
            return

    #将爬取的商品信息保存到mongo
    def save_to_mongo(self,item):
        client = pymongo.MongoClient(MONGO_URI)
        db = client[MONGO_DB]
        if db[MONGO_TB].insert(item):
            print('save to mongo:',item)

    def run1(self):
        print('running')
        while True:
            item = self.parse_product()
            self.save_to_mongo(item)

    #开了100个协程进行爬取，由于需要抓取所有评论数，所以效率还是不太高
    def run(self):
        gevent.joinall([
            gevent.spawn(self.run1) for i in range(100)
        ])


if __name__ == '__main__':
    parser = jingdong_parser()
    parser.run()



