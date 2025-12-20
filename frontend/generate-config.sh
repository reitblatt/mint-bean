#!/bin/sh
# Generate runtime configuration from environment variables

cat > /usr/share/nginx/html/config.js <<EOF
window.__RUNTIME_CONFIG__ = {
  apiUrl: '${API_URL:-/api/v1}'
};
EOF

echo "Generated runtime config with API_URL=${API_URL:-/api/v1}"
