# -*- coding: utf-8 -*-
import scrapy
import re
import json
from ..items import MusicItem, DataItem


class MusicSpiderSpider(scrapy.Spider):
    name = 'music_spider'
    # start_urls = ['https://music.163.com/discover/playlist/?order=hot&cat=%E5%85%A8%E9%83%A8&limit=35&offset=0']
    start_urls = []
    for page in range(38):
        start_urls.append('https://music.163.com/discover/playlist/?order=hot&cat=%E5%85%A8%E9%83%A8&limit=35&offset={}'.format(page * 35))

    def parse(self, response):
        music_list_id = response.xpath('//a[@class="msk"]/@href').getall()
        for i in range(len(music_list_id)):
            url = 'https://music.163.com' + str(music_list_id[i])
            yield scrapy.Request(url, callback=self.get_music_id)

    def get_music_id(self, response):
        music_id_list = response.xpath('//ul[@class="f-hide"]/li/a/@href').getall()
        for i in range(len(music_id_list)):
            url = 'https://music.163.com' + str(music_id_list[i])
            id = re.sub('\D', '', music_id_list[i])
            comment_url = 'http://music.163.com/api/v1/resource/comments/R_SO_4_{}?limit=20&offset=0'.format(id)
            yield scrapy.Request(url, callback=self.get_info, meta={'comment_url': comment_url})

    def get_info(self, response):
        comment_url = response.meta['comment_url']
        music_name = response.xpath('//em[@class="f-ff2"]/text()').get()
        singer_name = response.xpath('//p[@class="des s-fc4"][1]/span/@title').get()
        music_item = MusicItem()
        music_item['music_name'] = music_name
        music_item['singer_name'] = singer_name
        # music_item['music_id'] = re.sub('[(music.163.com)(\D)]', '', response.url)
        yield scrapy.Request(comment_url, callback=self.get_comment, meta={'mitem': music_item})

    def get_comment(self, response):
        music_item = response.meta['mitem']
        json_data = json.loads(response.body)
        user = json_data['hotComments'][0]['user']['nickname']
        comment = json_data['hotComments'][0]['content']
        like_count = json_data['hotComments'][0]['likedCount']
        data_item = DataItem()
        data_item['user'] = user
        data_item['comment'] = comment
        data_item['like_count'] = like_count
        data_item['music_id'] = re.findall(r'R_SO_4_(.*?)?limit', response.url)[0]
        data_item['music_name'] = music_item['music_name']
        data_item['singer_name'] = music_item['singer_name']
        yield data_item
