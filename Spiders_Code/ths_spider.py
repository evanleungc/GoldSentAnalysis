# -*- coding: utf-8 -*-
# Author: Kanghua Liang @PKU
import re
import os
import random
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
    newsdf = pd.read_csv('thsdata.csv', encoding = 'gbk')
    print ('existed')
except:
    newsdf = pd.DataFrame({'date':[], 'time':[], 'title':[]}) #预定义一个数据表，用来更新每一页数据并输出，防止数据丢失

iplist = get_ip()[0]

year = 2017
state = 0
for page in range(1, 609): #对每一页进行循环新闻抓取
    head = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'} #伪造浏览器头
    if page % 50 == 0 or page == 1: #每抓取50页更换一次IP
        ip = random.sample(iplist, 1)
        proxy = {'proxies':ip}
        print ('更换IP')
    
    url = 'http://invest.10jqka.com.cn/hj_list/index_%s.shtml' %page #新浪财经黄金新闻每一页链接
    while 1:
        try:
            htmltext = requests.get(url, headers = head, proxies = proxy, timeout = 10).text #获得页面html文本
            break #不断更换IP直到请求成功
        except:
            iplist = get_ip()[0]
            ip = random.sample(iplist, 1) #请求超时更换IP
            proxy = {'proxies':ip}
            print ('请求超时，更换IP')

    titleregex = '<span class="arc-title">[^.]*<a target="_blank" title="(.+?)"' #标题
    titlelist = usere(titleregex, htmltext)

    datelist = []
    timelist = []
    timeregex = '<a target="_blank" title=".*"[^.]*?href=".*">.+?</a>[^.]*?<span>(.+?)</span>'
    tmptimelist = usere(timeregex, htmltext)
    for t in tmptimelist: #将年月和具体时间分开
        splitregex = '\d+'
        splitlist = usere(splitregex, t)
        if int(splitlist[0]) == 12 and state == 0:
            year -= 1
            state = 1
        if int(splitlist[0]) != 12 and state == 1:
            state = 0
        tmpdate = int(str(year) + splitlist[0] + splitlist[1]) #连接年月日，并转换为数字
        tmptime = splitlist[2] + ':' + splitlist[3] #连接当日具体时间
        print (tmpdate)
        datelist.append(tmpdate)
        timelist.append(tmptime)

    tmpdf = pd.DataFrame({'date':datelist, 'time':timelist, 'title':titlelist}) #每完成一页，生成一个临时数据表
    newsdf = pd.concat([newsdf, tmpdf]) #实时更新新闻表，并输出，防止数据丢失
    newsdf.to_csv('/Users/apple/Desktop/gold/thsdata.csv', index = False, encoding = 'gbk')

    print ('成功更新第%s页' %page) #实时输出更新信息




