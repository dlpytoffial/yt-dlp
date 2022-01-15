# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    get_elements_text_and_html_by_attribute,
    unescapeHTML,
)


class TVOpenGrBaseIE(InfoExtractor):
    def _return_canonical_url(self, url, video_id):
        webpage = self._download_webpage(url, video_id)
        canonical_url = self._og_search_url(webpage)
        title = self._og_search_title(webpage)
        return self.url_result(canonical_url, ie=TVOpenGrWatchIE.ie_key(), video_id=video_id, video_title=title)


class TVOpenGrWatchIE(TVOpenGrBaseIE):
    IE_NAME = 'tvopengr:watch'
    IE_DESC = 'tvopen.gr (and ethnos.gr) videos'
    _VALID_URL = r'https?://(?P<netloc>(?:www\.)?(?:tvopen|ethnos)\.gr)/watch/(?P<id>\d+)/(?P<slug>[^/]+)'
    _API_ENDPOINT = 'https://www.tvopen.gr/templates/data/player'

    _TESTS = [{
        'url': 'https://www.ethnos.gr/watch/101009/nikoskaprabelosdenexoymekanenanasthenhsemethmethmetallaxhomikron',
        'md5': '8728570e3a72e0f8d9475ba94859fdc1',
        'info_dict': {
            'id': '101009',
            'title': 'md5:51f68773dcb6c70498cd326f45fefdf0',
            'display_id': 'nikoskaprabelosdenexoymekanenanasthenhsemethmethmetallaxhomikron',
            'description': 'md5:78fff49f18fb3effe41b070e5c7685d6',
            'thumbnail': 'https://opentv-static.siliconweb.com/imgHandler/1920/d573ba71-ec5f-43c6-b4cb-d181f327d3a8.jpg',
            'ext': 'mp4',
            'upload_date': '20220109',
            'timestamp': 1641686400,
        },
    }, {
        'url': 'https://www.tvopen.gr/watch/100979/se28099agapaomenalla7cepeisodio267cmhthrargiapashskakias',
        'md5': '38f98a1be0c577db4ea2d1b1c0770c48',
        'info_dict': {
            'id': '100979',
            'title': 'md5:e021f3001e16088ee40fa79b20df305b',
            'display_id': 'se28099agapaomenalla7cepeisodio267cmhthrargiapashskakias',
            'description': 'md5:ba17db53954134eb8d625d199e2919fb',
            'thumbnail': 'https://opentv-static.siliconweb.com/imgHandler/1920/9bb71cf1-21da-43a9-9d65-367950fde4e3.jpg',
            'ext': 'mp4',
            'upload_date': '20220108',
            'timestamp': 1641600000,
        },
    }]

    def _extract_formats_and_subs(self, options, video_id):
        formats, subs = [], {}
        for format_id, format_url in options.items():
            if format_id not in ('stream', 'httpstream', 'mpegdash'):
                continue
            ext = determine_ext(format_url)
            if ext == 'm3u8':
                formats_, subs_ = self._extract_m3u8_formats_and_subtitles(
                    format_url, video_id, 'mp4', m3u8_id=format_id,
                    fatal=False)
            elif ext == 'mpd':
                formats_, subs_ = self._extract_mpd_formats_and_subtitles(
                    format_url, video_id, 'mp4', fatal=False)
            else:
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                })
                continue
            formats.extend(formats_)
            self._merge_subtitles(subs_, target=subs)
        self._sort_formats(formats)
        return formats, subs

    def _real_extract(self, url):
        netloc, video_id, display_id = self._match_valid_url(url).group('netloc', 'id', 'slug')
        if netloc.find('tvopen.gr') == -1:
            return self._return_canonical_url(url, video_id)
        webpage = self._download_webpage(url, video_id)
        info = self._search_json_ld(webpage, video_id, expected_type='VideoObject')
        info['formats'], info['subtitles'] = self._extract_formats_and_subs(
            self._download_json(self._API_ENDPOINT, video_id, query={'cid': video_id}),
            video_id)
        max_dimensions = max(
            [tuple(format.get(k) or 0 for k in ('width', 'height')) for format in info['formats']],
            default=(0, 0))
        if max_dimensions[0]:
            for thumbnail in info['thumbnails']:
                thumbnail['url'] = re.sub(r'(/imgHandler/)\d+', rf'\g<1>{max_dimensions[0]}', thumbnail['url'])
                thumbnail['width'], thumbnail['height'] = max_dimensions
        description, _html = next(get_elements_text_and_html_by_attribute('class', 'description', webpage))
        if description and _html.startswith('<span '):
            info['description'] = description
        info['id'] = video_id
        info['display_id'] = display_id
        return info


class TVOpenGrEmbedIE(TVOpenGrBaseIE):
    IE_NAME = 'tvopengr:embed'
    IE_DESC = 'tvopen.gr embedded videos'
    _VALID_URL = r'(?:https?:)?//(?:www\.|cdn\.|)(?:tvopen|ethnos).gr/embed/(?P<id>\d+)'

    _TESTS = [{
        'url': 'https://cdn.ethnos.gr/embed/100963',
        'md5': '2da147881f45571d81662d94d086628b',
        'info_dict': {
            'id': '100963',
            'display_id': 'koronoiosapotoysdieythyntestonsxoleionselftestgiaosoysdenbrhkan',
            'title': 'md5:2c71876fadf0cda6043da0da5fca2936',
            'description': 'md5:17482b4432e5ed30eccd93b05d6ea509',
            'thumbnail': 'https://opentv-static.siliconweb.com/imgHandler/1920/5804e07f-799a-4247-a696-33842c94ca37.jpg',
            'ext': 'mp4',
            'upload_date': '20220108',
            'timestamp': 1641600000,
        },
    }]

    @classmethod
    def _extract_urls(cls, webpage, origin_url=None):
        EMBED_RE = r'''<iframe[^>]+?src=(?P<_q1>["'])(?P<url>%s)(?P=_q1)''' % cls._VALID_URL
        for mobj in re.finditer(EMBED_RE, webpage):
            yield unescapeHTML(mobj.group('url'))

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self._return_canonical_url(url, video_id)
