set -eux

OUTPUT_FILE=${OUTPUT_FILE:-processed_traces.txt}
PROC_MAPS_FILE=proc_maps.txt
ASPROF_CMD=${ASPROF_CMD:-agentpath:./build/lib/libasyncProfiler.so=start,timeout=10,collapsed,file=/dev/null,event=cpu,interval=10ms}

rm -f traces*.txt $PROC_MAPS_FILE $OUTPUT_FILE
rm -rf build

CXXFLAGS_EXTRA="-O0 -ggdb3 -finstrument-functions -finstrument-functions-exclude-file-list=src/tracing.cpp,/usr/lib,/usr/include,stl_tree,strl_map,stl_vector"
make -j CXXFLAGS_EXTRA="$CXXFLAGS_EXTRA"
javac MyMain.java

PROC_MAPS_COPY_PATH=$PROC_MAPS_FILE java $ASPROF_CMD MyMain > /dev/null 2> ${OUTPUT_FILE}.err &
sleep 20

JPID=$(jps | grep MyMain | awk '{print $1}')
if [ -z "$JPID" ]; then exit 1; fi

trap "kill -9 $JPID || true" EXIT
kill -SIGTERM $JPID

python3 -W ignore process-instrumentation/process.py $PROC_MAPS_FILE "traces*.txt" true > $OUTPUT_FILE
