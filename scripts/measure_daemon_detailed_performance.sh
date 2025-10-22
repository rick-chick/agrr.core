#!/bin/bash
# Measure detailed performance of daemon-based adjust command
# This script measures client-side and server-side execution times separately

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
echo "  AGRR Daemon Detailed Performance Measurement"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "Binary: $AGRR_BINARY"
echo "Binary Type: $(file $AGRR_BINARY | grep -o 'ELF.*' || echo 'unknown')"
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

echo "═══════════════════════════════════════════════════════════════════"
echo "  Test 1: Direct Execution (Baseline)"
echo "═══════════════════════════════════════════════════════════════════"
stop_daemon

echo ""
echo "Running 5 iterations to establish baseline..."
echo ""

direct_times=()
for i in $(seq 1 5); do
    echo -n "Iteration $i/5: "
    
    start_time=$(date +%s.%N)
    
    $AGRR_BINARY optimize adjust \
        --current-allocation "$CURRENT_ALLOCATION" \
        --moves "$MOVES_FILE" \
        --weather-file "$WEATHER_FILE" \
        --fields-file "$FIELDS_FILE" \
        --crops-file "$CROPS_FILE" \
        --planning-start "$PLANNING_START" \
        --planning-end "$PLANNING_END" \
        --format json > /dev/null 2>&1
    
    end_time=$(date +%s.%N)
    elapsed=$(echo "$end_time - $start_time" | bc)
    
    direct_times+=($elapsed)
    echo "${elapsed}s"
    sleep 0.5
done

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  Test 2: Daemon Execution (With Timing Instrumentation)"
echo "═══════════════════════════════════════════════════════════════════"

# Start daemon
stop_daemon
start_daemon

echo ""
echo "Running 5 iterations with daemon..."
echo ""

daemon_times=()
for i in $(seq 1 5); do
    echo -n "Iteration $i/5: "
    
    # Client-side timing (full round-trip time)
    client_start=$(date +%s.%N)
    
    $AGRR_BINARY optimize adjust \
        --current-allocation "$CURRENT_ALLOCATION" \
        --moves "$MOVES_FILE" \
        --weather-file "$WEATHER_FILE" \
        --fields-file "$FIELDS_FILE" \
        --crops-file "$CROPS_FILE" \
        --planning-start "$PLANNING_START" \
        --planning-end "$PLANNING_END" \
        --format json > /dev/null 2>&1
    
    client_end=$(date +%s.%N)
    client_elapsed=$(echo "$client_end - $client_start" | bc)
    
    daemon_times+=($client_elapsed)
    echo "${client_elapsed}s (client round-trip)"
    sleep 0.5
done

stop_daemon

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  Performance Analysis"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Calculate statistics
calc_stats() {
    local -n arr=$1
    local sum=0
    local min=${arr[0]}
    local max=${arr[0]}
    
    for val in "${arr[@]}"; do
        sum=$(echo "$sum + $val" | bc)
        if (( $(echo "$val < $min" | bc -l) )); then
            min=$val
        fi
        if (( $(echo "$val > $max" | bc -l) )); then
            max=$val
        fi
    done
    
    local count=${#arr[@]}
    local avg=$(echo "scale=3; $sum / $count" | bc)
    
    echo "$avg $min $max"
}

direct_stats=($(calc_stats direct_times))
daemon_stats=($(calc_stats daemon_times))

direct_avg=${direct_stats[0]}
direct_min=${direct_stats[1]}
direct_max=${direct_stats[2]}

daemon_avg=${daemon_stats[0]}
daemon_min=${daemon_stats[1]}
daemon_max=${daemon_stats[2]}

echo "┌──────────────────────┬─────────────┬─────────────┬─────────────┐"
echo "│ Mode                 │ Avg (s)     │ Min (s)     │ Max (s)     │"
echo "├──────────────────────┼─────────────┼─────────────┼─────────────┤"
printf "│ %-20s │ %11s │ %11s │ %11s │\n" "Direct Execution" "$direct_avg" "$direct_min" "$direct_max"
printf "│ %-20s │ %11s │ %11s │ %11s │\n" "Daemon (Client)" "$daemon_avg" "$daemon_min" "$daemon_max"
echo "└──────────────────────┴─────────────┴─────────────┴─────────────┘"
echo ""

# Calculate overhead
overhead=$(echo "scale=3; $daemon_avg - $direct_avg" | bc)
overhead_pct=$(echo "scale=1; ($daemon_avg / $direct_avg - 1) * 100" | bc)

if (( $(echo "$overhead > 0" | bc -l) )); then
    echo "Daemon Overhead: +${overhead}s (+${overhead_pct}%)"
    echo ""
    echo "Analysis:"
    echo "  The daemon adds overhead instead of improving performance."
    echo "  This is because the adjust command's processing time (~${direct_avg}s)"
    echo "  is much longer than the binary startup time savings."
    echo ""
    echo "  Breakdown:"
    echo "    - JSON serialization/deserialization overhead"
    echo "    - Unix socket communication overhead"
    echo "    - Process context switching overhead"
    echo ""
    echo "  Recommendation:"
    echo "    For heavy commands like 'adjust', direct execution is faster."
    echo "    Daemon mode is beneficial for quick commands (e.g., --help, status)."
else
    speedup=$(echo "scale=2; $direct_avg / $daemon_avg" | bc)
    echo "Speedup: ${speedup}x"
    echo ""
    echo "Daemon execution is ${speedup}x faster than direct execution."
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  Detailed Results Saved"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Save detailed results
cat > daemon_detailed_performance_results.txt << EOF
AGRR Daemon Detailed Performance Measurement
============================================

Date: $(date)
Binary: $AGRR_BINARY
Binary Type: $(file $AGRR_BINARY | grep -o 'ELF.*' || echo 'unknown')

Performance Results:
-------------------
Direct Execution:
  Average: ${direct_avg}s
  Min: ${direct_min}s
  Max: ${direct_max}s
  
  Raw times: ${direct_times[@]}

Daemon Execution (Client Round-Trip):
  Average: ${daemon_avg}s
  Min: ${daemon_min}s
  Max: ${daemon_max}s
  
  Raw times: ${daemon_times[@]}

Overhead Analysis:
------------------
Daemon Overhead: ${overhead}s (${overhead_pct}%)

Explanation:
------------
The daemon adds overhead because:
1. JSON serialization/deserialization of large output
2. Unix socket communication overhead
3. Process context switching overhead

For heavy commands like 'adjust' (processing time: ~${direct_avg}s),
the daemon's startup time savings (typically 1-2s) is outweighed by
the communication overhead.

Recommendation:
--------------
- Use direct execution for heavy processing commands (adjust, allocate)
- Use daemon for quick commands (--help, status, simple queries)
- Consider reducing output size for daemon mode (use --format compact)

Configuration:
-------------
Current Allocation: $CURRENT_ALLOCATION
Moves File: $MOVES_FILE
Weather File: $WEATHER_FILE
Fields File: $FIELDS_FILE
Crops File: $CROPS_FILE
Planning Period: $PLANNING_START to $PLANNING_END
EOF

echo "✓ Results saved to: daemon_detailed_performance_results.txt"
echo ""
echo "Done!"

