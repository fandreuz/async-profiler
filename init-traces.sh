set -eux

PROC_MAPS_FILE=proc_maps.txt
OUTPUT_FILE=processed_traces.txt

rm -f traces*.txt $PROC_MAPS_FILE $OUTPUT_FILE

make -j7 CXXFLAGS_EXTRA="-O0 -ggdb3 -finstrument-functions -finstrument-functions-exclude-file-list=src/tracing.cpp,/usr/lib,/usr/include,stl_tree,strl_map,stl_vector -Wl,-Map=asprof.map"
javac MyMain.java

ASPROF_CMD=-agentpath:./build/lib/libasyncProfiler.so=start,timeout=10,collapsed,file=/dev/null,event=cpu,interval=100ms
PROC_MAPS_COPY_PATH=$PROC_MAPS_FILE java $ASPROF_CMD MyMain > /dev/null &
sleep 20

JPID=$(jps | grep MyMain | awk '{print $1}')
if [ -z "$JPID" ]; then exit 1; fi

trap "kill -9 $JPID || true" EXIT

kill -SIGTERM $JPID
python3 process-instrumentation/process.py $PROC_MAPS_FILE "traces*.txt" > $OUTPUT_FILE
