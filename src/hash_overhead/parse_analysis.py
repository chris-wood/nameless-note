with open("cisco_uris.out", "r") as fh:
    lines = []
    for line in fh:
        line = line.strip().split(",")
        lines.append(float(line[1]))
    import statistics
    print "%f,%f,%f" % (statistics.mean(lines), min(lines), max(lines))