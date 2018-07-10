import sys
import orm,asyncio
from models import User,Blog,Comment


def test( loop ):
    yield from orm.create_pool( loop = loop, user='root', password='123456', db='test' )
    u=User(id = 1, name='guutasaTest1',email='guutasa1@test.com',passwd='guutasapasswd',image='about:blank')
    yield from u.save()

if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    loop.run_until_complete( asyncio.wait([test( loop )]) )  
    loop.close()
    if loop.is_closed():
        sys.exit(0)