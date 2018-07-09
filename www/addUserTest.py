import ORM_EXAMPLE
import aiomysql
import asyncio
from model import User, Blog, Comment

@asyncio.coroutine
def test():
	
	pool = yield from aiomysql.create_pool(loop=loop, host='localhost', port=3306, user='guutasa', password='123456', db='test')
	
	user1 = User(name="guutasa", passwd='123456', email="hdusjm@163.com", image='about:blank')
	
	yield from user1.save()

	pool.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(test())
