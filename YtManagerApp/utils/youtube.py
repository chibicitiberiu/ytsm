from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from django.conf import settings
import re

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'


class YoutubeChannelInfo(object):
    def __init__(self, result_dict):
        self.__id = result_dict['id']
        self.__snippet = result_dict['snippet']
        self.__contentDetails = result_dict['contentDetails']

    def getId(self):
        return self.__id

    def getTitle(self):
        return self.__snippet['title']

    def getDescription(self):
        return self.__snippet['description']

    def getCustomUrl(self):
        return self.__snippet['customUrl']

    def getDefaultThumbnailUrl(self):
        return self.__snippet['thumbnails']['default']['url']

    def getBestThumbnailUrl(self):
        best_url = None
        best_res = 0
        for _, thumb in self.__snippet['thumbnails'].items():
            res = thumb['width'] * thumb['height']
            if res > best_res:
                best_res = res
                best_url = thumb['url']
        return best_url

    def getUploadsPlaylist(self):
        return self.__contentDetails['relatedPlaylists']['uploads']


class YoutubePlaylistInfo(object):
    def __init__(self, result_dict):
        self.__id = result_dict['id']
        self.__snippet = result_dict['snippet']

    def getId(self):
        return self.__id

    def getChannelId(self):
        return self.__snippet['channelId']

    def getTitle(self):
        return self.__snippet['title']

    def getDescription(self):
        return self.__snippet['description']

    def getDefaultThumbnailUrl(self):
        return self.__snippet['thumbnails']['default']['url']

    def getBestThumbnailUrl(self):
        best_url = None
        best_res = 0
        for _, thumb in self.__snippet['thumbnails'].items():
            res = thumb['width'] * thumb['height']
            if res > best_res:
                best_res = res
                best_url = thumb['url']
        return best_url


class YoutubePlaylistItem(object):
    def __init__(self, result_dict):
        self.__snippet = result_dict['snippet']

    def getVideoId(self):
        return self.__snippet['resourceId']['videoId']

    def getPublishDate(self):
        return self.__snippet['publishedAt']

    def getTitle(self):
        return self.__snippet['title']

    def getDescription(self):
        return self.__snippet['description']

    def getDefaultThumbnailUrl(self):
        return self.__snippet['thumbnails']['default']['url']

    def getBestThumbnailUrl(self):
        best_url = None
        best_res = 0
        for _, thumb in self.__snippet['thumbnails'].items():
            res = thumb['width'] * thumb['height']
            if res > best_res:
                best_res = res
                best_url = thumb['url']
        return best_url

    def getPlaylistIndex(self):
        return self.__snippet['position']


class YoutubeAPI(object):
    def __init__(self, service):
        self.service = service

    @staticmethod
    def build_public() -> 'YoutubeAPI':
        service = build(API_SERVICE_NAME, API_VERSION, developerKey=settings.YOUTUBE_API_KEY)
        return YoutubeAPI(service)

    @staticmethod
    def parse_channel_url(url):
        """
        Parses given channel url, returns a tuple of the form (type, value), where type can be one of:
            * channel_id
            * channel_custom
            * user
            * playlist_id
        :param url: URL to parse
        :return: (type, value) tuple
        """
        match = re.search(r'youtube\.com/.*[&?]list=([^?&/]+)', url)
        if match:
            return 'playlist_id', match.group(1)

        match = re.search(r'youtube\.com/user/([^?&/]+)', url)
        if match:
            return 'user', match.group(1)

        match = re.search(r'youtube\.com/channel/([^?&/]+)', url)
        if match:
            return 'channel_id', match.group(1)

        match = re.search(r'youtube\.com/(?:c/)?([^?&/]+)', url)
        if match:
            return 'channel_custom', match.group(1)

        raise Exception('Unrecognized URL format!')

    def get_playlist_info(self, list_id) -> YoutubePlaylistInfo:
        result = self.service.playlists()\
            .list(part='snippet', id=list_id)\
            .execute()

        if len(result['items']) <= 0:
            raise Exception("Invalid playlist ID.")

        return YoutubePlaylistInfo(result['items'][0])

    def get_channel_info_by_username(self, user) -> YoutubeChannelInfo:
        result = self.service.channels()\
            .list(part='snippet,contentDetails', forUsername=user)\
            .execute()

        if len(result['items']) <= 0:
            raise Exception('Invalid user.')

        return YoutubeChannelInfo(result['items'][0])

    def get_channel_info(self, channel_id) -> YoutubeChannelInfo:
        result = self.service.channels()\
            .list(part='snippet,contentDetails', id=channel_id)\
            .execute()

        if len(result['items']) <= 0:
            raise Exception('Invalid channel ID.')

        return YoutubeChannelInfo(result['items'][0])

    def search_channel(self, custom) -> str:
        result = self.service.search()\
            .list(part='id', q=custom, type='channel')\
            .execute()

        if len(result['items']) <= 0:
            raise Exception('Could not find channel!')

        channel_result = result['items'][0]
        return channel_result['id']['channelId']

    def list_playlist_videos(self, playlist_id):
        kwargs = {
            "part": "snippet",
            "maxResults": 50,
            "playlistId": playlist_id
        }
        last_page = False

        while not last_page:
            result = self.service.playlistItems()\
                .list(**kwargs)\
                .execute()

            for item in result['items']:
                yield YoutubePlaylistItem(item)

            if 'nextPageToken' in result:
                kwargs['pageToken'] = result['nextPageToken']
            else:
                last_page = True

    # @staticmethod
    # def build_oauth() -> 'YoutubeAPI':
    #     flow =
    #     credentials =
    #     service = build(API_SERVICE_NAME, API_VERSION, credentials)
