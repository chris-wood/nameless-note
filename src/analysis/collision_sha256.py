import getopt
import crc16
import binascii
import mmh3
import siphash
import hashlib
import sys
import time
import os
import os.path
import shutil
import pickle
import obfuscate
from urlparse import urlparse
from pydht.local.disk import LocalDiskDHT
from pydht.local.db import LocalDbDHT
from pydht.local.memory import LocalMemoryDHT


COMPONENT_LIMIT = 20
NUM_OF_HASHTABLES = 100
DHT_PATH = "dht_tmp/"

counters = []
sizeUsed = ["16", "32", "48", "64", "128", "160"]
dhts = {
    "16"  : [],
    "32"  : [],
    "48"  : [],
    "64"  : [],
    "128" : [],
    "160" : []
}
obfuscator = obfuscate.ObfuscatorSHA256()


def usage():
    print "python collision_sha256.py -i <inputPath> -c <componentsLimit>"
    print "                           -d <dhtType> -s <hashSize> -t <dataType>"
    print ""
    print "\t-i, --ipath <inputPath>"
    print "\t\tis the path of a directory containing several files each"
    print "\t\tcontaining name prefixes of a specific length (in terms of number"
    print "\t\tof components)."
    print "\t-c, --climit <componentsLimit>"
    print "\t\tis the maximum number of components in a URI."
    print "\t-d, --dhttype <dhtType>"
    print "\t\tidentifies where the DHT is stored, either 'disk', 'db' or"
    print "\t\t'memory'. Default is 'memory'."
    print "\t-s, --hsize <hashSize>"
    print "\t\tis the size of the hash (obfuscation) function to use. Options:"
    print "\t\t'16', '32', '48', '64', '128', '160', or a comma separate list of"
    print "\t\tany of the previous values."
    print "\t-t, --dtype <dataType>"
    print "\t\tis the data type, either 'raw' or 'obfuscated'. The second"
    print "\t\tassumes that the data is already obfuscated into network names."


def main(argv):
    global COMPONENT_LIMIT
    global start_time
    global counters

    start_time = time.time()

    inputPath = ""
    dhtType = "memory"
    hashSize = ""
    dataType = ""
    try:
        opts, args = getopt.getopt(argv,"hi:c:d:s:t:", ["help", "ipath=",
                                                        "climit=", "dhttype",
                                                        "hsize=", "dtype="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-i", "--ipath"):
            inputPath = arg
        elif opt in ("-c", "--climit"):
            COMPONENT_LIMIT = int(arg)
        elif opt in ("-d", "--dhttype"):
            dhtType = arg
        elif opt in ("-s", "--hsize"):
            hashSize = arg
        elif opt in ("-t", "--dtype"):
            dataType = arg
        else:
            usage()
            sys.exit(2)

    if inputPath == "":
        print "Missing input path."
        usage()
        sys.exit(2)

    if os.path.isfile(inputPath):
        print "Input path must be a directory."
        usage()
        sys.exit(2)

    if hashSize == "":
        print "Missing hash size."
        usage()
        sys.exit(2)

    if dataType == "":
        print "Missing data type."
        usage()
        sys.exit(2)

    if dhtType not in ("disk", "db", "memory"):
        print "DHT type must be either 'disk', 'db', or 'memory'."
        sys.exit(2)

    if dataType not in ("raw", "obfuscated"):
        print "Data type must be either 'raw' or 'obfuscated'."
        sys.exit(2)

    sizes = []
    for size in hashSize.split(","):
        if not size in sizeUsed:
            print "Unknown hash size: '" + size + "'."
            sys.exit(2)
        else:
            sizes.append(size)

    if dataType == "obfuscated" and len(sizes) > 1:
        print "When 'obfuscated' data type is used, only one size can be " \
            "processed at a time."
        sys.exit(2)

    # Prepare DHTs.
    if dhtType == "disk":
        if os.path.isdir(DHT_PATH):
            shutil.rmtree(DHT_PATH, ignore_errors=True)

    for i in range(0, COMPONENT_LIMIT):
        for size in sizes:
            if dhtType == "disk":
                dhts[size].append(LocalDiskDHT(int(size), NUM_OF_HASHTABLES,
                                               DHT_PATH + "/" + size + "/" +
                                               str(i + 1)))
            elif dhtType == "db":
                dhts[size].append(LocalDbDHT(int(size), NUM_OF_HASHTABLES,
                                             DHT_PATH + "/" + size + "/" +
                                             str(i + 1)))
            elif dhtType == "memory":
                dhts[size].append(LocalMemoryDHT(int(size), NUM_OF_HASHTABLES))

    # Initialize all counters to 0.
    counters = [0] * COMPONENT_LIMIT

    print "Processing input files..."
    for i in range(0, COMPONENT_LIMIT):
        processFile(os.path.join(inputPath, str(i + 1) + "-component"),
                    sizes, dataType, i)

    outputResults(sizes)
    print("--- %s seconds ---" % (time.time() - start_time))

    # Cleaning up.
    print "Cleaning up..."
    if dhtType in ("db"):
        for size in sizes:
            for i in range(0, COMPONENT_LIMIT):
                dhts[size][i].close()
    if dhtType in ("disk", "db"):
        shutil.rmtree(DHT_PATH, ignore_errors=True)
    print("--- %s seconds ---" % (time.time() - start_time))


def processFile(filePath, sizes, dataType, compIndex):
    global start_time
    global counters

    print "\t'" + filePath + "'...",

    fileSize = os.path.getsize(filePath)
    totalBytesRead = 0

    progress = "{:.4f}".format(0).zfill(8)
    print progress,
    previousProgress = len(progress)
    count = 0
    with open(filePath, "r") as inFile:
        for line in inFile:
            count = count + 1
            totalBytesRead = totalBytesRead + len(line)

            # Print the progress.
            if count % 100 == 0:
                back="\b" * (previousProgress + 2)
                print back,
                progress = "{:.4f}".format(round(
                    (float(totalBytesRead) / fileSize) * 100, 4)).zfill(8) + "%"
                print progress,
                previousProgress = len(progress)

            counters[compIndex] = counters[compIndex] + 1

            if dataType == "raw":
                # Calculate hashes and insert them into the corresponding
                # DHT.
                hashValue = obfuscator.obfuscate(line)
                for size in sizes:
                    dhts[size][compIndex].insert(
                        int(hashValue[:((int(size) / 8) * 2)], 16))
            else:
                dhts[sizes[0]][compIndex].insert(int(line, 16))

    back="\b" * (previousProgress + 2)
    print back,
    progress = "{:.4f}".format(100).zfill(8)
    print progress
    previousProgress = len(progress)
    print("\t--- %s seconds ---" % (time.time() - start_time))


def outputResults(sizes):
    collisions = processResults(sizes)
    saveResults(collisions, sizes)


def processResults(sizes):
    global start_time
    collisions = {}

    print "Processing results..."
    for i in range(0, COMPONENT_LIMIT):
        print "\t" + str(i + 1) + " component(s)..."
        if counters[i] == 0:
            continue

        for size in sizes:
            if size not in collisions:
                collisions[size] = []

            hashCount, valueCount, totalCount = dhts[size][i].countCollision()
            collisions[size].append(str(hashCount) + "," + str(valueCount) +
                                    "," + str(totalCount))

        print("\t--- %s seconds ---" % (time.time() - start_time))

    return collisions


def saveResults(collisions, sizes):
    if os.path.isdir("collision_sha256_output"):
        if len(sizes) == len(sizeUsed):
            shutil.rmtree("collision_sha256_output", ignore_errors=True)
    else:
        os.makedirs("collision_sha256_output")

    print "Saving results in text format..."
    for size in sizes:
        print "\t./collision_sha256_output/" + size + ".out..."
        with open("collision_sha256_output/" + size + ".out", "w+") as outFile:
            pickle.dump(collisions[size], outFile)


def strip_scheme(url):
    parsed = urlparse(url)
    scheme = "%s://" % parsed.scheme
    return parsed.geturl().replace(scheme, '', 1)


if __name__ == "__main__":
    main(sys.argv[1:])
