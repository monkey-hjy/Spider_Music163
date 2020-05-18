import execjs
import requests
from lxml import etree
import re
import time
import pymongo
import json
import sys
import os
import datetime


def get_exist_music():
    exist_music = []
    data = table.find()
    for i in data:
        exist_music.append(i['music_name'])
    return exist_music


def restart():
    python = sys.executable
    os.execl(python, python, *sys.argv)


def get_ip():
    url = 'http://192.168.1.177:5000/paid'
    return requests.get(url).text


def get_info(id, self):
    url = f'https://music.163.com/song?id={id}'
    html = etree.HTML(self.get_response(url).text)
    music_name = html.xpath('//em[@class="f-ff2"]/text()')[0]
    singer_name = html.xpath('//a[@class="s-fc7"]/text()')[0]
    album = html.xpath('//a[@class="s-fc7"]/text()')[1]
    comment = get_comment(id, self)
    data = {
        'music_name': music_name,
        'singer_name': singer_name,
        'album': album,
        'comment': comment
    }
    table.insert_one(data)
    print(f"{data['music_name']} --- {datetime.datetime.now()}")


def get_comment(id, self):
    comment = []
    js = open('./Music163.js', 'r', encoding='utf8').read()
    ctx = execjs.compile(js)
    key = ctx.call('start', id, 0)
    url = f'https://music.163.com/weapi/v1/resource/comments/R_SO_4_{id}?csrf_token='
    data = {
        'params': key['params'],
        'encSecKey': key['encSecKey']
    }
    response = requests.post(url, data=data, headers=self.headers).json()
    comment_count = response['total']
    if int(comment_count) >= 60:
        for page in range(3):
            key = ctx.call('start', id, page)
            url = f'https://music.163.com/weapi/v1/resource/comments/R_SO_4_{id}?csrf_token='
            data = {
                'params': key['params'],
                'encSecKey': key['encSecKey']
            }
            response = requests.post(url, data=data, headers=self.headers).json()
            comment += get_comment_data(response)
    else:
        for page in range(int(comment_count) // 20):
            key = ctx.call('start', id, page)
            url = f'https://music.163.com/weapi/v1/resource/comments/R_SO_4_{id}?csrf_token='
            data = {
                'params': key['params'],
                'encSecKey': key['encSecKey']
            }
            response = requests.post(url, data=data, headers=self.headers).json()
            comment += get_comment_data(response)
    return comment


def get_comment_data(response):
    comment = []
    # 获取到热评的信息
    try:
        hot_comment = response['hotComments']
        for i in range(len(hot_comment)):
            info = {
                'nickname': hot_comment[i]['user']['nickname'],
                'avatarUrl': hot_comment[i]['user']['avatarUrl'],
                'content': hot_comment[i]['content'],
                'likedCount': hot_comment[i]['likedCount'],
                'time': time.strftime("%Y-%m-%d", time.localtime(hot_comment[i]['time'] // 1000))
            }
            comment.append(info)
    except:
        pass
    # 获取到普通评论的信息
    comments = response['comments']
    for i in range(len(comments)):
        info = {
            'nickname': comments[i]['user']['nickname'],
            'avatarUrl': comments[i]['user']['avatarUrl'],
            'content': comments[i]['content'],
            'likedCount': comments[i]['likedCount'],
            'time': time.strftime("%Y-%m-%d", time.localtime(comments[i]['time'] // 1000))
        }
        comment.append(info)
    return comment


# 抓取榜单音乐信息
class Bnagdan:
    def __init__(self):
        self.url = 'https://music.163.com/discover/toplist'
        self.headers = {'user-agent': 'Mozilla/5.0'}
        self.proxies = {'https': 'https://' + get_ip()}

    def get_response(self, url):
        while True:
            try:
                response = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=10)
                if response.status_code == 200:
                    print(f'{url} --- {response}', end=' --- ')
                    return response
                else:
                    self.proxies = {'https': 'https://' + get_ip()}
                    print(f'IP更换为{self.proxies}')
            except:
                self.proxies = {'https': 'https://' + get_ip()}
                print(f'IP更换为{self.proxies}')

    def get_music_list_id(self, url):
        # 获取榜单id
        html = etree.HTML(self.get_response(url).text)
        music_list_id = html.xpath('//ul[@class="f-cb"][1]//li/@data-res-id')
        for id in music_list_id:
            self.get_music_id(id)

    def get_music_id(self, music_list_id):
        '''
        获取到本歌单内所有歌曲的id
        :param music_list_id: 歌单ID
        :return:
        '''
        music_list_url = f'https://music.163.com/discover/toplist?id={music_list_id}'
        html = etree.HTML(self.get_response(music_list_url).text)
        music_id = html.xpath('//ul[@class="f-hide"]//li/a/@href')
        for i in range(len(music_id)):
            id = re.sub('\D', '', music_id[i])
            get_info(id, self)

    def main(self):
        self.get_music_list_id(self.url)


class Gedan:
    def __init__(self):
        self.url = 'https://music.163.com/discover/playlist'
        self.headers = {'user-agent': 'Mozilla/5.0', 'referer': 'https://music.163.com/'}
        self.proxies = {'https': 'https://' + get_ip()}

    def get_response(self, url):
        while True:
            try:
                response = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=10)
                if response.status_code == 200:
                    print(f'{url} --- {response}', end=' --- ')
                    return response
                else:
                    self.proxies = {'https': 'https://' + get_ip()}
                    print(f'IP更换为{self.proxies}')
            except:
                self.proxies = {'https': 'https://' + get_ip()}
                print(f'IP更换为{self.proxies}')

    def get_music_list_id(self, url):
        # 获取歌单id
        html = etree.HTML(self.get_response(url).text)
        music_list_id = html.xpath('//div[@class="u-cover u-cover-1"]/a/@href')
        for i in range(5, len(music_list_id)):
            list_id = re.sub('\D', '', music_list_id[i])
            print(f"歌单ID为{list_id} --- {self.proxies} -- {i}")
            self.get_music_id(list_id)

    def get_music_id(self, music_list_id):
        '''
        获取到本歌单内所有歌曲的id
        :param music_list_id: 歌单ID
        :return:
        '''
        music_list_url = f'https://music.163.com/playlist?id={music_list_id}'
        html = etree.HTML(self.get_response(music_list_url).text)
        music_id = html.xpath('//ul[@class="f-hide"]//li/a/@href')
        music_name = html.xpath('//ul[@class="f-hide"]//li/a/text()')
        exist_music = get_exist_music()
        for i in range(len(music_id)):
            if music_name[i] not in exist_music:
                id = re.sub('\D', '', music_id[i])
                print(f'{i+1}/{len(music_id)} --- {id} --- {self.proxies}', end=' --- ')
                get_info(id, self)
                # print(music_name[i])
            else:
                print(f'{datetime.datetime.now()} --- {music_name[i]} --- 抓取过了！ --- {i+1}/{len(music_id)}')

    def main(self):
        print(self.proxies)
        self.get_music_list_id(self.url)


class Geshou:
    def __init__(self):
        self.url = 'https://music.163.com/discover/artist'
        self.headers = {'user-agent': 'Mozilla/5.0', 'referer': 'https://music.163.com/'}
        self.proxies = {'https': 'https://' + get_ip()}

    def get_response(self, url):
        while True:
            try:
                response = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=10)
                if response.status_code == 200:
                    print(f'{url} --- {response}', end=' --- ')
                    return response
                else:
                    self.proxies = {'https': 'https://' + get_ip()}
                    print(f'IP更换为{self.proxies}')
            except:
                self.proxies = {'https': 'https://' + get_ip()}
                print(f'IP更换为{self.proxies}')

    def get_singer_id(self, url):
        js = open('./Music163_Singer.js', 'r', encoding='utf8').read()
        ctx = execjs.compile(js)
        key = ctx.call('start')
        url = 'https://music.163.com/weapi/artist/top?csrf_token='
        data = {
            'params': key['params'],
            'encSecKey': key['encSecKey']
        }
        response = requests.post(url, data=data, headers=self.headers).json()['artists']
        for i in range(len(response)):
            singer_id = response[i]['id']
            self.get_zuopin(singer_id)
            self.get_album(f'https://music.163.com/artist/album?id={singer_id}')
            self.get_singer_info(singer_id)

    def get_zuopin(self, singer_id):
        singer_zp_url = f'https://music.163.com/artist?id={singer_id}'
        response = self.get_response(singer_zp_url).text
        result = json.loads(re.findall(r'<textarea id="song-list-pre-data" style="display:none;">(.*?)</textarea>', response)[0])
        for i in range(len(result)):
            info = {
                'album_name': result[i]['album']['name'],
                'name': result[i]['name'],
                'artists_name': result[i]['artists'][0]['name']
            }
            table.insert_one(info)
            print(info)

    def get_album(self, singer_url):
        singer_album_url = singer_url
        html = etree.HTML(self.get_response(singer_album_url).text)
        album_id = html.xpath('//a[@class="msk"]/@href')
        for i in range(len(album_id)):
            id = re.sub('\D', '', album_id[i])
            album_url = f"https://music.163.com/album?id={id}"
            the_html = etree.HTML(self.get_response(album_url).text)
            try:
                info = {
                    'album_name': the_html.xpath('//h2[@class="f-ff2"]/text()')[0],
                    'singer': the_html.xpath('//a[@class="s-fc7"]//text()')[0],
                    'up_time': the_html.xpath('//p[@class="intr"]/text()')[0],
                    'up_com': the_html.xpath('//p[@class="intr"]/text()')[1].replace('\n', ''),
                    'context': ''.join(the_html.xpath('//div[@id="album-desc-more"]//text()')),
                    'comments': self.get_album_comment(id)
                }
            except:
                info = {
                    'album_name': the_html.xpath('//h2[@class="f-ff2"]/text()')[0],
                    'singer': the_html.xpath('//a[@class="s-fc7"]//text()')[0],
                    'up_time': the_html.xpath('//p[@class="intr"]/text()')[0],
                    'up_com': None,
                    'context': ''.join(the_html.xpath('//div[@id="album-desc-more"]//text()')),
                    'comments': self.get_album_comment(id)
                }
            print(info)
            table_album.insert_one(info)
        next_url = html.xpath('//a[@class="zbtn znxt"]/@href')
        if next_url:
            self.get_album('https://music.163.com' + next_url[0])

    def get_album_comment(self, album_id):
        comment = []
        js = open('./Music163_Album.js', 'r', encoding='utf8').read()
        ctx = execjs.compile(js)
        key = ctx.call('start', album_id)
        url = f'https://music.163.com/weapi/v1/resource/comments/R_AL_3_{album_id}?csrf_token='
        data = {
            'params': key['params'],
            'encSecKey': key['encSecKey']
        }
        response = requests.post(url, headers=self.headers, data=data).json()['hotComments']
        for i in range(len(response)):
            info = {
                'avatarUrl': response[i]['user']['avatarUrl'],
                'nickname': response[i]['user']['nickname'],
                'content': response[i]['content'],
                'likedCount': response[i]['likedCount'],
                'time': time.strftime("%Y-%m-%d", time.localtime(response[i]['time'] // 1000))
            }
            comment.append(info)
        return comment

    def get_singer_info(self, singer_id):
        url = f'https://music.163.com/artist/desc?id={singer_id}'
        response = self.get_response(url).text
        html = etree.HTML(response)
        singer_name = html.xpath('//h2[@id="artist-name"]/text()')[0]
        result = re.findall(r'<div class="n-artdesc">(.*?)</div>', response, re.S)[0]
        print(singer_name)
        data = {
            'singer_name': singer_name,
            'singer_info': result
        }
        table_singer_info.insert_one(data)

    def main(self):
        self.get_singer_id(self.url)


if __name__ == '__main__':
    os.system('cls')
    client = pymongo.MongoClient('localhost')
    table = client['test']['music163']
    table_album = client['test']['music163_album']
    table_singer_info = client['test']['table_singer_info']
    # bd = Bnagdan()
    # bd.main()
    gd = Gedan()
    gd.main()
    # gs = Geshou()
    # gs.main()


