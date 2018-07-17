import re
import time
import json
import logging
import hashlib
import base64
import asyncio
from coroweb import get, post
from models import User, Comment, Blog, next_id



# TEST 1

# @get('/')
# async def index(request):
# 	users = await User.findAll()
# 	return{
# 		'__template__':'test.html',
# 		'users':users
# 	}

# TEST 2
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

