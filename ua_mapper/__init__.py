import hashlib

import redis

from django.conf import settings


#------------------------------------------------------------------------------
def get_server(host_port=None):
    if not host_port:
        try:
            host_port = settings.UA_MAPPER_REDIS
        except:
            raise Exception('No UA_MAPPER_REDIS setting found.')
    try:
        colon = host_port.rindex(':')
    except ValueError:
        raise Exception('%s isn\'t a correct Redis host:port string.' % host_port)

    host, port = host_port.split(":")
    return redis.Redis(host=host, port=int(port))

#------------------------------------------------------------------------------
def get_template_set(user_agent_string, host_port=None):
    prefix = getattr(settings, 'UA_MAPPER_KEY_PREFIX', '')
    user_agent_md5 = hashlib.md5(user_agent_string).hexdigest()
    key = "%s%s" % (prefix, user_agent_md5)
    return get_server(host_port).get(key)


if __name__ == '__main__':
    print get_template_set('Mozilla/5.0 (Linux; U; Android 1.6; pl-pl; Era G1 Build/DRC92) AppleWebKit/525.10+ (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2',
                           '127.0.0.1:6379')
