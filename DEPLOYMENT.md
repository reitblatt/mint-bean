# MintBean Production Deployment Guide

This guide explains how to deploy MintBean in various production scenarios with runtime configuration support.

## Overview

MintBean now supports **runtime configuration** for the frontend, meaning you can:
- Build the Docker images once
- Deploy them to any environment
- Configure the API URL at container startup (not build time)

## Configuration Files

### `.env` File

Create a `.env` file in the project root with your configuration:

```bash
# Backend Configuration
DATABASE_URL=sqlite:///./data/mintbean.db
SECRET_KEY=<generate-with-openssl-rand-hex-32>
DEBUG=false

# CORS - Allow your frontend domain(s)
ALLOWED_ORIGINS=https://mint.reitblatt.co

# Beancount Configuration
BEANCOUNT_FILE_PATH=/path/to/your/beancount/main.beancount
BEANCOUNT_REPO_PATH=/path/to/your/beancount/repo

# Plaid Configuration
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_ENV=production  # or sandbox

# Frontend API URL (runtime configuration)
API_URL=/api/v1  # See deployment scenarios below

# Application Settings
LOG_LEVEL=INFO
```

## Deployment Scenarios

### Scenario 1: Single Domain with Path-Based Routing (Recommended)

**Setup**: Frontend and backend on same domain, different paths
- `https://mint.reitblatt.co/` → Frontend
- `https://mint.reitblatt.co/api/*` → Backend

**Configuration**:
```bash
# .env
ALLOWED_ORIGINS=https://mint.reitblatt.co
API_URL=/api/v1
```

**Reverse Proxy (Nginx)**:
```nginx
server {
    listen 443 ssl http2;
    server_name mint.reitblatt.co;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:8080;  # frontend container
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;  # backend container
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Docker Compose**:
```yaml
# Expose only to localhost, reverse proxy handles external access
services:
  mintbean-backend:
    ports:
      - "127.0.0.1:8000:8000"

  mintbean-frontend:
    ports:
      - "127.0.0.1:8080:80"
```

### Scenario 2: Different Subdomains

**Setup**:
- `https://mint.reitblatt.co` → Frontend
- `https://api.mint.reitblatt.co` → Backend

**Configuration**:
```bash
# .env
ALLOWED_ORIGINS=https://mint.reitblatt.co
API_URL=https://api.mint.reitblatt.co/api/v1
```

**Reverse Proxy (Nginx)**:
```nginx
# Frontend
server {
    listen 443 ssl http2;
    server_name mint.reitblatt.co;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8080;
        # ... proxy headers
    }
}

# Backend
server {
    listen 443 ssl http2;
    server_name api.mint.reitblatt.co;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        # ... proxy headers
    }
}
```

### Scenario 3: Completely Different Servers

**Setup**:
- Frontend on `server1.example.com`
- Backend on `server2.example.com`

**Backend Server `.env`**:
```bash
ALLOWED_ORIGINS=https://server1.example.com
```

**Frontend Server `.env`**:
```bash
API_URL=https://server2.example.com/api/v1
```

### Scenario 4: Direct Container Access (No Reverse Proxy)

**Setup**: Access containers directly on their ports

**Configuration**:
```bash
# .env
ALLOWED_ORIGINS=http://your-server-ip:8080
API_URL=http://your-server-ip:8000/api/v1
```

**Docker Compose**:
```yaml
services:
  mintbean-backend:
    ports:
      - "8000:8000"

  mintbean-frontend:
    ports:
      - "8080:80"
```

## Deployment Steps

### 1. Build Images

```bash
# Build both services
docker compose -f docker-compose.prod.yml build
```

### 2. Configure Environment

```bash
# Generate secure secret key
openssl rand -hex 32

# Create .env file with your configuration
cp .env.example .env
# Edit .env with your settings
```

### 3. Start Services

```bash
# Start in detached mode
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Check status
docker compose -f docker-compose.prod.yml ps
```

### 4. Verify Configuration

```bash
# Check frontend config was generated
docker exec mintbean-frontend cat /usr/share/nginx/html/config.js

# Should show:
# window.__RUNTIME_CONFIG__ = {
#   apiUrl: '/api/v1'
# };
```

## SSL/TLS Setup

### Using Caddy (Easiest)

Caddy automatically handles SSL certificates via Let's Encrypt:

```caddyfile
mint.reitblatt.co {
    # Frontend
    handle /* {
        reverse_proxy localhost:8080
    }

    # Backend
    handle /api/* {
        reverse_proxy localhost:8000
    }
}
```

### Using Certbot with Nginx

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d mint.reitblatt.co

# Certificates auto-renew
```

## Monitoring and Maintenance

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f mintbean-backend
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Backup Database

```bash
# Backup SQLite database
cp data/mintbean.db data/mintbean.db.backup-$(date +%Y%m%d)

# Or use docker volume backup
docker run --rm -v $(pwd)/data:/data -v $(pwd)/backups:/backups \
  alpine sh -c "cp /data/mintbean.db /backups/mintbean.db.backup-$(date +%Y%m%d)"
```

## Troubleshooting

### Frontend Can't Connect to Backend

1. Check runtime config:
   ```bash
   docker exec mintbean-frontend cat /usr/share/nginx/html/config.js
   ```

2. Verify CORS settings match your domain:
   ```bash
   docker compose -f docker-compose.prod.yml exec mintbean-backend env | grep ALLOWED_ORIGINS
   ```

3. Check browser console for CORS errors

### Permission Errors

```bash
# Ensure data directory has correct permissions
chmod 777 data
```

### Container Won't Start

```bash
# Check logs for errors
docker compose -f docker-compose.prod.yml logs

# Verify .env file exists and is valid
cat .env
```

## Security Checklist

- [ ] Set strong `SECRET_KEY` (32+ random characters)
- [ ] Set `DEBUG=false` in production
- [ ] Configure `ALLOWED_ORIGINS` to your specific domain(s), never use "*"
- [ ] Use HTTPS/SSL in production
- [ ] Keep Plaid credentials secure
- [ ] Regularly backup database
- [ ] Keep Docker images updated
- [ ] Restrict database file permissions (chmod 600 data/mintbean.db)

## Example: mint.reitblatt.co Setup

For your specific case with `mint.reitblatt.co`:

### .env
```bash
ALLOWED_ORIGINS=https://mint.reitblatt.co
API_URL=/api/v1
SECRET_KEY=<your-secret-key>
DEBUG=false
PLAID_ENV=production
```

### Nginx Config
```nginx
server {
    listen 443 ssl http2;
    server_name mint.reitblatt.co;

    ssl_certificate /etc/letsencrypt/live/mint.reitblatt.co/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mint.reitblatt.co/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name mint.reitblatt.co;
    return 301 https://$server_name$request_uri;
}
```

### Docker Compose Ports
```yaml
# Update docker-compose.prod.yml
services:
  mintbean-backend:
    ports:
      - "127.0.0.1:8000:8000"

  mintbean-frontend:
    ports:
      - "127.0.0.1:8080:80"
```

Then run:
```bash
docker compose -f docker-compose.prod.yml up -d
```
