import scrapy
from scrapy import Spider
from scrapy.http import Request
import re
import datetime
from lxml import etree
import time
from datetime import datetime,timedelta
from weibo.items import TweetItem
from .utils import extract_weibo_content,extract_comment_content
import requests
from scrapy.utils.project import get_project_settings
import collections


class SearchSpider(scrapy.Spider):
    #print('aaaaaaaaaa')
    name = 'search'
    allowed_domains = ["weibo.cn"]
    start_urls = ['http://weibo.cn']
    base_url='https://weibo.cn'
    setting=get_project_settings()
    headers=setting.get("DEFAULT_REQUEST_HEADERS")
    lists=[]

    

    def start_requests(self):
        
        print('start_requests...')
        def init_url_by_keyword():

            keywords=['KEYWORD']
           
            date_start=datetime.strptime("2019-04-26",'%Y-%m-%d')
            date_end=datetime.strptime("2020-12-01",'%Y-%m-%d')
            time_spread=timedelta(days=1)
            urls=[]
            url_format="https://weibo.cn/search/mblog?hideSearchFrame=&keyword={}" \
                        "&advancedfilter=1&starttime={}&endtime={}&sort=time&page=1"
            while date_start < date_end :
                next_time=date_start+time_spread
                urls.extend(
                    [url_format.format(keyword,date_start.strftime("%Y%m%d"),next_time.strftime("%Y%m%d")) for keyword in keywords]

                )
                date_start=next_time
            return urls,keywords

        urls,keywords=init_url_by_keyword()

        for url in urls:
            yield Request(url,callback=self.parse,meta={'keywords':keywords})


    def parse(self,response):
        print('parse...')
        keywords=response.meta['keywords']
        time.sleep(3)
        if response.url.endswith('page=1'):
            all_page=re.search(r'/>&nbsp;1/(\d+)页</div>',response.text)
            if all_page:
                all_page=all_page.group(1)
                all_page=int(all_page)

                for page_num in range(2,all_page+1):
                    page_url=response.url.replace('page=1','page={}'.format(page_num))
                    yield Request(page_url,self.parse,dont_filter=True,meta=response.meta)
        tree_node=etree.HTML(response.body)
        tweet_nodes=tree_node.xpath('//div[@class="c" and @id]')
        
        for tweet_node in tweet_nodes:
            try:
                item=TweetItem()
                item['keywords']=keywords
                all_content_link=tweet_node.xpath('.//a[text()="全文" and contains(@href,"ckAll=1")]')
                if all_content_link:
                    all_content_url=self.base_url+all_content_link[0].xpath('./@href')[0]
                    yield Request(all_content_url,callback=self.parse_all_content,meta={'item':item},priority=1)
                else:
                    tweet_html = etree.tostring(tweet_node, encoding='unicode')
                    item['content'] = extract_weibo_content(tweet_html)
                    # yield item
                comment_nums = tweet_node.xpath('.//a[contains(text(),"评论[") and not(contains(text(),"原文"))]/text()')[-1]
                comment_num = int(re.search('\d+',comment_nums).group())
                attitude_nums=tweet_node.xpath('.//a[contains(text(),"转发[")]/text()')[-1]
                attitude_num = int(re.search('\d+',attitude_nums).group())
                
               
                
                if comment_num > 0:
                   
                    comment_url= tweet_node.xpath('.//a[@class="cc" and not(contains(text(),"原文"))]/@href')
                    comment_url=''.join(comment_url)
                    
                    if comment_url:
                        
                        time.sleep(5)
                        
                        comment_url=comment_url.replace('#cmtfrm','&page=1')
                        yield Request(comment_url,callback=self.comment_page,meta={'item':item},dont_filter=True,priority=2)
                        item['comment_num']=(comment_num if comment_num else 0)
                        item['attitude_num']=(attitude_num if attitude_num else 0)
                if not comment_num:
                    item['attitude_num']=(attitude_num if attitude_num else 0)
                    item['comment']=''
                    item['comment_num']=(comment_num if comment_num else 0)
                    yield item
            
                
                
                

            except Exception as e:
                self.logger.error(e)

    def parse_all_content(self,response):
        print('parse_all_content...')
        tree_node=etree.HTML(response.body)
        item=response.meta['item']
        content_node=tree_node.xpath('//*[@id="M_"]/div[1]')[0]
        tweet_html=etree.tostring(content_node,encoding='utf-8')
        
        item['content']=extract_weibo_content(tweet_html)
        yield item

    def comment_page(self,response):
        print('comment_page...')
        
        if  response.url.endswith('page=1'):
            comment_page_num=re.search(r'/>&nbsp;1/(\d+)页</div>',response.text)
            if comment_page_num:
                yield Request(response.url,callback=self.multi_commit,meta=response.meta,priority=4)
                    
            else:
                yield Request(response.url,callback=self.single_commit,meta=response.meta,priority=4)      

    def single_commit(self,response):
        page_node=etree.HTML(response.body)
        item=response.meta['item']
        comment_node=page_node.xpath('//div[@class="c" and contains(@id,"_")]/span[1]/text()')
        print(comment_node)
        item['comment']=comment_node
        yield item

    def multi_commit(self,response):
        try:
            item=response.meta['item']
            page_node=etree.HTML(response.body)
            comment_nodes=page_node.xpath('//div[@class="c" and contains(@id,"_")]/span[1]/text()')
            self.lists.append(comment_nodes)
            
           
            
            
            current_page_num=re.search(r'/>&nbsp;(\d+)/(\d+)页</div>',response.text)
            
            if(current_page_num):
                comment_page_num=current_page_num.group(2)
                current_page_num=current_page_num.group(1)
                print(current_page_num)
                print(comment_page_num)
                current_page_num=int(current_page_num)
                comment_page_num=int(comment_page_num)
                if current_page_num<comment_page_num:
                    url_nexts=page_node.xpath('//*[@id="pagelist"]/form/div/a[1]/@href')
                    url_nexts=''.join(url_nexts)
                    url_next='https://weibo.cn'+url_nexts
                    print(url_next)
                    yield Request(url_next,callback=self.multi_commit,meta={'item':item},priority=5)
                if current_page_num==comment_page_num:
                    item['comment']=self.lists
                    yield item
                    self.lists=[]
                    pass
        except Exception as e:
            self.logger.error(e)

        
        
    
        


    
        
