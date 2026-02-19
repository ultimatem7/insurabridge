#!/bin/bash
# Quick Start Script for Healthcare Claims Automation Platform
# Tests backend functionality without requiring frontend

set -e

echo "🏥 Healthcare Claims Automation Platform - Quick Start"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo -e "${YELLOW}📝 Please edit .env with your EHR credentials before continuing${NC}"
    echo ""
    read -p "Press Enter when ready to continue..."
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${BLUE}🐳 Starting Docker services...${NC}"
docker-compose up -d

echo ""
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Check backend health
echo ""
echo -e "${BLUE}🏥 Checking backend health...${NC}"

MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is healthy!${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Backend failed to start. Check logs with: docker-compose logs backend${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 System is running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Display system info
echo -e "${BLUE}📊 System Status:${NC}"
echo ""

# Backend health
HEALTH=$(curl -s http://localhost:8000/health)
echo -e "  Backend API:     ${GREEN}✓ Running${NC}"
echo "    URL:           http://localhost:8000"
echo "    API Docs:      http://localhost:8000/docs"
echo ""

# Database health
if curl -s http://localhost:8000/health/db | grep -q "healthy"; then
    echo -e "  PostgreSQL:      ${GREEN}✓ Connected${NC}"
else
    echo -e "  PostgreSQL:      ${YELLOW}⚠ Check connection${NC}"
fi

# LLM health
if curl -s http://localhost:8000/health/llm | grep -q "healthy"; then
    echo -e "  LLM Service:     ${GREEN}✓ Connected${NC}"
else
    echo -e "  LLM Service:     ${YELLOW}⚠ Not available (fallback mode)${NC}"
fi

echo ""

# List available providers
echo -e "${BLUE}🔐 Available EHR Providers:${NC}"
curl -s http://localhost:8000/auth/providers | python3 -m json.tool 2>/dev/null || echo "  Unable to fetch providers"

echo ""
echo -e "${BLUE}📖 Quick Test Commands:${NC}"
echo ""
echo "# View API documentation:"
echo "  open http://localhost:8000/docs"
echo ""
echo "# Test health endpoint:"
echo "  curl http://localhost:8000/health | jq"
echo ""
echo "# Check all health:"
echo "  curl http://localhost:8000/health/ready | jq"
echo ""
echo "# List EHR providers:"
echo "  curl http://localhost:8000/auth/providers | jq"
echo ""
echo "# Initiate Epic login (in browser):"
echo "  open http://localhost:8000/auth/epic/login"
echo ""
echo "# View logs:"
echo "  docker-compose logs -f backend"
echo ""

echo -e "${BLUE}📚 Documentation:${NC}"
echo "  - README.md          - Project overview"
echo "  - DEPLOYMENT.md      - Deployment guide"
echo "  - PROJECT_SUMMARY.md - Technical summary"
echo ""

echo -e "${BLUE}🛑 To stop:${NC}"
echo "  docker-compose down"
echo ""

echo -e "${GREEN}✨ Ready for testing!${NC}"
echo ""
