import sys
import os
import os.path
import time
from urlparse import urlparse
from pystat.running import RunningStat


SEPARATOR = ","
COMPONENTS_LIMIT = 20


def usage():
    print "python collision.py <inputPath>"
    print ""
    print "\t<inputPath>"
    print "\t\tis the path of a file containing the URI list, or a path to a"
    print "\t\tdirectory with a lot of files containing URI lists."


def main(argv):
    global start_time

    start_time = time.time()

    inputPath = ""
    if len(argv) != 1:
        usage()
        sys.exit(2)

    inputPath = argv[0]

    if inputPath == "":
        print "Missing input path."
        usage()
        sys.exit(2)

    # Prepare RunningStat instances.
    nameLengthStat = RunningStat()
    compLengthStat = RunningStat()
    numOfCompsStat = RunningStat()
    compsStat = []
    for i in range(0, COMPONENTS_LIMIT):
        compsStat.append(0)

    print "Processing input files..."
    if os.path.isfile(inputPath):
        processFile(inputPath, nameLengthStat, compLengthStat,
                    numOfCompsStat, compsStat)
    else:
        for filePath in [os.path.join(inputPath, f) for f in
                         sorted(os.listdir(inputPath)) if
                         os.path.isfile(os.path.join(inputPath, f))]:
            processFile(filePath, nameLengthStat, compLengthStat,
                        numOfCompsStat, compsStat)

    saveResults(nameLengthStat, compLengthStat,
                numOfCompsStat, compsStat, SEPARATOR)
    print("--- %s seconds ---" % (time.time() - start_time))


def processFile(filePath, nameLengthStat, compLengthStat, numOfCompsStat,
                compsStat):
    global start_time

    print "\t'" + filePath + "'..."
    with open(filePath, "r") as inFile:
        for line in inFile:
            components = strip_scheme(
                line.strip("\r").strip("\n")).split("/")

            if len(components) <= 20:
                compsStat[len(components) - 1] = compsStat[len(components) - 1] \
                                                 + 1

            name = "".join(components)

            nameLengthStat.push(len(name))
            for comp in components:
                compLengthStat.push(len(comp))
            numOfCompsStat.push(len(components))

    print("\t--- %s seconds ---" % (time.time() - start_time))


def saveResults(nameLengthStat, compLengthStat, numOfCompsStat, compsStat,
                separator):
    print "Saving URI statistics..."
    with open("uri_stat.csv", "w") as outFile:
        outFile.write(separator + "Count" + separator + "Mean" + separator +
                      "Variance" + separator + "Stdev" + separator + "Min" +
                      separator + "Max\n")
        outFile.write("Name length," +
                      str(nameLengthStat.count()) + separator +
                      str(nameLengthStat.mean()) + separator +
                      str(nameLengthStat.variance()) + separator +
                      str(nameLengthStat.stdev()) + separator +
                      str(nameLengthStat.min()) + separator +
                      str(nameLengthStat.max()) + "\n")
        outFile.write("Components length," +
                      str(compLengthStat.count()) + separator +
                      str(compLengthStat.mean()) + separator +
                      str(compLengthStat.variance()) + separator +
                      str(compLengthStat.stdev()) + separator +
                      str(compLengthStat.min()) + separator +
                      str(compLengthStat.max()) + "\n")
        outFile.write("Number of components," +
                      str(numOfCompsStat.count()) + separator +
                      str(numOfCompsStat.mean()) + separator +
                      str(numOfCompsStat.variance()) + separator +
                      str(numOfCompsStat.stdev()) + separator +
                      str(numOfCompsStat.min()) + separator +
                      str(numOfCompsStat.max()) + "\n")

    print "Saving components statistics..."
    with open("comps_stat.csv", "w") as outFile:
        outFile.write("Number of Components" + separator + "Count\n")
        for i in range(0, COMPONENTS_LIMIT):
            outFile.write(str(i + 1) + separator + str(compsStat[i]) + "\n")


def strip_scheme(url):
    parsed = urlparse(url)
    scheme = "%s://" % parsed.scheme
    return parsed.geturl().replace(scheme, '', 1)


if __name__ == "__main__":
    main(sys.argv[1:])
