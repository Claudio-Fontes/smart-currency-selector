#!/bin/bash

# Smart Currency Selector - Production Deployment Script
# Este script facilita o deploy e gerenciamento do sistema em produção

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PRODUCTION_DIR="$(dirname "$(dirname "$(realpath "$0")")")"
PROJECT_ROOT="$(dirname "$PRODUCTION_DIR")"
ENV_FILE="$PRODUCTION_DIR/.env"

echo -e "${BLUE}🐳 Smart Currency Selector - Production Deployment${NC}"
echo "================================================"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are available."
}

# Check environment file
check_env_file() {
    print_status "Checking environment configuration..."
    
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "Environment file not found. Creating from template..."
        cp "$PRODUCTION_DIR/.env.example" "$ENV_FILE"
        print_error "Please edit $ENV_FILE with your configuration before running again."
        exit 1
    fi
    
    # Check for required variables
    source "$ENV_FILE"
    
    if [ -z "$DEXTOOLS_API_KEY" ] || [ "$DEXTOOLS_API_KEY" = "your_dextools_api_key_here" ]; then
        print_error "Please configure DEXTOOLS_API_KEY in $ENV_FILE"
        exit 1
    fi
    
    if [ -z "$SOLANA_PRIVATE_KEY" ] || [ "$SOLANA_PRIVATE_KEY" = "your_solana_wallet_private_key_here" ]; then
        print_error "Please configure SOLANA_PRIVATE_KEY in $ENV_FILE"
        exit 1
    fi
    
    print_status "Environment configuration is valid."
}

# Build and start services
start_services() {
    print_status "Starting services..."
    cd "$PRODUCTION_DIR"
    
    # Build images
    print_status "Building Docker images..."
    docker-compose build --no-cache
    
    # Start services
    print_status "Starting containers..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 10
    
    # Check service health
    check_services_health
}

# Stop services
stop_services() {
    print_status "Stopping services..."
    cd "$PRODUCTION_DIR"
    docker-compose down
    print_status "Services stopped."
}

# Restart services
restart_services() {
    print_status "Restarting services..."
    stop_services
    start_services
}

# Check services health
check_services_health() {
    print_status "Checking services health..."
    cd "$PRODUCTION_DIR"
    
    # Check database
    if docker-compose exec -T database pg_isready -U admin -d smart_currency > /dev/null 2>&1; then
        print_status "✅ Database is healthy"
    else
        print_warning "⚠️  Database is not ready yet"
    fi
    
    # Check backend
    if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
        print_status "✅ Backend is healthy"
    else
        print_warning "⚠️  Backend is not ready yet"
    fi
    
    # Check frontend
    if curl -f http://localhost:3000/health > /dev/null 2>&1; then
        print_status "✅ Frontend is healthy"
    else
        print_warning "⚠️  Frontend is not ready yet"
    fi
    
    # Show running containers
    print_status "Running containers:"
    docker-compose ps
}

# View logs
view_logs() {
    cd "$PRODUCTION_DIR"
    
    if [ -n "$1" ]; then
        # Show logs for specific service
        print_status "Showing logs for $1..."
        docker-compose logs -f "$1"
    else
        # Show logs for all services
        print_status "Showing logs for all services..."
        docker-compose logs -f
    fi
}

# Enable trading
enable_trading() {
    print_status "Enabling automatic trading..."
    cd "$PRODUCTION_DIR"
    
    docker-compose exec database psql -U admin -d smart_currency -c \
        "UPDATE trade_config SET config_value = 'true' WHERE config_key = 'auto_trading_enabled';"
    
    print_status "✅ Automatic trading enabled!"
    print_warning "Monitor the trading activity carefully."
}

# Disable trading
disable_trading() {
    print_status "Disabling automatic trading..."
    cd "$PRODUCTION_DIR"
    
    docker-compose exec database psql -U admin -d smart_currency -c \
        "UPDATE trade_config SET config_value = 'false' WHERE config_key = 'auto_trading_enabled';"
    
    print_status "✅ Automatic trading disabled!"
}

# Show trading status
show_status() {
    print_status "Trading System Status:"
    cd "$PRODUCTION_DIR"
    
    docker-compose exec database psql -U admin -d smart_currency -c \
        "SELECT 
            COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_trades,
            COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as closed_trades,
            COUNT(CASE WHEN profit_loss_percentage > 0 THEN 1 END) as winning_trades,
            (SELECT config_value FROM trade_config WHERE config_key = 'auto_trading_enabled') as auto_trading
         FROM trades;"
}

# Update containers
update_containers() {
    print_status "Updating containers..."
    cd "$PRODUCTION_DIR"
    
    # Pull latest changes (if using git)
    if [ -d "$PROJECT_ROOT/.git" ]; then
        print_status "Pulling latest changes..."
        cd "$PROJECT_ROOT"
        git pull
    fi
    
    cd "$PRODUCTION_DIR"
    
    # Rebuild and restart
    docker-compose build --no-cache
    docker-compose up -d
    
    print_status "✅ Containers updated successfully!"
}

# Show help
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       - Start all services"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  status      - Show trading status"
    echo "  health      - Check services health"
    echo "  logs [service] - View logs (optional: specific service)"
    echo "  enable-trading - Enable automatic trading"
    echo "  disable-trading - Disable automatic trading"
    echo "  update      - Update containers with latest changes"
    echo "  help        - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs monitor"
    echo "  $0 enable-trading"
    echo ""
}

# Main script logic
case "$1" in
    "start")
        check_docker
        check_env_file
        start_services
        print_status "🚀 System started! Access the dashboard at http://localhost:3000"
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        check_docker
        restart_services
        ;;
    "health")
        check_services_health
        ;;
    "status")
        show_status
        ;;
    "logs")
        view_logs "$2"
        ;;
    "enable-trading")
        enable_trading
        ;;
    "disable-trading")
        disable_trading
        ;;
    "update")
        update_containers
        ;;
    "help"|"")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac