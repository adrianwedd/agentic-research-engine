#!/usr/bin/env bash
set -e

# enhanced-setup.sh
# Comprehensive setup for Agentic Research Engine development

echo "Setting up Agentic Research Engine development environment..."

validate_environment() {
    echo "Validating system requirements..."
    if ! command -v python3 >/dev/null 2>&1; then
        echo "Python3 is required but not installed." >&2
        exit 1
    fi
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if python3 - <<PY
import sys
sys.exit(0 if (sys.version_info.major, sys.version_info.minor) >= (3, 10) else 1)
PY
    then
        echo "Python version ${PY_VER} detected"
    else
        echo "Python 3.10+ is required (found ${PY_VER})" >&2
        exit 1
    fi
    if ! command -v docker >/dev/null 2>&1; then
        echo "Docker is required but not installed." >&2
        exit 1
    fi
    if ! command -v poetry >/dev/null 2>&1; then
        echo "Warning: Poetry not found. You may want to install it." >&2
    fi
}

verify_services() {
    echo "Verifying core services..."
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            echo "Docker daemon running"
        else
            echo "Warning: Docker daemon not running" >&2
        fi
    fi
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        echo "API endpoint reachable"
    else
        echo "Warning: API endpoint not reachable" >&2
    fi
}

setup_dev_tools() {
    echo "Installing development tools..."
    bash "$(dirname "$0")/agent-setup.sh"
    pre-commit install >/dev/null
}

setup_neo4j_indexes() {
    if [ -n "${NEO4J_URI:-}" ]; then
        echo "Configuring Neo4j indexes..."
        python "$(dirname "$0")/neo4j_setup.py" || echo "Warning: failed to create Neo4j indexes" >&2
    fi
}

main() {
    validate_environment
    verify_services
    setup_dev_tools
    setup_neo4j_indexes
    echo "Development environment setup complete."
}

main "$@"

