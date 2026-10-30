import json
from functools import wraps
from django.core.cache import cache
from django.http import HttpResponse

def rate_limit(key, limit=5, period=300):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            k = f"{key}:{request.META.get('REMOTE_ADDR', 'x')}"
            n = cache.get(k, 0)
            if n >= limit:
                r = HttpResponse(status=204)
                r['HX-Trigger'] = json.dumps({'showToast': {'title': 'Dibatasi',
                    'message': 'Terlalu banyak percobaan, coba lagi nanti.', 'type': 'error'}})
                return r
            cache.set(k, n + 1, period)
            return view(request, *args, **kwargs)
        return wrapper
    return decorator