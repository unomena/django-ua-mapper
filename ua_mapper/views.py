from django.http import HttpResponse

from ua_mapper.mapper import UAMapper

def map_request(request):
    mapper = UAMapper()
    user_agent, device, value = mapper.map_by_request(request)
    return HttpResponse(value)
