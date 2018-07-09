# encoding: utf-8

import orm
# from models import User,Blog,Comment
import asyncio

async def test():

    # 创建连接池,里面的host,port,user,password需要替换为自己数据库的信息
    await orm.create_pool(loop=loop, host='127.0.0.1', port=3306, user='root', password='123456',db='test')

    # 没有设置默认值的一个都不能少
    u = User(name='vvipi', email='vvipi@qq.com', passwd='123', image='about:blank',id='001')

    await u.save()
    print('user saved')

    await orm.destory_pool()

# 获取EventLoop:
loop = asyncio.get_event_loop()

# 把协程丢到EventLoop中执行
loop.run_until_complete(test())
