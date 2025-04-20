set -eux

OUTPUT_FILE=${OUTPUT_FILE:-processed_traces.txt}
ASPROF_CMD=${ASPROF_CMD:--agentpath:./build/lib/libasyncProfiler.so=start,timeout=10,collapsed,file=/dev/null,event=cpu,interval=10ms}
WAIT_TIME_S=${WAIT_TIME_S:-20}
THREADS_COUNT=${THREADS_COUNT:-5}

rm -rf build traces*.txt $OUTPUT_FILE

CXXFLAGS_EXTRA="-finstrument-functions -finstrument-functions-exclude-file-list=src/tracing.cpp,src/tsc.h,/usr/lib,/usr/include -O0 -ggdb3"
make -j CXXFLAGS_EXTRA="$CXXFLAGS_EXTRA"
javac MyMain.java

java $ASPROF_CMD MyMain $THREADS_COUNT $WAIT_TIME_S > /dev/null 2> ${OUTPUT_FILE}.err &
sleep $((5 + $WAIT_TIME_S))

python3 process-instrumentation/process_trees.py "traces*.txt" false | \
    grep -v "Profiler::timerLoop/workspaces/async-profiler/src/profiler.cpp " | \
    grep -v "Profiler::jvmtiTimerEntry/workspaces/async-profiler/src/profiler.h " | \
    grep -v "WaitableMutex::waitUntil/workspaces/async-profiler/src/mutex.cpp " \
    > $OUTPUT_FILE
