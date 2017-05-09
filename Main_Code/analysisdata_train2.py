# -*- coding: utf-8 -*-

import os
import re
import random
os.chdir('/Users/apple/Desktop/GoldSentAnalysis/News_Categorization')
import datetime
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn import svm
from NewsSent import News #从外部导入写好的情绪判别类
import matplotlib.pyplot as plt
from sklearn.cross_validation import train_test_split

def usere(regex, content):
    pattern = re.compile(regex)
    content = re.findall(pattern, content)
    return content

def genvar(content, dictionary):
    wordslist = News(content).cut()
    emptydict = dictionary
    retvardict = dictionary
    var = list(set(list(dictionary.keys())).intersection(set(wordslist)))
    if var == []:
        return emptydict
    for i in var:
        retvardict[i] = [1]
    return retvardict

def get_possentnum(self): #groupby时寻找积极情绪
    count = 0
    for i in self.values:
        if i == 1:
            count += 1
    return count

def get_negsentnum(self):#groupby时寻找消极情绪
    count = 0
    for i in self.values:
        if i == -1:
            count += 1
    return count

def get_neusentnum(self):#groupby时寻找中性情绪
    count = 0
    for i in self.values:
        if i == 0:
            count += 1
    return count

def join_news(self):
    newslist = []
    for i in self.values:
        newslist.append(i)
    joinnews = ''.join(newslist)
    return joinnews

goldnews = pd.read_csv('analysisdata.csv', encoding = 'gbk')
#新闻数据处理
goldnews['date'] = list(map(lambda x : int(x), goldnews['date']))
goldnews['title'] = list(map(lambda x : News(x), goldnews['title'])) #将黄金新闻标题转化为新闻类
goldnews['content'] = list(map(lambda x : x.content, goldnews['title'])) #新建一列记录新闻标题情绪内容
goldnews['date'] = list(map(lambda x : int(x), goldnews['date'])) #将日期转换为整数

#收益率数据处理
golddata = pd.read_csv('goldetf.csv', encoding = 'gbk') #读取黄金ETF行情数据
colnames = ['date', 'open', 'high', 'low', 'close', 'turnover', 'volume'] #更改列名称，方便处理
golddata.columns = colnames
golddata['date'] = list(map(lambda x : int(datetime.datetime.strptime(x, '%Y/%m/%d').strftime('%Y%m%d')), golddata['date'])) #将日期转换为整数
fivedaysreturnlist = [np.nan] * len(golddata)
for i in range(0, len(golddata)-4):
    fivedaysreturn = golddata['close'].iloc[i+4] / golddata['open'].iloc[i] - 1
    fivedaysreturnlist[i] = fivedaysreturn
golddata['fivedaysreturn'] = fivedaysreturnlist

#新闻数据日期处理
tradedate = list(golddata['date'])
newsdate = list(map(lambda x : int((datetime.datetime.strptime(str(x), '%Y%m%d') + datetime.timedelta(1)).strftime('%Y%m%d')), goldnews['date'])) #将新闻日期后移一天与交易日对齐
goldnews['newsdate'] = newsdate #以下部分按照交易日头尾取新闻
goldnews = goldnews[goldnews['newsdate'] >= min(tradedate)]
goldnews = goldnews[goldnews['newsdate'] <= max(tradedate)]
newsdate = list(goldnews['newsdate'])
newsdatelist = []
for i in newsdate: #如果新闻当天不是交易日，将新闻日期移动到交易日
    if i in tradedate:
        newsdatelist.append(i)
    else:
        while 1:
            i = int((datetime.datetime.strptime(str(i), '%Y%m%d') + datetime.timedelta(1)).strftime('%Y%m%d'))
            if i in tradedate:
                newsdatelist.append(i)
                break
goldnews['newsdate'] = newsdatelist

#
grouped = goldnews.groupby('newsdate')
joinnews = grouped.content.agg(join_news)
joinnewsdf = pd.DataFrame({'date':list(joinnews.index), 'joinnews':list(joinnews.values)})
golddata = pd.merge(golddata, joinnewsdf)
golddata = golddata.dropna()

###################手动生成变量方式    
sentdict = pd.read_csv('sentdict.csv', encoding = 'gbk')
highfreqwords = list(sentdict['words'])
vardict = dict(zip(highfreqwords, [[0]]*len(highfreqwords)))
vardict2 = dict(zip(highfreqwords, [[]]*len(highfreqwords)))
vardf2 = pd.DataFrame(vardict2) #生成变量表

for idx, i in enumerate(golddata['joinnews']):
    vardict = dict(zip(highfreqwords, [[0]]*len(highfreqwords)))
    var = genvar(i, vardict)
    slicedf = pd.DataFrame(var)
    vardf2 = pd.concat([vardf2, slicedf])
    print (idx)

###################
Xtrain = vardf2.values
ytrain = golddata['fivedaysreturn'].values
ytrainlist = []
for i in ytrain:
    if i >= 0:
        ytrainlist.append(1)
    else:
        ytrainlist.append(0)
ytrain = np.array(ytrainlist)

X_train, X_valid, y_train, y_valid = train_test_split(Xtrain, ytrain, test_size = 0.7, random_state = 12)
params = {'colsample_bytree': 0.6, 'silent': 0, 'eval_metric': 'error',
    'nthread': 6, 'min_child_weight': 1, 'n_estimators': 205.0,
        'subsample': 0.7, 'eta': 0.005,
            'objective': 'reg:logistic',
                'max_depth': 12.0, 'gamma': 1, 'booster': 'gbtree'}

num_boost_round = 10000

#将数据转换为DMatrix
dtrain = xgb.DMatrix(X_train, y_train, missing=-999)
dvalid = xgb.DMatrix(X_valid, y_valid, missing=-999)
watchlist = [(dtrain, 'train'), (dvalid, 'eval')]

#训练
gbm = xgb.train(params, dtrain, num_boost_round,\
                evals = watchlist, early_stopping_rounds = 1000, verbose_eval = True)


###########机器学习判断涨跌
Xtrain = vardf2.iloc[0:-200]
ytrain = golddata['zhangdie'].iloc[0:-200]
Xtest = vardf2.iloc[-200:]
ytest = golddata['zhangdie'].iloc[-200:]
Xtrain = Xtrain.values
ytrain = ytrain.values
Xtest = Xtest.values
ytest = ytest.values
X_train, X_test, y_train, y_test = train_test_split(Xtrain, ytrain, test_size=0.4, random_state=0)
clf = svm.SVC(C=3.0, cache_size=200, class_weight=None, coef0=0.0,
    decision_function_shape=None, degree=1, gamma='auto', kernel='rbf',
    max_iter=-1, probability=True, random_state=2, shrinking=True,
    tol=0.001, verbose=False).fit(X_train, y_train)
clf.score(X_test, y_test)
a = clf.predict(Xtest)
b = ytest
print (sum(a==b)/len(b))

