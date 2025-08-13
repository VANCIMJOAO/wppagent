#!/bin/bash

# Monitoring Infrastructure Test Suite for WhatsApp Agent
# Tests all monitoring components: Prometheus, Grafana, Metrics Integration

set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ((PASSED_TESTS++))
            ;;
        "FAIL")
            echo -e "${RED}❌ $message${NC}"
            ((FAILED_TESTS++))
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️ $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️ $message${NC}"
            ;;
    esac
    ((TOTAL_TESTS++))
}

# Function to test service availability
test_service() {
    local service_name=$1
    local url=$2
    local expected_content=$3
    
    echo "🔍 Testing $service_name..."
    
    if curl -s --max-time 10 "$url" | grep -q "$expected_content"; then
        print_status "SUCCESS" "$service_name is accessible and responding correctly"
    else
        print_status "FAIL" "$service_name is not responding or content mismatch"
    fi
}

# Function to test Docker service
test_docker_service() {
    local service_name=$1
    
    echo "🔍 Testing Docker service: $service_name..."
    
    if docker-compose -f docker-compose.monitoring.yml ps | grep -q "$service_name.*Up"; then
        print_status "SUCCESS" "Docker service $service_name is running"
    else
        print_status "FAIL" "Docker service $service_name is not running"
    fi
}

# Function to test metrics endpoint
test_metrics_endpoint() {
    echo "🔍 Testing application metrics endpoint..."
    
    # Test if metrics endpoint returns Prometheus format
    if curl -s http://localhost:8000/metrics | grep -q "# HELP"; then
        print_status "SUCCESS" "Application metrics endpoint is working"
        
        # Test specific metrics
        if curl -s http://localhost:8000/metrics | grep -q "http_requests_total"; then
            print_status "SUCCESS" "HTTP metrics are being collected"
        else
            print_status "FAIL" "HTTP metrics not found"
        fi
        
        if curl -s http://localhost:8000/metrics | grep -q "webhook_messages_processed_total"; then
            print_status "SUCCESS" "Webhook metrics are being collected"
        else
            print_status "WARNING" "Webhook metrics not found (may be normal if no messages processed)"
        fi
        
    else
        print_status "FAIL" "Application metrics endpoint not working"
    fi
}

# Function to test Prometheus configuration
test_prometheus_config() {
    echo "🔍 Testing Prometheus configuration..."
    
    # Check if Prometheus config exists
    if [[ -f "prometheus/prometheus.yml" ]]; then
        print_status "SUCCESS" "Prometheus configuration file exists"
        
        # Check if it contains our application target
        if grep -q "whatsapp-agent" prometheus/prometheus.yml; then
            print_status "SUCCESS" "WhatsApp Agent target configured in Prometheus"
        else
            print_status "FAIL" "WhatsApp Agent target not found in Prometheus config"
        fi
        
    else
        print_status "FAIL" "Prometheus configuration file not found"
    fi
    
    # Check alerting rules
    if [[ -f "prometheus/alerts/whatsapp_agent_alerts.yml" ]]; then
        print_status "SUCCESS" "Alerting rules file exists"
    else
        print_status "FAIL" "Alerting rules file not found"
    fi
}

# Function to test Grafana configuration
test_grafana_config() {
    echo "🔍 Testing Grafana configuration..."
    
    # Check dashboard file
    if [[ -f "grafana/whatsapp_agent_dashboard.json" ]]; then
        print_status "SUCCESS" "Grafana dashboard configuration exists"
        
        # Check if dashboard has panels
        if grep -q '"panels"' grafana/whatsapp_agent_dashboard.json; then
            print_status "SUCCESS" "Dashboard contains visualization panels"
        else
            print_status "FAIL" "Dashboard panels not found"
        fi
        
    else
        print_status "FAIL" "Grafana dashboard file not found"
    fi
    
    # Check datasource configuration
    if [[ -f "grafana/datasources/prometheus.yml" ]]; then
        print_status "SUCCESS" "Grafana datasource configuration exists"
    else
        print_status "FAIL" "Grafana datasource configuration not found"
    fi
}

# Function to test Python dependencies
test_python_dependencies() {
    echo "🔍 Testing Python monitoring dependencies..."
    
    if python -c "import prometheus_client" 2>/dev/null; then
        print_status "SUCCESS" "prometheus_client package is installed"
    else
        print_status "FAIL" "prometheus_client package not installed"
    fi
    
    if python -c "import psutil" 2>/dev/null; then
        print_status "SUCCESS" "psutil package is installed"
    else
        print_status "FAIL" "psutil package not installed"
    fi
}

# Function to test metrics integration
test_metrics_integration() {
    echo "🔍 Testing metrics integration..."
    
    # Test if metrics module can be imported
    if python -c "
import sys
sys.path.append('$PWD')
from app.utils.metrics import metrics_collector
print('Metrics module loaded successfully')
" 2>/dev/null; then
        print_status "SUCCESS" "Metrics module can be imported"
    else
        print_status "FAIL" "Metrics module import failed"
    fi
    
    # Test metrics generation
    if python -c "
import sys
sys.path.append('$PWD')
from app.utils.metrics import get_metrics_response
response = get_metrics_response()
assert 'text/plain' in response.media_type
print('Metrics generation working')
" 2>/dev/null; then
        print_status "SUCCESS" "Metrics generation is working"
    else
        print_status "FAIL" "Metrics generation failed"
    fi
}

# Main test execution
main() {
    echo "🚀 Starting WhatsApp Agent Monitoring Infrastructure Tests"
    echo "============================================================"
    
    # Test 1: Configuration Files
    echo -e "\n📋 Phase 1: Configuration Files"
    test_prometheus_config
    test_grafana_config
    
    # Test 2: Python Dependencies and Integration
    echo -e "\n🐍 Phase 2: Python Dependencies and Integration"
    test_python_dependencies
    test_metrics_integration
    
    # Test 3: Application Metrics (if app is running)
    echo -e "\n📊 Phase 3: Application Metrics"
    if curl -s --max-time 5 http://localhost:8000/health >/dev/null 2>&1; then
        print_status "INFO" "Application appears to be running, testing metrics"
        test_metrics_endpoint
    else
        print_status "WARNING" "Application not running, skipping live metrics tests"
    fi
    
    # Test 4: Docker Services (if docker-compose is available)
    echo -e "\n🐳 Phase 4: Docker Monitoring Services"
    if command -v docker-compose >/dev/null 2>&1; then
        # Check if monitoring stack is running
        if docker-compose -f docker-compose.monitoring.yml ps | grep -q "Up"; then
            print_status "INFO" "Monitoring stack is running, testing services"
            
            test_docker_service "prometheus"
            test_docker_service "grafana"
            test_docker_service "node-exporter"
            
            # Test service endpoints if they're running
            test_service "Prometheus" "http://localhost:9090/-/healthy" "Prometheus is Healthy"
            test_service "Grafana" "http://localhost:3000/api/health" "ok"
            test_service "Node Exporter" "http://localhost:9100/metrics" "node_"
            
        else
            print_status "WARNING" "Monitoring stack not running, skipping Docker service tests"
            print_status "INFO" "To start monitoring stack: docker-compose -f docker-compose.monitoring.yml up -d"
        fi
    else
        print_status "WARNING" "Docker Compose not available, skipping Docker service tests"
    fi
    
    # Test 5: Integration Tests
    echo -e "\n🔗 Phase 5: Integration Tests"
    
    # Test if Prometheus can scrape application metrics
    if curl -s --max-time 5 http://localhost:9090/api/v1/targets 2>/dev/null | grep -q "whatsapp-agent"; then
        print_status "SUCCESS" "Prometheus is configured to scrape application metrics"
    else
        print_status "WARNING" "Prometheus target configuration not verified (may be normal if stack not running)"
    fi
    
    # Summary
    echo -e "\n📈 Test Results Summary"
    echo "======================="
    echo -e "Total Tests: $TOTAL_TESTS"
    echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
    
    success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    
    if [[ $success_rate -ge 80 ]]; then
        echo -e "\n${GREEN}🎉 MONITORING INFRASTRUCTURE: READY FOR PRODUCTION${NC}"
        echo -e "Success Rate: ${GREEN}$success_rate%${NC}"
        
        echo -e "\n📋 Quick Start Commands:"
        echo -e "  ${BLUE}Start monitoring stack:${NC} docker-compose -f docker-compose.monitoring.yml up -d"
        echo -e "  ${BLUE}Access Grafana:${NC} http://localhost:3000 (admin/admin123)"
        echo -e "  ${BLUE}Access Prometheus:${NC} http://localhost:9090"
        echo -e "  ${BLUE}View metrics:${NC} http://localhost:8000/metrics"
        
        exit 0
    elif [[ $success_rate -ge 60 ]]; then
        echo -e "\n${YELLOW}⚠️ MONITORING INFRASTRUCTURE: PARTIALLY READY${NC}"
        echo -e "Success Rate: ${YELLOW}$success_rate%${NC}"
        echo -e "Some components need attention before production deployment."
        exit 1
    else
        echo -e "\n${RED}❌ MONITORING INFRASTRUCTURE: NOT READY${NC}"
        echo -e "Success Rate: ${RED}$success_rate%${NC}"
        echo -e "Multiple issues need to be resolved before deployment."
        exit 2
    fi
}

# Execute main function
main "$@"
