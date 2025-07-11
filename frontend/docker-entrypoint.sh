#!/bin/sh
set -e

# Default values
API_URL="${API_URL:-http://backend:8000}"
WS_URL="${WS_URL:-ws://backend:8000}"

echo "Starting nginx with:"
echo "  API_URL: $API_URL"
echo "  WS_URL: $WS_URL"

# Replace environment variables in nginx config
envsubst '${API_URL} ${WS_URL}' < /etc/nginx/conf.d/default.conf > /tmp/default.conf
mv /tmp/default.conf /etc/nginx/conf.d/default.conf

# Create runtime config for React app
cat > /usr/share/nginx/html/config.js <<EOF
window.__RUNTIME_CONFIG__ = {
  API_URL: "${API_URL}",
  WS_URL: "${WS_URL}",
  ENVIRONMENT: "${ENVIRONMENT:-production}"
};
EOF

# Execute CMD
exec "$@"