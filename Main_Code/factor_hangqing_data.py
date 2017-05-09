import os
os.chdir('/Users/apple/Desktop/GoldSentAnalysis/News_Categorization')
import datetime
import numpy as np
import pandas as pd
from NewsSent import News #从外部导入写好的情绪判别类
import matplotlib.pyplot as plt

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

def get_frac(scorelist, fracnum):#因子分组计算收益
    rangelist = np.linspace(0,100,fracnum + 1)
    rangelist = rangelist[1:]
    fracvaluelist = []
    for i in rangelist:
        fracvalue = np.percentile(scorelist, i)
        fracvaluelist.append(fracvalue)
    return fracvaluelist


def factor_test(dataset, factor, groupnum):#因子分组检测
    fracvaluelist = get_frac(dataset[factor], groupnum)
    dataset['group'] = [0]*len(golddata)
    j = 0
    for idx, i in enumerate(fracvaluelist):
        indexlist = dataset[factor][dataset[factor] <= i][dataset[factor] >= j].index
        dataset['group'].loc[list(indexlist)] = idx + 1
        j = i
    testresult = dataset.groupby('group').fivedaysreturn.mean()
    return testresult

goldnews = pd.read_csv('hangqingdata.csv', encoding = 'gbk')
#新闻数据处理
goldnews['date'] = list(map(lambda x : int(x), goldnews['date']))
goldnews['title'] = list(map(lambda x : News(x), goldnews['title'])) #将黄金新闻标题转化为新闻类
goldnews['score'] = list(map(lambda x : x.get_score(), goldnews['title'])) #新建一列记录新闻标题情绪打分
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

#新闻数据情绪类型处理，生成5种情绪指标
sentimenttypelist = []
for i in goldnews['score']:
    if i >= 1:
        sentimenttypelist.append(1)
    elif i <= -1:
        sentimenttypelist.append(-1)
    else:
        sentimenttypelist.append(0)
goldnews['sent'] = sentimenttypelist
grouped = goldnews.groupby('newsdate')
possent = grouped.sent.agg(get_possentnum) / grouped.sent.count()
possentdf = pd.DataFrame({'date':list(possent.index), 'possent':list(possent.values)})
negsent = grouped.sent.agg(get_negsentnum) / grouped.sent.count()
negsentdf = pd.DataFrame({'date':list(negsent.index), 'negsent':list(negsent.values)})
neusent = grouped.sent.agg(get_neusentnum) / grouped.sent.count()
neusentdf = pd.DataFrame({'date':list(neusent.index), 'neusent':list(neusent.values)})

posfrac = grouped.sent.agg(get_possentnum) / grouped.sent.agg(get_negsentnum)
posfracdf = pd.DataFrame({'date':list(posfrac.index), 'posfrac':list(posfrac.values)})
negfrac =grouped.sent.agg(get_negsentnum) / grouped.sent.agg(get_possentnum)
negfracdf = pd.DataFrame({'date':list(negfrac.index), 'negfrac':list(negfrac.values)})
golddata = pd.merge(golddata, possentdf)
golddata = pd.merge(golddata, negsentdf)
golddata = pd.merge(golddata, neusentdf)
golddata = pd.merge(golddata, posfracdf)
golddata = pd.merge(golddata, negfracdf)

possentlist = list(golddata['possent'])
negsentlist = list(golddata['negsent'])
neusentlist = list(golddata['neusent'])
possentprev1 = [np.nan]
negsentprev1 = [np.nan]
neusentprev1 = [np.nan]
possentprev1.extend(possentlist[0:-1])
negsentprev1.extend(negsentlist[0:-1])
neusentprev1.extend(neusentlist[0:-1])
possentprev2 = [np.nan] * 2
negsentprev2 = [np.nan] * 2
neusentprev2 = [np.nan] * 2
possentprev2.extend(possentlist[0:-2])
negsentprev2.extend(negsentlist[0:-2])
neusentprev2.extend(neusentlist[0:-2])
golddata['possentprev1'] = possentprev1
golddata['negsentprev1'] = negsentprev1
golddata['neusentprev1'] = neusentprev1
golddata['possentprev2'] = possentprev2
golddata['negsentprev2'] = negsentprev2
golddata['neusentprev2'] = neusentprev2

newscount = list(grouped.score.count().values)
golddata['newscount'] = newscount

#因子单调性检测
golddata = golddata.dropna()
sentimentfactor = ['possent', 'negsent', 'neusent', 'posfrac', 'negfrac', 'newscount']
picture = plt.figure
for i in sentimentfactor:
    plt.plot(factor_test(golddata, i, 10))
plt.xlabel('groups')
plt.ylabel('five days return')
plt.title('Factor Analysis For Hangqing Data')
plt.legend(sentimentfactor)
