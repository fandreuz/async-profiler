set -eux

rm -f traces*.txt

make -j7 CXXFLAGS_EXTRA="-O0 -ggdb3 -finstrument-functions -finstrument-functions-exclude-file-list=src/tracing.cpp,/usr/lib,/usr/include,stl_tree,strl_map,stl_vector -Wl,-Map=asprof.map"
javac MyMain.java

java -agentpath:./build/lib/libasyncProfiler.so=start,timeout=10,collapsed,file=/dev/null,event=cpu,interval=100ms MyMain &
sleep 20

JPID=$(jps | grep MyMain | awk '{print $1}')
if [ -z "$JPID" ]; then exit 1; fi

BASE_ADDRESS=$(cat /proc/$JPID/maps | grep profiler | awk '{print $1}' | awk -F  '-' '{print $1}' | head -n 1)
echo $BASE_ADDRESS > base_address.txt
cat /proc/$JPID/maps > proc_maps.txt

kill -SIGTERM $JPID
sleep 2

python3 process-instrumentation/process.py $BASE_ADDRESS > processed_traces.txt
