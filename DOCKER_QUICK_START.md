# Docker Quick Start

Get MintBean running with Docker in under 5 minutes.

## Prerequisites

- Docker Desktop installed and running
- At least 2GB free disk space

## Development Mode (with hot-reload)

### 1. Clone and Configure

```bash
git clone <repository-url>
cd mint-bean
cp .env.example .env
```

### 2. Edit `.env` (Minimum Required)

```env
SECRET_KEY=change-this-to-something-random
```

### 3. Start the Application

```bash
make docker-dev-build
```

That's it! The application is now running:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000/docs

### 4. View Logs

```bash
make docker-dev-logs
```

Press `Ctrl+C` to stop viewing logs (containers keep running).

### 5. Stop the Application

```bash
make docker-dev-down
```

## Production Mode (optimized builds)

### 1. Configure for Production

Edit `.env` with production values:

```env
SECRET_KEY=<generate-strong-random-key>
DEBUG=false
PLAID_CLIENT_ID=<your-production-id>
PLAID_SECRET=<your-production-secret>
PLAID_ENV=production
ALLOWED_ORIGINS=https://yourdomain.com
```

### 2. Build and Start

```bash
make docker-prod-build
```

Access:
- Frontend: http://localhost (port 80)
- Backend: http://localhost:8000/docs

### 3. Stop Production

```bash
make docker-prod-down
```

## Useful Commands

```bash
# Development
make docker-dev              # Start (without rebuilding)
make docker-dev-build        # Build and start
make docker-dev-down         # Stop
make docker-dev-logs         # View logs
make docker-dev-restart      # Restart services

# Production
make docker-prod             # Start
make docker-prod-build       # Build images
make docker-prod-down        # Stop
make docker-prod-logs        # View logs

# Maintenance
make docker-clean            # Remove containers and volumes
make docker-prune            # Clean up unused Docker resources

# Testing
make test-docker             # Run tests in Docker
```

## Troubleshooting

### Can't connect to frontend

1. Check if containers are running:
   ```bash
   docker compose ps
   ```

2. Wait for health checks (can take 30-40s for backend):
   ```bash
   make docker-dev-logs
   ```

### Port already in use

Edit `docker-compose.yml` to use different ports:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Changed from 8000
  frontend:
    ports:
      - "3000:5173"  # Changed from 5173
```

### Database errors

Reset the database:

```bash
make docker-dev-down
rm -f data/mintbean.db
make docker-dev-build
```

### Out of disk space

Clean up Docker:

```bash
make docker-prune
```

## Next Steps

- Read full documentation: [DOCKER.md](DOCKER.md)
- Configure Plaid integration
- Set up SSL/TLS for production
- Configure custom beancount files

## Getting Help

- Check logs: `make docker-dev-logs`
- Full docs: See [DOCKER.md](DOCKER.md)
- Issues: https://github.com/your-repo/issues
