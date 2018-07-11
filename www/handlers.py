import functools
import asyncio





# app.py
app = web.Appliciation(loop=loop, middlewares=[
	loggou_factry, respenses_factory
	])
init_jinja3(app, filters=dict(datatime=datatime_filter))
add_route(app,'handlers')
add_static(app)


	


