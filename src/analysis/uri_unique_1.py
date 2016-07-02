import getopt
import sys
import time
import os
import os.path
import shutil
import obfuscate
import ntpath
from urlparse import urlparse


components = {}


def usage():
    print "python uri_unique.py -i <inputPath> -o <outputPath>"
    print ""
    print "\t-i, --ipath <inputPath>"
    print "\t\tis the path of a file containing the URI list, or a path to a"
    print "\t\tdirectory with a lot of files containing URI lists. If -p is"
    print "\t\tprovided, <inputPath> is the path of the output files to be"
    print "\t\tplotted."
    print "\t-o, --opath <outputPath>"
    print "\t\tis the path where unique URIs will be stored."


def main(argv):
    global start_time

    start_time = time.time()

    inputPath = ""
    outputPath = ""
    componentsRange = "5-5"
    try:
        opts, args = getopt.getopt(argv,"hi:o:pc:d:s:", ["help", "ipath=",
                                                         "opath="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-i", "--ipath"):
            inputPath = arg
        elif opt in ("-o", "--opath"):
            outputPath = arg
        else:
            usage()
            sys.exit(2)

    if inputPath == "":
        print "Missing input path."
        usage()
        sys.exit(2)

    if outputPath == "":
        print "Missing output path."
        usage()
        sys.exit(2)

    if componentsRange == "":
        print "Missing components range."
        usage()
        sys.exit(2)

    if len(componentsRange.split("-")) != 2:
        print "Components range must be a range, e.g., '1-20'."
        sys.exit(2)

    minComponent = int(componentsRange.split("-")[0])
    maxComponent = int(componentsRange.split("-")[1])

    if minComponent < 1 or maxComponent < 1:
        print "Components range must be positive."
        sys.exit(2)

    if not os.path.isdir(outputPath):
        os.makedirs(outputPath)

    print "Processing input files..."
    if os.path.isfile(inputPath):
        processFile(inputPath, outputPath, minComponent, maxComponent)
    else:
        for filePath in [os.path.join(inputPath, f) for f in
                         sorted(os.listdir(inputPath)) if
                         os.path.isfile(os.path.join(inputPath, f))]:
            processFile(filePath, outputPath, minComponent, maxComponent)


def processFile(filePath, outputPath, minComponent, maxComponent):
    global start_time

    print "\t'" + filePath + "'... ",

    fileSize = os.path.getsize(filePath)
    totalBytesRead = 0

    progress = "{:.4f}".format(0).zfill(8)
    print progress,
    previousProgress = len(progress)
    count = 0
    with open(filePath, "r") as inFile:
        with open(os.path.join(outputPath, str(minComponent) + "-component"),
                  "w+") as outFile:
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

                # Do the actual work.
                strComponents = strip_scheme(
                    line.strip("\r").strip("\n")).split("/")

                if len(strComponents) < minComponent:
                    continue

                for i in range(minComponent, maxComponent + 1):
                    if len(strComponents) < i:
                        break

                    uri= "/" + "/".join(strComponents[:i])
                    if not uri in components:
                        components[uri] = 0
                        outFile.write(uri + "\n")

    back="\b" * (previousProgress + 2)
    print back,
    progress = "{:.4f}".format(100).zfill(8)
    print progress
    previousProgress = len(progress)
    print("\t--- %s seconds ---" % (time.time() - start_time))


def strip_scheme(url):
    parsed = urlparse(url)
    scheme = "%s://" % parsed.scheme
    return parsed.geturl().replace(scheme, '', 1)


if __name__ == "__main__":
    main(sys.argv[1:])
