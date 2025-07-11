#!/bin/bash

# Setup script for Educational RPG Platform
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎮 Educational RPG Platform - Setup Script${NC}"
echo -e "${BLUE}==========================================${NC}\n"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to generate random string
generate_key() {
    openssl rand -base64 32
}

# Check prerequisites
echo -e "${GREEN}1. Checking prerequisites...${NC}"

MISSING_DEPS=()

if ! command_exists git; then
    MISSING_DEPS+=("git")
fi

if ! command_exists docker; then
    MISSING_DEPS+=("docker")
fi

if ! command_exists docker-compose; then
    MISSING_DEPS+=("docker-compose")
fi

if ! command_exists node; then
    MISSING_DEPS+=("nodejs")
fi

if ! command_exists npm; then
    MISSING_DEPS+=("npm")
fi

if ! command_exists python3; then
    MISSING_DEPS+=("python3")
fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    echo -e "${RED}Missing dependencies: ${MISSING_DEPS[*]}${NC}"
    echo -e "${YELLOW}Please install the missing dependencies and run this script again.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites installed${NC}\n"

# Create environment files
echo -e "${GREEN}2. Creating environment files...${NC}"

# Create .env file for development
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env << EOF
# Environment
ENVIRONMENT=development

# Database
POSTGRES_DB=educational_rpg
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$(generate_key)

# Backend
SECRET_KEY=$(generate_key)
JWT_SECRET_KEY=$(generate_key)
ENCRYPTION_KEY=$(openssl rand -base64 32 | tr -d '\n' | head -c 32 | base64)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/educational_rpg
REDIS_URL=redis://localhost:6379

# Frontend
VITE_API_URL=http://localhost:8000/api/v1
VITE_WEBSOCKET_URL=ws://localhost:8000/ws

# External Services (add your keys here)
OPENAI_API_KEY=
STRIPE_API_KEY=
STRIPE_WEBHOOK_SECRET=

# Admin
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin

# Monitoring
GF_ADMIN_USER=admin
GF_ADMIN_PASSWORD=admin
EOF
    echo -e "${GREEN}✓ Created .env file${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists, skipping...${NC}"
fi

# Create backend .env
if [ ! -f backend/.env ]; then
    cp .env backend/.env
    echo -e "${GREEN}✓ Created backend/.env${NC}"
fi

# Create frontend .env
if [ ! -f frontend/.env ]; then
    cat > frontend/.env << EOF
VITE_API_URL=http://localhost:8000/api/v1
VITE_WEBSOCKET_URL=ws://localhost:8000/ws
VITE_ENVIRONMENT=development
EOF
    echo -e "${GREEN}✓ Created frontend/.env${NC}"
fi

echo ""

# Install dependencies
echo -e "${GREEN}3. Installing dependencies...${NC}"

# Backend dependencies
echo -e "${YELLOW}Installing backend dependencies...${NC}"
cd backend
pip3 install -r requirements.txt
pip3 install -r requirements-dev.txt
cd ..
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Frontend dependencies
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd frontend
npm install
cd ..
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

# Root dependencies (for Playwright)
echo -e "${YELLOW}Installing E2E test dependencies...${NC}"
npm install
npx playwright install --with-deps
echo -e "${GREEN}✓ E2E test dependencies installed${NC}"

echo ""

# Create necessary directories
echo -e "${GREEN}4. Creating necessary directories...${NC}"
mkdir -p backend/logs
mkdir -p backend/uploads
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources
mkdir -p nginx/ssl
echo -e "${GREEN}✓ Directories created${NC}\n"

# Database setup
echo -e "${GREEN}5. Setting up database...${NC}"
docker-compose up -d postgres redis
echo -e "${YELLOW}Waiting for database to be ready...${NC}"
sleep 10

# Run migrations
echo -e "${YELLOW}Running database migrations...${NC}"
cd backend
alembic upgrade head
cd ..
echo -e "${GREEN}✓ Database setup complete${NC}\n"

# Create test data (optional)
read -p "Do you want to create test data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Creating test data...${NC}"
    cd backend
    python scripts/seed_data.py
    cd ..
    echo -e "${GREEN}✓ Test data created${NC}"
fi

echo ""

# Git hooks setup
echo -e "${GREEN}6. Setting up Git hooks...${NC}"
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Run linting and tests before commit

echo "Running pre-commit checks..."

# Backend checks
cd backend
ruff check . || exit 1
black --check . || exit 1

# Frontend checks
cd ../frontend
npm run lint || exit 1
npm run type-check || exit 1

echo "Pre-commit checks passed!"
EOF

chmod +x .git/hooks/pre-commit
echo -e "${GREEN}✓ Git hooks configured${NC}\n"

# Final instructions
echo -e "${GREEN}🎉 Setup completed successfully!${NC}\n"
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Update the .env file with your API keys"
echo -e "2. Start the development servers:"
echo -e "   ${YELLOW}docker-compose up${NC}"
echo -e "3. Access the application:"
echo -e "   - Frontend: ${BLUE}http://localhost:3000${NC}"
echo -e "   - Backend API: ${BLUE}http://localhost:8000${NC}"
echo -e "   - API Docs: ${BLUE}http://localhost:8000/docs${NC}"
echo -e "   - pgAdmin: ${BLUE}http://localhost:5050${NC}"
echo -e "   - Redis Commander: ${BLUE}http://localhost:8081${NC}"
echo -e "\n${GREEN}Happy coding! 🚀${NC}"