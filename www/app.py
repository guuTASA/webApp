import logging
logging.basicConfig(level=logging.INFO)

import asyncio
import os
import json
import time
import orm
from datetime import datetime
from aiohttp import web
from jinja2 import Enviorment, FileSystemLoader
from coroweb import add_routes, add_static


def index(request):
    return web.Response(body=b'<h1>helloworld</h1>', content_type='text/html')


@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
