import sys
import getopt
import os
import os.path
import ntpath
import shutil
from urlparse import urlparse


def usage():
    print "python url_to_name.py -i <inputPath> -o <outputPath>"
    print ""
    print "\t-i <inputPath>"
    print "\t\tis the path of a file containing the URI list, or a path to a"
    print "\t\tdirectory with a lot of files containing URI lists."
    print "\t-o <outputPath>"
    print "\t\tis the path of the output directory."


def main(argv):
    inputPath = ""
    outputPath = ""
    try:
        opts, args = getopt.getopt(argv,"hi:o:p", ["help", "ipath=", "opath="])
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

    if inputPath == "":
        print "Missing output path."
        usage()
        sys.exit(2)

    if os.path.isfile(outputPath):
        print "Output path must be a directory."
        sys.exit(2)

    # Creating output path.
    if os.path.isdir(outputPath):
        shutil.rmtree(outputPath, ignore_errors=True)
    os.makedirs(outputPath)

    if os.path.isfile(inputPath):
        convertFile(inputPath, outputPath)
    else:
        for filePath in [os.path.join(inputPath, f) for f in
                         sorted(os.listdir(inputPath)) if
                         os.path.isfile(os.path.join(inputPath, f))]:
            convertFile(filePath, outputPath)


def convertFile(filePath, outputPath):
    print "Converting '" + filePath + "'..."
    with open(filePath, "r") as inFile:
        fileName = ntpath.basename(filePath)
        with open(os.path.join(outputPath, fileName), "w") as outFile:
            for line in inFile:
                # Strip and split line.
                components = strip_scheme(
                    line.strip("\r").strip("\n")).split("/")

                # Ignore username/password if any.
                tmp = components[0].split("@")
                if len(tmp) == 2:
                    components[0] = tmp[1]

                # Ignore port number if any.
                components[0] = components[0].split(":")[0]

                # Ignore www.
                components[0] = components[0].strip("www.")

                # Reconstruct the name. If the domain is an IP address, keep it
                # as it is. If not, reverse it.
                name = ""
                if validate_ip(components[0]):
                    name = "/".join(components)
                else:
                    domain = components[0].split(".")
                    name = "/".join(domain[::-1]) + "/" + "/".join(
                        components[1:])

                outFile.write(name + "\n")


def strip_scheme(url):
    parsed = urlparse(url)
    scheme = "%s://" % parsed.scheme
    return parsed.geturl().replace(scheme, '', 1)


def validate_ip(s):
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True


if __name__ == "__main__":
    main(sys.argv[1:])
