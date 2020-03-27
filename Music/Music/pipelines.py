# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from .items import MusicItem
import pymysql


class MusicPipeline(object):
    def __init__(self):
        # 连接数据库
        self.con = pymysql.connect(host='localhost', db='demo', user='root', passwd='root', charset='utf8')
        self.cursor = self.con.cursor()

    def process_item(self, item, spider):
        # insert_music = "insert into music(music_name, singer_name, music_id) values ('%s', '%s', '%s')" % \
        #                (item['music_name'], item['singer_name'], item['music_id'])
        # try:
        #     self.cursor.execute(insert_music)
        #     self.con.commit()
        # except Exception as e:
        #     print('错误是---------->', e)
        insert_music = "insert into music(music_name, singer_name, user, comment, like_count, music_id) " \
                       "value ('%s', '%s', '%s', '%s', '%s', '%s')" % \
                       (item['music_name'], item['singer_name'], item['user'], item['comment'], item['like_count'], item['music_id'])
        try:
            self.cursor.execute(insert_music)
            self.con.commit()
        except Exception as e:
            print('错误是---------------->', e)
        return item

    def close(self, spider):
        self.con.close()