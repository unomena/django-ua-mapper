Django UA Mapper
================

A simple Django management command mapping the complete set of Wurfl database User-Agent header strings to some value determined by a user defined module. The resulting value is stored in Redis with the md5'd User-Agent header string as key.


Installation
------------
#. Install or add django-ua-mapper to your Python path.
#. Add ``ua_mapper`` to your ``INSTALLED_APPS`` setting in your project's ``settings.py`` file. 
#. Add a ``UA_MAPPER_REDIS`` setting to your project's ``settings.py`` file. This setting specifies the host and port to the Redis instance you want to use for storage, i.e::

    UA_MAPPER_REDIS = '127.0.0.1:6379'

#. Add a ``UA_MAPPER_CLASS`` setting to your project's ``settings.py`` file. This setting specifies the module to use for the actual mapping (see Mapper Class below), i.e.::

    UA_MAPPER_CLASS = 'project.uamappers.SimpleMapper'

#. Optionally add a ``UA_MAPPER_KEY_PREFIX`` setting to your project's ``settings.py`` file. This setting specifies a prefix string to use in combination with the User-Agent header string as Redis key, i.e.::

    UA_MAPPER_KEY_PREFIX = 'projectkeyprefix'

#. Optionally if you want to be able to map User-Agent header strings directly through a Django view, add ua_mapper url include to the project's urls.py file::
    
    (r'^mapper/', include('ua_mapper.urls')),

Now if you hit ``http://<host>/mapper/map-request/`` a mapping will be performed and its result stored in Redis for the requesting User-Agent header string.

Usage
-----

Update Wurfl Database
~~~~~~~~~~~~~~~~~~~~~

#. To update the Wurfl database run the ``updatewurfl`` command as follows::

    $ ./manage.py updatewurfl

#. The Wurfl database will only be updated when a new downloadable Wurfl database is found. To force an update run the command as follows::

    $ ./manage.py updatewurfl --force

Perform Wurfl to Redis Mapping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. To map the complete set of Wurfl devices to Redis run the ``mapuseragents`` command as follows::

    $ ./manage.py mapuseragents

#. Redis will only be updated when no new Wurfl database could be found. To force an update run the command as follows::

    $ ./manage.py mapuseragents --force

Mapper Class
------------
The mapper class is a single Python class that defines the following method:

map
~~~

map(self, device)

``device`` is a Wurfl device object. This method is called for each device in the Wurfl database whenever ``mapuseragents`` is run. ``map()`` must return a string, which will be stored in Redis as the value for the md5'd User-Agent key. 

Example
~~~~~~~

This example mapper returns a simple category string for each device, based on the device's resolution::

    class SimpleMapper(object):
        def map(self, device):
            if device.resolution_width < 240:
                return 'medium'
            else:
                return 'high'


