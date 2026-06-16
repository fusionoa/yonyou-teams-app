#!/usr/bin/env python3
with open("/etc/nginx/conf.d/timesheet.conf", "r") as f:
    content = f.read()

logout_block = """
    # Handle CAS logout - redirect back to teams entry after logout
    location /yonyou-sso/cas/logout {
        proxy_pass https://euc.yonyoucloud.com/cas/logout;
        proxy_http_version 1.1;
        proxy_set_header Host euc.yonyoucloud.com;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_ssl_server_name on;
        proxy_ssl_name euc.yonyoucloud.com;
        proxy_redirect https://euc.yonyoucloud.com/ /yonyou-sso/;
        add_header X-Frame-Options "ALLOWALL" always;
    }

"""

if "location /yonyou-sso/" in content and "location /yonyou-sso/cas/logout" not in content:
    content = content.replace("    location /yonyou-sso/ {", logout_block + "    location /yonyou-sso/ {")

with open("/etc/nginx/conf.d/timesheet.conf", "w") as f:
    f.write(content)

print("Updated")