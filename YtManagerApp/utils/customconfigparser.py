import os
import os.path
import re
from configparser import Interpolation, NoSectionError, NoOptionError, InterpolationMissingOptionError, \
    InterpolationDepthError, InterpolationSyntaxError, ConfigParser

MAX_INTERPOLATION_DEPTH = 10


class ExtendedInterpolatorWithEnv(Interpolation):
    """Advanced variant of interpolation, supports the syntax used by
    `zc.buildout'. Enables interpolation between sections.

    This modified version also allows specifying environment variables
    using ${env:...}, and allows adding additional options using 'set_additional_options'. """

    _KEYCRE = re.compile(r"\$\{([^}]+)\}")

    def __init__(self, **kwargs):
        self.__kwargs = kwargs

    def set_additional_options(self, **kwargs):
        self.__kwargs = kwargs

    def before_get(self, parser, section, option, value, defaults):
        L = []
        self._interpolate_some(parser, option, L, value, section, defaults, 1)
        return ''.join(L)

    def before_set(self, parser, section, option, value):
        tmp_value = value.replace('$$', '')  # escaped dollar signs
        tmp_value = self._KEYCRE.sub('', tmp_value)  # valid syntax
        if '$' in tmp_value:
            raise ValueError("invalid interpolation syntax in %r at "
                             "position %d" % (value, tmp_value.find('$')))
        return value

    def _resolve_option(self, option, defaults):
        if option in self.__kwargs:
            return self.__kwargs[option]
        return defaults[option]

    def _resolve_section_option(self, section, option, parser):
        if section == 'env':
            return os.getenv(option, '')
        return parser.get(section, option, raw=True)

    def _interpolate_some(self, parser, option, accum, rest, section, map,
                          depth):
        rawval = parser.get(section, option, raw=True, fallback=rest)
        if depth > MAX_INTERPOLATION_DEPTH:
            raise InterpolationDepthError(option, section, rawval)
        while rest:
            p = rest.find("$")
            if p < 0:
                accum.append(rest)
                return
            if p > 0:
                accum.append(rest[:p])
                rest = rest[p:]
            # p is no longer used
            c = rest[1:2]
            if c == "$":
                accum.append("$")
                rest = rest[2:]
            elif c == "{":
                m = self._KEYCRE.match(rest)
                if m is None:
                    raise InterpolationSyntaxError(option, section,
                                                   "bad interpolation variable reference %r" % rest)
                path = m.group(1).split(':')
                rest = rest[m.end():]
                sect = section
                opt = option
                try:
                    if len(path) == 1:
                        opt = parser.optionxform(path[0])
                        v = self._resolve_option(opt, map)
                    elif len(path) == 2:
                        sect = path[0]
                        opt = parser.optionxform(path[1])
                        v = self._resolve_section_option(sect, opt, parser)
                    else:
                        raise InterpolationSyntaxError(
                            option, section,
                            "More than one ':' found: %r" % (rest,))
                except (KeyError, NoSectionError, NoOptionError):
                    raise InterpolationMissingOptionError(
                        option, section, rawval, ":".join(path)) from None
                if "$" in v:
                    self._interpolate_some(parser, opt, accum, v, sect,
                                           dict(parser.items(sect, raw=True)),
                                           depth + 1)
                else:
                    accum.append(v)
            else:
                raise InterpolationSyntaxError(
                    option, section,
                    "'$' must be followed by '$' or '{', "
                    "found: %r" % (rest,))


class ConfigParserWithEnv(ConfigParser):
    _DEFAULT_INTERPOLATION = ExtendedInterpolatorWithEnv()

    def set_additional_interpolation_options(self, **kwargs):
        """
        Sets additional options to be used in interpolation.
        Only works with ExtendedInterpolatorWithEnv
        :param kwargs:
        :return:
        """
        if isinstance(self._interpolation, ExtendedInterpolatorWithEnv):
            self._interpolation.set_additional_options(**kwargs)
