import itertools
from typing import Iterable


def first_true(*args, default=False, pred=None):
    """Returns the first true value in the iterable.

    If no true value is found, returns *default*

    If *pred* is not None, returns the first item
    for which pred(item) is true.

    """
    # first_true([a,b,c], x) --> a or b or c or x
    # first_true([a,b], x, f) --> a if f(a) else b if f(b) else x
    return next(filter(pred, args), default)


def as_chunks(iterable: Iterable, chunk_size: int):
    """
    Iterates an iterable in chunks of chunk_size elements.
    :param iterable: An iterable containing items to iterate.
    :param chunk_size: Chunk size
    :return: Returns a generator which will yield chunks of size chunk_size
    """

    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, chunk_size))
        if not chunk:
            return
        yield chunk
