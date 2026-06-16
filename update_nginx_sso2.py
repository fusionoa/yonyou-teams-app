#!/usr/bin/env python3
"""Update Nginx to proxy to new YonSuite SSO endpoint"""

with open("/etc/nginx/conf.d/timesheet.conf", "r") as f:
    content = f.read()

# Replace the old SSO proxy with new one pointing to c2.yonyoucloud.com SSO page
old_block = """    # YonSuite SSO reverse proxy (CAS-based)
    location /yonyou-sso/ {
        proxy_pass https://euc.yonyoucloud.com/;
        proxy_http_version 1.1;
        proxy_set_header Host euc.yonyoucloud.com;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_ssl_server_name on;
        proxy_ssl_name euc.yonyoucloud.com;
        proxy_set_header Accept-Encoding "";
        sub_filter_types text/html text/css application/javascript application/json;
        sub_filter_once off;
        sub_filter 'euc.yonyoucloud.com' '$host';
        sub_filter 'c2.yonyoucloud.com' '$host';
        sub_filter 'href="/' 'href="$scheme://$host/';
        sub_filter "href='/'" "href='$scheme://$host/'";
        sub_filter 'src="/' 'src="$scheme://$host/';
        sub_filter "src='/'" "src='$scheme://$host/'";
        sub_filter 'action="/' 'action="$scheme://$host/';
        add_header X-Frame-Options "ALLOWALL" always;
    }"""

new_block = """    # YonSuite SSO reverse proxy (direct login page)
    location /yonyou-sso/ {
        proxy_pass https://c2.yonyoucloud.com/iuap-uuas-user/fe-free/;
        proxy_http_version 1.1;
        proxy_set_header Host c2.yonyoucloud.com;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Accept-Encoding "";
        proxy_ssl_server_name on;
        proxy_ssl_name c2.yonyoucloud.com;
        sub_filter_types text/html text/css application/javascript;
        sub_filter_once off;
        sub_filter 'c2.yonyoucloud.com' '$host';
        sub_filter 'href="/' 'href="$scheme://$host/';
        sub_filter "href='/'" "href='$scheme://$host/'";
        sub_filter 'src="/' 'src="$scheme://$host/';
        add_header X-Frame-Options "ALLOWALL" always;
    }"""

if "location /yonyou-sso/" in content:
    content = content.replace(old_block, new_block)

with open("/etc/nginx/conf.d/timesheet.conf", "w") as f:
    f.write(content)

print("Updated Nginx SSO proxy")
