#!/bin/bash
echo "=== Testing Yonyou Cloud API endpoints ==="

endpoints=(
    "GET|https://c2.yonyoucloud.com/api/v1/auth/login"
    "GET|https://c2.yonyoucloud.com/rest/v1/"
    "POST|https://c2.yonyoucloud.com/login"
    "POST|https://c2.yonyoucloud.com/api/login"
    "POST|https://c2.yonyoucloud.com/api/v1/login"
    "GET|https://c2.yonyoucloud.com/api/"
    "POST|https://euc.yonyoucloud.com/cas/v1/tickets"
    "GET|https://euc.yonyoucloud.com/cas/"
    "GET|https://euc.yonyoucloud.com/cas/thirdSaml2Login?thirdUCId=u10pzze8"
    "GET|https://c2.yonyoucloud.com/"
)

for entry in "${endpoints[@]}"; do
    method="${entry%%|*}"
    url="${entry##*|}"
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 -X "$method" "$url" 2>/dev/null)
    echo "$code  [$method] $url"
done

echo ""
echo "=== Testing CAS login with JSON payload ==="
echo '{"username":"test@test.com","password":"test"}' | curl -s -o /dev/null -w "%{http_code}" --max-time 8 -X POST \
    -H "Content-Type: application/json" \
    -d @- \
    "https://euc.yonyoucloud.com/cas/v1/tickets" 2>/dev/null
echo "  POST /cas/v1/tickets (JSON)"

echo ""
echo "=== Testing SAML redirect (follow redirects) ==="
curl -s -o /tmp/saml_resp.html -w "%{http_code} redirect_count=%{num_redirects}" --max-time 10 -L -X GET \
    "https://euc.yonyoucloud.com/cas/thirdSaml2Login?thirdUCId=u10pzze8&service=https%3A%2F%2Fc2.yonyoucloud.com" 2>/dev/null
echo ""
echo "Final URL: $?"
grep -o 'action="[^"]*"' /tmp/saml_resp.html 2>/dev/null | head -3