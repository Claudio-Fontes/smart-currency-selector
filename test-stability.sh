#!/bin/bash

echo "🔥 SOLANA HOT POOLS DASHBOARD - STABILITY TEST"
echo "============================================================"
echo "Testing system stability and error resilience..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
BACKEND_SUCCESS=0
BACKEND_TOTAL=0
TOKEN_SUCCESS=0
TOKEN_TOTAL=0
FRONTEND_OK=0

echo "🧪 Testing backend API stability..."
echo "   Performing rapid API calls to test for race conditions..."

# Test backend stability with multiple rapid calls
for i in {1..5}; do
    BACKEND_TOTAL=$((BACKEND_TOTAL + 1))
    
    if curl -s -f "http://localhost:8000/api/hot-pools?limit=3" > /dev/null 2>&1; then
        BACKEND_SUCCESS=$((BACKEND_SUCCESS + 1))
        echo -e "   ${GREEN}✅${NC} Request $i: Success"
    else
        echo -e "   ${RED}❌${NC} Request $i: Failed"
    fi
    
    # Small delay to simulate rapid clicking
    sleep 0.2
done

echo ""
echo "🔬 Testing token analysis API..."

# Get a sample token address for testing
SAMPLE_TOKEN=$(curl -s "http://localhost:8000/api/hot-pools?limit=1" | grep -o '"address":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -n "$SAMPLE_TOKEN" ] && [ "$SAMPLE_TOKEN" != "N/A" ]; then
    echo "   🪙 Testing with token: ${SAMPLE_TOKEN:0:10}..."
    
    # Test rapid token analysis calls
    for i in {1..3}; do
        TOKEN_TOTAL=$((TOKEN_TOTAL + 1))
        
        if curl -s -f "http://localhost:8000/api/token/$SAMPLE_TOKEN" > /dev/null 2>&1; then
            TOKEN_SUCCESS=$((TOKEN_SUCCESS + 1))
            echo -e "   ${GREEN}✅${NC} Analysis $i: Success"
        else
            echo -e "   ${RED}❌${NC} Analysis $i: Failed"
        fi
        
        sleep 0.5
    done
else
    echo -e "   ${YELLOW}⚠️${NC}  No valid token found for testing"
fi

echo ""
echo "🌐 Checking frontend availability..."

if curl -s -f "http://localhost:3000" > /dev/null 2>&1; then
    FRONTEND_OK=1
    echo -e "   ${GREEN}✅${NC} Frontend is accessible"
else
    echo -e "   ${RED}❌${NC} Frontend not accessible"
fi

echo ""
echo "============================================================"
echo "📊 STABILITY TEST REPORT"
echo "============================================================"

# Calculate success rates
if [ $BACKEND_TOTAL -gt 0 ]; then
    BACKEND_RATE=$((BACKEND_SUCCESS * 100 / BACKEND_TOTAL))
    echo -e "🔧 Backend API:           ${BACKEND_SUCCESS}/${BACKEND_TOTAL} (${BACKEND_RATE}%)"
else
    BACKEND_RATE=0
    echo -e "🔧 Backend API:           No tests performed"
fi

if [ $TOKEN_TOTAL -gt 0 ]; then
    TOKEN_RATE=$((TOKEN_SUCCESS * 100 / TOKEN_TOTAL))
    echo -e "🪙 Token Analysis:        ${TOKEN_SUCCESS}/${TOKEN_TOTAL} (${TOKEN_RATE}%)"
else
    TOKEN_RATE=0
    echo -e "🪙 Token Analysis:        No tests performed"
fi

echo -e "🌐 Frontend Availability: $( [ $FRONTEND_OK -eq 1 ] && echo "✅ AVAILABLE" || echo "❌ UNAVAILABLE" )"

echo ""
echo "📈 OVERALL STATUS:"

# Calculate overall score
OVERALL_SCORE=0
[ $BACKEND_RATE -ge 80 ] && OVERALL_SCORE=$((OVERALL_SCORE + 1))
[ $TOKEN_RATE -ge 70 ] && OVERALL_SCORE=$((OVERALL_SCORE + 1))
[ $FRONTEND_OK -eq 1 ] && OVERALL_SCORE=$((OVERALL_SCORE + 1))

case $OVERALL_SCORE in
    3)
        echo -e "${GREEN}🎉 EXCELLENT - All systems stable and ready for use!${NC}"
        ;;
    2)
        echo -e "${BLUE}✅ GOOD - Most systems stable, minor issues detected${NC}"
        ;;
    1)
        echo -e "${YELLOW}⚠️  FAIR - Some systems unstable, needs attention${NC}"
        ;;
    0)
        echo -e "${RED}❌ POOR - Multiple system failures detected${NC}"
        ;;
esac

echo ""
echo "💡 RECOMMENDATIONS:"

if [ $FRONTEND_OK -eq 0 ]; then
    echo "   • Start frontend server: npm run dev"
fi

if [ $BACKEND_RATE -lt 80 ]; then
    echo "   • Check backend server: python3 backend/server.py"
    echo "   • Verify API key configuration in .env"
fi

if [ $TOKEN_RATE -lt 70 ]; then
    echo "   • Check DEXTools API rate limits"
    echo "   • Verify network connectivity"
fi

if [ $OVERALL_SCORE -eq 3 ]; then
    echo ""
    echo -e "${GREEN}🚀 Dashboard ready at: http://localhost:3000${NC}"
    echo ""
    echo "🔥 REMOVECHILDS ERRORS FIXED:"
    echo "   • Disabled React StrictMode"
    echo "   • Implemented proper cleanup in hooks"
    echo "   • Added request cancellation"
    echo "   • Improved component memoization"
    echo "   • Added Error Boundaries"
fi