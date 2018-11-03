from typing import Iterable
from xml.etree import ElementTree
import re


class FormatNotSupportedError(Exception):
    pass


class SubFileParser(object):

    def probe(self, file_handle) -> bool:
        """
        Tests if file matches file format.
        :param file: File path
        :return: True if file matches, false otherwise
        """
        return False

    def parse(self, file_handle) -> Iterable[str]:
        """
        Parses file and returns a list of subscription URLs.
        :param file:
        :return:
        """
        return []


class SubscriptionListFileParser(SubFileParser):
    """
    A subscription list file is file which contains just a bunch of URLs.
    Comments are supported using # character.
    """

    def __is_url(self, text: str) -> bool:
        return text.startswith('http://') or text.startswith('https://')

    def probe(self, file_handle):
        file_handle.seek(0)
        for line in file_handle:
            if isinstance(line, bytes) or isinstance(line, bytearray):
                line = line.decode()
            # Trim comments and spaces
            line = re.sub('(^|\s)#.*', '', line).strip()
            if len(line) > 0:
                return self.__is_url(line)
        return False

    def parse(self, file_handle):
        file_handle.seek(0)
        for line in file_handle:
            if isinstance(line, bytes) or isinstance(line, bytearray):
                line = line.decode()
            # Trim comments and spaces
            line = re.sub('(^|\s)#.*', '', line).strip()
            if len(line) > 0:
                yield line


class OPMLParser(SubFileParser):
    """
    Parses OPML files (emitted by YouTube)
    """
    def __init__(self):
        self.__cached_file = None
        self.__cached_tree: ElementTree.ElementTree = None

    def __parse(self, file_handle):
        if file_handle == self.__cached_file:
            return self.__cached_tree

        file_handle.seek(0)
        tree = ElementTree.parse(file_handle)

        self.__cached_file = file_handle
        self.__cached_tree = tree
        return self.__cached_tree

    def probe(self, file_handle):
        try:
            tree = self.__parse(file_handle)
        except ElementTree.ParseError:
            # Malformed XML
            return False

        return tree.getroot().tag.lower() == 'opml'

    def parse(self, file_handle):
        tree = self.__parse(file_handle)
        root = tree.getroot()

        for node in root.iter('outline'):
            if 'xmlUrl' in node.keys():
                yield node.get('xmlUrl')


PARSERS = (
    OPMLParser(),
    SubscriptionListFileParser()
)


def parse(file_handle) -> Iterable[str]:
    for parser in PARSERS:
        if parser.probe(file_handle):
            return parser.parse(file_handle)

    raise FormatNotSupportedError('This file cannot be parsed!')
