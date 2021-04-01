# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TweetItem(scrapy.Item):
    # define the fields for your item here like:
    #weibo=scrapy.Field()
    keywords=scrapy.Field()
    
    content = scrapy.Field()
    comment = scrapy.Field()
    attitude_num=scrapy.Field()
    comment_num=scrapy.Field()
    

    
    
