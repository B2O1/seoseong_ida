from django.conf import settings

def naver_maps(request):
    return {
        "NAVER_MAPS_CLIENT_ID": settings.NAVER_MAPS_CLIENT_ID
    }
def google_maps(request):
    return{
        "GOOGLE_API_KEY" : settings.GOOGLE_API_KEY
    }
