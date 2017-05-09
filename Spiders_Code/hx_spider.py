# -*- coding: utf-8 -*-
# Author: Kanghua Liang @PKU
import re
import os
import random
import datetime
import requests
import pandas as pd

os.chdir('/Users/apple/Desktop/gold')#切换到当前目录

def usere(regex, getcontent): #定义使用正则表达式的函数
    pattern = re.compile(regex)
    content = re.findall(pattern, getcontent)
    return content

def get_ip(): #使用爬虫从外部网站获取IP，如果被反爬虫，更换IP
    head = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'}
    ipurl = 'http://www.xicidaili.com/nt/'
    iphtml = requests.get(ipurl, headers = head, timeout = 60).content
    regex1 = 'alt="Cn" /></td>[^.]*<td>(.+?)</td>'
    regex2 = 'alt="Cn" /></td>[^.]*<td>.*?</td>[^.]*<td>(.+?)</td>[^.]*<td>[^.]*<a href'
    iplist = usere(regex1, iphtml)
    portlist = usere(regex2, iphtml)
    return (iplist, portlist)

#先尝试从外部读入新闻更新数据，如果读取不到，创建新的数据表
try:
    newsdf = pd.read_csv('hxdata.csv', encoding = 'gbk')
    print ('existed')
except:
    newsdf = pd.DataFrame({'date':[], 'time':[], 'title':[]}) #预定义一个数据表，用来更新每一页数据并输出，防止数据丢失

iplist = get_ip()[0]

state = 0
for page in range(1, 2983): #对每一页进行循环新闻抓取
    head = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'} #伪造浏览器头
    if page % 50 == 0 or page == 1: #每抓取50页更换一次IP
        ip = random.sample(iplist, 1)
        proxy = {'proxies':ip}
        print ('更换IP')
    
    url = 'http://open.tool.hexun.com/MongodbNewsService/newsListPageByJson.jsp?id=101790947&s=30&cp=%s&priority=0&callback=hx_json31494059443141' %page #新浪财经黄金新闻每一页链接
    while 1:
        try:
            htmltext = requests.get(url, headers = head, proxies = proxy, timeout = 10).text #获得页面html文本
            break #不断更换IP直到请求成功
        except:
            #iplist = get_ip()[0]
            ip = random.sample(iplist, 1) #请求超时更换IP
            proxy = {'proxies':ip}
            print ('请求超时，更换IP')

    titleregex = '"title":"(.+?)"' #标题
    titlelist = usere(titleregex, htmltext)

    timeregex = 'entityurl":"http://.*?/(.+?)/'
    datelist = usere(timeregex, htmltext)
    datelist = [int(datetime.datetime.strptime(i, '%Y-%m-%d').strftime('%Y%m%d')) for i in datelist]
    timelist = [u'00:00'] * len(datelist)

    tmpdf = pd.DataFrame({'date':datelist, 'time':timelist, 'title':titlelist}) #每完成一页，生成一个临时数据表
    newsdf = pd.concat([newsdf, tmpdf]) #实时更新新闻表，并输出，防止数据丢失
    #newsdf.to_csv('/Users/apple/Desktop/gold/hxdata.csv', index = False, encoding = 'gbk')

    print ('成功更新第%s页' %page) #实时输出更新信息




