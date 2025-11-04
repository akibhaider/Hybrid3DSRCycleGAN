#!/bin/bash

# Monitor the non-linear co-registration progress

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║      NON-LINEAR CO-REGISTRATION MONITORING (ANTs SyN Registration)         ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if process is running
PROCESS_RUNNING=$(ps aux | grep -v grep | grep "non_linear_coregistration.py" | wc -l)

if [ $PROCESS_RUNNING -gt 0 ]; then
    echo "✓ Registration process is RUNNING"
    echo ""
    
    # Show process info
    echo "Process info:"
    ps aux | grep -v grep | grep "non_linear_coregistration.py" | awk '{printf "  PID: %s, CPU: %s%%, MEM: %s%%, Time: %s\n", $2, $3, $4, $10}'
    echo ""
else
    echo "✗ Registration process is NOT running"
    echo ""
fi

# Count completed registrations
COMPLETED=$(find '/mnt/Data/AKIB/Training data/' -name '*_to_T1_Warped.nii.gz' 2>/dev/null | wc -l)
EXPECTED=200

echo "Progress:"
echo "  Completed: $COMPLETED / $EXPECTED registrations"

# Calculate percentage
PERCENTAGE=$(echo "scale=1; ($COMPLETED * 100) / $EXPECTED" | bc)
echo "  Progress: ${PERCENTAGE}%"
echo ""

# Show progress bar
FILLED=$(echo "scale=0; $COMPLETED / 4" | bc)
BAR=""
for i in $(seq 1 50); do
    if [ $i -le $FILLED ]; then
        BAR="${BAR}█"
    else
        BAR="${BAR}░"
    fi
done
echo "  [$BAR]"
echo ""

# Show most recent outputs
echo "Most recent registrations (last 5):"
find '/mnt/Data/AKIB/Training data/' -name '*_to_T1_Warped.nii.gz' -type f -printf '%T+ %p\n' 2>/dev/null | sort -r | head -5 | while read line; do
    timestamp=$(echo "$line" | cut -d' ' -f1)
    filepath=$(echo "$line" | cut -d' ' -f2-)
    filename=$(basename "$filepath")
    echo "  $timestamp - $filename"
done
echo ""

# Estimate time remaining
if [ $COMPLETED -gt 0 ]; then
    # Get time of first and last file
    FIRST_TIME=$(find '/mnt/Data/AKIB/Training data/' -name '*_to_T1_Warped.nii.gz' -type f -printf '%T@\n' 2>/dev/null | sort | head -1)
    LAST_TIME=$(find '/mnt/Data/AKIB/Training data/' -name '*_to_T1_Warped.nii.gz' -type f -printf '%T@\n' 2>/dev/null | sort | tail -1)
    
    ELAPSED=$(echo "$LAST_TIME - $FIRST_TIME" | bc)
    
    if [ $(echo "$ELAPSED > 0" | bc) -eq 1 ]; then
        AVG_TIME=$(echo "scale=2; $ELAPSED / $COMPLETED" | bc)
        REMAINING=$(echo "scale=2; $AVG_TIME * ($EXPECTED - $COMPLETED)" | bc)
        REMAINING_MIN=$(echo "scale=1; $REMAINING / 60" | bc)
        
        echo "Time estimates:"
        echo "  Average per registration: ${AVG_TIME}s"
        echo "  Estimated time remaining: ${REMAINING_MIN} minutes"
        echo ""
    fi
fi

# Show log file tail (if exists and not empty)
LOG_FILE="/mnt/code/AKIB/Hybrid3DSRCycleGAN/nonlinear_coregistration_output.log"
if [ -f "$LOG_FILE" ] && [ -s "$LOG_FILE" ]; then
    echo "Recent log output (last 10 lines):"
    tail -10 "$LOG_FILE" | sed 's/^/  /'
    echo ""
fi

echo "════════════════════════════════════════════════════════════════════════════"
echo "To check progress again, run: bash monitor_nonlinear_registration.sh"
echo "To view full log: tail -f nonlinear_coregistration_output.log"
echo "════════════════════════════════════════════════════════════════════════════"
