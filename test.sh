#!/bin/bash

echo "🧪 Testing Chatting Platform Setup"
echo "=================================="

# Function to test URL
test_url() {
    local url=$1
    local name=$2
    local expected_code=${3:-200}
    
    echo -n "Testing $name... "
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$url" 2>/dev/null); then
        if [ "$response" = "$expected_code" ]; then
            echo "✅ OK ($response)"
            return 0
        else
            echo "❌ FAIL (got $response, expected $expected_code)"
            return 1
        fi
    else
        echo "❌ FAIL (connection error)"
        return 1
    fi
}

# Check if services are running
echo "📊 Checking Docker services..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ No services appear to be running. Please run: ./start.sh"
    exit 1
fi

echo "✅ Docker services are running"
echo ""

# Test backend health
test_url "http://localhost:8000/health" "Backend Health"

# Test backend API docs
test_url "http://localhost:8000/docs" "Backend API Docs"

# Test frontend
test_url "http://localhost:3000" "Frontend"

# Test admin page
test_url "http://localhost:3000/admin" "Admin Page"

echo ""
echo "🔍 Service Status:"
docker-compose ps

echo ""
echo "📝 Quick Tests:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Try admin login at http://localhost:3000/admin (admin/admin123)"
echo "3. Test Tally webhook:"
echo "   curl -X POST http://localhost:8000/webhook/tally -H 'Content-Type: application/json' -d @tally_form.json"

echo ""
echo "🎉 Setup test completed!"