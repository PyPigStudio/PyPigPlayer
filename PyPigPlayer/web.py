import html
import json
import re
import traceback
import urllib.parse
import urllib.request

import faker

import popup
from init import *


music_u = ''


class Music:
    """
    单曲信息。
    """

    _: str = ''
    album: str = ''
    id: int = 0
    mid: str = ''
    name: str = ''
    singer: str = ''
    url: str = ''
    vip: bool = False

    def __init__(self, name: str, singer: str, album: str, id: int, _: str, vip: bool = False, mid: str = '') -> None:
        self.name = name
        self.singer = singer
        self.album = album
        self.id = id
        self._ = _
        if _ == 'netease':
            self.url = f'https://music.163.com/#/song?id={id}'
        else:
            self.url = 'https://y.qq.com/n/ryqq/songDetail/'+mid
        self.vip = vip
        self.mid = mid


def get(url: str, headers: dict = {}, retry: int = 3) -> bytes:
    """
    获取 URL 数据。
    """
    if not retry:
        traceback.print_exc()
        err.set('无法访问 '+url)
    headers['User-Agent'] = faker.Faker().user_agent()
    req = urllib.request.Request(url, headers=headers)
    try:
        return urllib.request.urlopen(req).read()
    except:
        return get(url, headers, retry-1)


def get_json(url: str, headers: dict = {}):
    """
    获取 URL 数据并按 JSON 格式解析。
    """
    data = get(url, headers)
    return json.loads(data.decode(errors='ignore'))


def link(music: Music) -> str:
    """
    获取歌曲音频链接。
    """
    try:
        if music._ == 'netease':
            return f'http://music.163.com/song/media/outer/url?id={music.id}'
        else:
            info.set('正在获取音频链接……')
            data = get_json(
                'https://u.y.qq.com/cgi-bin/musicu.fcg?data={%22data%22:{%22module%22:%22vkey.GetVkeyServer%22,%22method%22:%22CgiGetVkey%22,%22param%22:{%22guid%22:%220%22,%22songmid%22:[%22'+music.mid+'%22]}}}')
            return 'http://ws.stream.qqmusic.qq.com/'+data['data']['data']['midurlinfo'][0]['purl']

    except Exception as e:
        traceback.print_exc()
        err.set('获取音频链接失败:'+str(e))

    finally:
        if music._ == 'qqmusic':
            info.clear()


def lrc(music: Music) -> str:
    """
    获取歌词。
    """
    info.set('正在获取歌词……')
    try:
        if music._ == 'netease':
            data = get_json(
                f'http://music.163.com/api/song/media?id={music.id}')
            return data['lyric'] if 'lyric' in data else ''
        else:
            data = get_json(f'https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_yqq.fcg?nobase64=1&format=json&musicid={music.id}', {
                            'referer': f'https://y.qq.com/n/yqq/song/{music.mid}.html'})
            return html.unescape(html.unescape(data['lyric'])) if 'lyric' in data else ''

    except Exception as e:
        traceback.print_exc()
        err.set('获取歌词失败:'+str(e))

    finally:
        info.clear()


def search(name: str) -> list:
    """
    搜索歌曲。
    """
    try:
        name = urllib.parse.quote_plus(name)
        info.set('正在网易云音乐搜索……')
        ret1 = [Music(i['name'], ','.join(j['name'] for j in i['artists']), i['album']['name'], i['id'], 'netease', i['fee'] == 1)
                for i in get_json('http://music.163.com/api/search/get?type=1&limit=100&s='+name)['result']['songs'] if not i['status']]
        ret2 = []
        # info.set('正在QQ音乐搜索……')
        # ret2 = [Music(i['songname'], ','.join(j['name'] for j in i['singer']), i['albumname'], i['songid'], 'qqmusic', i['pay']['payplay'], i['songmid'])
        #        for i in get_json('https://c.y.qq.com/soso/fcgi-bin/search_for_qq_cp?n=99&format=json&w='+name)['data']['song']['list']]

        ret = []
        i = j = 0
        while i < len(ret1) and j < len(ret2):
            for a, l in ((i, ret1), (j, ret2)):
                for k in range(5):
                    if a+k == len(l):
                        break
                    ret.append(l[a+k])
            i += 5
            j += 5
        while i < len(ret1):
            ret.append(ret1[i])
            i += 1
        while j < len(ret2):
            ret.append(ret2[j])
            j += 1
        return ret

    except Exception as e:
        traceback.print_exc()
        err.set('搜索失败:'+str(e))

    finally:
        info.clear()


def singer() -> None:
    """
    下载网易云音乐歌手所有歌曲。
    """
    try:
        id = popup.input('请输入网易云音乐歌手ID', '下载歌手所有歌曲')
        if id:
            songs = set()
            info.set('正在获取歌手专辑列表……')
            albums = set(i['id'] for i in get_json(
                f'http://music.163.com/api/artist/albums/{id}?limit=500')['hotAlbums'])
            for times in range(100):
                ok = set()
                for num, album in enumerate(albums):
                    info.set(
                        f'正在获取歌手歌曲列表(第{times+1}次尝试，{num+1}/{len(albums)}，共{len(songs)}首)……')
                    data = get_json(
                        f'http://music.163.com/api/album/{album}?limit=500')
                    if 'album' in data:
                        for i in data['album']['songs']:
                            songs.add(Music(i['name'], ','.join(
                                j['name'] for j in i['artists']), i['album']['name'], i['id'], 'netease'))
                        ok.add(album)
                for i in ok:
                    albums.remove(i)
                if len(albums) == 0:
                    break
            info.clear()
            if popup.yesno(f'确认下载{len(songs)}首歌曲?', '歌手歌曲获取完毕'):
                skip_mp3 = popup.yesno('是否跳过音频，仅下载歌词?', '下载模式')
                savepath = popup.folder('请选择保存文件夹')
                fail_num = 0
                for num, i in enumerate(songs):
                    success = False
                    for times in range(3):
                        info.set(
                            f'正在下载歌曲({num+1}/{len(songs)}'+(f'，重试{times}次' if times else '')+f'，失败{fail_num}首)……')
                        filepath = os.path.join(savepath, re.sub(
                            r'[\/\\\:\*\?\"\<\>\|]', '_',  i.singer+' - '+i.name+'.mp3'))
                        if skip_mp3:
                            success = True
                            break
                        open(filepath, 'wb').write(get(link(i)))
                        if len(open(filepath, 'rb').read()) > 1e5:
                            success = True
                            break
                    if success:
                        lrc = lrc(i)
                        if lrc:
                            open(filepath[:-3]+'lrc',
                                 'wb').write(lrc(i).encode(errors='ignore'))
                    else:
                        os.remove(filepath)
                        fail_num += 1
                popup.print(
                    f'成功{len(songs)-fail_num}首，失败{fail_num}首。', '下载歌手歌曲完毕')

    except Exception as e:
        traceback.print_exc()
        err.set('下载歌手歌曲失败:'+str(e))

    finally:
        info.clear()


def songlist() -> None:
    """
    下载网易云音乐歌单。
    """
    global music_u
    try:
        id = popup.input('请输入网易云音乐歌单ID', '下载歌单')
        if id:
            def getsongs():
                while True:
                    if music_u:
                        data = get_json(
                            f'https://music.163.com/api/playlist/detail?id={id}', {'cookie': 'MUSIC_U='+music_u})
                    else:
                        data = get_json(
                            f'https://music.163.com/api/playlist/detail?id={id}')
                    if 'result' in data:
                        print(json.dumps(data, indent=4, sort_keys=True),
                              file=open('1.txt', 'w'))
                        break
                return [Music(i['name'], ','.join(
                    j['name'] for j in i['artists']), i['album']['name'], i['id'], 'netease') for i in data['result']['tracks']]
            info.set('正在获取歌单……')
            songs = getsongs()
            if len(songs) == 10:
                if not music_u:
                    music_u = popup.input(
                        '获取完整歌单需要输入登陆网页版后的cookie\n请粘贴 MUSIC_U 到下方(若不知如何查看可留空)', '未登录只能下载前10首')
                    if music_u:
                        songs = getsongs()
            info.clear()
            if popup.yesno(f'确认下载{len(songs)}首歌曲?', '歌单获取完毕'):
                skip_mp3 = popup.yesno('是否跳过音频，仅下载歌词?', '下载模式')
                savepath = popup.folder('请选择保存文件夹')
                fail_num = 0
                for num, i in enumerate(songs):
                    success = False
                    for times in range(3):
                        info.set(
                            f'正在下载歌曲({num+1}/{len(songs)}'+(f'，重试{times}次' if times else '')+f'，失败{fail_num}首)……')
                        filepath = os.path.join(savepath, re.sub(
                            r'[\/\\\:\*\?\"\<\>\|]', '_',  i.singer+' - '+i.name+'.mp3'))
                        if skip_mp3:
                            success = True
                            break
                        open(filepath, 'wb').write(get(link(i)))
                        if len(open(filepath, 'rb').read()) > 1e5:
                            success = True
                            break
                    if success:
                        lrc = lrc(i)
                        if lrc:
                            open(filepath[:-3]+'lrc',
                                 'wb').write(lrc(i).encode(errors='ignore'))
                    else:
                        os.remove(filepath)
                        fail_num += 1
                popup.print(
                    f'成功{len(songs)-fail_num}首，失败{fail_num}首。', '下载歌单完毕')

    except Exception as e:
        traceback.print_exc()
        err.set('下载歌手歌曲失败:'+str(e))

    finally:
        info.clear()


def toplist(topid: int) -> list:
    """
    获取 QQ 音乐榜单。
    """
    info.set('正在获取榜单……')
    try:
        data = get_json(
            f'https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg?topid={topid}')['songlist']
        return [Music(i['data']['songname'], ','.join(j['name'] for j in i['data']['singer']), i['data']['albumname'], i['data']['songid'], 'qqmusic', i['data']['pay']['payplay'], i['data']['songmid'])
                for i in data]

    except Exception as e:
        traceback.print_exc()
        err.set('获取榜单失败:'+str(e))

    finally:
        info.clear()
