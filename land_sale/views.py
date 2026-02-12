from django.http import JsonResponse, HttpResponse, Http404
from django.conf import settings
import os
import mimetypes


def health_check(request):
    """Health check endpoint for monitoring"""
    return JsonResponse({"status": "ok", "service": "land_sale"})


def serve_media(request, path):
    """
    Serve media files in production with proper headers
    This view is used when DEBUG=False to ensure media files are accessible
    """
    # Build the full file path
    file_path = os.path.join(settings.MEDIA_ROOT, path)

    # Security check: prevent directory traversal attacks
    if not os.path.abspath(file_path).startswith(os.path.abspath(settings.MEDIA_ROOT)):
        raise Http404("Invalid file path")

    # Check if file exists
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise Http404("File not found")

    # Determine content type
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = 'application/octet-stream'

    # Read and serve the file
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()

        response = HttpResponse(file_data, content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
        response['Cache-Control'] = 'public, max-age=31536000'  # Cache for 1 year

        # Add CORS headers for cross-origin access
        if 'HTTP_ORIGIN' in request.META:
            origin = request.META['HTTP_ORIGIN']
            allowed_origins = [
                'http://localhost:3000',
                'http://localhost:3006',
                'https://map-details.vercel.app'
            ]
            if origin in allowed_origins:
                response['Access-Control-Allow-Origin'] = origin
                response['Access-Control-Allow-Credentials'] = 'true'

        return response
    except Exception as e:
        raise Http404(f"Error serving file: {str(e)}")
