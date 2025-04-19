set -eux

OUTPUT_FILE=${OUTPUT_FILE:-processed_traces.txt}
PROC_MAPS_FILE=proc_maps.txt
ASPROF_CMD=${ASPROF_CMD:--agentpath:./build/lib/libasyncProfiler.so=start,timeout=10,collapsed,file=/dev/null,event=cpu,interval=10ms}
WAIT_TIME_S=${WAIT_TIME_S:-20}
THREADS_COUNT=${THREADS_COUNT:-5}

rm -rf build traces*.txt $PROC_MAPS_FILE $OUTPUT_FILE

CXXFLAGS_EXTRA="-fplugin=./instrument-attribute-gcc-plugin/instrument_attribute.so -finstrument-functions -O0 -ggdb3"
make -j CXXFLAGS_EXTRA="$CXXFLAGS_EXTRA"
javac MyMain.java

PROC_MAPS_COPY_PATH=$PROC_MAPS_FILE java $ASPROF_CMD MyMain $THREADS_COUNT $WAIT_TIME_S > /dev/null 2> ${OUTPUT_FILE}.err &
sleep 20

python3 process-instrumentation/process_trees.py $PROC_MAPS_FILE "traces*.txt" > $OUTPUT_FILE
