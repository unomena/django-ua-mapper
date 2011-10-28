import hashlib
import os
import re
import sys
from optparse import OptionParser, make_option
from urllib import urlopen

from django.core.management.base import BaseCommand
        
from wurfl2python import WurflPythonWriter, DeviceSerializer

WURFL_ARCHIVE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "wurfl.xml.gz")
WURFL_XML_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "wurfl.xml")
WURFL_PY_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "wurfl.py")

class Command(BaseCommand):
    help = 'Updates Wurfl devices database.'
    option_list = BaseCommand.option_list + (
        make_option('-f', '--force',
            default=False,
            action="store_true",
            dest='force',
            help='Delete poll instead of closing it'
        ),
    )

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
        if self.fetch_latest_wurfl() or force:
            self.wurfl_to_python()
            from wurfl import devices
            print "Done."
        else:
            print "Done. Wurfl unchanged."
