import hashlib

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module

from pywurfl.algorithms import TwoStepAnalysis
import redis

class UAMapper(object):
    def get_mapper(self):
        try:
            mapper_path = settings.UA_MAPPER_CLASS
        except:
            raise ImproperlyConfigured('No UA_MAPPER_CLASS setting found.')
        try:
            dot = mapper_path.rindex('.')
        except ValueError:
            raise ImproperlyConfigured('%s isn\'t a UA Mapper module.' % mapper_path)
        module, classname = mapper_path[:dot], mapper_path[dot+1:]    
        try:
                mod = import_module(module)
        except ImportError, e:
            raise ImproperlyConfigured('Could not import UA Mapper %s: "%s".' % (module, e))    
        try:
            mapper_class = getattr(mod, classname)
        except AttributeError:
            raise ImproperlyConfigured('UA mapper module "%s" does not define a "%s" class.' % (module, classname))
   
        mapper_instance = mapper_class()
        if not hasattr(mapper_instance, 'map'):
            raise ImproperlyConfigured('UA mapper class "%s" does not define a map method. Implement the method to receive a Wurfl device object and return an appropriate value to be stored in Redis.' % classname)
        
        if not hasattr(mapper_instance, 'map'):
            raise ImproperlyConfigured('UA mapper class "%s" does not define a map method.' % classname)
        
        return mapper_class()
    
    def get_redis_server(self):
        try:
            host_port = settings.UA_MAPPER_REDIS
        except:
            raise CommandError('No UA_MAPPER_REDIS setting found.')
        try:
            colon = host_port.rindex(':')
        except ValueError:
            raise CommandError('%s isn\'t a correct Redis host:port string.' % host_port)
    
        host, port = host_port.split(":")
        return redis.Redis(host=host, port=int(port))

    def map(self, user_agent, device):
        mapper = self.get_mapper()
        redis_server = self.get_redis_server()
        value = mapper.map(device, user_agent)
        try:
            prefix = getattr(settings, 'UA_MAPPER_KEY_PREFIX', '')
            user_agent_md5 = hashlib.md5(user_agent).hexdigest()
            key = "%s%s" % (prefix, user_agent_md5)
            redis_server.set(key, value)
            print 'Set Redis key "%s" to value "%s" for user agent: %s.' % (key, value, user_agent)
        except redis.exceptions.RedisError, e:
            raise Exception('Unable to set Redis key "%s" to value "%s": %s' % (user_agent, value, e))
        return user_agent, device, value

    def map_by_request(self, request):
        from ua_mapper.management.commands import wurfl
        user_agent = unicode(request.META.get('HTTP_USER_AGENT', ''))
        if user_agent:
            devices = wurfl.devices
            search_algorithm = TwoStepAnalysis(devices)
            device = devices.select_ua(user_agent, search=search_algorithm)
            return self.map(user_agent, device)
