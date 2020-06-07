import glob
import os
import sys
import pandas as pd

if __name__=="__main__":
    list_of_files=glob.glob('data/mainraw/*')
    latest_file=max(list_of_files, key=os.path.getctime)
    main=pd.read_csv(latest_file)
    games=pd.read_csv("data/update/games.csv")
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
