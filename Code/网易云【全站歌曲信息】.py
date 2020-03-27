# -*- coding: utf-8 -*-
# @Time    : 2020/3/18 16:45
# @Author  : Monkey
# @File    : 网易云【全站歌曲信息】.py
# @Software: PyCharm
# @Demand  : 
import requests
from lxml import etree
import re
import os
import csv
from threading import Thread
import numpy as np
import pandas as pd


def get_html(url):
    headers = {'user-agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers).text
    html = etree.HTML(r)
    return html


def get_json(url):
    headers = {'user-agent': 'Mozilla/5.0'}
    j = requests.get(url, headers=headers).json()
    return j


# 获取歌单的id
def get_url_list_id(html):
    id = html.xpath('//a[@class="msk"]/@href')
    for i in range(len(id)):
        id[i] = re.sub('\D', '', id[i])
    return id


# 获取歌单内音乐的id
def get_music_id(music_list_id):
    html = get_html(f'https://music.163.com/playlist?id={music_list_id}')
    id = html.xpath('//ul[@class="f-hide"]//li//a/@href')
    for i in range(len(id)):
        id[i] = re.sub('\D', '', id[i])
    return id


# 获取歌曲信息
def get_music_info(id):
    html = get_html(f'https://music.163.com/song?id={id}')
    c_data = get_comment_info(id)
    data = {
        'music_name': html.xpath('//em[@class="f-ff2"]/text()')[0],
        'singer': html.xpath('//p[@class="des s-fc4"][1]/span/@title')[0],
        'music_id': id,
        'comment': c_data['comment'],
        'comment_user': c_data['comment_user'],
        'comment_like_count': c_data['comment_like_count'],
        'comment_count': c_data['comment_count']
    }
    return data


# 获取热评的信息
def get_comment_info(id):
    comment_json = get_json(f'http://music.163.com/api/v1/resource/comments/R_SO_4_{id}?limit=20&offset=0')
    try:
        # 如果有热评的话
        if len(comment_json['hotComments']) != 0:
            comment_data = {
                'comment': comment_json['hotComments'][0]['content'],
                'comment_user': comment_json['hotComments'][0]['user']['nickname'],
                'comment_like_count': comment_json['hotComments'][0]['likedCount'],
                'comment_count': comment_json['total']
            }
        else:
            comment_data = {
                'comment': comment_json['comments'][0]['content'],
                'comment_user': comment_json['comments'][0]['user']['nickname'],
                'comment_like_count': comment_json['comments'][0]['likedCount'],
                'comment_count': comment_json['total']
            }
    except:
        comment_data = {
            'comment': '',
            'comment_user': '',
            'comment_like_count': '',
            'comment_count': ''
        }
    return comment_data


# 将数据存储到本地
def save(data):
    path = 'f://SpiderData//网易云音乐【全站】.csv'
    # # 如果文件不存在，则先写入表头
    # if not os.path.isfile(path):
    #     with open(path, 'w', newline='', encoding='ANSI') as f:
    #         write = csv.DictWriter(f, fieldnames=list(data.keys()))
    #         # 写表头
    #         write.writeheader()
    # # 写入数据
    # with open(path, 'a', newline='', encoding='ANSI') as f:
    #     write = csv.DictWriter(f, fieldnames=list(data.keys()))
    #     write.writerow(data)

    try:
        d = pd.DataFrame(data, index=[0])
        if os.path.exists(path):
            d.to_csv(path, encoding='ANSI', mode='a', header=False, index=False)
        else:
            d.to_csv(path, encoding='ANSI', mode='a', index=False)
    except:
        d.to_csv('f://SpiderData//网易云音乐-Error.csv', encoding='utf8', mode='a', index=False, header=False)


def main(start, end):
    for i in range(start, end):
        # 获取到当前歌单中所有歌曲的id
        music_id = get_music_id(url_list_id[i])
        # 遍历id，获取到每一首音乐的信息
        for j in range(len(music_id)):
            music_info = get_music_info(music_id[j])
            # 将获取到的信息存储到本地
            save(music_info)
            csv_reader = csv.reader(open('f://SpiderData//网易云音乐【全站】.csv', encoding='ANSI'))
            print('\r', f'1-{i+1}-{j+1}/{len(music_id)}\t\t{np.array(len(list(csv_reader)))}', end='', flush=True)


if __name__ == '__main__':
    data_count = 0
    for page in range(37):
        url = f'https://music.163.com/discover/playlist/?order=hot&cat=%E5%85%A8%E9%83%A8&limit=35&offset={page*35}'
        html = get_html(url)
        # 获取到当前页面的歌单id
        url_list_id = get_url_list_id(html)

        # 普通方法
        for i in range(len(url_list_id)):
            # 获取到当前歌单中所有歌曲的id
            music_id = get_music_id(url_list_id[i])
            # 遍历id，获取到每一首音乐的信息
            for j in range(len(music_id)):
                music_info = get_music_info(music_id[j])
                # 将获取到的信息存储到本地
                save(music_info)
                data_count += 1
                print('\r', f'页码：{page+1}\t歌单：{i+1}\t歌曲：{j+1}/{len(music_id)}\t总数：{data_count}', end='', flush=True)

    # # 多线程方法
    # thread = []
    # # 每页35个歌单，7个线程
    # for i in range(7):
    #     thread.append(Thread(target=main, args=(i * 5, (i + 1) * 5)))
    # for t in thread:
    #     t.start()
    # for t in thread:
    #     t.join()
