import os
import sys
import statistics

times = {}
sizes = {}

with open(sys.argv[1], "r") as fh:
    for line in fh:
        try:
            num, offset, size, time = line.strip().split(",")
            offset = int(offset)
            if offset not in times:
                times[offset] = []
                sizes[offset] = []
            times[offset].append(float(time))
            sizes[offset].append(float(size))
        except:
            pass


for offset in times:
    v1 = statistics.mean(times[offset])
    v2 = statistics.mean(sizes[offset])
    normalized = map(lambda (t, s) : float(t) / float(s), filter(lambda (t, s) : s > 0, zip(times[offset], sizes[offset])))
    v3 = statistics.mean(normalized)

    print "%d,%f,%f,%f" % (offset, v1, v2, v3)




        