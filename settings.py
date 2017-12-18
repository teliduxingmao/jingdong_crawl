
#保存商品信息的mongo数据库的相关信息
MONGO_URI = 'localhost'
MONGO_DB = 'jingdong'
MONGO_TB = 'jinkoushipin'
MONGO_PASSWD = ''
#保存商品ID的redis数据库的相关信息
REDIS_URI = 'localhost'
SET_KEY = 'jingdong-jinkoushipin-id'
LIST_KEY = 'jingdong-jinkoushipin'
REDIS_PORT = 6379
REDIS_PASSWD = ''

#需要搜索的商品的起始页
URL_LIST = ['https://list.jd.com/list.html?cat=1320,5019,5020&page={}',
                    'https://list.jd.com/list.html?cat=1320,5019,5021&page={}',
                    'https://list.jd.com/list.html?cat=1320,5019,5022&page={}',
                    'https://list.jd.com/list.html?cat=1320,5019,5023&page={}',
                    'https://list.jd.com/list.html?cat=1320,5019,12215&page={}',
                    'https://list.jd.com/list.html?cat=1320,5019,5024&page={}']