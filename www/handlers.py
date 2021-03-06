import re
import time
import json
import logging
import hashlib
import base64
import asyncio
import markdown2

from coroweb import get, post
from models import User, Comment, Blog, next_id
from apis import APIValueError, APIResourceNotFoundError, Page
from config import configs
from aiohttp import web


COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret


# 检查是否是管理员
def check_admin(request):
	logging.info('Check admin here')
	if request.__user__ is None or not request.__user__.admin:
		raise APIpermissionError()


# 用在哪里了? 用在api_blogs里，传页数，转换成数字
def get_page_index(page_str):
	p = 1
	try:
		p = int (page_str)
	except ValueError as e:
		pass
	if p < 1:
		p = 1
	return p


# 文字转html???
def text2html(text):
	lines = map(lambda s:'<p>%s<p>' % s.replace('&','&amp;').replace('<', '&lt;').replace('>', '&gt;'), filter(lambda s: s.strip() != '', text.split('\n')))
	# 上边这一行是什么东西 ???
	return ''.join(lines)


# 生成用户的cookie
def user2cookie(user, max_age): # max_age是cookie的有效期吗?
	# build coodie string by: id-expires-sha1
	expires = str(int(time.time() + max_age))
	s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
	# 这里为什么用分隔符分开呢?
	L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
	return '-'.join(L)


# 为什么这个是异步操作 上边的就不是呢?
# 如果cookie有效，则解析cookie并加载用户
async def cookie2user(cookie_str):
	if not cookie_str:
		return None
	try:
		L = cookie_str.split('-')
		if len(L) != 3:
			return None
		uid, expires, sha1 = L
		if int (expires) < time.time():
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


# 主页
@get('/')
async def index(*, page='1'):
	page_index = get_page_index(page)
	num = await Blog.findNumber('count(id)')
	page = Page(num)
	if num == 0:
		blogs = []
	else:
		blogs = await Blog.findAll(orderBy='created_at desc', limit=(page.offset, page.limit))
	return {
		'__template__':'blogs.html',
		'page':page,
		'blogs':blogs
	}	


# 日志页
@get('/blog/{id}')
async def get_blog(id):
	blog = await Blog.find(id)
	logging.info('===============logging blog.content here============== %s' % blog.content)
	comments = await Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
	for c in comments:
		c.html_content = text2html(c.content)
	blog.html_content = markdown2.markdown(blog.content)
	return{
		'__template__':'blog.html',
		'blog':blog,
		'comments':comments
	}


# 注册
@get('/register')
def register():
	return{
		'__template__':'register.html'
	}


# 登录
@get('/signin')
def signin():
	return{
		'__template__':'signin.html'
	}


# 注册 2
@post('/api/authenticate') # authenticate 认证
async def authenticate(*, email, passwd):
	logging.info("herehere==authenticate==!!!-=====!!!")
	if not email:
		raise APIValueError('email', 'Invalid email')
	if not passwd:
		raise APIValueError('passwd', 'Invalid 你没写 password')
	users = await User.findAll('email=?', [email])
	if len(users) == 0:
		raise APIValueError('email', 'Email not exist')
	user = users[0]
	# check password
	sha1 = hashlib.sha1()
	sha1.update(user.id.encode('utf-8'))
	sha1.update(b':') # ???
	sha1.update(passwd.encode('utf-8'))
	logging.info('%s' % sha1.hexdigest())
	logging.info('%s' % user.passwd)
	if user.passwd != sha1.hexdigest():
		raise APIValueError('passwd', 'Invalid 你写错了 password')
	# authenticate ok, set cookie:
	r = web.Response()
	r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
	user.passwd = '******'
	r.content_type = 'application/json'
	r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
	return r


# 登出
@get('/signout')
def signout(request):
	referer = request.headers.get('Referer')
	r = web.HTTPFound(referer or '/')
	r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
	logging.info('user signed out')
	return r


# 将/manage/定向到日志列表管理页
@get('/manage/')
def manage():
	# 老师写的是定到评论管理页
	return 'redirect:/manage/blogs'


# 带 /manage/ 的页面，都是要检查用户权限的，只有admin = 1 的可以进
# 如果 admin != 1 会跳转到登录界面，同时日志有提示（此处应在界面上提示）


# 评论管理
@get('/manage/comments')
def manage_comments(*, page='1'):
	return {
		'__template__': 'manage_comments.html',
		'page_index': get_page_index(page)
	}


# 博客管理
@get('/manage/blogs')
def manage_blogs(*, page='1'):
	return{
		'__template__':'manage_blogs.html',
		'page_index':get_page_index(page)
	}


# 创建博客
@get('/manage/blogs/create')
def manage_create_blog():
	logging.info('manage_create_blog here')
	return{
		'__template__':'manage_blog_edit.html',
		'id':'',
		'action':'/api/blogs'
	}


# 编辑博客
@get('/manage/blogs/edit')
def manage_edit_blog(*, id):
	return{
		'__template__':'manage_blog_edit.html',
		'id':id,
		'action':'/api/blogs/%s' % id
	}


# 用户管理
@get('/manage/users')
def manage_users(*, page='1'):
	return{
		'__template__':'manage_users.html',
		'page_index': get_page_index(page)
	}

# 评论列表
@get('/api/comments')
async def api_comments(*, page='1'):
	page_index = get_page_index(page)
	num = await Comment.findNumber('count(id)')
	p = Page(num, page_index)
	if num == 0:
		return dict(page=p, comments=())
	comments = await Comment.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
	return dict(page=p, comments=comments)


# 发表评论
@post('/api/blogs/{id}/comments')
async def api_create_comment(id, request, *, content):
	user = request.__user__
	if user is None:
		raise APIpermissionError('Please signin first.')
	if not content or not content.strip():
		raise APIValueError('content')
	blog = await Blog.find(id)
	if blog is None:
		raise APIResourceNotFoundError('Blog')
	comment = Comment(blog_id=blog.id, user_id=user.id, user_name=user.name, user_image=user.image, content=content.strip())
	await comment.save()
	return comment


# 删除评论
@post('/api/comments/{id}/delete')
async def api_delete_comments(id, requests):
	check_admin(request)
	c = await Comment.find(id)
	if c is None:
		raise APIResourceNotFoundError('Comment')
	await c.remove()
	return dict(id=id)


# 用户列表
@get('/api/users')
async def api_get_users(*, page='1'):
	page_index = get_page_index(page)
	num = await User.findNumber('count(id)')
	p = Page(num, page_index)
	if num == 0:
		return dict(page=p, users=())
	users = await User.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
	for u in users:
		u.passwd = '******'
	logging.info("find users")
	return dict(page=p, users=users)


_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$') # 40位Hash字符串
# _RE_ 是怎么用的?


@post('/api/users')
async def api_register_user(*, email, name, passwd):
	if not name or not name.strip():
		raise APIValueError('name')
	if not email or not _RE_EMAIL.match(email):
		raise APIValueError('email')
	if not passwd or not _RE_SHA1.match(passwd):
		raise  APIValueError('passwd')
	users = await User.findAll('email=?', [email])
	if len(users) > 0:
		raise  APIError('register:failed', 'email', 'Email is already in use.')
	uid = next_id()
	sha1_passwd = '%s:%s' % (uid, passwd)
	user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
	await user.save()
	# make session cookie
	# ???
	r = web.Response()
	r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
	user.passwd = '******'
	r.content_type = 'application/json'
	r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
	return r


@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
	check_admin(request)
	logging.info('admin checked here (handlers)')
	if not name or not name.strip():
		raise APIValueError('name', 'name cannot be empty')
	if not summary or not summary.strip():
		raise APIValueError('summary', 'summary connot be empty')
	if not content or not content.strip():
		raise APIValueError('content', 'content cannot be empty')
	blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image, name=name.strip(), summary=summary.strip(), content=content.strip())
	await blog.save()
	logging.info('blog saved here (handlers)')
	return blog


@get('/api/blogs/{id}')
async def api_get_blog(*, id):
	blog = await Blog.find(id)
	return blog


@get('/api/blogs')
async def api_blogs(*, page='1'):
	page_index = get_page_index(page)
	num = await Blog.findNumber('count(id)')
	p = Page(num, page_index)
	# 这里为什么要传总数进去呢?
	if num == 0:
		return dict(page=p, blogs=())
	blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
	return dict(page=p, blogs=blogs) 


# 编辑博客
@post('/api/blogs/{id}')
async def api_update_blog(id, request, *, name, summary, content):
	check_admin(request)
	blog = await Blog.find(id)
	if not name or not name.strip():
		raise APIValueError('name', 'name cannot be empty')
	if not summary or not summary.strip():
		raise APIValueError('summary', 'summary connot be empty')
	if not content or not content.strip():
		raise APIValueError('content', 'content cannot be empty')
	blog.name = name.strip()
	blog.summary = summary.strip()
	blog.content = content.strip()
	await blog.update()
	return blog


# 删除博客
@post('/api/blogs/{id}/delete')
async def api_delete_blog(request, *, id):
	check_admin(request)
	blog = await Blog.find(id)
	await blog.remove()
	return dict(id=id)



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
# @get('/') 
# async def index(request):
# 	summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
# 	blogs = [
# 		Blog(id=1, name='Test Blog1', summary=summary, created_at=time.time()-120),
# 		Blog(id=2, name='Test Blog2', summary=summary, created_at=time.time()-3600),
# 		Blog(id=3, name='Test Blog3', summary=summary, created_at=time.time()-640000)
# 	]
# 	return{
# 		'__template__':'blogs.html',
# 		'blogs':blogs,
# 		# '__users__':request.__user__
# 	}


# TEST 1
# @get('/')
# async def index(request):
# 	users = await User.findAll()
# 	return{
# 		'__template__':'test.html',
# 		'users':users
# 	}
