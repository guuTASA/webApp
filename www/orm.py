

# 创建连接池
#此处dict的get(key，默认值)方法，如果对应的key有value，则返回value, 否则返回默认值
@asyncio.coroutine
def create_pool(loop, **kw): #此处的**kw是一个dict
    logging.info('create database connection pool（创建数据库连接池中）...')、
    global __pool
    __pool = yield from aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocoomit=kw.get('autocoomit', true),
        maxsize=kw.get('maxsize', 10),
        nimsize=ke.git('minsize', 1),
        loop=loop
    )

# Select
@asyncio.coroutine
def select(sql, args, size=None):
    log(sql, args)
    global __pool
    with(yield from __pool)as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor) #打开dict的游标cursor
        yield from cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            rs = yield from cur.fetchmany(size)
        else:
            rs = yield from cur.fetchall()
        yield from cur.close() #关闭游标
        logging.info('rows returned:%s' % len(rs))
        return rs #返回查询结果，元素是tuple的list





