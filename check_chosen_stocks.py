
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use("fivethirtyeight")
import datetime


today_string = datetime.datetime.now().strftime("%Y-%m-%d")
print today_string

with open("output/buy/%s.txt"%today_string,"r") as fr1:
    buy_codes = fr1.read().split("\n")[:-1]
with open("output/sell/%s.txt"%today_string,"r") as fr2:
    sell_codes = fr2.read().split("\n")[:-1]



buy_code_dict={}
for buy_code in buy_codes:
    dt = pd.read_csv("data/hs300s_withIndicators/%s.csv"%buy_code,index_col=0)
    increase_list = []
    for i in range(1,11,1):
        increase_list.append(round(dt['close'].diff(i).tolist()[-1],2))
    buy_code_dict[buy_code] = increase_list
    
buy_code_increase = pd.DataFrame(buy_code_dict,index=['d1','d2','d3','d4','d5','d6','d7','d8','d9','d10']).T
buy_code_increase.to_csv("output/buy/data/buy_code_increase.csv",header=True, index=True)


sell_code_dict={}
for sell_code in sell_codes:
    dt = pd.read_csv("data/hs300s_withIndicators/%s.csv"%sell_code,index_col=0)
    increase_list = []
    for i in range(1,11,1):
        increase_list.append(round(dt['close'].diff(i).tolist()[-1],2))
    sell_code_dict[sell_code] = increase_list
    
sell_code_increase = pd.DataFrame(sell_code_dict,index=['d1','d2','d3','d4','d5','d6','d7','d8','d9','d10']).T
sell_code_increase.to_csv("output/sell/data/sell_code_increase.csv",header=True, index=True)



plt.figure(figsize=(15,9))
plt.subplot(211)
for i in range(len(buy_code_increase)):
    plt.plot(range(10),buy_code_increase.iloc[i,:],lw=.8);
    plt.title("buy code increase");plt.xticks([]);plt.legend(loc=1)
    
plt.subplot(212)    
for j in range(len(sell_code_increase)):
    plt.plot(range(10),sell_code_increase.iloc[j,:],lw=.8);
    plt.title("sell code increase");plt.xticks([]);plt.legend(loc=1)
plt.savefig("img/%s.png"%today_string)




