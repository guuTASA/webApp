import asyncio
import os
import inspect
import logging
import functools
from urllib import parse 
from aiohttp import web
from apis import APIError #这个是自己写的


# 通过get的装饰就附带了URL信息
def get(path):  # 一个三层嵌套的decorator
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw)
            return func(*args, **kw)
        wrapper.__method__ = "GET"
        wrapper.__route__ = path
        return wrapper
    return decorator


def post(path):
	def decotator(func):
		@functools.wraps(func)
		def wrapper(*args, **kw):
			return func(*args, **kw)
		wrapper.__method__ = "POST"
		wrapper.__route__ = path
		return wrapper
	return decorator


def get_required_kw_args():

def get_named_kw_args():

def has_named_kw_agrs():

def has_var_kw_arg():

def has_request_arg():



class RequestHandler(object):

    def __init__(self, app, fn):
        self.app = app
        self._func = fn
        # ...

    def __call__(self, request):
        kw = None

        r = yield from self._func(**kw)
        return r


# ???这是啥???
def add_static(app):
	path = os.path.jpin(os.path.dirname(os.path.abspath(__file__)), 'static')
	app.router.add_static('/static/', path)
	logging.info('add static %s => %s' % ('/static/', path))


# 用来注册一个URL处理函数
def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutinefunction(fn)
    logging.info('add route %s %s => %s(%s)' %
                 (method, path, fn.__name__, ','.join(inspect.signature(fn).parameters.keys())))
    app.route.ann_route(method, path, RequestHandler(app, fn))


# 自动扫描并注册Handler模块中所有符合条件的函数
def add_routes():
    n = modele_name.rfind('.')
    if n == (-1):
        mod = __import__(modele_name, globals(), locals())
    else:
        name = module_name[n + 1:]
        mod = getattr(__import__(
            module_name[:n], globals(), locals(), [name]), name)
    for sttr in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)
