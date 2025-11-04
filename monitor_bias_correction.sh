#!/bin/bash
# Monitor N4 Bias Correction Progress

LOG_FILE="/mnt/code/AKIB/Hybrid3DSRCycleGAN/bias_correction_output.log"
TOTAL_PATIENTS=50

echo "========================================="
echo "N4 Bias Correction Progress Monitor"
echo "========================================="
date
echo ""

# Check if process is running
PROCESS=$(ps aux | grep "bias_correction.py" | grep -v grep | grep -v monitor)
if [ -z "$PROCESS" ]; then
    echo "❌ Process NOT running"
    echo ""
    echo "Checking completion status..."
    if grep -q "N4 Bias Field Correction Pipeline Complete" "$LOG_FILE" 2>/dev/null; then
        echo "✅ Process COMPLETED successfully!"
    else
        echo "⚠️  Process stopped unexpectedly"
    fi
else
    echo "✅ Process IS running"
    echo "$PROCESS" | awk '{print "   PID:", $2, "| CPU:", $3"% | Runtime:", $10}'
    echo ""
fi

# Count completed patients
if [ -f "$LOG_FILE" ]; then
    COMPLETED=$(grep -c "Processing Patient:" "$LOG_FILE")
    CURRENT=$(grep "Processing Patient:" "$LOG_FILE" | tail -1 | awk '{print $3}')
    
    echo "Progress: Patient $CURRENT / $TOTAL_PATIENTS"
    echo "Completed: $COMPLETED patients"
    
    # Calculate percentage
    PERCENT=$((COMPLETED * 100 / TOTAL_PATIENTS))
    echo "Percentage: ${PERCENT}%"
    
    # Progress bar
    FILLED=$((PERCENT / 2))
    printf "["
    for ((i=0; i<50; i++)); do
        if [ $i -lt $FILLED ]; then
            printf "="
        else
            printf " "
        fi
    done
    printf "] ${PERCENT}%%\n"
    
    echo ""
    echo "Last 5 lines of log:"
    echo "---"
    tail -5 "$LOG_FILE"
    echo "---"
    
    # Estimate remaining time
    if [ "$COMPLETED" -gt 0 ] && [ ! -z "$PROCESS" ]; then
        RUNTIME=$(echo "$PROCESS" | awk '{print $10}')
        echo ""
        echo "Current runtime: $RUNTIME"
        REMAINING=$((TOTAL_PATIENTS - COMPLETED))
        echo "Remaining: $REMAINING patients"
    fi
else
    echo "⚠️  Log file not found: $LOG_FILE"
fi

echo ""
echo "========================================="
