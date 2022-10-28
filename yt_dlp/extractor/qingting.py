from .common import InfoExtractor

from ..utils import traverse_obj


class QingTingIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|m\.)?(?:qingting\.fm|qtfm\.cn)/v?channels/(?P<channel>\d+)/programs/(?P<id>\d+)'
    _TESTS = {
        'url': 'https://www.qingting.fm/channels/378005/programs/22257411/',
        'md5': '47e6a94f4e621ed832c316fd1888fb3c',
        'info_dict': {
            'id': '22257411',
            'ext': 'mp3',
            'title': '用了十年才修改，谁在乎教科书？-睡前消息-蜻蜓FM听头条',
        }
    }

    def _real_extract(self, url):
        channel_id, pid = self._match_valid_url(url).groups()
        webpage = self._download_webpage(
            f'https://m.qtfm.cn/vchannels/{channel_id}/programs/{pid}/', pid)
        info = self._search_json(r'window\.__initStores\s*=', webpage, 'program info', pid)
        return {
            'id': pid,
            'title': traverse_obj(info, ('ProgramStore', 'programInfo', 'title')),
            'channel_id': channel_id,
            'url': traverse_obj(info, ('ProgramStore', 'programInfo', 'audioUrl')),
            'ext': 'm4a',
        }
