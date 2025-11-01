#!/bin/bash
# test_all_docker_composes.sh - Test all docker-compose configurations
# Extracts comments from each file and runs the container for 10 seconds

LOG_FILE="/workspaces/NetAlertX/test/docker_tests/configurations/test_results.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Docker Compose Tests - $(date)" > "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"

# Function to extract comments from docker-compose file
extract_comments() {
    local file="$1"
    echo "File: $(basename "$file")" >> "$LOG_FILE"
    echo "----------------------------------------" >> "$LOG_FILE"

    # Extract lines starting with # until we hit a non-comment line
    awk '
    /^#/ {
        # Remove the # and any leading/trailing whitespace
        comment = substr($0, 2)
        sub(/^ */, "", comment)
        sub(/ *$/, "", comment)
        if (comment != "") {
            print comment
        }
    }
    /^[^#]/ && !/^$/ {
        exit
    }
    ' "$file" >> "$LOG_FILE"

    echo "" >> "$LOG_FILE"
}

# Function to run docker-compose test
run_test() {
    local file="$1"
    local dirname
    dirname=$(dirname "$file")
    local basename
    basename=$(basename "$file")

    echo "Testing: $basename" >> "$LOG_FILE"
    echo "Directory: $dirname" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    echo "Running docker-compose up..." >> "$LOG_FILE"
    timeout 10s docker-compose -f "$basename" up 2>&1 >> "$LOG_FILE"

    # Clean up
    docker-compose -f "$basename" down -v 2>/dev/null || true
    docker volume prune -f 2>/dev/null || true

find "$SCRIPT_DIR" -name "docker-compose*.yml" -type f -print0 | sort -z | while IFS= read -r -d '' file; do
    extract_comments "$file"
    run_test "$file"
done


echo "All tests completed - $(date)" >> "$LOG_FILE"
echo "Results saved to: $LOG_FILE"