#!/bin/bash
# Measure adjust command performance via daemon
# This script starts the daemon, runs adjust command, and measures execution time

set -e

# Change to project root directory
cd "$(dirname "$0")/.."

# Configuration
# Check for onedir or onefile binary
if [ -f "./dist/agrr/agrr" ]; then
    AGRR_BINARY="./dist/agrr/agrr"
elif [ -f "./dist/agrr" ]; then
    AGRR_BINARY="./dist/agrr"
else
    echo "❌ Error: AGRR binary not found"
    echo "   Please run: ./scripts/build_standalone.sh --onedir"
    exit 1
fi
TEST_DATA_DIR="./test_data"

# Test data files
CURRENT_ALLOCATION="$TEST_DATA_DIR/test_current_allocation.json"
MOVES_FILE="$TEST_DATA_DIR/test_adjust_moves.json"
WEATHER_FILE="$TEST_DATA_DIR/weather_2023.json"
FIELDS_FILE="$TEST_DATA_DIR/fields_correct.json"
CROPS_FILE="$TEST_DATA_DIR/crops_correct.json"

# Planning period
PLANNING_START="2023-05-01"
PLANNING_END="2023-10-31"

echo "═══════════════════════════════════════════════════════════════════"
echo "  AGRR Daemon Adjust Performance Measurement"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# AGRR_BINARY is already validated above

# Check if test data files exist
for file in "$CURRENT_ALLOCATION" "$MOVES_FILE" "$WEATHER_FILE" "$FIELDS_FILE" "$CROPS_FILE"; do
    if [ ! -f "$file" ]; then
        echo "❌ Error: Test data file not found: $file"
        exit 1
    fi
done

echo "✓ AGRR binary: $AGRR_BINARY"
echo "✓ Test data files verified"
echo ""

# Function to check if daemon is running
check_daemon_status() {
    $AGRR_BINARY daemon status > /dev/null 2>&1
    return $?
}

# Function to stop daemon
stop_daemon() {
    echo "Stopping daemon..."
    $AGRR_BINARY daemon stop > /dev/null 2>&1 || true
    sleep 1
}

# Function to start daemon
start_daemon() {
    echo "Starting daemon..."
    $AGRR_BINARY daemon start
    sleep 2  # Wait for daemon to be ready
}

# Function to measure execution time
measure_execution_time() {
    local mode=$1
    local output_file=$2
    
    echo ""
    echo "───────────────────────────────────────────────────────────────────"
    echo "  Mode: $mode"
    echo "───────────────────────────────────────────────────────────────────"
    
    # Measure execution time (3 runs for average)
    local total_time=0
    local runs=3
    
    for i in $(seq 1 $runs); do
        echo -n "Run $i/$runs: "
        
        local start_time=$(date +%s.%N)
        
        $AGRR_BINARY optimize adjust \
            --current-allocation "$CURRENT_ALLOCATION" \
            --moves "$MOVES_FILE" \
            --weather-file "$WEATHER_FILE" \
            --fields-file "$FIELDS_FILE" \
            --crops-file "$CROPS_FILE" \
            --planning-start "$PLANNING_START" \
            --planning-end "$PLANNING_END" \
            --format json > /dev/null 2>&1
        
        local end_time=$(date +%s.%N)
        local elapsed=$(echo "$end_time - $start_time" | bc)
        
        echo "${elapsed}s"
        total_time=$(echo "$total_time + $elapsed" | bc)
        
        # Wait a bit between runs
        sleep 0.5
    done
    
    local avg_time=$(echo "scale=3; $total_time / $runs" | bc)
    echo ""
    echo "Average execution time: ${avg_time}s"
    echo "$mode,$avg_time" >> "$output_file"
}

# Output file for results
RESULTS_FILE="daemon_adjust_performance_results.csv"
echo "mode,avg_time_seconds" > "$RESULTS_FILE"

# Test 1: Without daemon (direct execution)
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  Test 1: Direct Execution (No Daemon)"
echo "═══════════════════════════════════════════════════════════════════"
stop_daemon
measure_execution_time "direct" "$RESULTS_FILE"

# Test 2: With daemon (first run - daemon startup included)
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  Test 2: Daemon Execution (Cold Start)"
echo "═══════════════════════════════════════════════════════════════════"
stop_daemon
start_daemon
measure_execution_time "daemon_cold" "$RESULTS_FILE"

# Test 3: With daemon (warm run - daemon already running)
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  Test 3: Daemon Execution (Warm Run)"
echo "═══════════════════════════════════════════════════════════════════"
# Daemon already running from Test 2
measure_execution_time "daemon_warm" "$RESULTS_FILE"

# Clean up
stop_daemon

# Display results
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  Performance Comparison"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Read results and calculate improvement
direct_time=$(grep "^direct," "$RESULTS_FILE" | cut -d',' -f2)
daemon_cold_time=$(grep "^daemon_cold," "$RESULTS_FILE" | cut -d',' -f2)
daemon_warm_time=$(grep "^daemon_warm," "$RESULTS_FILE" | cut -d',' -f2)

# Calculate speedup
if [ -n "$direct_time" ] && [ -n "$daemon_warm_time" ]; then
    speedup=$(echo "scale=2; $direct_time / $daemon_warm_time" | bc)
else
    speedup="N/A"
fi

echo "┌─────────────────────────┬──────────────┬─────────────┐"
echo "│ Mode                    │ Time (s)     │ Speedup     │"
echo "├─────────────────────────┼──────────────┼─────────────┤"
printf "│ %-23s │ %12s │ %11s │\n" "Direct Execution" "$direct_time" "1.00x"
printf "│ %-23s │ %12s │ %11s │\n" "Daemon (Cold Start)" "$daemon_cold_time" "N/A"
printf "│ %-23s │ %12s │ %11s │\n" "Daemon (Warm Run)" "$daemon_warm_time" "${speedup}x"
echo "└─────────────────────────┴──────────────┴─────────────┘"
echo ""

# Save detailed results
DETAILED_RESULTS="daemon_adjust_performance_results.txt"
cat > "$DETAILED_RESULTS" << EOF
AGRR Daemon Adjust Performance Measurement Results
=================================================

Date: $(date)
Binary: $AGRR_BINARY
Test Data: $TEST_DATA_DIR

Performance Results:
-------------------
Direct Execution:      ${direct_time}s  (baseline)
Daemon (Cold Start):   ${daemon_cold_time}s
Daemon (Warm Run):     ${daemon_warm_time}s

Speedup: ${speedup}x

Files:
------
- CSV Results: $RESULTS_FILE
- Detailed Results: $DETAILED_RESULTS

Configuration:
--------------
Current Allocation: $CURRENT_ALLOCATION
Moves File: $MOVES_FILE
Weather File: $WEATHER_FILE
Fields File: $FIELDS_FILE
Crops File: $CROPS_FILE
Planning Period: $PLANNING_START to $PLANNING_END

EOF

echo "✓ Results saved to:"
echo "  - CSV: $RESULTS_FILE"
echo "  - Detailed: $DETAILED_RESULTS"
echo ""
echo "Done!"

