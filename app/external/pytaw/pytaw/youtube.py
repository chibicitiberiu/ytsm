import collections
import configparser
import itertools
import logging
import os
from urllib.parse import urlsplit, parse_qs
import typing
from abc import ABC, abstractmethod
from datetime import timedelta

import googleapiclient.discovery
from oauth2client.client import AccessTokenCredentials

from .utils import (
    datetime_to_string,
    string_to_datetime,
    youtube_duration_to_seconds,
    iterate_chunks,
)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class DataMissing(Exception):
    """Exception raised if data is not found in a Resource data store."""
    pass


class InvalidURL(Exception):
    """Exception raised if an URL is not valid."""
    pass


class YouTube(object):
    """The interface to the YouTube API.

    Connects to the API by passing a developer api key, and provides some high-level methods for
    querying it.

    """

    def __init__(self, key=None, access_token=None):
        """Initialise the YouTube class.

        :param key: developer api key (you need to get this from google)
        :param access_token: access token from some other oauth2 authentication flow

        """
        if key is not None and access_token is not None:
            raise ValueError("you should provide a developer key or an access token, but not both")

        build_kwargs = {
            'serviceName': 'youtube',
            'version': 'v3',
            'cache_discovery': False,  # suppress an annoying warning
        }

        if access_token is not None:
            # build credentials using given access token
            credentials = AccessTokenCredentials(access_token=access_token, user_agent='pytaw')
            build_kwargs['credentials'] = credentials

        else:
            # use a develop key, either passed directly or from a config file
            if key is not None:
                developer_key = key

            else:
                # neither an access token or a key has been given, so look for a developer key in
                #  the default config file
                config_file_path = os.path.join(os.path.expanduser('~'), ".pytaw.conf")
                if not os.path.exists(config_file_path):
                    config_file_path = "/etc/pytaw.conf"

                if os.path.exists(config_file_path):
                    config = configparser.ConfigParser()
                    config.read(config_file_path)
                    developer_key = config['youtube']['developer_key']
                else:
                    raise ValueError("didn't find a developer key or an access token.")

            build_kwargs['developerKey'] = developer_key

        # build_kwargs now contains credentials, or a developer key
        self.build = googleapiclient.discovery.build(**build_kwargs)

    def __repr__(self):
        return "<YouTube object>"

    def search(self, **kwargs):
        """Search YouTube, returning an instance of `ListResponse`.

        API parameters should be given as keyword arguments.

        :return: ListResponse object containing the requested resource instances

        """
        api_params = {
            'part': 'id,snippet',
            'maxResults': 50,
        }
        api_params.update(kwargs)

        # convert certain parameters from datetime to youtube-compatible string
        datetime_fields = (
            'publishedBefore',
            'publishedAfter',
        )
        for field in datetime_fields:
            try:
                api_params[field] = datetime_to_string(api_params[field])
            except KeyError:
                pass

        query = Query(self, 'search', api_params)
        return ListResponse(query)

    def subscriptions(self, **kwargs):
        """Fetch list of channels that the authenticated user is subscribed to.

        API parameters should be given as keyword arguments.

        :return: ListResponse object containing channel instances

        """
        api_params = {
            'part': 'id,snippet',
            'mine': True,
            'maxResults': 50,
        }
        api_params.update(kwargs)

        query = Query(self, 'subscriptions', api_params)
        return ListResponse(query)

    def video(self, id, **kwargs):
        """Fetch a Video instance.

        Additional API parameters should be given as keyword arguments.

        :param id: youtube video id e.g. 'jNQXAC9IVRw'
        :return: Video instance if video is found, else None

        """
        api_params = {
            'part': 'id',
            'id': id,
        }
        api_params.update(kwargs)

        query = Query(self, 'videos', api_params)
        return ListResponse(query).first()

    def videos(self, id_list: typing.Iterable[str], **kwargs):
        """Fetch multiple videos.

        :param id_list: List of video IDs to fetch
        :return: Iterable list of video objects.
        """
        response_list = []
        for id_list_chunk in iterate_chunks(id_list, 50):
            api_params = {
                'part': 'id',
                'id': ','.join(id_list_chunk),
            }
            api_params.update(kwargs)

            query = Query(self, 'videos', api_params)
            response_list.append(ListResponse(query))

        return itertools.chain(*response_list)

    def parse_url(self, url: str) -> dict:
        """
        Parses a YouTube URL, and attempts to identify what resource it refers to.
        :param url: URL to parse
        :return: Returns a dictionary, containing the url 'type', and the url resource ('video', 'playlist', 'channel',
        'channel_custom', 'username')
        """
        result = {'type': 'unknown'}

        url_spl = urlsplit(url)
        url_path = url_spl.path.split('/')
        url_query = parse_qs(url_spl.query)

        if url_spl.netloc.endswith('youtube.com'):

            # http://www.youtube.com/watch?v=-wtIMTCHWuI
            if url_path[1] == 'watch':
                result['type'] = 'video'
                result['video'] = url_query['v'][0]
                if 'list' in url_query:
                    result['playlist'] = url_query['list'][0]

            # http://www.youtube.com/v/-wtIMTCHWuI?version=3&autohide=1
            # https://www.youtube.com/embed/M7lc1UVf-VE
            elif url_path[1] == 'v':
                result['type'] = 'video'
                result['video'] = url_path[2]
                if 'list' in url_query:
                    result['playlist'] = url_query['list'][0]

            # https://www.youtube.com/playlist?list=PLJRbJuI_csVDXhgRJ1xv6z-Igeb7CKroe
            elif url_path[1] == 'playlist':
                result['type'] = 'playlist'
                result['playlist'] = url_query['list'][0]

            # https://www.youtube.com/channel/UC0QHWhjbe5fGJEPz3sVb6nw
            elif url_path[1] == 'channel':
                result['type'] = 'channel'
                result['channel'] = url_path[2]

            # https://www.youtube.com/c/LinusTechTips
            elif url_path[1] == 'c':
                result['type'] = 'channel_custom'
                result['channel_custom'] = url_path[1]

            # https://www.youtube.com/user/LinusTechTips
            elif url_path[1] == 'user':
                result['type'] = 'user'
                result['username'] = url_path[2]

            # http://www.youtube.com/oembed?url=http%3A//www.youtube.com/watch?v%3D-wtIMTCHWuI&format=json
            elif url_path[1] == 'oembed':
                return self.parse_url(url_query['url'][0])

            # http://www.youtube.com/attribution_link?a=JdfC0C9V6ZI&u=%2Fwatch%3Fv%3DEhxJLojIE_o%26feature%3Dshare
            elif url_path[1] == 'attribution_link':
                return self.parse_url('http://youtube.com/' + url_query['u'][0])

            # https://www.youtube.com/results?search_query=test
            elif url_path[1] == 'search' or url_path[1] == 'results':
                result['type'] = 'search'
                result['query'] = url_query['search_query'][0]

            # Custom channel URLs might have the format https://www.youtube.com/LinusTechTips, which are pretty much
            # impossible to handle properly
            else:
                raise InvalidURL('Unrecognized URL format: ' + url)

        # http://youtu.be/-wtIMTCHWuI
        elif url_spl.netloc == 'youtu.be':
            result['type'] = 'video'
            result['video'] = url_path[1]

        # https://youtube.googleapis.com/v/My2FRPA3Gf8
        elif url_spl.netloc == 'youtube.googleapis.com':
            if url_path[1] == 'v':
                result['type'] = 'video'
                result['video'] = url_path[2]
            else:
                raise InvalidURL('Unrecognized URL format: ' + url)

        else:
            raise InvalidURL('Unrecognized URL format: ' + url)

        return result

    def __find_channel_by_custom_url(self, custom_part):
        # See https://stackoverflow.com/a/37947865
        # Using the YT API, the only way to obtain a channel using a custom URL that we know of is to search for it.
        # Another option (which might be more reliable) could be scraping the page
        api_params = {
            'part': 'id',
            'type': 'channel',
            'q': custom_part,
        }

        return self.search(**api_params).first()

    def channel(self, channel_id=None, username=None, url=None, **kwargs):
        """Fetch a Channel instance.

        Additional API parameters should be given as keyword arguments.

        :param id: youtube channel id e.g. 'UCMDQxm7cUx3yXkfeHa5zJIQ'
        :return: Channel instance if channel is found, else None

        """
        api_params = {
            'part': 'id',
        }

        if channel_id is not None:
            api_params['id'] = channel_id
        elif username is not None:
            api_params['forUsername'] = username
        elif url is not None:
            parse = self.parse_url(url)
            if parse['type'] == 'channel':
                api_params['id'] = parse['channel']
            elif parse['type'] == 'user':
                api_params['forUsername'] = parse['username']
            elif parse['type'] == 'channel_custom':
                return self.__find_channel_by_custom_url(parse['channel_custom'])
            else:
                raise InvalidURL('Can\'t extract channel from given URL.')
        else:
            raise ValueError('Please specify exactly one of: channel_id, username, url')

        api_params.update(kwargs)

        query = Query(self, 'channels', api_params)
        return ListResponse(query).first()

    def playlist(self, id=None, url=None, **kwargs):
        """Fetch a Playlist instance.

        Additional API parameters should be given as keyword arguments.

        :param id: youtube channel id e.g. 'UCMDQxm7cUx3yXkfeHa5zJIQ'
        :return: Channel instance if channel is found, else None

        """
        api_params = {
            'part': 'id',
        }

        if id is not None:
            api_params['id'] = id
        elif url is not None:
            parse = self.parse_url(url)
            if 'playlist' in parse:
                api_params['id'] = parse['playlist']
        else:
            raise ValueError('Please specify exactly one of: id, url')

        api_params.update(kwargs)

        query = Query(self, 'playlists', api_params)
        return ListResponse(query).first()

    def playlist_items(self, id, **kwargs):
        """Fetch a Playlist instance.

        Additional API parameters should be given as keyword arguments.

        :param id: youtube channel id e.g. 'UCMDQxm7cUx3yXkfeHa5zJIQ'
        :return: Channel instance if channel is found, else None

        """
        api_params = {
            'part': 'id,snippet',
            'playlistId': id,
        }
        api_params.update(kwargs)

        query = Query(self, 'playlist_items', api_params)
        return ListResponse(query)


class Query(object):
    """Everything we need to execute a query and retrieve the raw response dictionary."""

    def __init__(self, youtube, endpoint, api_params=None):
        """Initialise the query.

        :param youtube: YouTube instance
        :param endpoint: string giving the api endpoint to query, e.g. 'videos', 'search'...
        :param api_params: dict of keyword parameters to send (directly) to the api

        """
        self.youtube = youtube
        self.endpoint = endpoint
        self.api_params = api_params or dict()

        if 'part' not in api_params:
            api_params['part'] = 'id'

        endpoint_func_mapping = {
            'search': self.youtube.build.search().list,
            'videos': self.youtube.build.videos().list,
            'channels': self.youtube.build.channels().list,
            'subscriptions': self.youtube.build.subscriptions().list,
            'playlists': self.youtube.build.playlists().list,
            'playlist_items': self.youtube.build.playlistItems().list,
        }

        try:
            self.query_func = endpoint_func_mapping[self.endpoint]
        except KeyError:
            raise ValueError(f"youtube api endpoint '{self.endpoint}' not recognised.")

    def __repr__(self):
        return "<Query '{}' api_params={}>".format(self.endpoint, self.api_params)

    def execute(self, api_params=None):
        """Execute the query.

        :param api_params: extra api parameters to send with the query.
        :return: api response dictionary

        """
        if api_params is not None:
            # update only for this query execution
            query_params = self.api_params.copy()
            query_params.update(api_params)
        else:
            query_params = self.api_params

        log.debug(f"executing query with {str(query_params)}")
        return self.query_func(**query_params).execute()


class ListResponse(collections.Iterator):
    """Executes a query and creates a data structure containing Resource instances.

    When iterated over, this object behaves like an iterator, paging through the results and
    creating Resource instances (Video, Channel, Playlist...) as they are required.

    When indexed with an integer n, returns the nth Resource.

    When sliced, returns a list of Resource instances.

    Due to limitations in the API, you'll never get more than ~500 from a search result -
    definitely for the 'search' endoint and probably others as well. Also, the value given in
    pageInfo.totalResults for how many results are returned is pretty worthless.  It may be an
    estimate of total numbers of results _before filtering_, and it'll never be more than a
    million.  See this issue for more details: https://issuetracker.google.com/issues/35171641

    """

    def __init__(self, query):
        self.youtube = query.youtube
        self.query = query

        self.kind = None
        self.total_results = None
        self.results_per_page = None

        self._reset()

    def _reset(self):
        self._listing = None  # internal storage for current page listing
        self._list_index = None  # index of item within current listing
        self._no_more_pages = False  # flagged when we reach the end of the available results
        self._page_count = 0  # no. of pages processed
        self._item_count = 0  # total no. of items yielded
        self._next_page_token = None  # api page token required for the next page of results

    def __repr__(self):
        return "<ListResponse endpoint='{}', n={}, per_page={}>".format(
            self.query.endpoint, self.total_results, self.results_per_page
        )

    def __iter__(self):
        """Allow this object to act as an iterator."""
        return self

    def __next__(self):
        """Get the next resource.

        This method allows the list reponse to be iterated over.  First we fetch a page of search
        results, load the response into memory and and return each resource in turn.  If we're at
        the end of a page we fetch a new one, replacing the old page in memory.

        """
        # fetch the next page of items if we haven't fetched the first page yet, or alternatively
        #  if we've run out of results on this page.  this check relies on results_per_page being
        #  set if _listing is not None (which of course it should be).
        if self._listing is None or self._list_index >= self.results_per_page:
            self._fetch_next()

        # get the next item.  if this fails now we must be out of results.
        # note: often you'll still get a next page token, even if the results end on this page,
        # meaning the _no_more_pages flag will not be set.
        # in this case, the items list on the _next_ page should be empty, but we don't check this.
        try:
            item = self._listing[self._list_index]
        except IndexError:
            log.debug(f"exhausted all results at item {self._item_count} "
                      f"(item {self._list_index + 1} on page {self._page_count})")
            self._no_more_pages = True  # unnecessary but true
            raise StopIteration()

        self._list_index += 1
        self._item_count += 1
        return create_resource_from_api_response(self.youtube, item)

    def __getitem__(self, index):
        """Get a specific resource or list of resources.

        This method handles indexing by integer or slice, e.g.:
            listresponse[n]     returns the nth Resource instance
            listresponse[:n]    returns the first n Resources as a list

        We do this by just repeatedly calling the __next__() method until we have the items we're
        looking for, which is a pretty dumb way of doing it but it'll do for now.

        Before finding an item or items, we call _reset() so that if this response has been used
        as an iterator we go back and start again.  After the requested item or items have been
        found we _reset() again so that the response can still be iterated over.

        """
        if isinstance(index, int):
            # if an integer is used we just return a single item.  we'll just __next__()
            # along until we're there.  this is a bit silly because we're creating a resource for
            #  each call and only returning the final one, but it'll do for now.
            self._reset()
            try:
                for _ in range(index):
                    self.__next__()
            except StopIteration:
                self._reset()
                raise IndexError("index out of range")

            # store item to be returned
            try:
                item = self.__next__()
            except StopIteration:
                self._reset()
                raise IndexError("index out of range")

            # reset so that this object can still be used as a generator
            self._reset()

            return item

        elif isinstance(index, slice):
            # if a slice is used we want to return a list (not a generator).  we'll use
            # __next__() to build up the list.
            start = 0 if index.start is None else index.start
            stop = index.stop
            step = index.step

            if step not in (1, None):
                raise NotImplementedError("can't use a slice step other than one")

            if start < 0 or (stop is not None and stop < 0):
                raise NotImplementedError("can't use negative numbers in slices")

            # ok if all that worked let's reset so that __next__() gives the first item in the
            # list response
            self._reset()

            if start > 0:
                # move to start position
                try:
                    for _ in range(start):
                        self.__next__()
                except StopIteration:
                    # if the slice start is greater than the total length you usually get an empty
                    # list
                    return []

            if stop is not None:
                # iterate over the range provided by the slice
                range_ = range(start, stop)
            else:
                # make the for loop iterate until StopIteration is raised
                range_ = itertools.count()

            items = []
            for _ in range_:
                try:
                    items.append(self.__next__())
                except StopIteration:
                    # if the slice end is greater than the total length you usually get a
                    # truncated list
                    break

            self._reset()
            return items

        else:
            raise KeyError(f"you can't index a ListResponse with '{index}'")

    def _fetch_next(self):
        """Fetch the next page of the API response and load into memory."""
        if self._no_more_pages:
            # we should only get here if results stop at a page boundary
            log.debug(f"exhausted all results at item {self._item_count} at page boundary "
                      f"(item {self._list_index + 1} on page {self._page_count})")
            raise StopIteration()

        # pass the next page token if this is not the first page we're fetching
        params = dict()
        if self._next_page_token:
            params['pageToken'] = self._next_page_token

        # execute query to get raw response dictionary
        raw = self.query.execute(api_params=params)

        # the following data shouldn't change, so store only if it's not been set yet
        # (i.e. this is the first fetch)
        if None in (self.kind, self.total_results, self.results_per_page):
            # don't use get() because if this data doesn't exist in the api response something
            # has gone wrong and we'd like an exception
            self.kind = raw['kind'].replace('youtube#', '')
            self.total_results = int(raw['pageInfo']['totalResults'])
            self.results_per_page = int(raw['pageInfo']['resultsPerPage'])

        # whereever we are in the list response we need the next page token.  if it's not there,
        # set a flag so that we know there's no more to be fetched (note _next_page_token is also
        #  None at initialisation so we can't check it that way).
        self._next_page_token = raw.get('nextPageToken', None)
        if self._next_page_token is None:
            self._no_more_pages = True

        # store items in raw format for processing by __next__()
        self._listing = raw['items']  # would like a KeyError if this fails (it shouldn't)
        self._list_index = 0
        self._page_count += 1

    def first(self):
        try:
            return self[0]
        except IndexError:
            return None


def create_resource_from_api_response(youtube, item):
    """Given a raw item from an API response, return the appropriate Resource instance."""

    # extract kind and id for the item.  if it's a search result then we have to do a bit of
    # wrangling. but we only extract the data - don't alter anything in the api response item!
    kind = item['kind'].replace('youtube#', '')
    if kind == 'searchResult':
        kind = item['id']['kind'].replace('youtube#', '')
        id_label = kind + 'Id'
        id = item['id'][id_label]
    else:
        id = item['id']

    if kind == 'video':
        return Video(youtube, id, item)
    elif kind == 'channel':
        return Channel(youtube, id, item)
    elif kind == 'playlist':
        return Playlist(youtube, id, item)
    elif kind == 'subscription':
        channel_id = item['snippet']['resourceId']['channelId']
        return Channel(youtube, id=channel_id)
    elif kind == 'playlistItem':
        return PlaylistItem(youtube, id, item)
    else:
        raise NotImplementedError(f"can't deal with resource kind '{kind}'")


class Thumbnail(object):
    def __init__(self, id: str, url: str, width: int, height: int):
        self.id = id
        self.url = url
        self.width = width
        self.height = height

    def __repr__(self):
        return f'<Thumbnail {self.id} {self.width}x{self.height} {self.url}>'


class Resource(ABC):
    """Base class for YouTube resource classes, e.g. Video, Channel etc."""

    @property
    @abstractmethod
    def ENDPOINT(self):
        pass

    @property
    @abstractmethod
    def ATTRIBUTE_DEFS(self):
        pass

    def __init__(self, youtube, id, data=None):
        """Initialise a Resource object.

        Need the YouTube instance, in case further queries are required, the resource id,
        and (optionally) some data in the form of an API response.

        """
        # if we need to query again for more data we'll need access to the youtube instance
        self.youtube = youtube

        # every resource has a unique id, it may be a different format for each resource type though
        self.id = id

        # data is the api response item for the resource.  it's a dictionary with 'kind',
        # 'etag' and 'id' keys, at least.  it may also have a 'snippet', 'contentDetails' etc.
        # containing more detailed info.  this dictionary could be accessed directly,
        # but we'll make the data accessible via class attributes where possible so that we can
        # do type conversion etc.
        #
        # if the data is from a search result we need to handle it differently.  search results
        # have some useful basic data and we'd like to use that if possible to prevent another
        # api request.  however, we'll need to know later if all we have is a search result (in
        # which case a lot of stuff will be missing) or a genuine resource api request.
        if data:
            if 'kind' in data and 'searchResult' in data['kind']:
                self._search_data = data
                self._data = {}
            else:
                self._search_data = {}
                self._data = data
        else:
            self._search_data = {}
            self._data = {}

        # this dictionary will log which attributes we've tried to fetch so that we don't get
        # stuck in an infinite loop if something goes badly wrong
        self._tried_to_fetch = {}

        # update attributes with whatever we've been given as data
        self._update_attributes()

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.__dict__ == other.__dict__

        # if they're different classes return NotImplemented instead of False so that we fallback
        #  to the default comparison method
        return NotImplemented

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __repr__(self):
        n_chars = 16
        if len(self.title) > n_chars:
            short_title = self.title[:(n_chars - 3)] + '...'
        else:
            short_title = self.title
        return f"<{type(self).__name__} {self.id} \"{short_title}\">"

    def __str__(self):
        return self.title

    def _update_attributes(self):
        """Take internally stored raw data and creates attributes with right types etc.

        Attributes defined in ATTRIBUTE_DEFS will be added as attributes, if they exist in
        internal data storage.

        """
        for attr_name, attr_def in self.ATTRIBUTE_DEFS.items():
            type_ = attr_def.type_
            part = attr_def.part
            if isinstance(attr_def.name, str):
                # may be a string or list - we want a list
                keys = [attr_def.name, ]
            else:
                keys = attr_def.name

            try:
                raw_value = self._get(part, *keys)
            except DataMissing:
                # if data is missing it basically means one of three things: we've not tried to
                # fetch it yet, we fetched the right part but it was null and not returned with
                # the query, or something is badly wrong (e.g. a bad AttributeDef).
                #
                # we check for the second case by looking in the data store to see if the part is
                #  there.  if it is, we set the attribute to show we've fetched and there was
                # nothing there.
                #
                # in the other two cases, just don't set this attribute right now.
                if self._data.get(part) is not None:
                    if type_ in ('str', 'string'):
                        raw_value = ''
                    elif type_ in ('int', 'integer', 'float'):
                        raw_value = 0
                    elif type_ == 'list':
                        raw_value = []
                    else:
                        raw_value = None
                else:
                    continue

            if type_ is None:
                value = raw_value
            elif type_ in ('str', 'string'):
                value = str(raw_value)
            elif type_ in ('int', 'integer'):
                value = int(raw_value)
            elif type_ == 'float':
                value = float(raw_value)
            elif type_ == 'list':
                value = list(raw_value)
            elif type_ == 'datetime':
                value = string_to_datetime(raw_value)
            elif type_ == 'timedelta':
                value = timedelta(seconds=youtube_duration_to_seconds(raw_value))
            elif type_ == 'thumbnails':
                value = []
                for key, val in raw_value.items():
                    url = val.get('url', None)
                    width = val.get('width', None)
                    height = val.get('width', None)
                    value.append(Thumbnail(key, url, width, height))
            else:
                raise TypeError(f"type '{type_}' not recognised.")

            setattr(self, attr_name, value)

    def _get(self, *keys):
        """Get a data attribute from the stored item response, if it exists.

        If it doesn't, raise DataMissing exception.  This could be because the necessary
        information was not included in the 'part' argument in the original query, or because
        youtube doesn't have the information stored (e.g. if country is not set by the user,
        the key is not present in the API response).

        :param *keys: one or more dictionary keys.  if there's more than one, we'll query
            them recursively, so _get('a', 'b', 'c') will return
            self._items['a']['b']['c']
        :return: the data attribute

        """

        def get_from_nested_dict(dict_, *keys):
            """Get item from a nested dictionary; raise KeyError if it's not there."""
            param = dict_
            for key in keys:
                param = param[key]
            return param

        try:
            param = get_from_nested_dict(self._data, *keys)
            return param
        except KeyError:
            pass

        try:
            param = get_from_nested_dict(self._search_data, *keys)
            return param
        except KeyError:
            pass

        raise DataMissing(f"attribute with keys {str(keys)} not present in self._data or "
                          f"self._search_data.  either it doesn't exist, or that part needs "
                          f"fetching.")

    def __getattr__(self, item):
        """If an attribute hasn't been set, this function tries to fetch and add it.

        Note: the __getattr__ method is only ever called when an attribute can't be found,
        therefore there is no need to check if the attribute already exists within this function.

        If the attribute isn't present in ATTRIBUTE_DEFS, raise AttributeError.

        :param item: attribute name
        :return: attribute value

        """
        if item not in self.ATTRIBUTE_DEFS:
            raise AttributeError(f"attribute '{item}' not recognised for resource type "
                                 f"'{type(self).__name__}'")

        if self._tried_to_fetch.get(item):
            raise AttributeError(f"already tried to fetch attribute '{item}'")

        # fetch the required part and update to (hopefully) set the required attribute
        self._fetch(part=self.ATTRIBUTE_DEFS[item].part)
        self._update_attributes()
        self._tried_to_fetch[item] = True

        # now getattr() should access the attribute directly.  if not, we'll get an attribute
        # error from this function because we've logged which items we've tried to fetch.
        return getattr(self, item)

    def _fetch(self, part):
        """Query the API for a specific data part.

        Build a query and execute it.  Update internal storage to reflect the new data.  Note:
        access to the data via attributes will not update until _update_attributes() is called.

        :param part: part string for the API query.

        """
        part_string = f"id,{part}"

        # get a raw listResponse from youtube
        response = Query(
            youtube=self.youtube,
            endpoint=self.ENDPOINT,
            api_params={'part': part_string, 'id': self.id}
        ).execute()

        # get the first resource item and update the internal data storage
        item = response['items'][0]
        self._data.update(item)


class AttributeDef(object):
    """Defines a Resource attribute.

    To make the API data available as attributes on Resource objects we need to know
        1. where to find the data in the API response, and
        2. what data type the attribute should have.

    This class defines the 'part' (in API terminology) that the attribute can be found in,
    and it's name (the dictionary key within the part), so that it can be found in the API
    response.

    If a non-existant part is given the API will raise a HttpError.  If a non-existant name is
    given (within an existing part) then ptyaw will fallback to the default for the given type.
    This is because it's tricky to know whether an attribute exists from the API response -
    sometimes an attribute will not be returned if it is null (e.g. if a user does not set a
    country for their channel it will simply not be returned in the API response).

    The data type should also be given as a string ('str', 'int', 'datetime' etc), so that we can
    convert it when we add the data as an attribute to the Resource instance.  If not given or
    None, no type conversion is performed.

    """

    def __init__(self, part, name, type_=None):
        self.part = part
        self.name = name
        self.type_ = type_


class Video(Resource):
    """A single YouTube video."""

    ENDPOINT = 'videos'
    ATTRIBUTE_DEFS = {
        #
        # snippet
        'title': AttributeDef('snippet', 'title', type_='str'),
        'description': AttributeDef('snippet', 'description', type_='str'),
        'published_at': AttributeDef('snippet', 'publishedAt', type_='datetime'),
        'tags': AttributeDef('snippet', 'tags', type_='list'),
        'channel_id': AttributeDef('snippet', 'channelId', type_='str'),
        'channel_title': AttributeDef('snippet', 'channelTitle', type_='str'),
        'thumbnails': AttributeDef('snippet', 'thumbnails', type_='thumbnails'),
        #
        # contentDetails
        'duration': AttributeDef('contentDetails', 'duration', type_='timedelta'),
        #
        # status
        'license': AttributeDef('status', 'license', type_='str'),
        #
        # statistics
        'n_views': AttributeDef('statistics', 'viewCount', type_='int'),
        'n_likes': AttributeDef('statistics', 'likeCount', type_='int'),
        'n_dislikes': AttributeDef('statistics', 'dislikeCount', type_='int'),
        'n_favorites': AttributeDef('statistics', 'favoriteCount', type_='int'),
        'n_comments': AttributeDef('statistics', 'commentCount', type_='int'),
    }

    @property
    def is_cc(self):
        return self.license == 'creativeCommon'

    @property
    def channel(self):
        return self.youtube.channel(id=self.channel_id)

    @property
    def url(self):
        return f"https://www.youtube.com/watch?v={self.id}"


class Channel(Resource):
    """A single YouTube channel."""

    ENDPOINT = 'channels'
    ATTRIBUTE_DEFS = {
        #
        # snippet
        'title': AttributeDef('snippet', 'title'),
        'description': AttributeDef('snippet', 'description'),
        'published_at': AttributeDef('snippet', 'publishedAt', type_='datetime'),
        'thumbnails': AttributeDef('snippet', 'thumbnails', type_='thumbnails'),
        'country': AttributeDef('snippet', 'country', type_='str'),
        'custom_url': AttributeDef('snippet', 'customUrl', type_='str'),
        #
        # statistics
        'n_videos': AttributeDef('statistics', 'videoCount', type_='int'),
        'n_subscribers': AttributeDef('statistics', 'subscriberCount', type_='int'),
        'n_views': AttributeDef('statistics', 'viewCount', type_='int'),
        'n_comments': AttributeDef('statistics', 'commentCount', type_='int'),
        #
        # content details - playlists
        '_related_playlists': AttributeDef('contentDetails', 'relatedPlaylists')
    }

    @property
    def uploads_playlist(self):
        playlists = self._related_playlists
        if 'uploads' in playlists:
            return self.youtube.playlist(playlists['uploads'])
        return None

    def most_recent_upload(self):
        response = self.most_recent_uploads(n=1)
        return response[0]

    def most_recent_uploads(self, n=50):
        if n > 50:
            raise ValueError(f"n must be less than 50, not {n}")

        api_search_params = {
            'part': 'id',
            'channelId': self.id,
            'maxResults': n,
            'order': 'date',
            'type': 'video',
        }
        response = self.youtube.search(**api_search_params)
        return response[:n]


class Playlist(Resource):
    """A single YouTube playlist."""

    ENDPOINT = 'playlists'
    ATTRIBUTE_DEFS = {
        #
        # snippet
        'title': AttributeDef('snippet', 'title'),
        'description': AttributeDef('snippet', 'description'),
        'published_at': AttributeDef('snippet', 'publishedAt', type_='datetime'),
        'thumbnails': AttributeDef('snippet', 'thumbnails', type_='thumbnails'),
        'channel_id': AttributeDef('snippet', 'channelId', type_='str'),
        'channel_title': AttributeDef('snippet', 'channelTitle', type_='str'),
    }

    @property
    def items(self):
        api_params = {
            'part': 'id,snippet',
            'maxResults': 50,
        }
        return self.youtube.playlist_items(self.id, **api_params)

    @property
    def channel(self):
        return self.youtube.channel(self.channel_id)


class PlaylistItem(Resource):
    """A playlist item."""
    ENDPOINT = 'playlist_items'
    ATTRIBUTE_DEFS = {
        #
        # snippet
        'title': AttributeDef('snippet', 'title'),
        'description': AttributeDef('snippet', 'description'),
        'channel_id': AttributeDef('snippet', 'channelId', type_='str'),
        'published_at': AttributeDef('snippet', 'publishedAt', type_='datetime'),
        'thumbnails': AttributeDef('snippet', 'thumbnails', type_='thumbnails'),
        'channel_title': AttributeDef('snippet', 'channelTitle', type_='str'),
        'playlist_id': AttributeDef('snippet', 'playlistId', type_='str'),
        'position': AttributeDef('snippet', 'position', type_='int'),
        'resource_kind': AttributeDef('snippet', ['resourceId', 'kind'], type_='str'),
        'resource_video_id': AttributeDef('snippet', ['resourceId', 'videoId'], type_='str'),
    }

    @property
    def video(self):
        if self.resource_kind == 'youtube#video':
            return self.youtube.video(self.resource_video_id)
        return None

