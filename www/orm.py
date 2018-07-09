import sys
import asyncio
import logging
logging.basicConfig(level=logging.INFO)

import aiomysql

# 这是啥??? 打印日志???


def log(sql, args=()):
    logging.info('SQL:%s' % sql)


# 这是啥??? 把查询字段计数替换成 ?,?,?,? 的形式
def create_args_string(num):
    lol = []
    for n in range(num):
        lol.append('?')
    return ','.join(lol)


# 创建连接池
@asyncio.coroutine
def create_pool(loop, **kw):  # 此处的**kw是一个dict
    logging.info('start creating database connection pool...')
    global __pool
    __pool = yield from aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )
    # 此处dict的get(key，默认值)方法，如果对应的key有value，则返回value, 否则返回默认值


@asyncio.coroutine
def destroy_pool():  # 关闭进程池
    global __pool
    if __pool is not None:
        __pool.close()  # close()不是一个协程
        yield from __pool.wait_closed()  # wait_close()是一个协程，所以用yield from


# Select
@asyncio.coroutine
def select(sql, args, size=None):
    log(sql, args)
    global __pool
    with(yield from __pool)as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)  # 打开dict的游标cursor
        # 这是啥??? 为什么有or()
        yield from cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            rs = yield from cur.fetchmany(size)
        else:
            rs = yield from cur.fetchall()
        yield from cur.close()  # 关闭游标
        logging.info('rows returned:%s' % len(rs))
        return rs  # 返回查询结果，元素是tuple的list


# Insert, Update, Delete
@asyncio.coroutine
def execute(sql, args, autocommit=True):  
    log(sql)
    global __pool
    with(yield from __pool) as conn:
        try:
            cur = yield from conn.cursor()
            yield from cur.execute(sql.replace('?', '%s'), args)
            yield from conn.commit()  # 此处手动提交???
            affected = cur.rowcount
            yield from cur.close()
            print('execute : ', affected)  # 可以没有这行
        except BaseException as e:
            raise
        return affected


class Field(object):

    def __init__(self, name, colunm_type, primary_key, default):
        # 表的字段包含名字、类型、是否为表的主键和默认值
        self.name = name
        self.colunm_type = colunm_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.colunm_type, self.name)
        # 返回 表名字 字段类型 和字段名


# Field子类 * 5，分别对应五种数据类型
class StringField(Field):

    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name, ddl, primary_key, default)

# bool不可以作为primary_key


class BooleanField(Field):

    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)


class IntegerField(Field):

    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'int', primary_key, default)


class FloatField(Field):

    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'float', primary_key, default)


class TextField(Field):

    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)


# 元类
class ModelMetaClass(type):
    # cls：要__init__的类，bases：继承父类的集合，attrs：类的方法集合

    def __new__(cls, name, bases, attrs):
        # 要排除对model类的修改
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        # 获取table名称
        tableName = attrs.get('__table__', None) or name
        logging.info('found table: %s (table: %s)' % (name, tableName))
        # 获取所有的Field和主键名
        mappings = dict()
        fields = []  # 保存的是除了主键以外的属性名
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('found mapping:%s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if primaryKey:  # 如果又出现一个主键，抛出错误
                        raise RuntimeError(
                            'Duplicate primary key for field :%s' % k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise RuntimeError('Primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)
            # 这一步没看懂
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs['__mappings__'] = mappings
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey
        attrs['__fields__'] = fields
        # 增删查改语句
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (
            primaryKey, ','.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ','.join(
            escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ','.join(
            map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (
            tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)


# ORM映射的基类
class Model(dict, metaclass=ModelMetaClass):
    # Model继承dict，具有字典的所有功能

    def __init__(self, **kw):  # 这个init声明可以去掉吗?
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribuye '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)
        # python内置函数getattr/setattr, None是getattr的默认返回值

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s :%s ' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    @asyncio.coroutine
    def find(cls, pk):
        # 'find objects by primarykey.'
        rs = yield from select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])  # 返回一条dict形式的记录

    @classmethod
    @asyncio.coroutine
    def find_all(cls, where=None, args=None, **kw):
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []

        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)

        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?,?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value')

        rs = yield from select(' '.join(sql), args)
        return [cls(**r) for r in rs]

    @classmethod
    @asyncio.coroutine
    def findAll(cls, **kw):
        rs = []
        if len(kw) == 0:
            rs = yield from select(cls.__select__, None)
        else:
            args = []
            values = []
            for k, v in kw.items():
                args.append('%s=?' % k)
                values.append(v)
            print('%s where %s' % (cls.__select__, ' and '.join(args)), values)
            rs = yield from select('%s where %s ' % (cls.__select__, ' and '.join(args)), values)
        return rs

    @classmethod
    @asyncio.coroutine
    def findNumber(cls, selectField, where=None, args=None):
        sql = ['select %s __num__ from `%s` ' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = yield from select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['__num__']

    @asyncio.coroutine
    def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        print('save: %s ' % args)
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = yield from execute(self.__insert__, args)
        if rows != 1:
            print(self.__insert__)
            logging.warning(
                'failed to insert record: affected rows: %s ' % rows)

    @asyncio.coroutine
    def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = yield from execute(self.__update__, args)
        if rows != 1:
            logging.warning(
                'failed to update record: affected rows: %s ' % rows)

    @asyncio.coroutine
    def delete(self):
        args = [self.getValue(self.__primary_key__)]
        rows = yield from execute(self.__delete__, args)
        if rows != 1:
            logging.warning(
                'failed ro delete by primary key : affected rows : %s ' % rows)


# 定义Field类，负责保存(数据库)表的字段名和字段类型


# if __name__ == "__main__":  # 一个类自带前后都有双下划线的方法，在子类继承该类的时候，这些方法会自动调用，比如__init__
#     class User2(Model):  # 虽然User类乍看没有参数传入，但实际上，User类继承Model类，Model类又继承dict类，所以User类的实例可以传入关键字参数
#         print('111')
#         id = IntegerField('id', primary_key=True)  # 主键为id， tablename为User，即类名
#         name = StringField('name')
#         email = StringField('email')
#         password = StringField('password')
#     # 创建异步事件的句柄
#     loop = asyncio.get_event_loop()

    # # 创建实例
    # @asyncio.coroutine
    # def test():
    #     yield from create_pool(loop=loop, host='localhost', port=3306, user='guutasa', password='123456', db='test')
    #     print('222')
    #     user = User2(id=2, name='Tom3',
    #                  email='3slysly759@gmail.com', password='312345')
    #     # yield from user.save()
    #     # yield from user.update()
    #     # yield from user.delete()
    #     # print('success')
    #     # r = yield from User2.findAll()
    #     # r = yield from User2.find(2)
    #     # r = yield from User2.findNumber(2)
    #     # r = yield from User2.find_all('3')
    #     print(r)

    #     yield from destroy_pool()  # 关闭pool

    # loop.run_until_complete(test())
    # loop.close()
    # if loop.is_closed():
    #     sys.exit(0)
