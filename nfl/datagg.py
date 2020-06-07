import numpy as np
import pandas as pd

if __name__=="__main__":
    his=pd.read_csv("data/nflscrapr/NFL Play by Play 2009-2018 (v5).csv")
    #print(his)
    d18=pd.read_csv("data/nflscrapr/scrp18.csv")
    #print(d18)
    d19=pd.read_csv("data/nflscrapr/scrp19.csv")
    #print(d19)
    #tst=pd.read_csv("data/nflscrapr/test1.csv")
    #print(tst)
    main=pd.concat([his,d18,d19],ignore_index=True, sort=False)
    games=pd.read_csv("data/nflscrapr/test2.csv")
    tmp=main.iloc[0:2].reset_index()
    for ind,row in games.iterrows():
        tmp1=tmp
        tmp1['home_team']=row['home']
        tmp1['away_team']=row['away']
        tmp1['game_date']=row['date']
        tmp1['game_id']=main['game_id'].max()+1
        tmp1['pass_attempt']=1
        tmp1['complete_pass']=1
        tmp1['rush_attempt']=1
        tmp1['timeout']=0
        tmp1['field_goal_attempt']=1
        tmp1.loc[0,'posteam']=row['home']
        tmp1.loc[0,'posteam_type']='home'
        tmp1.loc[0,'defteam']=row['away']
        tmp1.loc[0,'play_id']=main['play_id'].max()+1
        tmp1.loc[1,'posteam']=row['away']
        tmp1.loc[1,'posteam_type']='away'
        tmp1.loc[1,'defteam']=row['home']
        tmp1.loc[1,'play_id']=main['play_id'].max()+2
        main=pd.concat([main,tmp1],ignore_index=True, sort=False)
    main.to_csv("data/nflscrapr/agg.csv")
    #print(main)
