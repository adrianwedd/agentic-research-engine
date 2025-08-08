#!/bin/bash

# Phase 1 Technical Validation Monitoring Deployment Script
# ORCHESTRIX Integration Program

set -e

echo "=================================================="
echo "PHASE 1 TECHNICAL VALIDATION MONITORING"
echo "ORCHESTRIX Integration Program"
echo "=================================================="
echo ""

# Configuration
COORDINATION_DIR="$(dirname "$0")"
TRACKER_FILE="$COORDINATION_DIR/validation-tracker.json"
MONITOR_SCRIPT="$COORDINATION_DIR/monitor_validation.py"
LOG_FILE="$COORDINATION_DIR/validation_monitor.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
else
    print_status "Python 3 found: $(python3 --version)"
fi

# Check if coordination directory exists
if [ ! -d "$COORDINATION_DIR" ]; then
    print_warning "Creating coordination directory..."
    mkdir -p "$COORDINATION_DIR"
fi

# Check if tracker file exists
if [ ! -f "$TRACKER_FILE" ]; then
    print_warning "Validation tracker not found. Creating from template..."
    # Tracker should already exist from the Write command above
else
    print_status "Validation tracker found: $TRACKER_FILE"
fi

# Check if monitor script exists
if [ ! -f "$MONITOR_SCRIPT" ]; then
    print_error "Monitor script not found: $MONITOR_SCRIPT"
    exit 1
else
    print_status "Monitor script found: $MONITOR_SCRIPT"
    chmod +x "$MONITOR_SCRIPT"
fi

echo ""
echo "Select monitoring mode:"
echo "1) Run once and display report"
echo "2) Continuous monitoring (5-minute intervals)"
echo "3) Continuous monitoring (custom interval)"
echo "4) Background daemon mode"
echo "5) View current status only"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo ""
        print_status "Running single validation check..."
        python3 "$MONITOR_SCRIPT" --once --config "$TRACKER_FILE"
        ;;
    
    2)
        echo ""
        print_status "Starting continuous monitoring (5-minute intervals)..."
        print_warning "Press Ctrl+C to stop"
        python3 "$MONITOR_SCRIPT" --interval 300 --config "$TRACKER_FILE"
        ;;
    
    3)
        echo ""
        read -p "Enter interval in seconds (minimum 60): " interval
        if [ "$interval" -lt 60 ]; then
            print_warning "Interval too short, setting to 60 seconds"
            interval=60
        fi
        print_status "Starting continuous monitoring ($interval second intervals)..."
        print_warning "Press Ctrl+C to stop"
        python3 "$MONITOR_SCRIPT" --interval "$interval" --config "$TRACKER_FILE"
        ;;
    
    4)
        echo ""
        print_status "Starting background daemon..."
        nohup python3 "$MONITOR_SCRIPT" --interval 300 --config "$TRACKER_FILE" > "$LOG_FILE" 2>&1 &
        PID=$!
        echo $PID > "$COORDINATION_DIR/monitor.pid"
        print_status "Monitor started with PID: $PID"
        print_status "Logs: $LOG_FILE"
        print_status "To stop: kill $PID"
        ;;
    
    5)
        echo ""
        print_status "Current validation status:"
        echo ""
        if [ -f "$TRACKER_FILE" ]; then
            # Extract key metrics using Python
            python3 -c "
import json
import datetime

with open('$TRACKER_FILE', 'r') as f:
    data = json.load(f)
    
print('PHASE 1 VALIDATION STATUS')
print('=' * 40)
print(f\"Last Update: {data.get('timestamp', 'Unknown')}\")
print(f\"Overall Status: {data.get('overall_status', 'Unknown')}\")
print(f\"Risk Level: {data.get('risk_level', 'Unknown')}\")
print(f\"Confidence: {data.get('confidence_score', 0) * 100:.0f}%\")
print()
print('WORKSTREAM PROGRESS:')
for ws_name, ws_data in data.get('workstreams', {}).items():
    print(f\"  {ws_name.capitalize()}: {ws_data.get('completion_percentage', 0)}%\")
print()
assessment = data.get('go_no_go_assessment', {})
print(f\"Readiness: {assessment.get('readiness_percentage', 0):.0f}%\")
print(f\"Recommendation: {assessment.get('current_recommendation', 'Unknown')}\")
"
        else
            print_error "Tracker file not found"
        fi
        ;;
    
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=================================================="
echo "For support: orchestrix-prime@company.com"
echo "Documentation: ./coordination/phase1-technical-validation.md"
echo "=================================================="