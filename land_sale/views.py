from django.http import JsonResponse


def health_check(request):
    """Health check endpoint for monitoring"""
    return JsonResponse({"status": "ok", "service": "land_sale"})
