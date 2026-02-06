# Digital Ocean Deployment Guide

## Gunicorn Configuration for Port 8080

This project includes optimized Gunicorn configurations for deploying to Digital Ocean with port 8080.

## Files Overview

### 1. Procfile (Current - Inline Configuration)
```
release: python3 manage.py migrate --noinput && python3 manage.py collectstatic --noinput
web: gunicorn land_sale.wsgi:application --bind 0.0.0.0:8080 --workers 4 --threads 2 --worker-class gthread --timeout 120 --max-requests 1000 --max-requests-jitter 50 --access-logfile - --error-logfile - --log-level info --preload
```

**Use this if:** You prefer all configuration in one line (good for Railway, Heroku, Digital Ocean App Platform)

### 2. gunicorn.conf.py (Recommended for Production)
A dedicated Gunicorn configuration file with:
- Dynamic port binding (defaults to 8080)
- Environment variable support
- Worker management
- Logging configuration
- Performance optimizations

**Use this if:** You want cleaner, more maintainable configuration

To use: Replace Procfile content with:
```
release: python3 manage.py migrate --noinput && python3 manage.py collectstatic --noinput
web: gunicorn land_sale.wsgi:application -c gunicorn.conf.py
```

### 3. start_server.sh
Manual startup script for SSH/VM deployments.

**Use this if:** You're deploying directly to a VM or droplet

```bash
chmod +x start_server.sh
./start_server.sh
```

## Configuration Explained

### Workers & Threads
```
workers = 4          # Number of worker processes
threads = 2          # Threads per worker
worker_class = gthread  # Threaded workers for better concurrency
```

**Calculation:**
- Workers: `(2 * CPU_cores) + 1` (but start conservative with 4)
- Threads: 2-4 per worker
- Total concurrent requests: workers × threads = 4 × 2 = 8

**Adjust based on:**
- CPU cores available on your Digital Ocean droplet
- Memory available (each worker ~30-50MB)
- Request patterns (I/O bound vs CPU bound)

### Timeouts
```
timeout = 120        # Worker timeout in seconds
keepalive = 5        # Keep-alive timeout
```

**Adjust based on:**
- Pesapal API response times
- Database query complexity
- File upload sizes

### Memory Management
```
max_requests = 1000           # Restart worker after N requests
max_requests_jitter = 50      # Add randomness to prevent all workers restarting together
```

**Prevents memory leaks** by periodically recycling workers.

### Logging
```
accesslog = '-'      # Log to stdout
errorlog = '-'       # Log errors to stderr
loglevel = 'info'    # Log level
```

Digital Ocean will capture these logs in their dashboard.

## Environment Variables

Set these in Digital Ocean App Platform or your .env file:

```bash
# Required
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Optional - Gunicorn tuning
PORT=8080                      # Default: 8080
GUNICORN_WORKERS=4             # Default: 4
GUNICORN_THREADS=2             # Default: 2
GUNICORN_LOG_LEVEL=info        # Default: info

# Pesapal
PESAPAL_CONSUMER_KEY=...
PESAPAL_CONSUMER_SECRET=...
PESAPAL_ENVIRONMENT=live
```

## Digital Ocean App Platform Setup

1. **Create App** → Choose "Web Service"

2. **Configure Build Command:**
   ```
   pip install -r requirements.txt
   ```

3. **Configure Run Command (Option A - Using Procfile):**
   Digital Ocean automatically uses Procfile if present

4. **Configure Run Command (Option B - Direct):**
   ```
   gunicorn land_sale.wsgi:application -c gunicorn.conf.py
   ```

5. **Configure Port:**
   - HTTP Port: 8080
   - HTTP Routes: / (all traffic)

6. **Environment Variables:**
   Add all required variables from .env

## Digital Ocean Droplet (VM) Setup

### 1. Install Dependencies
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx postgresql
```

### 2. Setup Project
```bash
cd /var/www
git clone <your-repo>
cd land_sale
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
nano .env
# Add all environment variables
```

### 4. Run Migrations
```bash
python3 manage.py migrate
python3 manage.py collectstatic --noinput
```

### 5. Start Server
```bash
./start_server.sh
```

### 6. Configure Nginx (Optional)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/land_sale/staticfiles/;
    }
}
```

### 7. Create Systemd Service (Recommended)
```bash
sudo nano /etc/systemd/system/landsale.service
```

```ini
[Unit]
Description=Land Sale API
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/land_sale
Environment="PATH=/var/www/land_sale/venv/bin"
ExecStart=/var/www/land_sale/start_server.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable landsale
sudo systemctl start landsale
sudo systemctl status landsale
```

## Performance Tuning

### For Small Droplet (1 CPU, 1GB RAM):
```python
# gunicorn.conf.py
workers = 2
threads = 2
```

### For Medium Droplet (2 CPU, 2GB RAM):
```python
workers = 4
threads = 2
```

### For Large Droplet (4 CPU, 4GB RAM):
```python
workers = 8
threads = 4
```

## Monitoring & Health Checks

### Health Check Endpoint
```
GET /health/
```

Configure in Digital Ocean:
- Health Check Path: `/health/`
- Health Check Port: 8080

### View Logs
```bash
# Digital Ocean App Platform
do-cli apps logs <app-id>

# Droplet/VM
journalctl -u landsale -f
```

## Troubleshooting

### Server won't start on port 8080
```bash
# Check if port is in use
sudo lsof -i :8080

# Check Gunicorn logs
tail -f /var/log/gunicorn-error.log
```

### Workers timing out
Increase timeout in `gunicorn.conf.py`:
```python
timeout = 180  # 3 minutes
```

### High memory usage
Reduce workers or increase max_requests:
```python
workers = 2
max_requests = 500
```

### Database connection errors
Ensure DATABASE_URL is correctly set:
```bash
echo $DATABASE_URL
```

## Production Checklist

- [ ] DEBUG=False in settings
- [ ] SECRET_KEY is unique and secure
- [ ] ALLOWED_HOSTS configured
- [ ] DATABASE_URL points to production database
- [ ] PESAPAL_ENVIRONMENT=live
- [ ] Static files collected
- [ ] Migrations applied
- [ ] SSL/HTTPS enabled
- [ ] Environment variables secured
- [ ] Health checks configured
- [ ] Logging enabled
- [ ] Backup strategy in place

## Support

For issues, check:
1. Digital Ocean logs
2. Django logs: `python3 manage.py check --deploy`
3. Database connectivity: `python3 manage.py dbshell`
