# -*- coding: utf-8 -*-
#舆情数据分类为分析师点评、行情播报、新闻三类

import os
os.chdir('/Users/apple/Desktop/GoldSentAnalysis/News_Categorization')
import pandas as pd
golddata = pd.read_csv('golddata.csv', encoding = 'gbk')
locindex = []
for idx, i in enumerate(goldnews['title']):
    if u'\u91d1' in i and u'\u4e0a\u6d77\u91d1\u4ea4\u6240' not in i and u'\u91d1\u878d' not in i and u'\u7eb8\u9ec4\u91d1' not in i and u'\u57fa\u91d1' not in i and u'\u8d44\u91d1' not in i and u'\u94af\u91d1' not in i and u'\u91d1\u9053' not in i and u'[\u77ed\u8baf]' not in i and u'[\u5feb\u8baf]' not in i and u'\uff1a' in i:
        locindex.append(idx)
analysisdata = goldnews.iloc[locindex]
analysisdata.to_csv('analysisdata.csv', index = False, encoding = 'gbk')

locindex = []
for idx, i in enumerate(goldnews['title']):
    if u'\u91d1' in i and u'\u91d1\u878d' not in i and u'\u7eb8\u9ec4\u91d1' not in i and u'\u57fa\u91d1' not in i and u'\u8d44\u91d1' not in i and u'\u94af\u91d1' not in i and u'\u91d1\u9053' not in i and (u'\u4e0a\u6d77\u91d1\u4ea4\u6240' in i or u'[\u77ed\u8baf]' in i or u'[\u5feb\u8baf]' in i):
        locindex.append(idx)
hangqingdata = goldnews.iloc[locindex]
hangqingdata.to_csv('hangqingdata.csv', index = False, encoding = 'gbk')

locindex = []
for idx, i in enumerate(goldnews['title']):
    if u'\u91d1' in i and u'\u4e0a\u6d77\u91d1\u4ea4\u6240' not in i and u'\u91d1\u878d' not in i and u'\u7eb8\u9ec4\u91d1' not in i and u'\u57fa\u91d1' not in i and u'\u8d44\u91d1' not in i and u'\u94af\u91d1' not in i and u'\u91d1\u9053' not in i and u'[\u77ed\u8baf]' not in i and u'[\u5feb\u8baf]' not in i and u'\uff1a' not in i:
        locindex.append(idx)
newsdata = goldnews.iloc[locindex]
newsdata.to_csv('newsdata.csv', index = False, encoding = 'gbk')
