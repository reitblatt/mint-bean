#!/bin/bash
set -e

# PostgreSQL initialization script
# This runs when the PostgreSQL container is first created

echo "Initializing MintBean database..."

# Create extensions if needed
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable required PostgreSQL extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    -- Grant all privileges to the application user
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
    GRANT ALL ON SCHEMA public TO $POSTGRES_USER;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $POSTGRES_USER;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $POSTGRES_USER;

    -- Log success
    SELECT 'MintBean database initialized successfully!' AS status;
EOSQL

echo "Database initialization complete!"
