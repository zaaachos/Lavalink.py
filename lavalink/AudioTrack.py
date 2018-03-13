class InvalidTrack(Exception):
    def __init__(self, message):
        super().__init__(message)


class AudioTrack:
    def __init__(self, track, identifier, can_seek, author, duration, stream,
                 title, uri, requester, enable_msg: bool = True, is_ad: bool = False, quit_after_empty: bool = False, ):
        self.track = track
        self.identifier = identifier
        self.can_seek = can_seek
        self.author = author
        self.duration = duration
        self.stream = stream
        self.title = title
        self.uri = uri
        self.requester = requester
        self.enable_msg = enable_msg
        self.is_ad = is_ad
        self.quit_after_empty = quit_after_empty

    @classmethod
    def build(cls, track, requester, enable_msg: bool = True, is_ad: bool = False, quit_after_empty: bool = False):
        """ Returns an optional AudioTrack """
        try:
            _track = track['track']
            identifier = track['info']['identifier']
            can_seek = track['info']['isSeekable']
            author = track['info']['author']
            duration = track['info']['length']
            stream = track['info']['isStream']
            title = track['info']['title']
            uri = track['info']['uri']
            requester = requester
            enable_msg = enable_msg
            is_ad = is_ad
            quit_after_empty = quit_after_empty
        except KeyError:
            raise InvalidTrack('an invalid track was passed')

        return cls(_track, identifier, can_seek, author, duration, stream, title,
                   uri, requester, enable_msg, is_ad, quit_after_empty)

    @property
    def thumbnail(self):
        """ Returns the video thumbnail. Could be an empty string. """
        if 'youtube' in self.uri:
            return "https://img.youtube.com/vi/{}/default.jpg".format(self.identifier)

        return ""
