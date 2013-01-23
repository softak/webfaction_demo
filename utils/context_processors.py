from django.conf import settings as s

def settings(request):
    return {
       'DEV': s.DEV
    }
