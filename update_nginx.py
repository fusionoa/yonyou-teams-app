#!/usr/bin/env python3

nginx_conf = '''# HTTP to HTTPS Redirect
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name fbtimesheet.ddns.net;
    return 301 https://$host$request_uri;
}

# HTTPS Frontend + API Proxy
upstream timesheet_backend {
    server 127.0.0.1:5000;
    keepalive 32;
}

# SSO Proxy upstream
upstream sso_proxy {
    server 127.0.0.1:5001;
    keepalive 16;
}

server {
    listen 443 ssl http2;
    server_name fbtimesheet.ddns.net;

    ssl_certificate /etc/letsencrypt/live/fbtimesheet.ddns.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/fbtimesheet.ddns.net/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    root /var/www/timesheet/frontend;
    index index.html;

    location ~* \\.(html|js)$ {
        add_header Cache-Control "no-store, no-cache, must-revalidate";
        add_header Pragma "no-cache";
        expires 0;
    }

    # SSO Proxy for Yonyou Cloud
    location /sso/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_connect_timeout 30s;
        proxy_read_timeout 30s;
    }

    location /api/ {
        proxy_pass http://timesheet_backend/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass_header Authorization;
        proxy_set_header Connection "";
    }

    location /health {
        proxy_pass http://timesheet_backend/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
'''

with open('/etc/nginx/conf.d/timesheet.conf', 'w') as f:
    f.write(nginx_conf)

print('Nginx config updated successfully')
