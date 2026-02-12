# Media Files Configuration for Railway

## Current Setup

The application now serves media files (uploaded project maps, etc.) in production through a custom Django view with proper CORS headers.

### Configuration

**Settings** (`land_sale/settings.py`):
- `MEDIA_URL = '/media/'`
- `MEDIA_ROOT = os.path.join(BASE_DIR, 'media')`

**URL Routing** (`land_sale/urls.py`):
- Development (DEBUG=True): Uses Django's built-in `static()` helper
- Production (DEBUG=False): Uses custom `serve_media` view with CORS support

**Custom View** (`land_sale/views.py`):
- `serve_media(request, path)`: Serves media files with:
  - Proper MIME type detection
  - CORS headers for cross-origin requests
  - Security checks to prevent directory traversal
  - Caching headers for performance

## ⚠️ Important: Railway Storage Limitation

**Railway uses ephemeral storage** - files uploaded to the filesystem will be **lost on every deployment or container restart**.

### Solutions for Persistent Media Storage

#### Option 1: Railway Volumes (Recommended for Railway)
Add a Railway volume to persist the media directory:

```bash
# In Railway dashboard or railway.toml
[volumes]
media = "/app/media"
```

#### Option 2: Cloud Storage (Best Practice for Production)
Use a cloud storage service like:

- **AWS S3** - Most popular
- **Cloudinary** - Great for images with transformations
- **Google Cloud Storage**
- **Azure Blob Storage**

To implement cloud storage, install `django-storages`:

```bash
pip install django-storages[s3]  # For AWS S3
```

Update settings:
```python
# settings.py
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": "your-bucket-name",
            "region_name": "us-east-1",
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
```

#### Option 3: Database Storage (Not Recommended)
Store files as BLOBs in the database. This works but can significantly slow down your database.

## Current Status

✅ Media files can be served in production
✅ CORS headers configured for frontend access
✅ ProjectSerializer returns absolute URLs with metadata
⚠️ Files are stored in ephemeral storage (will be lost on redeploy)

## Next Steps

1. **Immediate**: Deploy the current changes to Railway
2. **Short-term**: Set up Railway volume for persistence
3. **Long-term**: Consider migrating to cloud storage (S3/Cloudinary)

## Testing

To test media serving in production:

```bash
# Upload a file through the API
curl -X POST https://your-app.railway.app/land/create_project/ \
  -H "Authorization: Bearer <token>" \
  -F "name=Test Project" \
  -F "location=Test Location" \
  -F "size=100" \
  -F "project_svg_map=@/path/to/map.svg"

# Access the media file
curl https://your-app.railway.app/media/project_maps/map.svg
```

The file should be served with proper headers and be accessible from the frontend.
