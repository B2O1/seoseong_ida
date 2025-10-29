from django.conf import settings

def naver_maps(request):
    return {
        "NAVER_MAPS_CLIENT_ID": settings.NAVER_MAPS_CLIENT_ID
    }

 