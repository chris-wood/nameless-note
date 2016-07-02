import sys
import getopt
import os
import os.path
import shutil
import pickle
import time
import numpy as np
import statistics as stat
from scipy.interpolate import UnivariateSpline
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from urlparse import urlparse
from pystat.running import RunningStat


# LENGTH_LIMIT is from here: http://www.boutell.com/newfaq/misc/urllength.html.
LENGTH_LIMIT = 2000
COMPONENT_LIMIT = 80
HASH256SIZE = 32
HASH384SIZE = 48
HASH512SIZE = 64

start_time = 0
tlv = []
hash256 = []
hash384 = []
hash512 = []


def usage():
    print "python tlv_vs_fingerprint.py -i <inputPath> -o <outputType> -p"
    print "                             -l <lengthLimit> -c <componentsLimit>"
    print ""
    print "\t-i <inputPath>"
    print "\t\tis the path of a file containing the URI list, or a path to a"
    print "\t\tdirectory with a lot of files containing URI lists. If -p is"
    print "\t\tprovided, <inputPath> is the path of the output files to be"
    print "\t\tplotted."
    print "\t-o <outputType>"
    print "\t\tis optional and it is either 'text' or 'plot'. 'text' outputs the"
    print "\t\tgraphs in text format to be plotted later, while 'plot' (default)"
    print "\t\tplots the result."
    print "\t-p"
    print "\t\tis optional and if present, tlv_vs_fingerprint plots the text"
    print "\t\toutput provided in <inputPath> directory."
    print "\t-l"
    print "\t\t(optional) is the length limit of the URI. The default is 2000"
    print "\t\tbytes"
    print "\t-c"
    print "\t\t(optional) is the maximum number of components in a URI. The"
    print "\t\tdefault is 80."


def main(argv):
    global LENGTH_LIMIT
    global COMPONENT_LIMIT
    global start_time
    start_time = time.time()

    inputPath = ""
    outputType = "plot"
    plot = False
    try:
        opts, args = getopt.getopt(argv,"hi:o:pl:c:", ["help", "ipath=",
                                                       "otype=", "plot",
                                                       "llimit=", "climit"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-i", "--ipath"):
            inputPath = arg
        elif opt in ("-o", "--otype"):
            outputType = arg
        elif opt in ("-p", "--plot"):
            plot = True
        elif opt in ("-l", "--llimit"):
            LENGTH_LIMIT = int(arg)
        elif opt in ("-c", "--climit"):
            COMPONENT_LIMIT = int(arg)
        else:
            usage()
            sys.exit(2)

    if inputPath == "":
        print "Missing input path."
        usage()
        sys.exit(2)

    if outputType not in ("text", "plot"):
        print "Output type must be either 'text' or 'plot'."
        usage()
        sys.exit(2)

    if outputType == "text" and plot == True:
        print "Output type 'plot' cannot be use with -p."
        usage()
        sys.exit(2)

    if plot == True and os.path.isfile(inputPath):
        print "If -p is used, <inputPath> must be a directory."
        usage()
        sys.exit(2)


    ratios256Stat = RunningStat()
    ratios384Stat = RunningStat()
    ratios512Stat = RunningStat()
    nameStat = RunningStat()
    print "Processing input files..."
    if plot == False:
        if os.path.isfile(inputPath):
            processFile(inputPath, ratios256Stat, ratios384Stat, ratios512Stat,
                        nameStat)
        else:
            for filePath in [os.path.join(inputPath, f) for f in
                             sorted(os.listdir(inputPath)) if
                             os.path.isfile(os.path.join(inputPath, f))]:
                processFile(filePath, ratios256Stat, ratios384Stat,
                            ratios512Stat, nameStat)

        outputResults(outputType, ratios256Stat, ratios384Stat, ratios512Stat,
                      nameStat)
        print("--- %s seconds ---" % (time.time() - start_time))
    else:
        plotResultsFromFile(inputPath)
        print("--- %s seconds ---" % (time.time() - start_time))


def processFile(filePath, ratios256Stat, ratios384Stat, ratios512Stat, nameStat):
    global start_time

    print "\t'" + filePath + "'..."
    with open(filePath, "r") as inFile:
        for line in inFile:
            # Skip all long URIs, this gets rid of outliers.
            if len(line) > LENGTH_LIMIT:
                continue

            name = strip_scheme(line.strip("\r").strip("\n")).split("/")

            # Skip all URIs with a lot of name components, this gets rid of
            # outliers.
            if len(name) > COMPONENT_LIMIT:
                continue

            # TLV encoding size.
            tlvEncodingSize = 0
            for component in name:
                # Each TLV component has 2 bytes for type and 2 bytes for length,
                # so 4 extra bytes in total
                tlvEncodingSize = len(component) + 4

            ratios256Stat.push(
                (float(HASH256SIZE) - tlvEncodingSize) / tlvEncodingSize)
            ratios384Stat.push(
                (float(HASH384SIZE) - tlvEncodingSize) / tlvEncodingSize)
            ratios512Stat.push(
                (float(HASH512SIZE) - tlvEncodingSize) / tlvEncodingSize)
            nameStat.push(tlvEncodingSize)

    print("\t--- %s seconds ---" % (time.time() - start_time))


def outputResults(outputType, ratios256Stat, ratios384Stat, ratios512Stat,
                  nameStat):
    meanOfRatios, ratioOfMeans = calculateFinalResults(ratios256Stat,
                                                       ratios384Stat,
                                                       ratios512Stat, nameStat)
    if outputType == "plot":
        plotResults(meanOfRatios, ratioOfMeans)
    elif outputType == "text":
        saveResults(meanOfRatios, ratioOfMeans)


def calculateFinalResults(ratios256Stat, ratios384Stat, ratios512Stat, nameStat):
    meanOfRatios = [ratios256Stat.mean() * 100, ratios384Stat.mean() * 100,
                    ratios512Stat.mean() * 100]
    ratioOfMeans = []
    ratioOfMeans.append(
        ((float(HASH256SIZE) - nameStat.mean()) / nameStat.mean()) * 100)
    ratioOfMeans.append(
        ((float(HASH384SIZE) - nameStat.mean()) / nameStat.mean()) * 100)
    ratioOfMeans.append(
        ((float(HASH512SIZE) - nameStat.mean()) / nameStat.mean()) * 100)

    return (meanOfRatios, ratioOfMeans)


def plotResults(meanOfRatios, ratioOfMeans):
    width = 0.2

    # Plot results.
    print "Plotting results..."
    fig, ax = plt.subplots()
    ind = np.arange(len(meanOfRatios))
    rects1 = ax.bar(ind, meanOfRatios, width, color='#0072bd')
    rects2 = ax.bar(ind + width, ratioOfMeans, width, color='#d95319')

    # Add some text for labels, title and axes ticks.
    ax.grid(True)
    ax.set_ylabel('Average fingerprint network overhead (%)')
    ax.set_xticks(ind + width)
    ax.set_xticklabels(('256-bit', '384-bit', '512-bit'))
    ax.set_xlim([-0.2, 2.6])
    ax.legend((rects1[0], rects2[0]),
              ('Average of overheads', 'Overhead compared to average name'),
              loc=2)

    autoLabel(ax, rects1)
    autoLabel(ax, rects2)

    # Save to file.
    pp = PdfPages('tlv_vs_fingerprint.pdf')
    plt.savefig(pp, format='pdf')
    pp.close()
    plt.cla()


def plotResultsFromFile(inputPath):
    global start_time

    print "Reading results stored in text format"
    meanOfRatios = []
    print "\t" + os.path.join(inputPath, "meanOfRations.out") + "..."
    with open(os.path.join(inputPath, "meanOfRatios.out"), "r") as inFile:
        meanOfRatios = pickle.load(inFile)

    ratioOfMeans = []
    print "\t" + os.path.join(inputPath, "ratioOfMeans.out") + "..."
    with open(os.path.join(inputPath, "ratioOfMeans.out"), "r") as inFile:
        ratioOfMeans = pickle.load(inFile)

    plotResults(meanOfRatios, ratioOfMeans)


def autoLabel(ax, rects):
    # Attach some text labels.
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., height + 3,
                '%d' % int(height),
                ha='center', va='bottom')


def saveResults(meanOfRatios, ratioOfMeans):
    global start_time

    if os.path.isdir("tlv_vs_fingerprint_output"):
        shutil.rmtree("tlv_vs_fingerprint_output", ignore_errors=True)
    os.makedirs("tlv_vs_fingerprint_output")

    print "Saving results in text format..."
    print "\t./tlv_vs_fingerprint_output/meanOfRatios.out..."
    with open("tlv_vs_fingerprint_output/meanOfRatios.out", "w+") as outFile:
        pickle.dump(meanOfRatios, outFile)

    print "\t./tlv_vs_fingerprint_output/ratioOfMeans.out..."
    with open("tlv_vs_fingerprint_output/ratioOfMeans.out", "w+") as outFile:
        pickle.dump(ratioOfMeans, outFile)


def strip_scheme(url):
    parsed = urlparse(url)
    scheme = "%s://" % parsed.scheme
    return parsed.geturl().replace(scheme, '', 1)


if __name__ == "__main__":
    main(sys.argv[1:])
