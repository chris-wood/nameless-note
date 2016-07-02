import math
import time
import obfuscate

from decimal import Decimal
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


hashUsed = ["CRC16", "CRC32", "MMH3", "SIPHASH", "MMH3_128", "SHA1"]
obfuscators = {
    "CRC16"    : obfuscate.ObfuscatorCRC16(),
    "CRC32"    : obfuscate.ObfuscatorCRC32(),
    "MMH3"     : obfuscate.ObfuscatorMMH3(),
    "SIPHASH"  : obfuscate.ObfuscatorSipHash(),
    "MMH3_128" : obfuscate.ObfuscatorMMH3_128(),
    "SHA1"     : obfuscate.ObfuscatorSHA1()
}
subplot = {
    "CRC16"    : [0, 0],
    "CRC32"    : [0, 1],
    "MMH3"     : [0, 2],
    "SIPHASH"  : [1, 0],
    "MMH3_128" : [1, 1],
    "SHA1"     : [1, 2]
}
colors = {
    "CRC16"    : "b",
    "CRC32"    : "g",
    "MMH3"     : "r",
    "SIPHASH"  : "c",
    "MMH3_128" : "m",
    "SHA1"     : "y"
}
labels = {
    "CRC16"    : "CRC 16-bit",
    "CRC32"    : "CRC 32-bit",
    "MMH3"     : "MurmurHash 32-bit",
    "SIPHASH"  : "SipHash 64-bit",
    "MMH3_128" : "MurmurHash 128-bit",
    "SHA1"     : "SHA1 160-bit"
}
MAX = {
    "CRC16"    : 2000,
    "CRC32"    : 400000,
    "MMH3"     : 400000,
    "SIPHASH"  : 100000000,
    "MMH3_128" : 100000000,
    "SHA1"     : 100000000
}


def main():
    start_time = time.time()

    print "Calculating probabilities..."
    for key in hashUsed:
        print "\t" + key + "... ",

        prob = []
        max_elements = math.pow(2, obfuscators[key].size())
        for n in range(1, MAX[key] + 1):
            prob.append(calculateProb(max_elements, n))
        
        print "plotting..."
        plot(prob, colors[key])
        print("\t--- %s seconds ---" % (time.time() - start_time))

        print "\tSaving the results..."
        finalizePlot(labels[key])
        saveGraph("birthday_" + key + ".pdf")
        print("\t--- %s seconds ---" % (time.time() - start_time))


# This is based on Taylor series:
# https://en.wikipedia.org/wiki/Birthday_problem#Approximations
def calculateProb(max_elements, n):
    noCollisionProb = math.exp((-1 * float(n) * (n - 1)) / (2 * max_elements))
    return 1 - noCollisionProb


def plot(prob, color):
    names = range(1, len(prob) + 1)
    plt.plot(names, prob, color)


def finalizePlot(text):
    # Set grid, axis labels, and legend.
    plt.grid(True)
    plt.xlabel("Number of names")
    plt.ylabel("Collision probability in " + text)


def saveGraph(fileName):
    pp = PdfPages(fileName)
    plt.savefig(pp, format='pdf')
    pp.close()
    plt.cla()


if __name__ == "__main__":
    main()
