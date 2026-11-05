import re
from collections import defaultdict


def fetch_hdfs_logs(log_file="data/HDFS.log", max_lines=None):
    block_logs = defaultdict(list)
    count = 0

    with open(log_file, "r") as f:
        for line in f:
            if max_lines and count >= max_lines:
                break
            match = re.search(r"(blk_-?\d+)", line)
            if match:
                block_logs[match.group(1)].append({"line": line.strip()})
            count += 1

    return block_logs
