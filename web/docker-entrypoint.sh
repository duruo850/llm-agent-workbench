#!/bin/sh
set -e

API_BASE="${VITE_API_BASE:-http://127.0.0.1:8000}"
cat > /usr/share/nginx/html/config.js <<EOF
window.__BILLMIND_ENV__ = { VITE_API_BASE: "${API_BASE}" };
EOF

exec nginx -g 'daemon off;'
