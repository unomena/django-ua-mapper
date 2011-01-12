import hashlib
import os
import re
import sys
from optparse import OptionParser, make_option
from urllib import urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.importlib import import_module
        
import redis
from wurfl2python import WurflPythonWriter, DeviceSerializer

import ua_mapper


WURFL_ARCHIVE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "wurfl.xml.gz")
WURFL_XML_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "wurfl.xml")
WURFL_PY_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "wurfl.py")

class Command(BaseCommand):
    help = 'Maps Wurfl devices to Redis.'
    option_list = BaseCommand.option_list + (
        make_option('-f', '--force',
            default=False,
            action="store_true",
            dest='force',
            help='Delete poll instead of closing it'
        ),
    )

    def get_mapper(self):
        try:
            mapper_path = settings.UA_MAPPER_CLASS
        except:
            raise CommandError('No UA_MAPPER_CLASS setting found.')
        try:
            dot = mapper_path.rindex('.')
        except ValueError:
            raise CommandError('%s isn\'t a UA Mapper module.' % mapper_path)
        module, classname = mapper_path[:dot], mapper_path[dot+1:]    
        try:
                mod = import_module(module)
        except ImportError, e:
            raise CommandError('Could not import UA Mapper %s: "%s".' % (module, e))    
        try:
            mapper_class = getattr(mod, classname)
        except AttributeError:
            raise CommandError('UA mapper module "%s" does not define a "%s" class.' % (module, classname))
   
        mapper_instance = mapper_class()
        if not hasattr(mapper_instance, 'map'):
            raise CommandError('UA mapper class "%s" does not define a map method. Implement the method to receive a Wurfl device object and return an appropriate value to be stored in Redis.' % classname)
        
        if not hasattr(mapper_instance, 'map'):
            raise CommandError('UA mapper class "%s" does not define a map method.' % classname)
        
        return mapper_class()
    
    def get_server(self):
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

    def get_md5(self, filename):
        f = open(filename, "r")
        m = hashlib.md5()
        m.update(f.read())
        f.close
        return m.hexdigest()

    def write_archive(self, filename, data):
        f = open(WURFL_ARCHIVE_PATH, "w")
        f.write(data)
        f.close()

    def fetch_latest_wurfl(self):
        """
        Fetch latest Wurfl db. Extract it and convert to wurfl.py
        Return True if db has been updated.

        TODO: Download URL resolution is completely retarded but I couldn't find a consistent repo from which to download wurfl.xml.
        """
        print "Checking for Wurfl update..."
        # Get latest version download page url.
        result = re.search('"(/projects/wurfl/files/WURFL/.*\..*\..*/)"', urlopen("http://sourceforge.net/projects/wurfl/files/WURFL/").read())
        download_page_url = "http://sourceforge.net%s" % result.group(1)
    
        # Get database download url.
        download_page = urlopen(download_page_url).read()
        result = re.search('"download_url": "(http://sourceforge.net/projects/wurfl/files/WURFL/.*\..*\..*/.*.xml.gz/download)"', download_page)
        download_url = result.group(1)
        result = re.search('"md5": "(.*)", "type"', download_page)
        new_md5 = result.group(1)

        # Only update if md5's don't match. 
        try:
            current_md5 = self.get_md5(WURFL_ARCHIVE_PATH)
            update = new_md5 != current_md5
        except IOError:
            update = True
        
        if update:
            print "Wurfl update found, downloading..."
            data = urlopen(download_url).read()
            self.write_archive(WURFL_ARCHIVE_PATH, data)
            os.system("gunzip -f %s" % WURFL_ARCHIVE_PATH) 
            self.write_archive(WURFL_ARCHIVE_PATH, data)
            return True
        
        print "No Wurfl update found."
        return False

    def wurfl_to_python(self):
        print "Compiling updated device list..."
        
        # Setup options.
        op = OptionParser()
        op.add_option("-l", "--logfile", dest="logfile", default=sys.stderr,
              help="where to write log messages")
       
        # Cleanup args for converter to play nicely.
        if '-f' in sys.argv:
            sys.argv.remove('-f')
        if '--force' in sys.argv:
            sys.argv.remove('--force')
        
        options, args = op.parse_args()
        options = options.__dict__
        options.update({"outfile": WURFL_PY_PATH})

        # Perform conversion.
        wurfl = WurflPythonWriter(WURFL_XML_PATH, device_handler=DeviceSerializer, options=options)
        wurfl.process()

    def handle(self, force, *args, **options):
        mapper = self.get_mapper()
        server = ua_mapper.get_server()
        if self.fetch_latest_wurfl() or force:
            self.wurfl_to_python()
            from wurfl import devices
            print "Updating Redis..."
            for i, ua in enumerate(devices.uas):
                device = devices.select_ua(ua)
                value = mapper.map(device)
                try:
                    prefix = getattr(settings, 'UA_MAPPER_KEY_PREFIX', None)
                    if prefix:
                        key = "%s%s" % (prefix, ua)
                    else:
                        key = ua
                    server.set(key, value)
                    print 'Set Redis key "%s" to value "%s".' % (key, value)
                except redis.exceptions.RedisError, e:
                    raise CommandError('Unable to set Redis key "%s" to value "%s": %s' % (ua, value, e))
            print "Done."
        else:
            print "Done. Redis unchanged."
