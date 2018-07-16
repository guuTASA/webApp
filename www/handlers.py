import re
import time
import json
import logging
import hashlib
import base64
import asyncio
from coroweb import get, post
from models import User, Comment, Blog, next_id



# TEST1
@get('/')
async def index(request):
	users = await User.findAll()
	return{
		'__template__':'test.html',
		'users':users
	}




