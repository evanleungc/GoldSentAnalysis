import os
os.chdir('/Users/apple/Desktop/GoldSentAnalysis/News_Categorization')
import datetime
import numpy as np
import pandas as pd
from NewsSent import News #从外部导入写好的情绪判别类
import matplotlib.pyplot as plt


goldnews1 = pd.read_csv('analysisdata.csv', encoding = 'gbk') #读取黄金新闻
goldnews2 = pd.read_csv('newsdata.csv', encoding = 'gbk')
goldnews3 = pd.read_csv('hangqingdata.csv', encoding = 'gbk')
goldnews = pd.concat([goldnews1, goldnews2, goldnews3])
locindex = []
for idx, i in enumerate(goldnews['title']):
    if u'\u91d1' in i and u'\u4e0a\u6d77\u91d1\u4ea4\u6240' not in i and u'\u91d1\u878d' not in i and u'\u7eb8\u9ec4\u91d1' not in i and u'\u57fa\u91d1' not in i and u'\u8d44\u91d1' not in i and u'\u94af\u91d1' not in i and u'\u91d1\u9053' not in i:
        locindex.append(idx)
goldnews = goldnews.iloc[locindex]
goldnews['title'] = list(map(lambda x : News(x), goldnews['title'])) #将黄金新闻标题转化为新闻类
goldnews['content'] = list(map(lambda x : x.content, goldnews['title'])) #新建一列记录新闻标题情绪内容
goldnews['date'] = list(map(lambda x : int(x), goldnews['date'])) #将日期转换为整数

golddata = pd.read_csv('goldetf.csv', encoding = 'gbk') #读取黄金ETF行情数据
colnames = ['date', 'open', 'high', 'low', 'close', 'turnover', 'volume'] #更改列名称，方便处理
golddata.columns = colnames
golddata['date'] = list(map(lambda x : int(datetime.datetime.strptime(x, '%Y/%m/%d').strftime('%Y%m%d')), golddata['date'])) #将日期转换为整数

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

score2list = []
newsnumlist = []
for idx, i in enumerate(golddata['date']):
    contentlist = []
    content = list(goldnews['content'][goldnews['newsdate'] == i])
    if content == []:
        score2list.append(0)
        newsnumlist.append(0)
        continue
    content = list(np.unique(content))
    newsnumlist.append(len(content))
    linkcontent = ','.join(content)
    score2list.append(News(linkcontent).get_score() / np.double(len(content)))
    print (idx)
golddata['score2'] = score2list
golddata['newsnum'] = newsnumlist


#策略
equity = 1
equitylist = []
golddata2 = golddata.iloc[:]

tradelist = [0]*len(golddata2)
state = 0
for i in range(1, len(golddata2)):
    if (golddata2['score2'].iloc[i] / golddata2['score2'].iloc[i-1] <= -3 and golddata2['score2'].iloc[i] / golddata2['score2'].iloc[i-1] != -np.inf and state == 0 and golddata2['score2'].iloc[i] > 0.1) or (golddata2['score2'].iloc[i] > 0.2 and state == 0):
        tradelist[i] = 1
        state = 1
    if state == 1:
        if golddata2['score2'].iloc[i] < -0.1:
            tradelist[i] = 2
            state = 0

    if (golddata2['score2'].iloc[i] / golddata2['score2'].iloc[i-1] <= -3 and golddata2['score2'].iloc[i] / golddata2['score2'].iloc[i-1] != -np.inf and state == 0 and golddata2['score2'].iloc[i] < -0.1) or (golddata2['score2'].iloc[i] < -0.2 and state == 0):
        tradelist[i] = -1
        state = -1
    if state == -1:
        if golddata2['score2'].iloc[i] > 0.1:
            tradelist[i] = -2
            state = 0


state = 0
lags = 0
longdatelist = []
clearlongdatelist = []
shortdatelist = []
clearshortdatelist = []
for idx, signal in enumerate(tradelist):
    if state == 0 and signal == 1:
        longprice = golddata2['open'].iloc[idx+lags]
        state = 1
        longdatelist.append(golddata2['date'].iloc[idx+lags])
    elif state == 1 and signal == 2:
        clearlongprice = golddata2['open'].iloc[idx+lags]
        clearlongdatelist.append(golddata2['date'].iloc[idx+lags])
        state = 0
        equity = equity * clearlongprice / longprice
    #equitylist.append(equity)
    if state == 0 and signal == -1:
        shortprice = golddata2['open'].iloc[idx+lags]
        state = -1
        shortdatelist.append(golddata2['date'].iloc[idx+lags])
    elif state == -1 and signal == -2:
        clearshortprice = golddata2['open'].iloc[idx+lags]
        state = 0
        equity = equity * shortprice / clearshortprice
    #equitylist.append(equity)
    if state == 0:
        equitylist.append(equity)
        clearshortdatelist.append(golddata2['date'].iloc[idx+lags])
    if state == 1:
        try:
            equity = equity * golddata2['open'].iloc[idx+lags] / golddata2['open'].iloc[idx+lags-1]
            equitylist.append(equity)
        except:
            break
    if state == -1:
        try:
            equity = equity * golddata2['open'].iloc[idx+lags-1] / golddata2['open'].iloc[idx+lags]
            equitylist.append(equity)
        except:
            break

plt.plot(equitylist)
plt.title('Strategy Result')
plt.ylabel('Equity')
plt.xlabel('Time Unit')

#计算最大回撤
drawbacklist = []
for i in range(len(equitylist)):
    j = i + 1
    while j<len(equitylist):
        drawbacklist.append(equitylist[j] / equitylist[i])
        j += 1
maxdrawback = min(drawbacklist) - 1

#计算年化收益
annualreturn = (equitylist[-1] - 1) / len(equitylist) * 250

#计算夏普收益
SR = (annualreturn - 0.035) / np.sqrt(np.var(equitylist))