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


# LENGTH_LIMIT is from here: http://www.boutell.com/newfaq/misc/urllength.html.
LENGTH_LIMIT = 2000
COMPONENT_LIMIT = 80
HASH16SIZE = 2
HASH32SIZE = 4
HASH48SIZE = 6
HASH64SIZE = 8
HASH128SIZE = 16
HASH160SIZE = 20

start_time = 0
tlv = []
hash16 = []
hash32 = []
hash48 = []
hash64 = []
hash128 = []
hash160 = []


def usage():
    print "python tlv_vs_obfuscate.py -i <inputPath> -o <outputType> -p -v"
    print "                           -o <errorType> -l <lengthLimit>"
    print "                           -c <componentsLimit>"
    print ""
    print "\t-i, --ipath <inputPath>"
    print "\t\tis the path of a file containing the URI list, or a path to a"
    print "\t\tdirectory with a lot of files containing URI lists. If -p is"
    print "\t\tprovided, <inputPath> is the path of the output files to be"
    print "\t\tplotted."
    print "\t-o, --otype <outputType>"
    print "\t\tis optional and it is either 'text' or 'plot'. 'text' outputs the"
    print "\t\tgraphs in text format to be plotted later, while 'plot' (default)"
    print "\t\tplots the result."
    print "\t-p, --plot"
    print "\t\tis optional and if present, tlv_vs_obfuscate plots the text"
    print "\t\toutput provided in <inputPath> directory."
    print "\t-v, --verbose"
    print "\t\tis optional and only takes effect if the output type is 'text' or"
    print "\t\t-p is used. In this case, the output files will contain all"
    print "\t\tdistribution data. If this option is not provided (default),"
    print "\t\ttlv_cs_obfuscate will only saves the mean and standard deviation"
    print "\t\tof the results."
    print "\t-e, --etype <errorType>"
    print "\t\tis the error type, either standard deviation 'stdev', minumum and"
    print "\t\tmaximum value 'yerr', or 'both'."
    print "\t-l, --llimit <lengthLimit>"
    print "\t\t(optional) is the length limit of the URI. The default is 2000"
    print "\t\tbytes"
    print "\t-c, --climit <componentsLimit>"
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
    verbose = False
    errorType = "both"
    try:
        opts, args = getopt.getopt(argv,"hi:o:pve:l:c:", ["help", "ipath=",
                                                          "otype=", "plot",
                                                          "verbose", "etype=",
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
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("-e", "--etype"):
            errorType = arg
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

    if errorType not in ("stdev", "yerr", "both"):
        print "Error type must be either 'stdev', 'yerr', or 'both'."
        usage()
        sys.exit(2)

    if plot == False:
        print "Processing input files..."
        if os.path.isfile(inputPath):
            processFile(inputPath)
        else:
            for filePath in [os.path.join(inputPath, f) for f in
                             sorted(os.listdir(inputPath)) if
                             os.path.isfile(os.path.join(inputPath, f))]:
                processFile(filePath)

        outputResults(outputType, verbose, errorType)
    else:
        plotResultsFromFile(inputPath, verbose, errorType)


def processFile(filePath):
    global start_time

    print "\t'" + filePath + "'... ",

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
            tlv.append(tlvEncodingSize)

            # 16-bit encoding size.
            hash16EncodingSize = (HASH16SIZE * len(name)) + 4
            hash16.append(hash16EncodingSize)

            # 32-bit encoding size.
            hash32EncodingSize = (HASH32SIZE * len(name)) + 4
            hash32.append(hash32EncodingSize)

            # 48-bit encoding size.
            hash48EncodingSize = (HASH48SIZE * len(name)) + 4
            hash48.append(hash48EncodingSize)

            # 64-bit encoding size.
            hash64EncodingSize = (HASH64SIZE * len(name)) + 4
            hash64.append(hash64EncodingSize)

            # 128-bit encoding size.
            hash128EncodingSize = (HASH128SIZE * len(name)) + 4
            hash128.append(hash128EncodingSize)

            # 160-bit encoding size.
            hash160EncodingSize = (HASH160SIZE * len(name)) + 4
            hash160.append(hash160EncodingSize)

    back="\b" * (previousProgress + 2)
    print back,
    progress = "{:.4f}".format(100).zfill(8)
    print progress
    previousProgress = len(progress)
    print("\t--- %s seconds ---" % (time.time() - start_time))


def outputResults(outputType, verbose, errorType):
    global start_time

    if outputType == "plot":
        if verbose:
            plotPDF()
        mean, meanDiff, std, min_yerr, max_yerr = calculateMeanErr(errorType)
        plotMeanErr(mean, meanDiff, std, min_yerr, max_yerr, errorType)
    elif outputType == "text":
        saveResults(verbose, errorType)

    print("--- %s seconds ---" % (time.time() - start_time))


def plotResultsFromFile(inputPath, verbose, errorType):
    global start_time
    if verbose:
        print "Reading verbose results stored in text format"

        plt.hold(True)

        print "\t" + os.path.join(inputPath, "tlv.out") + "..."
        with open(os.path.join(inputPath, "tlv.out"), "r") as inFile:
            tmp = pickle.load(inFile)
        plot(tmp, "TLV format")
        del tmp
        print("--- %s seconds ---" % (time.time() - start_time))

        print "\t" + os.path.join(inputPath, "hash16.out") + "..."
        with open(os.path.join(inputPath, "hash16.out"), "r") as inFile:
            tmp = pickle.load(inFile)
        plot(tmp, "16-bit format")
        del tmp
        print("--- %s seconds ---" % (time.time() - start_time))

        print "\t" + os.path.join(inputPath, "hash32.out") + "..."
        with open(os.path.join(inputPath, "hash32.out"), "r") as inFile:
            tmp = pickle.load(inFile)
        plot(tmp, "32-bit format")
        del tmp
        print("--- %s seconds ---" % (time.time() - start_time))

        print "\t" + os.path.join(inputPath, "hash48.out") + "..."
        with open(os.path.join(inputPath, "hash48.out"), "r") as inFile:
            tmp = pickle.load(inFile)
        plot(tmp, "48-bit format")
        del tmp
        print("--- %s seconds ---" % (time.time() - start_time))

        print "\t" + os.path.join(inputPath, "hash64.out") + "..."
        with open(os.path.join(inputPath, "hash64.out"), "r") as inFile:
            tmp = pickle.load(inFile)
        plot(tmp, "64-bit format")
        del tmp
        print("--- %s seconds ---" % (time.time() - start_time))

        print "\t" + os.path.join(inputPath, "hash128.out") + "..."
        with open(os.path.join(inputPath, "hash128.out"), "r") as inFile:
            tmp = pickle.load(inFile)
        plot(tmp, "128-bit format")
        del tmp
        print("--- %s seconds ---" % (time.time() - start_time))

        print "\t" + os.path.join(inputPath, "hash160.out") + "..."
        with open(os.path.join(inputPath, "hash160.out"), "r") as inFile:
            tmp = pickle.load(inFile)
        plot(tmp, "160-bit format")
        del tmp
        print("--- %s seconds ---" % (time.time() - start_time))

        finalizePlotPDF()

    print "Reading non-verbose results stored in text format"
    print "\t" + os.path.join(inputPath, "mean.out") + "..."
    with open(os.path.join(inputPath, "mean.out"), "r") as inFile:
        mean = pickle.load(inFile)

    print "\t" + os.path.join(inputPath, "meanDiff.out") + "..."
    with open(os.path.join(inputPath, "meanDiff.out"), "r") as inFile:
        meanDiff = pickle.load(inFile)

    std = []
    if errorType in ("stdev", "both"):
        print "\t" + os.path.join(inputPath, "std.out") + "..."
        with open(os.path.join(inputPath, "std.out"), "r") as inFile:
            tmp = pickle.load(inFile)
            std.extend(tmp)

    min_yerr = []
    max_yerr = []
    if errorType in ("yerr", "both"):
        print "\t" + os.path.join(inputPath, "min_yerr.out") + "..."
        with open(os.path.join(inputPath, "min_yerr.out"), "r") as inFile:
            tmp = pickle.load(inFile)
            min_yerr.extend(tmp)

        print "\t" + os.path.join(inputPath, "max_yerr.out") + "..."
        with open(os.path.join(inputPath, "max_yerr.out"), "r") as inFile:
            tmp = pickle.load(inFile)
            max_yerr.extend(tmp)

    plotMeanErr(mean, meanDiff, std, min_yerr, max_yerr, errorType)
    print("--- %s seconds ---" % (time.time() - start_time))


def plotPDF():
    print "Plotting PDF..."
    plt.hold(True)

    plot(tlv, "TLV format")
    plot(hash16, "16-bit format")
    plot(hash32, "32-bit format")
    plot(hash48, "48-bit format")
    plot(hash64, "64-bit format")
    plot(hash128, "128-bit format")
    plot(hash160, "160-bit format")

    finalizePlotPDF()


def finalizePlotPDF():
    # Set grid, axis labels, and legend.
    plt.grid(True)
    plt.xlabel("Average name length (bytes)")
    plt.ylabel("Probability density function")
    plt.xlim([0, 500])
    plt.legend()

    # Save to file.
    pp = PdfPages("tlv_vs_obfuscate_PDF.pdf")
    plt.savefig(pp, format='pdf')
    pp.close()
    plt.cla()


def plotMeanErr(mean, meanDiff, std, min_yerr, max_yerr, errorType):
    width = 0.35
    xShift = -0.20

    # Plot name lengths.
    print "Plotting name lengths..."

    if errorType in ("stdev", "both"):
        fig, ax = plt.subplots()
        ind = np.arange(len(mean))
        rects = ax.bar(ind + width, mean, width, color='#0072bd', yerr=std)

        # Add some text for labels, title and axes ticks.
        ax.grid(True)
        ax.set_ylabel('Average name length (bytes)')
        ax.set_xticks(ind + (width * 1.5))
        ax.set_xticklabels(('TLV', '16-bit', '32-bit', '48-bit', '64-bit',
                            '128-bit', '160-bit'))
        sign = [-1 if x < 0 else 1 for x in mean]
        autoLabel(ax, rects, 0, 3, xShift, sign)

        # Save to file.
        pp = PdfPages('tlv_vs_obfuscate_NameLengths_stdev.pdf')
        plt.savefig(pp, format='pdf')
        pp.close()
        plt.cla()

    if errorType in ("yerr", "both"):
        fig, ax = plt.subplots()
        ind = np.arange(len(mean))
        rects = ax.bar(ind + width, mean, width, color='#0072bd',
                       yerr=[min_yerr, max_yerr])

        # Add some text for labels, title and axes ticks.
        ax.grid(True)
        ax.set_ylabel('Average name length (bytes)')
        ax.set_xticks(ind + (width * 1.5))
        ax.set_xticklabels(('TLV', '16-bit', '32-bit', '48-bit', '64-bit',
                            '128-bit', '160-bit'))
        sign = [-1 if x < 0 else 1 for x in mean]
        autoLabel(ax, rects, 0, 3, xShift, sign)

        # Save to file.
        pp = PdfPages('tlv_vs_obfuscate_NameLengths_yerr.pdf')
        plt.savefig(pp, format='pdf')
        pp.close()
        plt.cla()

    # Plot name length difference.
    print "Plotting name length differences..."

    fig, ax = plt.subplots()
    ind = np.arange(len(meanDiff))
    rects = ax.bar(ind + width, meanDiff, width, color='#d95319')

    # Add some text for labels, title and axes ticks.
    ax.grid(True)
    ax.set_ylabel('Average name length increment (%)')
    ax.set_xticks(ind + (width * 1.5))
    ax.set_xticklabels(('16-bit', '32-bit', '48-bit', '64-bit', '128-bit',
                        '160-bit'))
    limits = ax.axis()
    if limits[2] < 0:
        ax.set_ylim([limits[2] - 50, limits[3] + 50])
    else:
        ax.set_ylim([limits[2], limits[3] + 50])
    sign = [-1 if x < 0 else 1 for x in meanDiff]
    autoLabel(ax, rects, 25, 3, 0, sign)

    # Save to file.
    pp = PdfPages('tlv_vs_obfuscate_NameLengthsDiff.pdf')
    plt.savefig(pp, format='pdf')
    pp.close()
    plt.cla()


def plot(sizes, legendText):
    n = (len(sizes) / 10) # number of bins
    hist, edges = np.histogram(sizes, bins=n)
    edges = edges[:-1] + (edges[1] - edges[0])/2   # convert bin edges to centers
    f = UnivariateSpline(edges, hist, s=n)
    y = f(edges)
    s = sum(y)
    ny = [(float(x) / s) for x in y]
    plt.plot(edges, ny, label=legendText)
    lims = plt.ylim()
    plt.ylim(0, lims[1])


def autoLabel(ax, rects, negativeHeightDiff, positiveHeightDiff, xShift, sign):
    # Attach some text labels.
    i = 0
    for rect in rects:
        height = rect.get_height()
        if sign[i] == -1:
            heightDiff = negativeHeightDiff
        else:
            heightDiff = positiveHeightDiff
        ax.text(rect.get_x() + rect.get_width()/2. + xShift,
                sign[i] * (height + heightDiff),
                '%d' % int(sign[i] * height),
                ha='center', va='bottom')
        i = i + 1


def saveResults(verbose, errorType):
    global start_time

    if os.path.isdir("tlv_vs_obfuscate_output"):
        shutil.rmtree("tlv_vs_obfuscate_output", ignore_errors=True)
    os.makedirs("tlv_vs_obfuscate_output")

    if verbose:
        print "Saving verbose results in text format..."

        print "\t./tlv_vs_obfuscate_output/tlv.out..."
        with open("tlv_vs_obfuscate_output/tlv.out", "w+") as outFile:
            pickle.dump(tlv, outFile)
        print("\t--- %s seconds ---" % (time.time() - start_time))

        print "\t./tlv_vs_obfuscate_output/hash16.out..."
        with open("tlv_vs_obfuscate_output/hash16.out", "w+") as outFile:
            pickle.dump(hash16, outFile)
        print("\t--- %s seconds ---" % (time.time() - start_time))

        print "\t./tlv_vs_obfuscate_output/hash32.out..."
        with open("tlv_vs_obfuscate_output/hash32.out", "w+") as outFile:
            pickle.dump(hash32, outFile)
        print("\t--- %s seconds ---" % (time.time() - start_time))

        print "\t./tlv_vs_obfuscate_output/hash48.out..."
        with open("tlv_vs_obfuscate_output/hash48.out", "w+") as outFile:
            pickle.dump(hash48, outFile)
        print("\t--- %s seconds ---" % (time.time() - start_time))

        print "\t./tlv_vs_obfuscate_output/hash64.out..."
        with open("tlv_vs_obfuscate_output/hash64.out", "w+") as outFile:
            pickle.dump(hash64, outFile)
        print("\t--- %s seconds ---" % (time.time() - start_time))

        print "\t./tlv_vs_obfuscate_output/hash128.out..."
        with open("tlv_vs_obfuscate_output/hash128.out", "w+") as outFile:
            pickle.dump(hash128, outFile)
        print("\t--- %s seconds ---" % (time.time() - start_time))

        print "\t./tlv_vs_obfuscate_output/hash160.out..."
        with open("tlv_vs_obfuscate_output/hash160.out", "w+") as outFile:
            pickle.dump(hash160, outFile)
        print("\t--- %s seconds ---" % (time.time() - start_time))

    mean, meanDiff, std, min_yerr, max_yerr = calculateMeanErr(errorType)

    print "Saving non-verbose results in text format..."
    print "\t./tlv_vs_obfuscate_output/mean.out..."
    with open("tlv_vs_obfuscate_output/mean.out", "w+") as outFile:
        pickle.dump(mean, outFile)

    print "\t./tlv_vs_obfuscate_output/meanDiff.out..."
    with open("tlv_vs_obfuscate_output/meanDiff.out", "w+") as outFile:
        pickle.dump(meanDiff, outFile)

    if errorType in ("stdev", "both"):
        print "\t./tlv_vs_obfuscate_output/std.out..."
        with open("tlv_vs_obfuscate_output/std.out", "w+") as outFile:
            pickle.dump(std, outFile)

    if errorType in ("yerr", "both"):
        print "\t./tlv_vs_obfuscate_output/min_yerr.out..."
        with open("tlv_vs_obfuscate_output/min_yerr.out", "w+") as outFile:
            pickle.dump(min_yerr, outFile)

        print "\t./tlv_vs_obfuscate_output/max_yerr.out..."
        with open("tlv_vs_obfuscate_output/max_yerr.out", "w+") as outFile:
            pickle.dump(max_yerr, outFile)


def calculateMeanErr(errorType):
    global start_time
    mean = []
    meanDiff = []
    std = []
    min_yerr = []
    max_yerr = []

    # Calculate means.
    print "Calculating means..."
    print "\tTLV mean..."
    mean.append(stat.mean(tlv))
    print("\t--- %s seconds ---" % (time.time() - start_time))
    print "\tHash 16-bit mean..."
    mean.append(stat.mean(hash16))
    print("\t--- %s seconds ---" % (time.time() - start_time))
    print "\tHash 32-bit mean..."
    mean.append(stat.mean(hash32))
    print("\t--- %s seconds ---" % (time.time() - start_time))
    print "\tHash 48-bit mean..."
    mean.append(stat.mean(hash48))
    print("\t--- %s seconds ---" % (time.time() - start_time))
    print "\tHash 64-bit mean..."
    mean.append(stat.mean(hash64))
    print("\t--- %s seconds ---" % (time.time() - start_time))
    print "\tHash 128-bit mean..."
    mean.append(stat.mean(hash128))
    print("\t--- %s seconds ---" % (time.time() - start_time))
    print "\tHash 160-bit mean..."
    mean.append(stat.mean(hash160))
    print("\t--- %s seconds ---" % (time.time() - start_time))

    # Calculate means difference.
    print "Calculating mean differences..."
    meanDiff.append(((mean[1] - mean[0]) / mean[0]) * 100)
    meanDiff.append(((mean[2] - mean[0]) / mean[0]) * 100)
    meanDiff.append(((mean[3] - mean[0]) / mean[0]) * 100)
    meanDiff.append(((mean[4] - mean[0]) / mean[0]) * 100)
    meanDiff.append(((mean[5] - mean[0]) / mean[0]) * 100)
    meanDiff.append(((mean[6] - mean[0]) / mean[0]) * 100)

    if errorType in ("stdev", "both"):
        std.extend(calculateSTD())
    if errorType in ("yerr", "both"):
        tmp1, tmp2 = calculateYerr()
        min_yerr.extend(tmp1)
        max_yerr.extend(tmp2)

    return (mean, meanDiff, std, min_yerr, max_yerr)


def calculateSTD():
    global start_time
    std = []

    print "Calculating standard deviations..."
    print "\tTLV standard deviation..."
    std.append(stat.stdev(tlv))
    print("\t--- %s seconds ---" % (time.time() - start_time))
    print "\tHash 16-bit standard deviation..."
    std.append(stat.stdev(hash16))
    print("\t--- %s seconds ---" % (time.time() - start_time))
    print "\tHash 32-bit standard deviation..."
    std.append(stat.stdev(hash32))
    print("\t--- %s seconds ---" % (time.time() - start_time))
    print "\tHash 48-bit standard deviation..."
    std.append(stat.stdev(hash48))
    print("\t--- %s seconds ---" % (time.time() - start_time))
    print "\tHash 64-bit standard deviation..."
    std.append(stat.stdev(hash64))
    print("\t--- %s seconds ---" % (time.time() - start_time))
    print "\tHash 128-bit standard deviation..."
    std.append(stat.stdev(hash128))
    print("\t--- %s seconds ---" % (time.time() - start_time))
    print "\tHash 160-bit standard deviation..."
    std.append(stat.stdev(hash160))
    print("\t--- %s seconds ---" % (time.time() - start_time))

    return std


def calculateYerr():
    min_yerr = []
    max_yerr = []

    print "Calculating y-axis error..."
    min_yerr.append(min(tlv))
    min_yerr.append(min(hash16))
    min_yerr.append(min(hash32))
    min_yerr.append(min(hash48))
    min_yerr.append(min(hash64))
    min_yerr.append(min(hash128))
    min_yerr.append(min(hash160))
    max_yerr.append(max(tlv))
    max_yerr.append(max(hash16))
    max_yerr.append(max(hash32))
    max_yerr.append(max(hash48))
    max_yerr.append(max(hash64))
    max_yerr.append(max(hash128))
    max_yerr.append(max(hash160))

    return (min_yerr, max_yerr)


def strip_scheme(url):
    parsed = urlparse(url)
    scheme = "%s://" % parsed.scheme
    return parsed.geturl().replace(scheme, '', 1)


if __name__ == "__main__":
    main(sys.argv[1:])
