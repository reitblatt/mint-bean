# Nginx Proxy Manager Setup for MintBean

This guide shows how to configure MintBean with Nginx Proxy Manager (NPM).

## Architecture

```
Internet → NPM (port 443) → {
  mint.reitblatt.co/       → mintbean-frontend:80
  mint.reitblatt.co/api/*  → mintbean-backend:8000
}
```

All communication happens via Docker network - no host ports needed.

## Step 1: Start MintBean

### Configure `.env`
```bash
ALLOWED_ORIGINS=https://mint.reitblatt.co
API_URL=/api/v1
SECRET_KEY=<generate-with-openssl-rand-hex-32>
DEBUG=false
PLAID_ENV=production
# ... other settings
```

### Start Services
```bash
docker compose -f docker-compose.prod.yml up -d
```

This creates:
- `mintbean-backend` container on port 8000 (internal only)
- `mintbean-frontend` container on port 80 (internal only)
- `mintbean` Docker network

## Step 2: Connect NPM to MintBean Network

NPM needs to join the `mintbean` network to access the containers.

### Option A: If NPM is already running
```bash
# Find NPM container name
docker ps | grep nginx-proxy-manager

# Connect NPM to mintbean network
docker network connect mintbean <npm-container-name>
```

### Option B: Add to NPM's docker-compose.yml
```yaml
services:
  npm:
    # ... existing config
    networks:
      - default
      - mintbean  # Add this

networks:
  default:
    # NPM's default network
  mintbean:
    external: true
    name: mintbean
```

Then restart NPM:
```bash
cd /path/to/npm
docker compose down
docker compose up -d
```

## Step 3: Configure Proxy Host in NPM

### In Nginx Proxy Manager Web UI:

1. **Go to "Hosts" → "Proxy Hosts" → "Add Proxy Host"**

2. **Details Tab:**
   - **Domain Names**: `mint.reitblatt.co`
   - **Scheme**: `http` (internal communication, NPM handles SSL)
   - **Forward Hostname/IP**: `mintbean-frontend` (container name)
   - **Forward Port**: `80`
   - **Cache Assets**: ✅ (optional)
   - **Block Common Exploits**: ✅
   - **Websockets Support**: ✅

3. **SSL Tab:**
   - **SSL Certificate**: Select or create new (Let's Encrypt)
   - **Force SSL**: ✅
   - **HTTP/2 Support**: ✅
   - **HSTS Enabled**: ✅

4. **Advanced Tab (IMPORTANT):**

   Add this custom nginx configuration to route `/api` to the backend:

   ```nginx
   location /api/ {
       proxy_pass http://mintbean-backend:8000;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
   }
   ```

   **Note**: Do NOT use the "Custom Locations" tab - it can cause health check failures. Use the Advanced tab instead.

5. **Click "Save"**

## Step 4: Verify Setup

### Test from command line:
```bash
# Should return frontend HTML
curl -I https://mint.reitblatt.co

# Should return {"status":"healthy","version":"0.1.0"}
curl https://mint.reitblatt.co/health

# Should return API response
curl https://mint.reitblatt.co/api/v1/
```

### Check runtime config:
```bash
# Verify frontend has correct API URL
docker exec mintbean-frontend cat /usr/share/nginx/html/config.js

# Should show:
# window.__RUNTIME_CONFIG__ = {
#   apiUrl: '/api/v1'
# };
```

### Test in browser:
1. Go to `https://mint.reitblatt.co`
2. Open browser DevTools → Network tab
3. API calls should go to `https://mint.reitblatt.co/api/v1/*`
4. All should return 200 (or appropriate status codes)

## Troubleshooting

### 502 Bad Gateway Error

**Check NPM is on mintbean network:**
```bash
docker network inspect mintbean
# Should show NPM container in "Containers" section
```

**Verify containers are running:**
```bash
docker ps | grep mintbean
```

**Check container names match:**
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
# Should show:
# mintbean-frontend    Up X minutes (healthy)
# mintbean-backend     Up X minutes (healthy)
```

### CORS Errors

**Check backend ALLOWED_ORIGINS:**
```bash
docker compose -f docker-compose.prod.yml exec mintbean-backend env | grep ALLOWED_ORIGINS
# Should show: ALLOWED_ORIGINS=https://mint.reitblatt.co
```

**Update .env and restart:**
```bash
# Edit .env
ALLOWED_ORIGINS=https://mint.reitblatt.co

# Restart backend
docker compose -f docker-compose.prod.yml restart mintbean-backend
```

### API Calls Going to Wrong URL

**Check frontend runtime config:**
```bash
docker exec mintbean-frontend cat /usr/share/nginx/html/config.js
```

**If wrong, update .env and restart:**
```bash
# Edit .env
API_URL=/api/v1

# Restart frontend
docker compose -f docker-compose.prod.yml restart mintbean-frontend

# Verify again
docker exec mintbean-frontend cat /usr/share/nginx/html/config.js
```

### NPM Can't Connect to Containers

**Ensure network exists:**
```bash
docker network ls | grep mintbean
```

**Recreate network connection:**
```bash
docker network disconnect mintbean <npm-container-name>
docker network connect mintbean <npm-container-name>
```

## Complete Example Setup

### `.env` file:
```bash
# Backend
DATABASE_URL=sqlite:///./data/mintbean.db
SECRET_KEY=supersecretkey123456789012345678  # Change this!
DEBUG=false

# CORS - Your domain
ALLOWED_ORIGINS=https://mint.reitblatt.co

# Beancount
BEANCOUNT_FILE_PATH=/path/to/your/main.beancount
BEANCOUNT_REPO_PATH=/path/to/your/beancount/repo

# Plaid
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=production

# Frontend - path-based routing via NPM
API_URL=/api/v1

# Logging
LOG_LEVEL=INFO
```

### Deploy:
```bash
# Start MintBean
docker compose -f docker-compose.prod.yml up -d

# Connect NPM to network
docker network connect mintbean nginx-proxy-manager

# Configure in NPM web UI as shown above

# Test
curl https://mint.reitblatt.co
curl https://mint.reitblatt.co/api/v1/
```

## Network Diagram

```
┌─────────────────────────────────────────────┐
│ Docker Host                                  │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │ mintbean network (bridge)              │ │
│  │                                        │ │
│  │  ┌──────────────────┐                 │ │
│  │  │ mintbean-backend │                 │ │
│  │  │ Port: 8000       │                 │ │
│  │  └──────────────────┘                 │ │
│  │           ▲                            │ │
│  │           │                            │ │
│  │  ┌──────────────────┐                 │ │
│  │  │ mintbean-frontend│                 │ │
│  │  │ Port: 80         │                 │ │
│  │  └──────────────────┘                 │ │
│  │           ▲                            │ │
│  │           │                            │ │
│  │  ┌──────────────────┐                 │ │
│  │  │ nginx-proxy-mgr  │                 │ │
│  │  │ Ports: 80, 443   │◄────Internet    │ │
│  │  └──────────────────┘                 │ │
│  │                                        │ │
│  └────────────────────────────────────────┘ │
│                                              │
└─────────────────────────────────────────────┘
```

## Maintenance

### View Logs
```bash
# MintBean logs
docker compose -f docker-compose.prod.yml logs -f

# NPM logs
docker logs -f nginx-proxy-manager
```

### Update MintBean
```bash
git pull
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Backup Database
```bash
cp data/mintbean.db data/mintbean.db.backup-$(date +%Y%m%d)
```
