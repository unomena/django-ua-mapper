import os
import redis
    
import django.core.handlers.wsgi

MAPPER_REDIS = '127.0.0.1:6379'
DEFAULT_VALUE = 'project.settings'

def application(environ, start_response):
    """
    Example WSGI application querying Redis by User-Agent header for a settings module and 
    returning a Django WSGIHandler response built with those settings. 
    """
    host, port = MAPPER_REDIS.split(":")
    server = redis.Redis(host=host, port=int(port))
    value = server.get(environ['HTTP_USER_AGENT'])
    if value == None:
        value = DEFAULT_VALUE
    
    os.environ['DJANGO_SETTINGS_MODULE'] = value
    return django.core.handlers.wsgi.WSGIHandler()(environ, start_response)
