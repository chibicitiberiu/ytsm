from googleapiclient.discovery import build
from googleapiclient.errors import Error as APIError
from google_auth_oauthlib.flow import InstalledAppFlow
from django.conf import settings
import re
from YtManagerApp.utils.iterutils import as_chunks

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

YOUTUBE_LIST_LIMIT = 50


class YoutubeException(Exception):
    pass


class YoutubeInvalidURLException(YoutubeException):
    pass


class YoutubeChannelNotFoundException(YoutubeException):
    pass


class YoutubeUserNotFoundException(YoutubeException):
    pass


class YoutubePlaylistNotFoundException(YoutubeException):
    pass


class YoutubeVideoNotFoundException(YoutubeException):
    pass


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
        try:
            return self.__snippet['customUrl']
        except KeyError:
            return None

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


class YoutubeVideoStatistics(object):
    def __init__(self, result_dict):
        self.id = result_dict['id']
        self.stats = result_dict['statistics']

    def get_view_count(self):
        return int(self.stats['viewCount'])

    def get_like_count(self):
        return int(self.stats['likeCount'])

    def get_dislike_count(self):
        return int(self.stats['dislikeCount'])

    def get_favorite_count(self):
        return int(self.stats['favoriteCount'])

    def get_comment_count(self):
        return int(self.stats['commentCount'])


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

        raise YoutubeInvalidURLException('Unrecognized URL format!')

    def get_playlist_info(self, list_id) -> YoutubePlaylistInfo:
        result = self.service.playlists()\
            .list(part='snippet', id=list_id)\
            .execute()

        if len(result['items']) <= 0:
            raise YoutubePlaylistNotFoundException("Invalid playlist ID.")

        return YoutubePlaylistInfo(result['items'][0])

    def get_channel_info_by_username(self, user) -> YoutubeChannelInfo:
        result = self.service.channels()\
            .list(part='snippet,contentDetails', forUsername=user)\
            .execute()

        if len(result['items']) <= 0:
            raise YoutubeUserNotFoundException('Invalid user.')

        return YoutubeChannelInfo(result['items'][0])

    def get_channel_info(self, channel_id) -> YoutubeChannelInfo:
        result = self.service.channels()\
            .list(part='snippet,contentDetails', id=channel_id)\
            .execute()

        if len(result['items']) <= 0:
            raise YoutubeChannelNotFoundException('Invalid channel ID.')

        return YoutubeChannelInfo(result['items'][0])

    def search_channel(self, custom) -> str:
        result = self.service.search()\
            .list(part='id', q=custom, type='channel')\
            .execute()

        if len(result['items']) <= 0:
            raise YoutubeChannelNotFoundException('Could not find channel!')

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

    def get_single_video_stats(self, video_id) -> YoutubeVideoStatistics:
        result = list(self.get_video_stats([video_id]))
        if len(result) < 1:
            raise YoutubeVideoNotFoundException('Could not find video with id ' + video_id + '!')
        return result[0]

    def get_video_stats(self, video_id_list):
        for chunk in as_chunks(video_id_list, YOUTUBE_LIST_LIMIT):
            kwargs = {
                "part": "statistics",
                "maxResults": YOUTUBE_LIST_LIMIT,
                "id": ','.join(chunk)
            }
            result = self.service.videos()\
                .list(**kwargs)\
                .execute()

            for item in result['items']:
                yield YoutubeVideoStatistics(item)

    # @staticmethod
    # def build_oauth() -> 'YoutubeAPI':
    #     flow =
    #     credentials =
    #     service = build(API_SERVICE_NAME, API_VERSION, credentials)
