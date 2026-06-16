#!/bin/bash
echo "=== Deep probe: REST API /rest/v1/ ==="
curl -s --max-time 10 -X GET "https://c2.yonyoucloud.com/rest/v1/" -H "Accept: application/json" 2>/dev/null | head -200
echo ""
echo "=== Deep probe: API /api/ ==="
curl -s --max-time 10 -X GET "https://c2.yonyoucloud.com/api/" -H "Accept: application/json" 2>/dev/null | head -200
echo ""
echo "=== CAS v1 tickets - correct format ==="
# Try TGT (Ticket Granting Ticket) format
curl -s --max-time 10 -X POST "https://euc.yonyoucloud.com/cas/v1/tickets" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test" 2>/dev/null | head -100
echo ""
echo "=== Check CAS API docs/description ==="
curl -s --max-time 10 -X GET "https://euc.yonyoucloud.com/cas/v1/tickets" 2>/dev/null | head -100
echo ""
echo "=== Where does /api/v1/auth/login redirect to? ==="
curl -s --max-time 10 -i -X GET "https://c2.yonyoucloud.com/api/v1/auth/login" 2>/dev/null | head -20