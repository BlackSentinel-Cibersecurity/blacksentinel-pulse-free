#!/bin/bash
# BlackSentinel Pulse - API Usage Examples
# Requires: curl, jq

set -e

BASE_URL="${PULSE_URL:-http://localhost:8000}"
echo "BlackSentinel Pulse API Examples"
echo "================================"
echo "Base URL: $BASE_URL"
echo ""

# 1. Health Check
echo "1. Health Check"
curl -s "$BASE_URL/api/v1/health" | jq .
echo ""

# 2. Login
echo "2. Login"
TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')
echo "Token obtained: ${TOKEN:0:20}..."
echo ""

# 3. Get User Info
echo "3. User Info"
curl -s "$BASE_URL/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

# 4. List Assets
echo "4. List Assets"
curl -s "$BASE_URL/api/v1/assets/?page=1&page_size=5" \
  -H "Authorization: Bearer $TOKEN" | jq '.total, .items[:2]'
echo ""

# 5. List Scans
echo "5. List Scans"
curl -s "$BASE_URL/api/v1/scans/?page=1&page_size=5" \
  -H "Authorization: Bearer $TOKEN" | jq '.total, .items[:2]'
echo ""

# 6. List Alerts
echo "6. List Alerts"
curl -s "$BASE_URL/api/v1/alerts/?page=1&page_size=5" \
  -H "Authorization: Bearer $TOKEN" | jq '.total, .items[:2]'
echo ""

# 7. Dashboard Summary
echo "7. Dashboard Summary"
curl -s "$BASE_URL/api/v1/dashboard/summary" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

# 8. OpenAPI Docs
echo "8. API Documentation available at: $BASE_URL/api/docs"
echo ""

echo "Done!"
