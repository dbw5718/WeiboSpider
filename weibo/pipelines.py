# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from scrapy.utils.project import get_project_settings
import csv
import os
import sys
import collections


class WeiboPipeline:
    def open_spider(self,spider):
        print('Begin.....')
    def process_item(self, item, spider):
        print(item)
        keyword=item['keywords']
        keyword=''.join(keyword)
        
        base_dir='结果文件' + os.sep + keyword

        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)
        file_path=base_dir+os.sep+keyword+'.csv'
        if not os.path.isfile(file_path):
            is_first_write=1
        else:
            is_first_write=0
        if item:
            item=collections.OrderedDict(item)
            
            with open(file_path,'a',encoding='utf-8-sig',newline="") as f:
                writer=csv.writer(f)
                if is_first_write:
                    header=['帖子标题','帖子内容','评论内容','评论条数','转载量']
                    writer.writerow(header)
                writer.writerow(['',item['content'],item['comment'],item['comment_num'],item['attitude_num']])
                    
        return item
    
        
    def close_spider(self,spider):
        print('End......')
        pass
        
