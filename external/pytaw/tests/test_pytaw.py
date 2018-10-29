import pytest
import logging
import sys
import collections
from datetime import datetime, timedelta

from googleapiclient.errors import HttpError

from pytaw import YouTube
from pytaw.youtube import Resource, Video, AttributeDef


logging.basicConfig(stream=sys.stdout)      # show log output when run with pytest -s
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@pytest.fixture
def youtube():
    """A YouTube instance initialised with a developer key loaded from config.ini"""
    return YouTube()


@pytest.fixture
def video(youtube):
    """A Video instance for the classic video 'Me at the zoo'"""
    return youtube.video('jNQXAC9IVRw')


@pytest.fixture
def channel(youtube):
    """A Channel instance for the 'YouTube Help' channel"""
    return youtube.channel('UCMDQxm7cUx3yXkfeHa5zJIQ')


@pytest.fixture
def search(youtube):
    """A ListResponse instance corresponding to a search for the query 'python'"""
    return youtube.search()


@pytest.fixture
def video_search(youtube):
    """A ListResponse instance corresponding to a video search for the query 'python'"""
    return youtube.search(q='python', type='video')


@pytest.fixture
def video_search_array(youtube):
    """An array of video searches with a wide range of results (zero to millions)."""
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    return [
        #
        # no results
        youtube.search(q='minecraft', type='video', publishedBefore=datetime(2000, 1, 1)),
        #
        # less than 100 results
        youtube.search(q='minecraft', type='video', publishedBefore=datetime(2005, 7, 1)),
        #
        # over 100 results
        youtube.search(q='minecraft', type='video', publishedBefore=datetime(2006, 1, 1)),
        #
        # variable number of results (hundreds or thousands...?)
        youtube.search(q='minecraft', type='video', publishedAfter=one_minute_ago),
        youtube.search(q='minecraft', type='video', publishedAfter=five_minutes_ago),
        #
        # over a million results
        youtube.search(q='minecraft', type='video'),
        youtube.search(q='minecraft'),
    ]


class TestResource:

    def test_equality(self, search):
        a = search[0]
        b = search[0]
        c = search[1]
        assert a == b
        assert a != c

    def test_unknown_attribute(self, video):
        with pytest.raises(AttributeError):
            _ = video.attribute_name_which_definitely_will_never_exist

    def test_unknown_part_in_attributedef(self, video):
        video.ATTRIBUTE_DEFS['x'] = AttributeDef('nonexistant_part', 'x')
        with pytest.raises(HttpError):
            _ = video.x

    def test_unknown_attribute_name_in_attributedef(self, video):
        video.ATTRIBUTE_DEFS['x'] = AttributeDef('snippet', 'nonexistant_attribute')
        assert video.x is None


class TestVideo:

    def test_bad_video_id(self, youtube):
        video = youtube.video('not_a_valid_youtube_video_id')
        assert video is None

    def test_title(self, video):
        assert video.title == "Me at the zoo"

    def test_published_at(self, video):
        assert video.published_at.isoformat() == '2005-04-24T03:31:52+00:00'

    def test_n_views(self, video):
        assert video.n_views > int(40e6)

    def test_tags(self, video):
        assert video.tags == ['jawed', 'karim', 'elephant', 'zoo', 'youtube', 'first', 'video']

    def test_duration(self, video):
        assert video.duration.total_seconds() == 19


class TestChannel:

    def test_title(self, channel):
        assert channel.title == "YouTube Help"


class TestSearch:

    def test_video_search_returns_a_video(self, video_search):
        assert isinstance(video_search[0], Video)

    def test_video_search_has_many_results(self, video_search):
        # make video_search unlazy (populate pageInfo attributes)
        _ = video_search[0]
        assert video_search.total_results > 10000

    def test_search_iteration(self, search):
        """Simply iterate over a search, creating all resources, to check for exceptions."""
        for resource in search:
            log.debug(resource)


class TestListResponse:

    def test_if_iterable(self, search):
        assert isinstance(search, collections.Iterator)

    def test_integer_indexing(self, search):
        assert isinstance(search[0], Resource)

    def test_slice_indexing(self, search):
        assert isinstance(search[1:3], list)

    def test_full_listing_iteration(self, video_search_array):
        """Iterate over all search results to check no exceptions are raised when paging etc.

        Even if millions of results are found, the API will never return more than 500 (by
        design), so we're okay to just bang right through the search results generator for the
        whole array of video searches.

        """
        for i, search in enumerate(video_search_array):
            c = 0
            for _ in search:
                c += 1

            log.debug(f"checked first {c} results (search #{i})")