# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MusicItem(scrapy.Item):
    music_name = scrapy.Field()
    singer_name = scrapy.Field()
    pass


class DataItem(scrapy.Item):
    music_name = scrapy.Field()
    singer_name = scrapy.Field()
    user = scrapy.Field()
    comment = scrapy.Field()
    like_count = scrapy.Field()
    music_id = scrapy.Field()
    pass
