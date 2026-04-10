#!/bin/bash

# E2E Test Runner for Otterdog
# This script helps run the E2E tests with proper setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Otterdog E2E Test Runner${NC}"
echo "========================="
echo ""

# Check if WireMock is required
if [ "$1" != "--no-wiremock" ]; then
    echo -e "${YELLOW}Starting WireMock server...${NC}"

    # Stop existing WireMock if running
    docker stop wiremock 2>/dev/null || true
    docker rm wiremock 2>/dev/null || true

    # Start WireMock
    docker run -d \
        --name wiremock \
        -p 8080:8080 \
        -v $(pwd)/tests/e2e/mocks/mappings:/home/wiremock/mappings \
        wiremock/wiremock:3.3.1

    # Wait for WireMock to be ready
    echo "Waiting for WireMock to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8080/__admin/health > /dev/null 2>&1; then
            echo -e "${GREEN}WireMock is ready!${NC}"
            break
        fi
        sleep 1
    done

    # Set environment variable
    export E2E_TESTING=true
    export GITHUB_API_URL=http://localhost:8080
fi

# Parse test selection
TEST_TYPE=${1:-all}

case $TEST_TYPE in
    all)
        echo -e "${YELLOW}Running all E2E tests...${NC}"
        poetry run pytest tests/e2e -v -m e2e
        ;;
    pr614)
        echo -e "${YELLOW}Running PR #614 tests...${NC}"
        poetry run pytest tests/e2e -v -m pr614
        ;;
    operations)
        echo -e "${YELLOW}Running operation tests...${NC}"
        poetry run pytest tests/e2e/operations -v
        ;;
    features)
        echo -e "${YELLOW}Running feature tests...${NC}"
        poetry run pytest tests/e2e/features -v
        ;;
    coverage)
        echo -e "${YELLOW}Running tests with coverage...${NC}"
        poetry run pytest tests/e2e -v --e2e-coverage
        echo ""
        echo -e "${GREEN}Coverage reports generated in coverage/ directory${NC}"
        ;;
    update-mocks)
        echo -e "${YELLOW}Updating mocks from OpenAPI spec...${NC}"
        poetry run python tests/e2e/mocks/generator.py
        ;;
    *)
        echo "Usage: $0 [all|pr614|operations|features|coverage|update-mocks] [--no-wiremock]"
        echo ""
        echo "Options:"
        echo "  all          - Run all E2E tests (default)"
        echo "  pr614        - Run only PR #614 feature tests"
        echo "  operations   - Run operation tests (import/apply/validate)"
        echo "  features     - Run feature-specific tests"
        echo "  coverage     - Run tests with coverage reporting"
        echo "  update-mocks - Update mocks from GitHub OpenAPI spec"
        echo ""
        echo "Flags:"
        echo "  --no-wiremock - Don't start WireMock (assumes it's already running)"
        exit 1
        ;;
esac

# Cleanup
if [ "$2" != "--no-wiremock" ] && [ "$1" != "--no-wiremock" ]; then
    echo ""
    echo -e "${YELLOW}Stopping WireMock...${NC}"
    docker stop wiremock
    docker rm wiremock
fi

echo ""
echo -e "${GREEN}E2E tests completed!${NC}"