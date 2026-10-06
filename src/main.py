import sys
from array import array

KEEP, DELETE, INSERT = 0, 1, 2


def myers_diff(old, new):
    """Return the shortest edit script as a list of KEEP / DELETE / INSERT codes.
    Works on any two sequences (lists of lines, or strings of characters)."""
    n, m = len(old), len(new)

    prefix = 0
    while prefix < n and prefix < m and old[prefix] == new[prefix]:
        prefix += 1
    suffix = 0
    while suffix < n - prefix and suffix < m - prefix and old[n - 1 - suffix] == new[m - 1 - suffix]:
        suffix += 1

    a = old[prefix:n - suffix]
    b = new[prefix:m - suffix]
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return [KEEP] * prefix + [DELETE] * n + [INSERT] * m + [KEEP] * suffix

    ids = {}
    a_ids = [ids.setdefault(item, len(ids)) for item in a]
    b_ids = [ids.setdefault(item, len(ids)) for item in b]


    max_d = n + m
    offset = max_d + 1
    furthest_x = array("i", bytes(4 * (2 * max_d + 3)))
    trace = []              
    final_d = 0

    for d in range(max_d + 1):
        trace.append(furthest_x[offset - d:offset + d + 1])
        reached_end = False
        for k in range(-d, d + 1, 2):
            go_down = k == -d or (k != d and furthest_x[offset + k - 1] < furthest_x[offset + k + 1])
            if go_down:
                x = furthest_x[offset + k + 1]          
            else:
                x = furthest_x[offset + k - 1] + 1     
            y = x - k

            while x < n and y < m and a_ids[x] == b_ids[y]:   
                x += 1
                y += 1

            furthest_x[offset + k] = x
            if x >= n and y >= m:
                final_d = d
                reached_end = True
                break
        if reached_end:
            break

    reversed_script = []
    x, y = n, m
    for d in range(final_d, 0, -1):
        saved = trace[d]
        k = x - y
        go_down = k == -d or (k != d and saved[k - 1 + d] < saved[k + 1 + d])
        prev_k = k + 1 if go_down else k - 1
        prev_x = saved[prev_k + d]
        prev_y = prev_x - prev_k
        x_after_edit = prev_x if go_down else prev_x + 1

        reversed_script.extend([KEEP] * (x - x_after_edit))    
        reversed_script.append(INSERT if go_down else DELETE)
        x, y = prev_x, prev_y

    reversed_script.extend([KEEP] * x)                          
    reversed_script.reverse()
    return [KEEP] * prefix + reversed_script + [KEEP] * suffix


def read_lines(path):
    with open(path, "rb") as f:
        lines = f.read().split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def to_ranges(positions):
    
    if not positions:
        return "."
    ranges = []
    start = last = positions[0]
    for p in positions[1:]:
        if p == last + 1:
            last = p
        else:
            ranges.append(f"{start}-{last + 1}")
            start = last = p
    ranges.append(f"{start}-{last + 1}")
    return ",".join(ranges)


def highlight_line(old_line, new_line):
    old_text = old_line.decode("utf-8", errors="surrogateescape")
    new_text = new_line.decode("utf-8", errors="surrogateescape")

    i = j = 0
    changed_in_old, changed_in_new = [], []
    for edit in myers_diff(old_text, new_text):
        if edit == KEEP:
            i += 1
            j += 1
        elif edit == DELETE:
            changed_in_old.append(i)
            i += 1
        else:
            changed_in_new.append(j)
            j += 1

    text = "? " + to_ranges(changed_in_old) + " | " + to_ranges(changed_in_new)
    return text.encode("utf-8") + b"\n"


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A_PATH B_PATH", file=sys.stderr)
        return 2
    command, a_path, b_path = sys.argv[1:]

    try:
        old_lines = read_lines(a_path)
        new_lines = read_lines(b_path)
    except OSError as error:
        print(f"error: cannot read file: {error}", file=sys.stderr)
        return 2

    script = myers_diff(old_lines, new_lines)

    output = []
    i = j = 0           
    pos = 0             
    while pos < len(script):
        if script[pos] == KEEP:
            output.append(b" " + old_lines[i] + b"\n")
            i += 1
            j += 1
            pos += 1
            continue

        deleted, inserted = [], []
        while pos < len(script) and script[pos] != KEEP:
            if script[pos] == DELETE:
                deleted.append(old_lines[i])
                i += 1
            else:
                inserted.append(new_lines[j])
                j += 1
            pos += 1

        for line in deleted:
            output.append(b"-" + line + b"\n")
        for number, line in enumerate(inserted):
            output.append(b"+" + line + b"\n")
            if command == "highlight" and number < len(deleted):
                output.append(highlight_line(deleted[number], line))

    sys.stdout.buffer.write(b"".join(output))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())