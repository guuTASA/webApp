import json
import logging
import inspect
import functools

class APIError(Exception):
	def __init__(self, error, data='', message=''):
		super(APIError, self).__init__(message)
		self.error = error
		self.data = data
		self.message = message


class APIValueError(APIError):
	def __init__(self, field, message=''):
		super(APIValueError, self).__init__('value:invalid', field, message)


class APIResourceNotFoundError(APIError):
	def __init__(self, field, message=''):
		super(APIResourceNotFoundError, self).__init__('value:notfound', field, message)


class APIPermissionError(APIError):
	def __init__(self, message=''):
		super(APIPermissionError, self).__init__('permission:forbidden', 'permission', message)


class Page(object):

	# item_count：数据总条数
	# page_index：第几页
	# page_size：一页显示多少条
	# page_offset：这一页之前有多少条
	# limit:这一页最大值，在无数据和当前页数 > 页总数时为 0
	def __init__(self, item_count, page_index=1, page_size=10):
		self.item_count = item_count
		self.page_size = page_size
		self.page_count = item_count // page_size + (1 if item_count % page_size > 0 else 0)
		# 注意此处python除法
		if (item_count=0) or (page_index > self.page_count):
			self.offset = 0
			self.limit = 0
			self.page_index = 1
		else:
			self.page_index = page_index
			self.offset = self.page_size * (page_index-1)
			self.limit = self.page_size
		self.has_next = self.page_index < self.page_count
		self.has_previous = self.page_index > 1

	def __str__(self):
		return 'item_count: %s, page_count: %s, page_index: %s, page_size: %s, limit: %s' % (self.item_count, self.page_count, self.page_index, self.offset, self.limit)

	# 这是什么意思?
	__repr__ = __str__


# ???
if __name__=='__main__':
	import doctest
	doctest.testmod()



