# -*- coding: utf-8 -*-
"""
Created on Fri May  5 08:35:22 2017

@author: liangkh
"""

from collections import Counter
import pandas as pd
import jieba.analyse
import jieba


#读取停词字典
stopwords = pd.read_csv('stopwords.csv')
stopwords = stopwords['words']
stopwords2 = []
for i in range(len(stopwords)):
    seg_list = jieba.cut(stopwords[i], cut_all = False)
    list1 = ('/'.join(seg_list))
    print (list1)
    a = list1.split('/')
    stopwords2.extend(a)
stopwords = stopwords2

#读取情绪字典
global sentdict
sentdict = pd.read_csv('sentdict.csv', encoding = 'gbk')
sentdict2 = {}
for i, j, k in zip(sentdict.words, sentdict.type, sentdict.strength):
	sentdict2[i] = [j, k]
sentdict = sentdict2

#新闻类
class News(object):

    def __init__(self, content):
        self.content = content
		
    def cut(self, cut_method = False, clean = True, stopwords = stopwords):
        cut_news = jieba.cut(self.content, cut_all = cut_method)
        cut_news = ('/'.join(cut_news))
        cut_news = cut_news.split('/')
        if clean == True:
            cut_news = [i for i in cut_news if i not in stopwords]
        return cut_news
        
    def get_tags(self):
        tags = jieba.analyse.extract_tags(self.content, topK = 5)
        return tags
		
    def get_score(self):
        cut_content = self.cut()
        score = 0
        for i in cut_content:
            try:
                score += sentdict[i][0] * sentdict[i][1]
                print ('get score successfully')
            except:
                continue
        return score
        
    def get_freqlist(self, clean = False):
        freqdict = dict(Counter(self.cut(clean = clean)))
        freqlist = sorted(freqdict.items(), key=lambda d:d[1], reverse = True) 
        return freqlist