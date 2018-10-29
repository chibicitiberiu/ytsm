import re
import urllib.parse
import typing
from datetime import datetime, timezone

import dateutil.parser
import itertools

def string_to_datetime(string):
    if string is None:
        return None
    else:
        return dateutil.parser.parse(string)


def datetime_to_string(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat()


def youtube_url_to_id(url):
    """Extract video id from a youtube url.

    If parsing fails, try regex.  If that fails, return None.

    The regex is from somewhere in this thread, I think:
        https://stackoverflow.com/questions/3452546/how-do-i-get-the-youtube-video-id-from-a-url

    """
    url = urllib.parse.unquote(url)
    url_data = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(url_data.query)
    try:
        # parse the url for a video query
        return query["v"][0]
    except KeyError:
        # use regex to try and extract id
        match = re.search(
            r"((?<=(v|V)/)|(?<=be/)|(?<=(\?|\&)v=)|(?<=embed/))([\w-]+)",
            url,
        )
        if match:
            return match.group()
        else:
            return None


def youtube_duration_to_seconds(value):
    """Convert youtube (ISO 8601) duration to seconds.

    https://en.wikipedia.org/wiki/ISO_8601#Durations
    https://regex101.com/r/ALmmSS/1

    """
    iso8601 = r"P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)W)?(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.match(iso8601, value)
    if match is None:
        return None

    group_names = ['years', 'months', 'weeks', 'days', 'hours', 'minutes', 'seconds']
    d = dict()
    for name, group in zip(group_names, match.groups(default=0)):
        d[name] = int(group)

    return int(
        d['years']*365*24*60*60 +
        d['months']*30*24*60*60 +
        d['weeks']*7*24*60*60 +
        d['days']*24*60*60 +
        d['hours']*60*60 +
        d['minutes']*60 +
        d['seconds']
    )


def iterate_chunks(iterable: typing.Iterable, chunk_size: int):
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