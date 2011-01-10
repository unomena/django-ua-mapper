Django UA Mapper
================

A simple Django management command mapping User-Agent header strings to some value determined by a user defined module. The resulting value is stored in Redis with the User-Agent header string as key.


Installation
------------
#. Install or add django-ua-mapper to your Python path.
#. Add a ``UA_MAPPER_REDIS`` setting to your project's ``settings.py`` file. This setting specifies the host and port to the Redis instance you want to use for storage, i.e::

    UA_MAPPER_REDIS = '127.0.0.1:6379'

#. Add a ``UA_MAPPER_CLASS`` setting to your project's ``settings.py`` file. This setting specifies the module to use for the actual mapping (see Mapper Class below), i.e.::

    UA_MAPPER_CLASS = 'project.uamappers.SimpleMapper'


Usage
-----

#. Run the command as follows::

    $ ./manage.py mapuseragents

Mapper Class
------------
The mapper class is a single Python class that defines the following method:

map
~~~

map(self, device)

Device is a Wurfl device object. This method is called for each device in the Wurfl database whenever ``mapuseragents`` is run. map() must return a string, which will be stored in Redis as the value for the User-Agent key. 

Example
~~~~~~~

This example mapper returns a simple category string for each device, based on the device's resolution::

    class SimpleMapper(object):
        def map(self, device):
            if device.resolution_width < 240:
                return 'medium'
            else:
                return 'high'

