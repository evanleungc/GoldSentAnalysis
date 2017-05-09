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
    newsdf = pd.read_csv('analysisdata.csv', encoding = 'gbk')
    print ('existed')
except:
    newsdf = pd.DataFrame({'date':[], 'time':[], 'title':[]}) #预定义一个数据表，用来更新每一页数据并输出，防止数据丢失

iplist = get_ip()[0]

for page in range(1500, 1600): #对每一页进行循环新闻抓取
    head = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'} #伪造浏览器头
    if page % 50 == 0 or page == 1: #每抓取50页更换一次IP
        ip = random.sample(iplist, 1)
        proxy = {'proxies':ip}
        print ('更换IP')
    
    url = 'http://roll.finance.sina.com.cn/finance/gjs/hjzx/index_%s.shtml' %page #新浪财经黄金新闻每一页链接
    while 1:
        try:
            htmltext = requests.get(url, headers = head, proxies = proxy, timeout = 10).text #获得页面html文本
            break #不断更换IP直到请求成功
        except:
            iplist = get_ip()[0]
            ip = random.sample(iplist, 1) #请求超时更换IP
            proxy = {'proxies':ip}
            print ('请求超时，更换IP')

    htmltext = htmltext.encode('latin1').decode('gbk') #网页编码后保留了等价的字节流数据，需latin1编码再gbk解码
    regex1 = '<ul class="list_009">([\s\S]*?)</ul>' #观察网页，发现需两层正则表达式获取文本，此为第一层
    content1 = usere(regex1, htmltext) #对下一层内容使用正则表达式进行文本提取
    
    titlelist = [] #初始化存储标题、日期、时间的列表
    datelist = []
    timelist = []
    for content in content1:
        titleregex = 'target="_blank">(.+?)</a>' #提取标题正则表达式
        timeregex = '<span>\((.+?)\)</span>' #提取时间正则表达式
        tmptitle = usere(titleregex, content) #提取标题并存储
        titlelist.extend(tmptitle)
        tmptimelist = usere(timeregex, content)
        for t in tmptimelist: #将年月和具体时间分开
            splitregex = '\d+'
            splitlist = usere(splitregex, t)
            if len(splitlist) == 4: #如果只提取到4个数字，证明第一个当前年份为2017年，需自动填充
                tmpdate = int('2017' + splitlist[0] + splitlist[1]) #连接年月日，并转换为数字
                tmptime = splitlist[2] + ':' + splitlist[3] #连接当日具体时间
            elif len(splitlist) == 5: #如果提取到5个数据，则已经包含年份信息
                tmpdate = int(splitlist[0] + splitlist[1] + splitlist[2])
                tmptime = splitlist[3] + splitlist[4]
            else:
                print ('日期格式有误，请检查网页结构是否改变') #时间长度不对时返回可能错误信息
            datelist.append(tmpdate) #存储提取好的日期、时间
            timelist.append(tmptime)
    
    tmpdf = pd.DataFrame({'date':datelist, 'time':timelist, 'title':titlelist}) #每完成一页，生成一个临时数据表
    newsdf = pd.concat([newsdf, tmpdf]) #实时更新新闻表，并输出，防止数据丢失
    newsdf.to_csv('/Users/apple/Desktop/gold/analysisdata.csv', index = False, encoding = 'gbk')

    print ('成功更新第%s页' %page) #实时输出更新信息




