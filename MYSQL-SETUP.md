# MySQL Database Setup Guide

MintBean supports both SQLite and MySQL databases. SQLite is the default and recommended option for single-user deployments, while MySQL is better suited for multi-user scenarios or when you need advanced database features.

## Choosing Your Database

### SQLite (Default - Recommended)
**Pros:**
- Zero configuration required
- Perfect for single-user setups
- File-based (easy backups)
- Lower resource usage
- Included by default

**Cons:**
- Limited concurrent write performance
- Not ideal for multi-user access

**Best for:** Personal finance tracking, single-user deployments

### MySQL
**Pros:**
- Better concurrent access performance
- Standard for production deployments
- Advanced features (replication, clustering)
- Better for multi-user scenarios

**Cons:**
- Requires additional service to run
- More complex setup
- Higher resource usage

**Best for:** Multi-user deployments, production environments

## Setup During Onboarding

During the onboarding wizard, you'll be presented with a 3-step process:

1. **Admin Account** - Create your admin user
2. **Database Configuration** - Choose SQLite or MySQL
3. **Plaid Configuration** - Set up Plaid API credentials

### Option 1: SQLite Setup

1. Select "SQLite (Recommended)" when prompted
2. Optionally customize the database file path (default: `./data/mintbean.db`)
3. Continue to Plaid configuration

That's it! No additional setup required.

### Option 2: MySQL Setup

#### Prerequisites

Before choosing MySQL during onboarding, you need a running MySQL server. You can use the included Docker service or an external MySQL server.

#### Using Docker MySQL (Included)

1. **Uncomment the MySQL service** in `docker-compose.prod.yml`:

```yaml
services:
  mintbean-mysql:
    image: mysql:8.0
    container_name: mintbean-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-your_secure_root_password}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-mintbean}
      MYSQL_USER: ${MYSQL_USER:-mintbean_user}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD:-your_secure_password}
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - mintbean
```

2. **Uncomment the mysql_data volume**:

```yaml
volumes:
  data:
    driver: local
  mysql_data:
    driver: local
```

3. **Uncomment the depends_on section** in the backend service:

```yaml
mintbean-backend:
  # ... other config ...
  depends_on:
    mintbean-mysql:
      condition: service_healthy
```

4. **Create a `.env` file** with your MySQL credentials:

```bash
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_DATABASE=mintbean
MYSQL_USER=mintbean_user
MYSQL_PASSWORD=your_secure_password
```

5. **Start the services**:

```bash
docker compose -f docker-compose.prod.yml up -d
```

6. **During onboarding**, select "MySQL" and enter:
   - **Host:** `mintbean-mysql` (the Docker service name)
   - **Port:** `3306`
   - **Database Name:** `mintbean` (or what you set in MYSQL_DATABASE)
   - **Username:** `mintbean_user` (or what you set in MYSQL_USER)
   - **Password:** Your MySQL password (from MYSQL_PASSWORD)

#### Using External MySQL Server

If you already have a MySQL server running:

1. Create a database for MintBean:

```sql
CREATE DATABASE mintbean CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'mintbean_user'@'%' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON mintbean.* TO 'mintbean_user'@'%';
FLUSH PRIVILEGES;
```

2. **During onboarding**, select "MySQL" and enter:
   - **Host:** Your MySQL server hostname/IP
   - **Port:** `3306` (or your custom port)
   - **Database Name:** `mintbean`
   - **Username:** `mintbean_user`
   - **Password:** Your MySQL password

## Migrating from SQLite to MySQL

If you started with SQLite and want to migrate to MySQL later:

### Option 1: Via Admin Panel (Planned)

A future update will add a migration tool in the admin panel to automatically migrate your data from SQLite to MySQL.

### Option 2: Manual Migration

1. **Export your SQLite data**:

```bash
# Using sqlite3 command-line tool
sqlite3 data/mintbean.db .dump > backup.sql
```

2. **Set up MySQL** (follow MySQL setup above)

3. **Convert and import the data**:

Since SQLite and MySQL have slightly different SQL syntax, you'll need to convert the dump file. You can use tools like:
- [sqlite3-to-mysql](https://github.com/techouse/sqlite3-to-mysql)
- Manual SQL editing for small databases

4. **Update database settings**:

Use the Settings API or update the app_settings table directly:

```bash
curl -X PUT http://your-domain/api/v1/settings/database \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "database_type": "mysql",
    "database_host": "mintbean-mysql",
    "database_port": 3306,
    "database_name": "mintbean",
    "database_user": "mintbean_user",
    "database_password": "your_secure_password"
  }'
```

5. **Restart the backend**:

```bash
docker compose -f docker-compose.prod.yml restart mintbean-backend
```

## Database Settings API

Admins can view and update database configuration through the API:

### View Current Database Settings

```bash
GET /api/v1/settings/database
Authorization: Bearer YOUR_ADMIN_TOKEN
```

Response:
```json
{
  "database_type": "sqlite",
  "database_host": null,
  "database_port": null,
  "database_name": null,
  "database_user": null,
  "database_password_masked": null,
  "sqlite_path": "./data/mintbean.db"
}
```

### Update Database Settings

```bash
PUT /api/v1/settings/database
Authorization: Bearer YOUR_ADMIN_TOKEN
Content-Type: application/json

{
  "database_type": "mysql",
  "database_host": "mintbean-mysql",
  "database_port": 3306,
  "database_name": "mintbean",
  "database_user": "mintbean_user",
  "database_password": "your_secure_password"
}
```

**⚠️ WARNING:** Changing database settings requires restarting the backend container for changes to take effect.

## Troubleshooting

### MySQL Connection Failed During Onboarding

**Error:** "Can't connect to MySQL server on 'mintbean-mysql'"

**Solutions:**
1. Ensure MySQL container is running: `docker ps | grep mysql`
2. Check MySQL logs: `docker logs mintbean-mysql`
3. Verify network connectivity: Both services must be on the same Docker network
4. Wait for MySQL to be fully ready (check health status)

### MySQL Authentication Failed

**Error:** "Access denied for user 'mintbean_user'@'%'"

**Solutions:**
1. Verify credentials in `.env` file match what you entered in onboarding
2. Check user was created correctly: `docker exec -it mintbean-mysql mysql -u root -p`
3. Run the GRANT statements again

### Character Encoding Issues

If you see encoding errors with special characters:

```sql
ALTER DATABASE mintbean CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Performance Tuning MySQL

For production deployments, consider adjusting MySQL settings in docker-compose.prod.yml:

```yaml
mintbean-mysql:
  command:
    - --max_connections=200
    - --innodb_buffer_pool_size=256M
    - --query_cache_size=0
    - --query_cache_type=0
```

## Backup and Recovery

### SQLite Backup

```bash
# Simple file copy
cp data/mintbean.db data/mintbean.db.backup-$(date +%Y%m%d)

# Using sqlite3
sqlite3 data/mintbean.db .dump > backup-$(date +%Y%m%d).sql
```

### MySQL Backup

```bash
# Using mysqldump via Docker
docker exec mintbean-mysql mysqldump -u mintbean_user -p mintbean > backup-$(date +%Y%m%d).sql

# Or using docker compose
docker compose -f docker-compose.prod.yml exec mintbean-mysql \
  mysqldump -u mintbean_user -p mintbean > backup-$(date +%Y%m%d).sql
```

### Restore MySQL Backup

```bash
docker exec -i mintbean-mysql mysql -u mintbean_user -p mintbean < backup.sql
```

## Migration Scripts

After upgrading MintBean, run the migration script to add new database configuration fields:

```bash
cd backend
python3 migrate_add_database_config.py
```

This script:
- Checks if new columns exist
- Adds database_type, database_host, database_port, etc.
- Sets sensible defaults (database_type='sqlite')
- Is safe to run multiple times (idempotent)
