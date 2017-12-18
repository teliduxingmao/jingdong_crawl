# jingdong_crawl
京东爬虫
爬取京东商品的价格、评论、名称、店铺、热评、全部评论

python3.5+requests,pyquery,pymongo,redis,gevent

其中crawl.py爬虫在京东上爬取商品id,通过redis的set来去重，并将id保存到list中

另一个parse.py从list中通过pop的方式获取商品id

由于需要获取商品的全部评论，所以即使开了100个协程，爬取速度还是不够快，可以通过多台机器从redis中获取id的形式来实现分布式爬取

settings中是一些数据库及其他的设置信息
