import os
os.chdir('/Users/apple/Desktop/GoldSentAnalysis/News_Categorization')
import operator
import datetime
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn import svm
from NewsSent import News #从外部导入写好的情绪判别类
import matplotlib.pyplot as plt
from sklearn.cross_validation import train_test_split

def genvar(content, vardict):
    wordslist = News(content).cut()
    var = list(set(list(vardict.keys())).intersection(set(wordslist)))
    if var == []:
        return vardict
    for i in var:
        vardict[i] = [1]
    return vardict

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

goldnews = pd.read_csv('analysisdata.csv', encoding = 'gbk')
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

#xgboost预测
traindata = golddata
variables = ['possent', 'negsent', 'neusent', 'possentprev1', 'negsentprev1', 'neusentprev1',\
             'possentprev2', 'negsentprev2', 'neusentprev2', 'posfrac', 'negfrac', 'newscount']

X = traindata[variables]
Xtrain = traindata[variables].values
ytrain = traindata['fivedaysreturn'].values
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

#画变量重要性图
def create_feature_map(features):
    outfile = open('xgb.fmap', 'w')
    for i, feat in enumerate(features):
        outfile.write('{0}\t{1}\tq\n'.format(i, feat))
    outfile.close()

features = list(X.columns)
create_feature_map(features)
importance = gbm.get_fscore(fmap='xgb.fmap')
importance = sorted(importance.items(), key=operator.itemgetter(1))

df = pd.DataFrame(importance, columns=['feature', 'fscore'])
df['fscore'] = df['fscore'] / df['fscore'].sum()

featp = df.plot(kind='barh', x='feature', y='fscore', legend=False, figsize=(6, 10))
plt.title('XGBoost Feature Importance')
plt.xlabel('relative importance')
fig_featp = featp.get_figure()
fig_featp.savefig('feature_importance_xgb.png', bbox_inches='tight', pad_inches=1)

#svm预测
traindata = golddata
variables = ['possent', 'negsent', 'neusent', 'possentprev1', 'negsentprev1', 'neusentprev1',\
             'possentprev2', 'negsentprev2', 'neusentprev2', 'posfrac', 'negfrac', 'newscount']

X = traindata[variables]
Xtrain = traindata[variables].values
ytrain = traindata['fivedaysreturn'].values
ytrainlist = []
for i in ytrain:
    if i >= 0:
        ytrainlist.append(1)
    else:
        ytrainlist.append(0)
ytrain = np.array(ytrainlist)
X_train, X_test, y_train, y_test = train_test_split(Xtrain, ytrain, test_size=0.3, random_state=0)
clf = svm.SVC(C=3.0, cache_size=200, class_weight=None, coef0=0.0,
              decision_function_shape=None, degree=1, gamma='auto', kernel='rbf',
              max_iter=-1, probability=True, random_state=2, shrinking=True,
              tol=0.001, verbose=False).fit(X_train, y_train)
for idx1, i in enumerate(X_test):
    for idx2, j in enumerate(i):
        if j == np.inf:
            X_test[idx1][idx2] = 0
clf.score(X_test, y_test)

#因子分组计算收益
def get_frac(scorelist, fracnum):
    rangelist = np.linspace(0,100,fracnum + 1)
    rangelist = rangelist[1:]
    fracvaluelist = []
    for i in rangelist:
        fracvalue = np.percentile(scorelist, i)
        fracvaluelist.append(fracvalue)
    return fracvaluelist

#因子分组检测
golddata = golddata.dropna()
def factor_test(dataset, factor, groupnum):
    fracvaluelist = get_frac(dataset[factor], groupnum)
    dataset['group'] = [0]*len(golddata)
    j = 0
    for idx, i in enumerate(fracvaluelist):
        indexlist = dataset[factor][dataset[factor] <= i][dataset[factor] >= j].index
        dataset['group'].loc[list(indexlist)] = idx + 1
        j = i
    testresult = dataset.groupby('group').fivedaysreturn.mean()
    return testresult

#因子单调性检测
sentimentfactor = ['possent', 'negsent', 'neusent', 'posfrac', 'negfrac', 'newscount']
picture = plt.figure
for i in sentimentfactor:
    plt.plot(factor_test(golddata, i, 10))
plt.xlabel('groups')
plt.ylabel('five days return')
plt.title('Factor Analysis')
plt.legend(sentimentfactor, loc = 'SouthWest')








