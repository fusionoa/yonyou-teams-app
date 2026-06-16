#!/usr/bin/env python3
import subprocess
import re

tests = [
    ("API v1 auth/login", "https://c2.yonyoucloud.com/api/v1/auth/login"),
    ("REST v1", "https://c2.yonyoucloud.com/rest/v1/"),
    ("POST /login", "https://c2.yonyoucloud.com/login", "POST"),
    ("POST /api/login", "https://c2.yonyoucloud.com/api/login", "POST"),
    ("CAS tickets", "https://euc.yonyoucloud.com/cas/v1/tickets", "POST"),
    ("CAS /cas", "https://euc.yonyoucloud.com/cas/"),
    ("thirdSaml2Login", "https://euc.yonyoucloud.com/cas/thirdSaml2Login?thirdUCId=u10pzze8"),
    ("c2.yonyoucloud.com", "https://c2.yonyoucloud.com/"),
]

for name, url in tests:
    method = "GET"
    if len(tests) > 2 and len(tests) > 0:
        pass
    cmd = f'curl -s -o /dev/null -w "%{{http_code}}" --max-time 8 -X GET "{url}" 2>/dev/null'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    code = result.stdout.strip()
    print(f"{code}  {name}")