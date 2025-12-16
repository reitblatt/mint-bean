# Docker Setup Guide

This guide covers both development and production Docker deployments for MintBean.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Production Setup](#production-setup)
- [Common Commands](#common-commands)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 2GB free disk space
- Port 8000 (backend) and 5173/80 (frontend) available

Check your Docker installation:

```bash
docker --version
docker compose version
```

## Development Setup

The development setup provides hot-reload for both frontend and backend, making it ideal for active development.

### 1. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and configure at minimum:

```env
# Required for authentication
SECRET_KEY=your-random-secret-key-change-this

# Plaid credentials (optional for development)
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_ENV=sandbox

# Beancount (optional)
BEANCOUNT_FILE_PATH=./example-data/example.beancount
BEANCOUNT_REPO_PATH=./example-data
```

### 2. Build and Start Services

Start all services in development mode:

```bash
docker compose up -d
```

Or build and start:

```bash
docker compose up --build -d
```

### 3. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. View Logs

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend

# Frontend only
docker compose logs -f frontend
```

### 5. Development Workflow

The development setup includes:

- **Hot Reload**: Code changes automatically reload
- **Volume Mounts**: Your local code is mounted in containers
- **Database Persistence**: SQLite database persists in `./data/`

Make changes to your code and they'll be reflected immediately.

## Production Setup

The production setup uses optimized multi-stage builds with minimal attack surface.

### 1. Environment Configuration

Create a production `.env` file:

```bash
cp .env.example .env
```

Configure production values:

```env
# IMPORTANT: Change these for production!
SECRET_KEY=<generate-a-strong-random-key>
DEBUG=false

# Database
DATABASE_URL=sqlite:///./data/mintbean.db

# Plaid Production
PLAID_CLIENT_ID=<your-production-client-id>
PLAID_SECRET=<your-production-secret>
PLAID_ENV=production

# CORS - Update with your actual domain
ALLOWED_ORIGINS=https://yourdomain.com
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]

# Beancount
BEANCOUNT_FILE_PATH=/path/to/your/beancount/main.beancount
BEANCOUNT_REPO_PATH=/path/to/your/beancount/repo
```

Generate a secure SECRET_KEY:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Build Production Images

```bash
docker compose -f docker-compose.prod.yml build
```

### 3. Start Production Services

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 4. Access Production Application

- **Frontend**: http://localhost (port 80)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 5. Production Features

The production setup includes:

- **Multi-stage builds**: Smaller image sizes
- **Non-root user**: Enhanced security
- **Health checks**: Automatic restart on failure
- **Nginx**: Optimized static file serving with gzip
- **4 workers**: Backend runs with multiple Uvicorn workers

### 6. SSL/TLS Setup (Recommended)

For production, use a reverse proxy like nginx or Caddy with SSL:

```nginx
# Example nginx config
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Or use Caddy (automatic HTTPS):

```
yourdomain.com {
    reverse_proxy localhost:80
    reverse_proxy /api/* localhost:8000
}
```

## Common Commands

### Starting Services

```bash
# Development
docker compose up -d

# Production
docker compose -f docker-compose.prod.yml up -d

# Build and start
docker compose up --build -d
```

### Stopping Services

```bash
# Development
docker compose down

# Production
docker compose -f docker-compose.prod.yml down

# Stop and remove volumes (WARNING: deletes database)
docker compose down -v
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend

# Last 100 lines
docker compose logs --tail=100
```

### Rebuilding

```bash
# Rebuild all services
docker compose build

# Rebuild specific service
docker compose build backend

# Force rebuild without cache
docker compose build --no-cache
```

### Executing Commands

```bash
# Run tests in backend
docker compose exec backend pytest

# Access backend shell
docker compose exec backend /bin/bash

# Access frontend shell
docker compose exec frontend /bin/sh

# Run database migrations
docker compose exec backend python migrate_add_environment.py
```

### Database Management

```bash
# Backup database
docker compose exec backend cp /app/data/mintbean.db /app/data/mintbean.db.backup

# Restore database (while stopped)
docker compose down
docker compose up -d
docker compose exec backend cp /app/data/mintbean.db.backup /app/data/mintbean.db
docker compose restart backend
```

### Monitoring

```bash
# View resource usage
docker compose stats

# View running containers
docker compose ps

# Check health status
docker compose ps
```

## Troubleshooting

### Container Won't Start

1. Check logs:
   ```bash
   docker compose logs backend
   docker compose logs frontend
   ```

2. Check health status:
   ```bash
   docker compose ps
   ```

3. Rebuild from scratch:
   ```bash
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   ```

### Port Already in Use

Change ports in `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Changed from 8000:8000
  frontend:
    ports:
      - "3000:5173"  # Changed from 5173:5173
```

### Database Issues

1. Check database file permissions:
   ```bash
   ls -la data/
   ```

2. Reset database (WARNING: deletes all data):
   ```bash
   docker compose down
   rm -f data/mintbean.db
   docker compose up -d
   ```

### Frontend Can't Connect to Backend

1. Check backend is running:
   ```bash
   docker compose ps backend
   curl http://localhost:8000/health
   ```

2. Check CORS settings in `.env`:
   ```env
   ALLOWED_ORIGINS=http://localhost:5173
   ```

3. Check network connectivity:
   ```bash
   docker compose exec frontend ping backend
   ```

### Out of Disk Space

Clean up Docker resources:

```bash
# Remove unused containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything unused (CAREFUL!)
docker system prune -a
```

### Permission Errors

Fix data directory permissions:

```bash
sudo chown -R $USER:$USER data/
chmod 755 data/
```

## Environment Variables Reference

### Backend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | - | JWT signing key |
| `DATABASE_URL` | Yes | sqlite:///./data/mintbean.db | Database connection |
| `DEBUG` | No | false | Debug mode |
| `ALLOWED_ORIGINS` | No | * | CORS allowed origins |
| `PLAID_CLIENT_ID` | No | - | Plaid API client ID |
| `PLAID_SECRET` | No | - | Plaid API secret |
| `PLAID_ENV` | No | sandbox | Plaid environment |
| `BEANCOUNT_FILE_PATH` | No | - | Path to beancount file |
| `BEANCOUNT_REPO_PATH` | No | - | Path to beancount repo |

### Frontend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | No | http://localhost:8000 | Backend API URL |

## Best Practices

### Development

1. Use volume mounts for hot-reload
2. Keep DEBUG=true
3. Use sandbox Plaid environment
4. Don't commit `.env` file
5. Regularly backup your database

### Production

1. Always use strong SECRET_KEY
2. Set DEBUG=false
3. Use production Plaid credentials
4. Set up proper CORS origins
5. Use HTTPS/SSL
6. Regular database backups
7. Monitor logs and health checks
8. Keep Docker images updated

### Security

1. Never commit secrets to git
2. Use `.dockerignore` to exclude sensitive files
3. Run containers as non-root user (production)
4. Keep dependencies updated
5. Use health checks
6. Implement rate limiting
7. Regular security audits

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [Vite Docker Guide](https://vitejs.dev/guide/env-and-mode.html)
