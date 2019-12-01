import numpy as np
import pandas as pd
import datetime
import time

def gamelag(gm):
    yr,wk=(gm[:4],gm[4:])
    if wk=='1':
        return str(int(yr)-1)+'17'
    else:
        return yr+str(int(wk)-1)

class nflsr:

    def __init__(self,fpath="nflscrapr/NFL Play by Play 2009-2018 (v5).csv",his=30):
        #Class instance initialization
        #Arguments:
            #fpath:path no fnlscrapr data
            #his: historical game range covered for each data point
        #Manually set into season bin partitions based on begin date of every season
        strts=pd.to_datetime(['2009-09-10','2010-09-09','2011-09-08','2012-09-05','2013-09-05','2014-09-04','2015-09-10','2016-09-08','2017-09-07','2018-09-06','2019-09-05','2020-09-05'], format='%Y-%m-%d')
        yrs=[2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019]
        bins=pd.IntervalIndex.from_tuples([(strts[i],strts[i+1]) for i in range(len(strts)-1)], closed='left')
        #Read in file and set several main variables that will be used in later aggregations
        main=pd.read_csv(fpath)
        main['game_date'] = pd.to_datetime(main['game_date'], format='%Y-%m-%d')
        main['year']=pd.cut(main['game_date'],bins).map(dict(zip(bins,yrs))).astype(int)
        main['ssn_start']=main['year'].map(dict(zip(yrs,strts[:-1])))
        main['week']=((main['game_date']-main['ssn_start']).astype(str).str.split(" ", expand=True)[0].astype(int)//7)+1
        main['off_home']=(main['home_team']==main['posteam']).astype(int)
        #Initialized class attributes:
            #datmain: main data set
            #his: historical game range covered for each data point
            #aggkeys: dictionary to reference for aggregation choices
        self.datmain=main
        self.his=his
        self.aggkeys={'mean':np.mean,'sum':np.sum,'max':np.max}

    def ts_agg(self,datmain,his,typid,keys,incols,aggcols,aggtyps):
        #Flexible aggregation method to be reused for different purposes
        #Arguments:
            #datmain: data run through aggregation
            #his: historical game range covered for each data point
            #typid:
        if len(typid)==0:
            dat=datmain[incols]
        if len(typid)==1:
            dat=datmain[datmain[typid[0]]==1][incols]
        if len(typid)==2:
            dat=datmain[datmain[typid[0]]==typid[1]][incols]
        aggdct={}
        for i in range(len(aggcols)):
            aggdct[aggcols[i]]=[self.aggkeys[key] for key in aggtyps[i]]
        dat=dat[keys+['week','year']+aggcols].groupby(keys+['week','year']).agg(aggdct).reset_index()
        dat.columns=dat.columns.get_level_values(0)
        dat['Game0']=dat['year'].astype(str)+dat['week'].astype(str)
        rnm={}
        for i in range(1,his+1):
            dat=dat.drop_duplicates()
            lagl=[]
            for col in aggcols:
                lagl.append(col+str(i))
                rnm[col]=col+str(i)
            rnm['Game0']='Game'+str(i)
            tmp=dat.rename(columns=rnm)
            dat['Game'+str(i)]=dat['Game'+str(i-1)].apply(gamelag)
            dat=dat.merge(tmp[['Game'+str(i),keys[0]]+lagl], how='left', on=['Game'+str(i),keys[0]])
        dat=dat.drop(columns=[col for col in dat.columns if col!='Game0' and 'Game' in col])
        return dat

    def gameres(self):
        dat=self.datmain[['play_id','game_id','week','year','home_team','away_team','total_home_score','total_away_score']]
        tmp=dat.groupby(['game_id']).agg({'play_id':self.aggkeys['max']}).reset_index()
        dat=dat.merge(tmp, how='inner', on=['game_id','play_id'])
        dat['homedif']=dat['total_home_score']-dat['total_away_score']
        dat['awaydif']=-dat['homedif']
        home=dat[['game_id','week','year','home_team','homedif']].rename(columns={"home_team":"team","homedif":"dif"})
        away=dat[['game_id','week','year','away_team','awaydif']].rename(columns={"away_team":"team","awaydif":"dif"})
        main=pd.concat([home,away]).sort_values(['team','year','week']).drop_duplicates().reset_index()
        main['win']=(main['dif']>0).astype(int)
        main['winpct']=main.sort_values(['team','year','week']).groupby(['team','year'])['win'].expanding().mean().reset_index()['win']
        self.results=main

    def passing(self):
        #dat=ts_agg(self.datmain,self.his,'rush_attempt',['rusher_player_id','rusher_player_name'],['rusher_player_id','rusher_player_name','week','year','yards_gained','rush_attempt','rush_touchdown'],['yards_gained','rush_attempt','rus$
        #self.passer=dat
        pass

    def rushing(self):
        dat=self.ts_agg(self.datmain,self.his,['rush_attempt'],
            ['rusher_player_id','rusher_player_name'],
            ['rusher_player_id','rusher_player_name','week','year','yards_gained','rush_attempt','rush_touchdown'],
            ['yards_gained','rush_attempt','rush_touchdown'],
            [['sum'],['sum'],['sum']])
        self.rusher=dat

    def receiving(self):
        comp=self.ts_agg(self.datmain,self.his,['complete_pass'],
            ['receiver_player_id','receiver_player_name'],
            ['receiver_player_id','receiver_player_name','week','year','complete_pass','air_yards','yards_after_catch','pass_touchdown'],
            ['complete_pass','air_yards','yards_after_catch','pass_touchdown'],
            [['sum'],['sum'],['sum'],['sum']])
        att=self.ts_agg(self.datmain,self.his,['pass_attempt'],
            ['receiver_player_id','receiver_player_name'],
            ['receiver_player_id','receiver_player_name','week','year','pass_attempt','air_yards'],
            ['pass_attempt','air_yards'],
            [['sum'],['sum']])
        main=att.merge(comp, how='left', on=['Game0','receiver_player_id'])
        self.receiver=main

    def kicking(self):
        pass

    def defense(self):
        res=self.ts_agg(self.results,self.his,(),
            ['team'],
            ['team','dif','winpct','week','year'],
            ['dif','winpct'],
            [['sum'],['sum']])

        self.datmain['fg']=(self.datmain['field_goal_result']=='made').astype(int)
        passatt=self.ts_agg(self.datmain,self.his,['pass_attempt'],
            ['defteam','game_id','off_home'],
            ['defteam','game_id','off_home','pass_attempt','week','year'],
            ['pass_attempt'],
            [['sum']]).drop(columns=['week','year'])
        passcomp=self.ts_agg(self.datmain,self.his,['complete_pass'],
            ['defteam'],
            ['defteam','week','year','complete_pass','air_yards','yards_after_catch','pass_touchdown'],
            ['complete_pass','air_yards','yards_after_catch','pass_touchdown'],
            [['sum'],['sum'],['sum'],['sum']]).drop(columns=['week','year'])
        rushing=self.ts_agg(self.datmain,self.his,['rush_attempt'],
            ['defteam'],
            ['defteam','week','year','rush_attempt','yards_gained','rush_touchdown'],
            ['rush_attempt','yards_gained','rush_touchdown'],
            [['sum'],['sum'],['sum']]).drop(columns=['week','year'])
        spcl=self.ts_agg(self.datmain,self.his,('timeout',0),
            ['defteam'],
            ['defteam','week','year','sack','interception','fumble_forced','qb_hit','return_touchdown'],
            ['sack','interception','fumble_forced','qb_hit','return_touchdown'],
            [['sum'],['sum'],['sum'],['sum'],['sum']]).drop(columns=['week','year'])
        fg=self.ts_agg(self.datmain,self.his,['field_goal_attempt'],
            ['defteam'],
            ['defteam','field_goal_attempt','fg','week','year'],
            ['field_goal_attempt','fg'],
            [['sum'],['mean']]).drop(columns=['week','year'])
        maind=passatt.merge(passcomp, how='left', on=['Game0','defteam']).merge(rushing, how='left', on=['Game0','defteam']).merge(spcl, how='left', on=['Game0','defteam']).merge(fg, how='left', on=['Game0','defteam'])\
            .merge(res, how='left', left_on=['Game0','defteam'], right_on=['Game0','team'])
        maind=maind.add_prefix('d_')

        passatt=self.ts_agg(self.datmain,self.his,['pass_attempt'],
            ['posteam','game_id'],
            ['posteam','game_id','pass_attempt','week','year'],
            ['pass_attempt'],
            [['sum']]).drop(columns=['week','year'])
        passcomp=self.ts_agg(self.datmain,self.his,['complete_pass'],
            ['posteam'],
            ['posteam','week','year','complete_pass','air_yards','yards_after_catch','pass_touchdown'],
            ['complete_pass','air_yards','yards_after_catch','pass_touchdown'],
            [['sum'],['sum'],['sum'],['sum']]).drop(columns=['week','year'])
        rushing=self.ts_agg(self.datmain,self.his,['rush_attempt'],
            ['posteam'],
            ['posteam','week','year','rush_attempt','yards_gained','rush_touchdown'],
            ['rush_attempt','yards_gained','rush_touchdown'],
            [['sum'],['sum'],['sum']]).drop(columns=['week','year'])
        spcl=self.ts_agg(self.datmain,self.his,('timeout',0),
            ['posteam'],
            ['posteam','week','year','sack','interception','fumble_forced','qb_hit','return_touchdown'],
            ['sack','interception','fumble_forced','qb_hit','return_touchdown'],
            [['sum'],['sum'],['sum'],['sum'],['sum']]).drop(columns=['week','year'])
        fg=self.ts_agg(self.datmain,self.his,['field_goal_attempt'],
            ['posteam'],
            ['posteam','field_goal_attempt','fg','week','year'],
            ['field_goal_attempt','fg'],
            [['sum'],['mean']]).drop(columns=['week','year'])
        maino=passatt.merge(passcomp, how='left', on=['Game0','posteam']).merge(rushing, how='left', on=['Game0','posteam']).merge(spcl, how='left', on=['Game0','posteam']).merge(fg, how='left', on=['Game0','posteam'])\
            .merge(res, how='left', left_on=['Game0','posteam'], right_on=['Game0','team']).drop(columns=['week','year'])
        maino=maino.add_prefix('o_')

        maind=maind.merge(maino, how='left', left_on='d_game_id', right_on='o_game_id')
        maind=maind[maind['d_defteam']!=maind['o_posteam']].reset_index()

        #[col for col in maind.columns if col!='Game0' and 'Game' in col]
        #maind=maind

        self.defend=maind
        for col in maind.columns:
            print(col)

    def spec_run(self):
        pass

    def full_run(self):
        pass

    def update(self):
        pass

if __name__=="__main__":
    run=nflsr()
    run.gameres()
    run.defense()
    print(run.defend)

