
class HTTPResponseWrapper(object):
    """
    This class is intended as a workaround for 'requests' module
    inability to consume HTTPResponse as a streaming upload source.
    I.e. if you want to download data from one url and upload it
    to another.
    The problem is that underlying code uses seek() and tell() to
    calculate stream length, but HTTPResponse throws a NotImplementedError,
    according to python file-like object implementation guidelines, since
    the stream is obviously non-rewindable.
    Another problem arises when requests.put() tries to calculate stream
    length with other methods. It tries several ways, including len()
    and __len__(), and falls back to reading the whole stream. But
    since the stream is not rewindable, by the time it tries to send
    actual content, there is nothing left in the stream.
    """
    def __init__(self, obj):
        self.obj = obj

    def __getattr__(self, attr):
        """
        Redirect member requests except seek() to original object
        """
        if attr in self.__dict__:
            return self.__dict__[attr]

        if attr == 'seek':
            raise AttributeError

        return getattr(self.obj, attr)

    def __len__(self):
        """
        __len__ will be used by requests to determine stream size
        """
        return int(self.getheader('content-length'))


def encode_matrix_parameters(parameters):
    """
    Performs encoding of url matrix parameters from dictionary to
    a string.
    See http://www.w3.org/DesignIssues/MatrixURIs.html for specs.
    """
    result = []

    for param in iter(sorted(parameters)):
        if isinstance(parameters[param], (list, tuple)):
            value = (';%s=' % (param)).join(parameters[param])
        else:
            value = parameters[param]

        result.append("%s=%s" % (param, value))

    return ';'.join(result)


def escape_chars(s):
    """
    Performs character escaping of comma, pipe and equals characters
    """
    return "".join(['\\' + ch if ch in '=|,' else ch for ch in s])


def encode_properties(parameters):
    """
    Performs encoding of url parameters from dictionary to a string. It does
    not escape backslash because it is not needed.

    See: http://www.jfrog.com/confluence/display/RTF/Artifactory+REST+API#ArtifactoryRESTAPI-SetItemProperties
    """
    result = []

    for param in iter(sorted(parameters)):
        if isinstance(parameters[param], (list, tuple)):
            value = ','.join([escape_chars(x) for x in parameters[param]])
        else:
            value = escape_chars(parameters[param])

        result.append("%s=%s" % (param, value))

    return '|'.join(result)
