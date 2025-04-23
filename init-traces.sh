set -eux

OUTPUT_FILE=${OUTPUT_FILE:-processed_traces.txt}
ASPROF_CMD=${ASPROF_CMD:-start,timeout=10,collapsed,file=/dev/null,event=cpu,interval=10ms}
WAIT_TIME_S=${WAIT_TIME_S:-20}
THREADS_COUNT=${THREADS_COUNT:-5}
SAMPLES_COUNT_FILE=${SAMPLES_COUNT_FILE:-samples_count.txt}

rm -rf build traces*.txt $OUTPUT_FILE $OUTPUT_FILE.err

CXXFLAGS_EXTRA="-finstrument-functions -finstrument-functions-exclude-file-list=src/tracing.cpp,src/tsc.h,/usr/lib,/usr/include -std=c++17"
make -j CXXFLAGS_EXTRA="$CXXFLAGS_EXTRA"
javac MyMain.java

timeout $(($WAIT_TIME_S + 5)) java -agentpath:./build/lib/libasyncProfiler.so=$ASPROF_CMD MyMain $THREADS_COUNT $WAIT_TIME_S > /dev/null 2> ${OUTPUT_FILE}.err

samples_count=$(grep "recordSample " traces*.txt | awk '{print $NF}' | awk '{s+=$1} END {print s}' )
if [ $samples_count -lt 100 ]; then
    echo "Low count for recordSample: $samples_count"
    exit 1
fi
echo $samples_count > $SAMPLES_COUNT_FILE

python3 process-instrumentation/process_trees.py "traces*.txt" false | \
    grep -v "Profiler::timerLoop " | \
    grep -v "Profiler::jvmtiTimerEntry " | \
    grep -v "WaitableMutex::waitUntil " \
    > $OUTPUT_FILE
