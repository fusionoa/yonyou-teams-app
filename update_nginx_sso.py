#!/usr/bin/env python3
"""
Update Nginx config to add SSO reverse proxy for Yonyou Cloud.
This proxies the SAML SSO flow through our own domain to avoid iframe blocking.
"""

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

    # SSO Reverse Proxy - proxy Yonyou SAML flow through our domain
    # This allows Teams WebView to complete SSO without iframe blocking
    location /yonyou-sso/ {
        proxy_pass https://euc.yonyoucloud.com/;
        proxy_http_version 1.1;
        proxy_set_header Host euc.yonyoucloud.com;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Accept-Encoding "";
        proxy_ssl_server_name on;
        proxy_ssl_name euc.yonyoucloud.com;
        proxy_buffer_size 128k;
        proxy_buffers 8 256k;
        proxy_busy_buffers_size 256k;
        proxy_read_timeout 120s;
        proxy_connect_timeout 30s;

        # Disable X-Frame-Options from upstream (we add our own)
        proxy_hide_header X-Frame-Options;
        add_header X-Frame-Options "ALLOWALL" always;

        # Handle SAML redirects - rewrite Location headers
        proxy_redirect https://euc.yonyoucloud.com/ /yonyou-sso/;
        proxy_redirect https://login.microsoftonline.com/ https://login.microsoftonline.com/;
        proxy_redirect https://c2.yonyoucloud.com/ https://fbtimesheet.ddns.net/yonyou-app/;
    }

    # Proxy c2.yonyoucloud.com through our domain
    location /yonyou-app/ {
        proxy_pass https://c2.yonyoucloud.com/;
        proxy_http_version 1.1;
        proxy_set_header Host c2.yonyoucloud.com;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Accept-Encoding "";
        proxy_ssl_server_name on;
        proxy_ssl_name c2.yonyoucloud.com;
        proxy_buffer_size 128k;
        proxy_buffers 8 256k;
        proxy_busy_buffers_size 256k;
        proxy_read_timeout 120s;
        proxy_connect_timeout 30s;

        proxy_hide_header X-Frame-Options;
        add_header X-Frame-Options "ALLOWALL" always;

        # Sub-filter to rewrite URLs in HTML content
        sub_filter_once off;
        sub_filter_types text/html text/javascript application/javascript text/css;
        sub_filter 'https://c2.yonyoucloud.com' '/yonyou-app';
        sub_filter 'https://euc.yonyoucloud.com' '/yonyou-sso';
        sub_filter '//c2.yonyoucloud.com' '/yonyou-app';
        sub_filter '//euc.yonyoucloud.com' '/yonyou-sso';
    }

    # SSO Token Proxy API
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

print('Nginx config updated with SSO reverse proxy')
