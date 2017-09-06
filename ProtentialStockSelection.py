import pandas as pd
import matplotlib.pyplot as plt
plt.style.use("fivethirtyeight")
import datetime
import numpy as np
import tushare as ts
import time
import os
from emailsent import mailtx
from code_lecture.featuresUtil import BBANDS,CCI,EVM,EWMA,ForceIndex,ROC,SMA

today_string = datetime.datetime.now().strftime("%Y-%m-%d")
OneMonthAgo  = (datetime.datetime.now()-datetime.timedelta(30)).strftime("%Y-%m-%d")
TwoMonthAgo  = (datetime.datetime.now()-datetime.timedelta(60)).strftime("%Y-%m-%d")

def InitializeStockInfo():
    
    # Initiallize all HS300 Stock infomation, ideally it happened every weekday
    # Raw data will be saved in data/hs300s/
    # after calulating, data with indicators are saved in data/hs300s_withIndicators/
    
    codes = ts.get_hs300s().code
    print "crawling stock infomation........."
    for code,j in zip(codes,range(len(codes))):
        if (j+1)%100==0: print "iteration %d out of 300"%(j+1)
        df = ts.get_hist_data(code)
        df[['open','close','high','low','volume','turnover']].to_csv("data/hs300s/%s.csv"%code)

    fileNames = os.listdir("data/hs300s/")
    codes = []
    for i in fileNames:
        codes.append(i.split(".")[0])
        
    # calculate the indicators #
    indicators=[BBANDS,CCI,EVM,EWMA,ForceIndex,ROC,SMA]
    lag_days=[5,10,20,30,40,60,80,120]
    print "getting indicators........"
    for code,j in zip(codes,range(len(codes))):
        if (j+1)%100==0: print "iteration at %d out of 300"%(j+1)
        df = pd.read_csv("data/hs300s/%s.csv"%code)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date').reset_index(drop=True)
        for indicator in indicators:
            for lag_day in lag_days:
                df = indicator(df,lag_day)
                df.to_csv("data/hs300s_withIndicators/%s.csv"%code)


def plot_indicator(code,startDate=OneMonthAgo,endDate=today_string):
    # plot BolingerBand, SMA, EMA, CCI, EVM, ROC, ForceIndex 

    # This function is used to visualise the plot of the indicators
    
    df = pd.read_csv("../stock/data/hs300s_withIndicators/%s.csv"%code,index_col=0)
    df['date'] = pd.to_datetime(df['date'])
    df = df[(df.date>=startDate)&(df.date<=endDate)].reset_index(drop=True)
    
    indicatorNames=['SMA','EMA','CCI','EVM','ROC','ForceIndex']
    plt.figure(figsize=(15,len(indicatorNames)*2.5))

    # BollingerBand_20 
    plt.subplot(7,1,1)
    plt.plot(df.date,df.close,color='black',lw=3)
    plt.plot(df.date,df.Upper_BollingerBand_20,color='g')
    plt.plot(df.date,df.Lower_BollingerBand_20,color='g')
    plt.title(code);plt.ylabel("BollingerBand")


    for indicator,j in zip(indicatorNames,range(len(indicatorNames))):
        plt.subplot(len(indicatorNames)+1,1,j+2)
        data = pd.concat([df.date,df.filter(regex='%s.*'%indicator)],axis=1)
        for i in range(1,8,1):
            plt.plot(data.date,data.iloc[:,i]);plt.legend(loc=2)
        plt.ylabel(indicator)


def DropNanStock(code):
    
    # will drop the stock if the infomation are not efficient.
    # 1. if the stock dosen't have data for most recent two months, drop
    # 2. if the stock doesn't change 10% during two month, drop 
    
    df = pd.read_csv("../stock/data/hs300s_withIndicators/%s.csv"%code,index_col=0)
    df['date'] = pd.to_datetime(df['date'])
    df = df[df.date>='2016-01-01'].reset_index(drop=True)
    
    df_2month = df[df.date>=TwoMonthAgo]
    
    # if the stock doesn't have data for the most 2 recent months, then drop
    if len(df_2month)<7:
        pass
    else:
    # if the stock doesn's change so much for the 2 recent months, then drop
        avgClose = np.average(df_2month.close)
        flut = max(df_2month.close) - min(df_2month.close)
        if (10.0*flut/avgClose<avgClose)&(avgClose<7):
#             print "%s doesn't change much"%code
            pass  
        else: 
            return code  #code that can be selected


def StockSelector(code,
                   save=False,
                   n_short_day=10,
                   n_long_day=60,
                   breakThroughType='short_to_long',
                   breakThroughDay=10,
                   indicator_selector=['SMA','EMA','EVM','ForceIndex','ROC'],
                   verbose=True):
    
    # n_short, n_long, breakThoughDay are in (5,10,20,30,40,60,80)
    
    # TO DO: 
    # 1. need to make each indicator's parameterized
    # 2. need to understand more of the parameters
    # 3. need to understand BollingerBand
    # 4. even though line didn't cross, but when they are close enough, we see them as they cross.
    # 5. each stock has diffrent parameters?
    # 6. remove EMA,ForceIndex,ROC add CCI?
    
    '''
    Break Through Type:
    SMA: short_to_long
    EMA: short_to_long
    EVM: break though 0
    ForceIndex: break_through_0
    ROC: break_through_0
    '''
    
    df = pd.read_csv("../stock/data/hs300s_withIndicators/%s.csv"%code,index_col=0)
    df = df.sort_values(by='date')
    df = df[df.date>=OneMonthAgo].reset_index(drop=True)
    df['date'] = pd.to_datetime(df['date'])

    
    DowntoUp = [] # whole container
    UptoDown = [] # whole container
    
    # -----------------  begin to select the stock  --------------------- rules: 2017/09/04#


    def OneIndicator(df,indicator,n_short=n_short_day,n_long=n_long_day,
                     break_through_type=breakThroughType,break_through_day=breakThroughDay):
        
        #--------------   initiallised parameters  -------------------------#
        # break_through_type=["short_to_long","break_through_0"]
        # if break_through_type='break_through_0': break_through_day=20
        
        # initiallise the containers for each indicator  
        
        
        _DowntoUp = []
        _UptoDown = []
        b_sign = 0   # buy signal
        s_sign = 0   # sell signal
 
        if break_through_type=='short_to_long':
            for i, next_i in zip(df.index[:-1],df.index[1:]):
                if (df.ix[i,indicator+"_"+str(n_short)]>df.ix[i,indicator+"_"+str(n_long)])&(df.ix[next_i,indicator+"_"+str(n_short)]<df.ix[next_i,indicator+"_"+str(n_long)]):
                    _UptoDown.append(next_i)
                    if next_i==df.index[-1]:   # sell signal
                        s_sign = 1
                
                if (df.ix[i,indicator+"_"+str(n_short)]<df.ix[i,indicator+"_"+str(n_long)])&(df.ix[next_i,indicator+"_"+str(n_short)]>df.ix[next_i,indicator+"_"+str(n_long)]):
                    _DowntoUp.append(next_i)
                    if next_i==df.index[-1]:   # buy signal
                        b_sign = 1
        
        if break_through_type=='break_through_0':
            for i, next_i in zip(df.index[:-1],df.index[1:]):
                if (df.ix[i,indicator+"_"+str(break_through_day)]>0)&(df.ix[next_i,indicator+"_"+str(break_through_day)]<0):
                    _UptoDown.append(next_i)
                    if next_i==df.index[-1]:
                        s_sign = 1
                    
                if (df.ix[i,indicator+"_"+str(break_through_day)]<0)&(df.ix[next_i,indicator+"_"+str(break_through_day)]>0):
                    _DowntoUp.append(next_i)
                    if next_i==df.index[-1]:
                        b_sign = 1
        if verbose:
            if break_through_type=='short_to_long':
                print indicator,"break through from",n_short,"-->",n_long
            if break_through_type=='break_through_0':
                print indicator,"break through y_axis line:",break_through_day
        
        
        return _DowntoUp,_UptoDown, b_sign, s_sign

    
    # get each indicator buy or sell signal
    
    if "SMA" in indicator_selector:
        SMA_DowntoUp,SMA_UptoDown,SMA_b_sign, SMA_s_sign = OneIndicator(df,"SMA",break_through_type='short_to_long')
    else: SMA_DowntoUp,SMA_UptoDown,SMA_b_sign, SMA_s_sign= None,None,0,0
        
    if "EMA" in indicator_selector:
        EMA_DowntoUp,EMA_UptoDown,EMA_b_sign, EMA_s_sign = OneIndicator(df,"EMA",break_through_type='short_to_long')
    else: EMA_DowntoUp,EMA_UptoDown,EMA_b_sign, EMA_s_sign= None,None,0,0

    if "EVM" in indicator_selector:    
        EVM_DowntoUp,EVM_UptoDown,EVM_b_sign, EVM_s_sign = OneIndicator(df,"EVM",break_through_type='break_through_0')
    else: EVM_DowntoUp,EVM_UptoDown,EVM_b_sign, EVM_s_sign= None,None,0,0
    
    if "ForceIndex" in indicator_selector:   
        ForceIndex_DowntoUp,ForceIndex_UptoDown,ForceIndex_b_sign, ForceIndex_s_sign = OneIndicator(df,"ForceIndex",break_through_type='break_through_0')
    else: ForceIndex_DowntoUp,ForceIndex_UptoDown,ForceIndex_b_sign, ForceIndex_s_sign = None,None,0,0
      
    if "ROC" in indicator_selector:    
        ROC_DowntoUp,ROC_UptoDown,ROC_b_sign, ROC_s_sign = OneIndicator(df,"ROC",break_through_type='break_through_0')
    else: ROC_DowntoUp,ROC_UptoDown,ROC_b_sign, ROC_s_sign= None,None,0,0
    
    
    #  append for all indicators signs
    for i in [SMA_DowntoUp,EMA_DowntoUp,EVM_DowntoUp,ForceIndex_DowntoUp,ROC_DowntoUp]:
        if i:
            for j in i:
                DowntoUp.append(j)
    
    for i in [SMA_UptoDown,EMA_UptoDown,EVM_UptoDown,ForceIndex_UptoDown,ROC_UptoDown]:
        if i:
            for j in i:
                UptoDown.append(j)
    
    # --------------------  visulise the choise ------------------------------ #
    if verbose:
        plt.figure(figsize=(15,13))
        plt.subplot(611)
        plt.plot(df.date,df.close,color='black',lw=3)
        plt.plot(df.date,df.Upper_BollingerBand_20,'g--',alpha=.7)
        plt.plot(df.date,df.Lower_BollingerBand_20,'g--',alpha=.7)
        plt.title(code)
        if len(DowntoUp)>0:
            for downup in DowntoUp:
                plt.axvline(df.ix[downup,"date"],color='red')
        if len(UptoDown)>0:
            for updown in UptoDown:
                plt.axvline(df.ix[updown,"date"],color='green')




        def plot_OneIndicator(df,indicator):

            if (indicator=="SMA")|(indicator=="EMA"):

                plt.plot(df.date,df[indicator+"_"+str(n_short_day)],color='orange')
                plt.plot(df.date,df[indicator+"_"+str(n_long_day)],color='blue')
                plt.legend(loc=2)

            if (indicator=="EVM")|(indicator=="ForceIndex")|(indicator=="ROC"):
                plt.plot(df.date,df[indicator+"_"+str(breakThroughDay)],color='orange')
                plt.legend(loc=2)


            if indicator=="SMA": _DowntoUp = SMA_DowntoUp;_UptoDown = SMA_UptoDown
            if indicator=="EMA": _DowntoUp = EMA_DowntoUp;_UptoDown = EMA_UptoDown
            if indicator=="EVM": _DowntoUp = EVM_DowntoUp;_UptoDown = EVM_UptoDown
            if indicator=="ForceIndex": _DowntoUp = ForceIndex_DowntoUp;_UptoDown = ForceIndex_UptoDown
            if indicator=="ROC": _DowntoUp = ROC_DowntoUp;_UptoDown = ROC_UptoDown

            if len(_DowntoUp)>0:
                for downup in _DowntoUp:
                    plt.axvline(df.ix[downup,"date"],color='red')
            if len(_UptoDown)>0:
                for updown in _UptoDown:
                    plt.axvline(df.ix[updown,"date"],color='green')
            plt.ylabel(indicator)

        if "SMA" in indicator_selector:
            plt.subplot(612) # SMA
            plot_OneIndicator(df,"SMA")


        if "EVM" in indicator_selector:
            plt.subplot(613) # EVM
            plot_OneIndicator(df,"EVM")

        if "EMA" in indicator_selector:
            plt.subplot(614) # EMA
            plot_OneIndicator(df,"EMA")

        if "ForceIndex" in indicator_selector:    
            plt.subplot(615) # ForceIndex
            plot_OneIndicator(df,"ForceIndex")

        if "ROC" in indicator_selector:
            plt.subplot(616) # ROC
            plot_OneIndicator(df,"ROC")

        plt.show()

        if save==True:
                plt.savefig("img/%s.png"%code)

    
    df_sign = pd.DataFrame({'SMA':[SMA_b_sign,SMA_s_sign],
                            'EVM':[EVM_b_sign,EVM_s_sign],
                            'EMA':[EMA_b_sign,EMA_s_sign],
                            'ForceIndex':[ForceIndex_b_sign,ForceIndex_s_sign],
                            'ROC':[ROC_b_sign,ROC_s_sign]})
    
    df_sign = df_sign.T
    df_sign.columns=['buySignal','sellSignal']
    
    return df_sign
    
if __name__=="__main__":
    
    start_time = time.time()
    
    InitializeStockInfo()  # initiallization

    # drop the stock that don't have enough data recently
    codes = []
    effective_codes=[]
    for i in os.listdir("data/hs300s/"):
        codes.append(i.split(".")[0])   
    for code in codes:
        effective_codes.append(DropNanStock(code))
    effective_code_list = pd.Series(effective_codes).dropna().tolist()

    N_drop = 300-len(effective_code_list)
    print "%d stocks don't have enough data or change much, dropped"%N_drop

    # save the effective_code_list in the file
    with open ("output/effective_code_list.txt","w") as f:
        for effective_code in effective_code_list:
            f.write("{}\n".format(effective_code))
    
   
    exec_time = time.time()-start_time
    print "execution spent %.2f minutes"%(exec_time*1.0/60)

    # initiallised parameters
    indicator_selector=['SMA','EMA','EVM']
    n_short = 10    
    n_long = 60
    breakThroughDay = 20

    # save the massage
    count=0
    buy_code=[]
    sell_code=[]
    msg=""
    msg += "Author: Tianxiong\nDate: "+today_string+"\n"
    msg += "indicator_selector: "+str(indicator_selector)
    msg += "\nn_short: "+str(n_short)+",\tn_long: "+str(n_long)+",\tbreak through day: "+str(breakThroughDay)
    msg +="\n-------------------------------------\n"
    
    for code in effective_code_list:
        df_sign = StockSelector(code=code,save=False,n_short_day=n_short,n_long_day=n_long,breakThroughDay=breakThroughDay,
                                verbose=False,indicator_selector=indicator_selector)
        if df_sign.sum().sum()>0:
            msg+="code: "+code
            if df_sign.sum(axis=0)[0]>0:
                msg += "\n buy signal:  "+str(df_sign[df_sign.buySignal>0].index.tolist()).split("[")[1].split("]")[0]
                buy_code.append(code)
	    if df_sign.sum(axis=0)[1]>0:
                msg += "\n sell signal: "+str(df_sign[df_sign.sellSignal>0].index.tolist()).split("[")[1].split("]")[0]
                sell_code.append(code)
    
            msg+="\n-------------------------------------\n"
            count+=1
    
    msg += "\n"+"job completed, spent "+str(exec_time*1.0/60)+" minutes!"
    msg += str(N_drop)+" stocks don't have enough data or changed much, dropped"
    msg += "\n"+str(count)+" stocks have been selected, please be noticed!"
    msg += "\n============================================\n"
    
    with open("output/buy/%s.txt"%today_string,"w") as f_buy:
        for bc in buy_code:
            f_buy.write("{}\n".format(bc))


    with open("output/sell/%s.txt"%today_string,"w") as f_sell:
        for sc in sell_code:
            f_sell.write("{}\n".format(sc))    
    
    # sending emails to stackholders
    mailtx(msg_text=msg,title="Intelligent Stock Selector",mailto="tx_wen@sina.com")   # myself
    mailtx(msg_text=msg,title="Intelligent Stock Selector",mailto="2857397423@qq.com") # dad
    mailtx(msg_text=msg,title="Intelligent Stock Selector",mailto='281278120@qq.com')  # Daowei

