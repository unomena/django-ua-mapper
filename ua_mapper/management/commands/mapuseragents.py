from ua_mapper.management.commands import updatewurfl
from ua_mapper.mapper import UAMapper 

class Command(updatewurfl.Command):
    help = 'Maps Wurfl devices to Redis.'

    def handle(self, force, *args, **options):
        mapper = UAMapper()
        if self.fetch_latest_wurfl() or force:
            self.wurfl_to_python()
            from wurfl import devices
            print "Updating Redis..."
            for i, ua in enumerate(devices.uas):
                device = devices.select_ua(ua)
                mapper.map(user_agent=ua, device=device)
            print "Done."
        else:
            print "Done. Redis unchanged."
