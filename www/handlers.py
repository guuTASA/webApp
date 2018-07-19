import re
import time
import json
import logging
import hashlib
import base64
import asyncio

from coroweb import get, post
from models import User, Comment, Blog, next_id
from apis import APIValueError, APIResourceNotFoundError
from config import configs

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret


def user2cookie(user, max_age): # max_age是cookie的有效期吗?
	# build coodie string by: id-expires-sha1
	expires = str(int(time.time() + max_age))
	s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
	# 这里为什么用分隔符分开呢?
	L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
	return '-'.join(L)

# 为什么这个是异步操作 上边的就不是呢?
async def cookie2user(cookie_str):
	if not cookie_str:
		return None
	try:
		L = cookie_str.split('-')
		if len(L) != 3:
			return None
		uid, expries, sha1 = L
		if int (expries) < time.time():
			return None
		user = await User.find(uid)
		if user is None:
			return None
		s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
		if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
			logging.info('invalid sha1')
			return None
		user.passwd = '******'
		return user
	except Exception as e:
		logging.exception(e)
		return None


_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$') # 40位Hash字符串
# _RE_ 是怎么用的?

@post('/api/users')
def api_register_user(*, email, name, passwd):
	if not name or not name.strip():
		raise APIValueError('name')
	if not email or not _RE_EMAIL.match(email):
		raise APIValueError('email')
	if not passwd or not _RE_SHA1.match(passwd):
		raise  APIValueError('passwd')
	users = yield from User.findAll('email=?', [email])
	if len(users) > 0:
		raise  APIError('register:failed', 'email', 'Email is already in use.')
	uid = next_id()
	sha1_passwd = '%s:%s' % (uid, passwd)
	user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
	yield from user.save()
	# make session cookie
	# ???
	r = web.Response()
	r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
	user.passwd = '******'
	r.content_type = 'application/json'
	r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
	return r


@get('/register')
def register():
	return{
		'__template__':'register.html'
	}


@get('/signin')
def signin():
	return{
		'__template__':'signin.html'
	}


@get('/signout')
def signout(request):
	referer = request.headers.get('Referer')
	r = web.HTTPFound(referer or '/')
	r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
	logging.info('user signed out')
	return r



@post('/api/authenticate') # authenticate 认证
def authenticate(*, email, passwd):
	if not email:
		raise APIValueError('email', 'Invalid email')
	if not passwd:
		raise APIValueError('passwd', 'Invalid password')
		users = yield from User.findAll('email=?', [email])
		if len(users) == 0:
			raise APIValueError('email', 'Email not exist')
		user = user[0]
		# check password
		sha1 = hashlib.sha1()
		sha1.update(user.id.encode('utf-8'))
		sha1.update(b':') # ???
		sha1.update(passwd.encode('utf-8'))
		if user.passwd != sha1.hexdigest():
			raise APIValueError('passwd', 'Invalid password')
		# authenticate ok, set cookie:
		r = web.Response()
		r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
		user.passwd = '******'
		r.content_type = 'application/json'
		r.body = json.dump(user, ensure_ascii=False).encode('utf-8')
		return r




# TEST 3
# Users 数据库中的信息
# @get('/api/users')
# async def api_get_users(*, page="1"):
# 	users = await User.findAll(orderBy='created_at desc')
# 	for u in users:
# 		u.passwd = '******'
# 	return dict(users=users)


# TEST 2
# 主页
@get('/') 
async def index(request):
	summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
	blogs = [
		Blog(id=1, name='Test Blog1', summary=summary, created_at=time.time()-120),
		Blog(id=2, name='Test Blog2', summary=summary, created_at=time.time()-3600),
		Blog(id=3, name='Test Blog3', summary=summary, created_at=time.time()-640000)
	]
	return{
		'__template__':'blogs.html',
		'blogs':blogs
	}


# TEST 1

# @get('/')
# async def index(request):
# 	users = await User.findAll()
# 	return{
# 		'__template__':'test.html',
# 		'users':users
# 	}




