#!/bin/bash

echo "🤖 EVE Chat Platform - AI Integration Test"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
VPS_IP="204.12.233.105"
BACKEND_URL="http://$VPS_IP:8001"
FRONTEND_URL="http://$VPS_IP:3000"

# Test counter
TESTS_PASSED=0
TESTS_TOTAL=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_status="$3"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    print_status "Testing: $test_name"
    
    if eval "$test_command"; then
        print_success "$test_name: PASSED"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        print_error "$test_name: FAILED"
        return 1
    fi
}

echo ""
print_status "Starting AI Integration Tests..."
echo ""

# Test 1: Backend Health
run_test "Backend Health" \
    "curl -s -o /dev/null -w '%{http_code}' $BACKEND_URL/health | grep -q '200'" \
    "200"

# Test 2: AI Model Health
run_test "AI Model Health" \
    "curl -s -o /dev/null -w '%{http_code}' $BACKEND_URL/ai/health | grep -q '200'" \
    "200"

# Test 3: AI Model Status Details
print_status "Testing: AI Model Status Details"
if curl -s "$BACKEND_URL/ai/health" > /tmp/ai_health.json 2>/dev/null; then
    print_success "AI Model Status: Retrieved"
    
    # Check if response contains expected fields
    if grep -q "model_name" /tmp/ai_health.json && \
       grep -q "device" /tmp/ai_health.json && \
       grep -q "status" /tmp/ai_health.json; then
        print_success "AI Model Status: Valid response format"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        print_warning "AI Model Status: Response format may be incomplete"
    fi
    
    # Show AI model details
    echo "   AI Model Details:"
    cat /tmp/ai_health.json | jq -r '.model_name, .device, .status' 2>/dev/null || \
    cat /tmp/ai_health.json | grep -E '"model_name"|"device"|"status"' 2>/dev/null || \
    echo "   (Raw response: $(cat /tmp/ai_health.json))"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
else
    print_error "AI Model Status: Failed to retrieve"
fi

# Test 4: AI Session Initialization
print_status "Testing: AI Session Initialization"
SESSION_ID="test_session_$(date +%s)"
if curl -s -X POST "$BACKEND_URL/ai/init-session" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$SESSION_ID\", \"system_prompt\": \"You are a helpful AI assistant.\"}" \
    > /tmp/init_response.json 2>/dev/null; then
    
    HTTP_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BACKEND_URL/ai/init-session" \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$SESSION_ID\", \"system_prompt\": \"You are a helpful AI assistant.\"}")
    
    if [ "$HTTP_STATUS" = "200" ]; then
        print_success "AI Session Initialization: PASSED"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        print_error "AI Session Initialization: FAILED (HTTP $HTTP_STATUS)"
    fi
else
    print_error "AI Session Initialization: Failed to send request"
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

# Test 5: AI Chat (if session was created)
if [ -n "$SESSION_ID" ]; then
    print_status "Testing: AI Chat"
    if curl -s -X POST "$BACKEND_URL/ai/chat" \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"Hello! How are you?\", \"max_tokens\": 100, \"temperature\": 0.7}" \
        > /tmp/chat_response.json 2>/dev/null; then
        
        HTTP_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BACKEND_URL/ai/chat" \
            -H "Content-Type: application/json" \
            -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"Hello! How are you?\", \"max_tokens\": 100, \"temperature\": 0.7}")
        
        if [ "$HTTP_STATUS" = "200" ]; then
            print_success "AI Chat: PASSED"
            
            # Check if response contains AI response
            if grep -q "response" /tmp/chat_response.json; then
                print_success "AI Chat: Valid response received"
                echo "   AI Response: $(cat /tmp/chat_response.json | jq -r '.response' 2>/dev/null | head -c 100)..."
            else
                print_warning "AI Chat: Response format may be incomplete"
            fi
            
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            print_error "AI Chat: FAILED (HTTP $HTTP_STATUS)"
        fi
    else
        print_error "AI Chat: Failed to send request"
    fi
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
fi

# Test 6: AI Memory Optimization
run_test "AI Memory Optimization" \
    "curl -s -o /dev/null -w '%{http_code}' -X POST $BACKEND_URL/ai/optimize-memory | grep -q '200'" \
    "200"

# Test 7: Frontend Accessibility
run_test "Frontend Accessibility" \
    "curl -s -o /dev/null -w '%{http_code}' $FRONTEND_URL | grep -q '200'" \
    "200"

# Test 8: Legacy API Endpoints (for backward compatibility)
run_test "Legacy API Health" \
    "curl -s -o /dev/null -w '%{http_code}' $BACKEND_URL/api/health | grep -q '200'" \
    "200"

# Cleanup test files
rm -f /tmp/ai_health.json /tmp/init_response.json /tmp/chat_response.json

echo ""
echo "=========================================="
print_status "AI Integration Test Results"
echo "=========================================="
echo "Tests Passed: $TESTS_PASSED/$TESTS_TOTAL"

if [ $TESTS_PASSED -eq $TESTS_TOTAL ]; then
    echo ""
    print_success "🎉 All AI integration tests passed!"
    print_success "The AI model is fully integrated and working correctly!"
    echo ""
    print_status "Next steps:"
    echo "  1. Test the chat interface in the frontend"
    echo "  2. Check the admin dashboard for AI status"
    echo "  3. Monitor backend logs for AI model performance"
    exit 0
else
    echo ""
    print_warning "⚠️ Some tests failed. Check the details above."
    print_status "Troubleshooting tips:"
    echo "  1. Check if backend is running: docker-compose ps"
    echo "  2. Check backend logs: docker-compose logs backend"
    echo "  3. Verify AI model loaded: curl $BACKEND_URL/ai/health"
    echo "  4. Check GPU availability: nvidia-smi"
    exit 1
fi 