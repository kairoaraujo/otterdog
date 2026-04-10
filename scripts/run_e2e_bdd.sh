#!/usr/bin/env bash
#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

# Run E2E BDD tests with nice visual output

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Otterdog E2E BDD Test Runner${NC}"
echo -e "${BLUE}===================================${NC}"
echo

# Check if WireMock is running
if curl -s http://localhost:8080/__admin/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ WireMock is running${NC}"
else
    echo -e "${YELLOW}⚠ WireMock is not running. Starting it...${NC}"
    docker run -d --name wiremock -p 8080:8080 wiremock/wiremock:3.3.1
    sleep 3
fi

# Default to all tests
TEST_FILTER="${1:-}"

# Build pytest command
PYTEST_CMD="poetry run pytest tests/e2e"

# Add test filter if provided
if [ -n "$TEST_FILTER" ]; then
    case "$TEST_FILTER" in
        smoke)
            echo -e "${BLUE}Running smoke tests only...${NC}"
            PYTEST_CMD="$PYTEST_CMD -m smoke"
            ;;
        happy)
            echo -e "${BLUE}Running happy path tests...${NC}"
            PYTEST_CMD="$PYTEST_CMD -m happy_path"
            ;;
        error)
            echo -e "${BLUE}Running error handling tests...${NC}"
            PYTEST_CMD="$PYTEST_CMD -m error_handling"
            ;;
        init)
            echo -e "${BLUE}Running init feature tests...${NC}"
            PYTEST_CMD="$PYTEST_CMD test_init_bdd.py"
            ;;
        *)
            echo -e "${BLUE}Running specific test: $TEST_FILTER${NC}"
            PYTEST_CMD="$PYTEST_CMD -k $TEST_FILTER"
            ;;
    esac
else
    echo -e "${BLUE}Running all E2E BDD tests...${NC}"
fi

# Add visual options
PYTEST_CMD="$PYTEST_CMD --gherkin-terminal-reporter -vv --color=yes"

# Add coverage if requested
if [ "$2" == "coverage" ]; then
    echo -e "${BLUE}Generating coverage report...${NC}"
    PYTEST_CMD="$PYTEST_CMD --cov=otterdog --cov-report=term-missing"
fi

# Add quiet mode if requested
if [ "$2" == "quiet" ]; then
    PYTEST_CMD="$PYTEST_CMD -q --tb=short"
fi

echo
echo -e "${BLUE}Command: $PYTEST_CMD${NC}"
echo -e "${BLUE}-----------------------------------${NC}"
echo

# Run the tests
$PYTEST_CMD

# Show summary
EXIT_CODE=$?
echo
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Some tests failed. Check the output above.${NC}"
fi

exit $EXIT_CODE