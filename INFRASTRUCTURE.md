# MintBean Production Infrastructure

## Self-Hosting Philosophy

MintBean is designed to be **fully self-hosted** with no mandatory SaaS dependencies. This approach provides:

- **Full Data Control**: All user financial data remains on infrastructure you control
- **No Vendor Lock-in**: Freedom to modify, migrate, or scale without vendor constraints
- **Cost Predictability**: No per-seat, per-request, or usage-based pricing surprises
- **Privacy**: No third-party access to sensitive financial information
- **Customization**: Ability to modify and extend all components

## Infrastructure Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Load Balancer / TLS                      │
│                    (Nginx + Let's Encrypt)                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│   Frontend     │    │    Backend      │    │   Monitoring    │
│   (React SPA)  │    │   (FastAPI)     │    │   Dashboard     │
│                │    │                 │    │  (Grafana UI)   │
└────────────────┘    └────────┬────────┘    └─────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
│   PostgreSQL   │   │   Prometheus    │   │   Grafana Loki  │
│   (Database)   │   │   (Metrics)     │   │   (Logs)        │
└────────────────┘   └─────────────────┘   └─────────────────┘
```

## Self-Hosted Observability Stack

### Error Tracking
**Options (choose one):**

#### Option 1: GlitchTip (Recommended)
- **Lightweight**: Minimal resource usage (~200MB RAM)
- **Sentry-compatible**: Drop-in replacement for Sentry SDK
- **Simple Setup**: Single Docker container
- **URL**: https://glitchtip.com

```yaml
services:
  glitchtip:
    image: glitchtip/glitchtip:latest
    environment:
      - DATABASE_URL=postgres://...
      - SECRET_KEY=...
      - EMAIL_URL=...  # Optional
    ports:
      - "8080:8080"
```

#### Option 2: Self-Hosted Sentry
- **Full-featured**: Complete Sentry experience
- **Resource-intensive**: ~4GB RAM minimum
- **Complex Setup**: 10+ containers required
- **URL**: https://develop.sentry.dev/self-hosted/

**Backend Integration:**
```python
# app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="http://your-glitchtip-instance/project-id",
    integrations=[FastApiIntegration()],
    environment="production",
)
```

### Centralized Logging
**Stack: Grafana Loki + Promtail**

- **Loki**: Log aggregation and storage (like Elasticsearch, but simpler)
- **Promtail**: Log shipping agent (runs on each host)
- **Grafana**: Unified dashboard for logs and metrics

**Why Loki over ELK Stack:**
- 10x lower resource usage (~300MB RAM vs 3GB for Elasticsearch)
- No indexing overhead (labels instead of full-text indices)
- Native Grafana integration
- Purpose-built for container logs

**Docker Compose:**
```yaml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yaml:/etc/loki/local-config.yaml
      - loki_data:/loki

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail-config.yaml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
```

**Backend Configuration:**
```python
# app/core/logging.py
import logging
import logging_loki

handler = logging_loki.LokiHandler(
    url="http://loki:3100/loki/api/v1/push",
    tags={"application": "mintbean-backend", "environment": "production"},
    version="1",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), handler],
)
```

### Metrics & Monitoring
**Stack: Prometheus + Grafana**

**Prometheus:**
- Time-series metrics database
- Pull-based model (scrapes /metrics endpoints)
- Powerful query language (PromQL)
- Built-in alerting

**Grafana:**
- Unified visualization for metrics (Prometheus) and logs (Loki)
- Pre-built dashboards available
- Alerting and notifications

**Docker Compose:**
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=changeme
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
```

**Backend Metrics:**
```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, make_asgi_app

# Define metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"]
)

# Add middleware to collect metrics
# app/main.py
from prometheus_client import make_asgi_app

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### Uptime Monitoring
**Tool: Uptime Kuma**

- **Simple**: Web-based uptime monitoring UI
- **Multi-protocol**: HTTP, TCP, Ping, DNS, Docker, etc.
- **Notifications**: Email, Slack, Discord, Telegram, etc.
- **Status Pages**: Public status page generation

**Docker Compose:**
```yaml
services:
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    ports:
      - "3001:3001"
    volumes:
      - uptime-kuma_data:/app/data
```

**Monitors to Configure:**
- Backend API health endpoint: `https://api.mintbean.com/health`
- Frontend application: `https://mintbean.com`
- PostgreSQL connectivity (via Docker monitor)
- SSL certificate expiration

### Database Backups
**Tool: pgBackRest**

- **Industry Standard**: Used by major PostgreSQL deployments
- **Incremental Backups**: Full, differential, and incremental backup types
- **Point-in-Time Recovery**: Restore to any timestamp
- **Compression**: Automatic backup compression
- **Encryption**: Optional backup encryption

**Alternative: Simple pg_dump Script**

For simpler deployments, a cron-based pg_dump script:

```bash
#!/bin/bash
# backend/scripts/backup.sh

BACKUP_DIR="/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/mintbean_$DATE.sql.gz"

# Create backup
docker exec mintbean-postgres pg_dump -U mintbean_user mintbean | gzip > "$BACKUP_FILE"

# Keep only last 30 days
find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +30 -delete

# Upload to off-site storage (optional)
# aws s3 cp "$BACKUP_FILE" s3://your-bucket/backups/
```

**Cron Configuration:**
```cron
# Daily backups at 2 AM
0 2 * * * /path/to/backend/scripts/backup.sh
```

## TLS/HTTPS Setup
**Tool: Nginx + Certbot (Let's Encrypt)**

**Why Nginx:**
- Industry-standard reverse proxy
- Efficient static file serving
- Advanced load balancing
- Rate limiting capabilities

**Nginx Configuration:**
```nginx
# nginx/nginx.conf
upstream backend {
    server backend:8000;
}

server {
    listen 443 ssl http2;
    server_name mintbean.com;

    ssl_certificate /etc/letsencrypt/live/mintbean.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mintbean.com/privkey.pem;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Frontend
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name mintbean.com;
    return 301 https://$host$request_uri;
}
```

**Let's Encrypt Setup:**
```yaml
# docker-compose.prod.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
      - certbot_conf:/etc/letsencrypt
      - certbot_www:/var/www/certbot
    command: "/bin/sh -c 'while :; do sleep 6h & wait $${!}; nginx -s reload; done & nginx -g \"daemon off;\"'"

  certbot:
    image: certbot/certbot
    volumes:
      - certbot_conf:/etc/letsencrypt
      - certbot_www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
```

**Initial Certificate:**
```bash
docker compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  -d mintbean.com \
  -d api.mintbean.com \
  --email admin@mintbean.com \
  --agree-tos
```

## Deployment Scenarios

### Scenario 1: Single Server (Small Scale)
**Suitable for**: <1,000 users, development/staging

```
Single VPS/Cloud Instance (4 vCPU, 8GB RAM):
├── Frontend (Nginx)
├── Backend (FastAPI)
├── PostgreSQL
├── Loki + Promtail
├── Prometheus
├── Grafana
└── GlitchTip
```

**Estimated Resources:**
- CPU: 2-3 vCPU average, 4 vCPU peak
- RAM: 4-6 GB average, 8 GB peak
- Storage: 50 GB SSD (20 GB app, 30 GB logs/metrics)

### Scenario 2: Multi-Container (Medium Scale)
**Suitable for**: 1,000-10,000 users

```
App Server (4 vCPU, 8GB RAM):
├── Frontend (Nginx)
├── Backend (FastAPI) x2 instances
└── Promtail

Database Server (2 vCPU, 4GB RAM, 100GB SSD):
└── PostgreSQL

Monitoring Server (2 vCPU, 4GB RAM, 100GB SSD):
├── Loki
├── Prometheus
├── Grafana
└── GlitchTip
```

**Estimated Resources:**
- Total: 8 vCPU, 16 GB RAM
- Storage: 250 GB total (100 GB DB, 150 GB monitoring)

### Scenario 3: Kubernetes (Large Scale)
**Suitable for**: >10,000 users, high availability

- Horizontal pod autoscaling for backend
- StatefulSet for PostgreSQL with replication
- Persistent volumes for data
- Helm charts for monitoring stack
- Ingress controller for TLS termination

## Docker Compose Organization

```
mint-bean/
├── docker-compose.yml              # Development environment
├── docker-compose.prod.yml         # Production application
├── docker-compose.monitoring.yml   # Monitoring stack (optional split)
├── .env.example                    # Environment template
├── .env                           # Actual environment (gitignored)
│
├── backend/
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   └── scripts/
│       ├── backup.sh
│       └── init-db.sh
│
├── frontend/
│   ├── Dockerfile
│   └── Dockerfile.prod
│
├── nginx/
│   ├── nginx.conf
│   └── ssl/                       # Let's Encrypt certificates
│
└── monitoring/
    ├── prometheus/
    │   └── prometheus.yml
    ├── loki/
    │   └── loki-config.yaml
    ├── promtail/
    │   └── promtail-config.yaml
    └── grafana/
        ├── dashboards/
        └── datasources/
```

## Resource Requirements Summary

### Minimum (Development/Staging)
- **CPU**: 2 vCPU
- **RAM**: 4 GB
- **Storage**: 20 GB SSD
- **Cost**: ~$20-40/month (DigitalOcean, Hetzner, Linode)

### Recommended (Small Production <1K users)
- **CPU**: 4 vCPU
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **Cost**: ~$40-80/month

### Scaling (Medium Production 1K-10K users)
- **CPU**: 8 vCPU (across multiple servers)
- **RAM**: 16 GB
- **Storage**: 250 GB SSD
- **Cost**: ~$150-300/month

### Enterprise (>10K users)
- **Kubernetes cluster**: 3+ nodes
- **CPU**: 16+ vCPU
- **RAM**: 32+ GB
- **Storage**: 500+ GB SSD
- **Cost**: $500+/month

## Security Considerations

### Data Protection
- **At-rest encryption**: Fernet encryption for Plaid secrets and database passwords
- **In-transit encryption**: TLS 1.2+ for all external communications
- **Database encryption**: Optional PostgreSQL transparent data encryption (TDE)
- **Backup encryption**: Optional pgBackRest backup encryption

### Access Control
- **Row-Level Security (RLS)**: PostgreSQL policies enforce data isolation
- **JWT authentication**: Stateless token-based auth with expiration
- **Rate limiting**: slowapi protects against brute force (5/min login, 3/hour onboarding)
- **CORS configuration**: Strict origin whitelisting

### Network Security
- **Firewall**: Only expose ports 80 (HTTP), 443 (HTTPS)
- **Internal networking**: Docker bridge networks for service isolation
- **Database access**: PostgreSQL only accessible from backend container
- **Monitoring access**: Grafana behind authentication

### Secrets Management
- **Environment variables**: Never commit to git (.env in .gitignore)
- **Docker secrets**: Use Docker secrets for sensitive configs in production
- **Encryption key**: ENCRYPTION_KEY stored securely, backed up separately
- **API keys**: Plaid secrets encrypted in database, only decrypted on use

## Cost Comparison: Self-Hosted vs SaaS

### SaaS Stack (1,000 users)
- Sentry: $26/month (Team plan)
- Datadog: $15/host/month = $45/month (3 hosts)
- PagerDuty: $21/user/month = $63/month (3 on-call)
- AWS RDS PostgreSQL: $50/month
- **Total: ~$184/month** ($2,208/year)

### Self-Hosted Stack (1,000 users)
- VPS (4 vCPU, 8GB RAM): $40/month (Hetzner)
- Database VPS (2 vCPU, 4GB RAM): $20/month
- Backups storage: $5/month (100 GB S3)
- Domain + SSL: $12/year = $1/month
- **Total: ~$66/month** ($792/year)

**Savings: $118/month ($1,416/year) or 64% cheaper**

### Additional Self-Hosted Benefits
- No per-user pricing (scales to 10K users at same cost)
- No data egress fees
- No vendor lock-in migration costs
- Full control over retention periods
- No surprise billing from usage spikes

## Migration Path from SaaS (If Needed)

If you've already deployed with SaaS solutions:

1. **Set up self-hosted infrastructure** alongside existing SaaS
2. **Dual-write logs/metrics** to both systems during transition
3. **Validate self-hosted dashboards** match SaaS alerts
4. **Switch primary monitoring** to self-hosted
5. **Keep SaaS as backup** for 1-2 billing cycles
6. **Cancel SaaS subscriptions** once confident

**Rollback Plan**: If self-hosted monitoring fails, SaaS is still active.

## Next Steps

To implement this infrastructure:

1. **Review PRODUCTION_READINESS.md** for prioritized tasks
2. **Start with monitoring stack**: Prometheus + Grafana + Loki (Day 1-2)
3. **Add error tracking**: GlitchTip (Day 3)
4. **Implement backups**: pg_dump script with cron (Day 4)
5. **Set up TLS**: Nginx + Let's Encrypt (Day 5)
6. **Configure alerting**: Grafana alerts + Uptime Kuma (Day 6)
7. **Load test**: Validate performance under expected load (Day 7)
8. **Document runbooks**: Common issues and solutions (Day 8)

All components are self-hosted, open-source, and production-ready.
