"""Bisection algorithms.

These algorithms are taken from Python's standard library, and modified so they take a 'key' parameter (similar to how
`sorted` works).
"""


def bisect_right(a, x, lo=0, hi=None, key=None):
    """Return the index where to insert item x in list a, assuming a is sorted.

    The return value i is such that all e in a[:i] have e <= x, and all e in
    a[i:] have e > x.  So if x already appears in the list, a.insert(x) will
    insert just after the rightmost x already there.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """
    if key is None:
        key = lambda x: x

    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo+hi)//2
        if key(x) < key(a[mid]): hi = mid
        else: lo = mid+1
    return lo


def bisect_left(a, x, lo=0, hi=None, key=None):
    """Return the index where to insert item x in list a, assuming a is sorted.

    The return value i is such that all e in a[:i] have e < x, and all e in
    a[i:] have e >= x.  So if x already appears in the list, a.insert(x) will
    insert just before the leftmost x already there.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """
    if key is None:
        key = lambda x: x

    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo+hi)//2
        if key(a[mid]) < key(x): lo = mid+1
        else: hi = mid
    return lo


# Create aliases
bisect = bisect_right


def group_by(data, key):
    """
    Groups the given data into a dictionary matching the structure { key : [values] }
    :param data: Iterable data to be grouped
    :param key: Key used to group the data
    :return: A dictionary containing the grouped data
    """
    result = {}
    for entry in data:
        entry_key = key(entry)
        if entry_key not in result:
            result[entry_key] = [entry]
        else:
            result[entry_key].append(entry)

    return result

