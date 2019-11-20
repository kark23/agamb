import numpy as np
import pandas as pd
import datetime

def gamelag(gm):
    yr,wk=(gm[:4],gm[4:])
    if wk=='1':
        return str(int(yr)-1)+'17'
    else:
        return yr+str(int(wk)-1)

def ts_agg(datmain,his,typid,keys,incols,aggcols):
    dat=datmain[datmain[typid]==1][incols]
    dat=dat[keys+['week','year']+aggcols].groupby(keys+['week','year']).sum().reset_index()
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
    return dat

class nflsr:

    def __init__(self,fpath="nflscrapr/NFL Play by Play 2009-2018 (v5).csv",his=30):
        strts=pd.to_datetime(['2009-09-10','2010-09-09','2011-09-08','2012-09-05','2013-09-05','2014-09-04','2015-09-10','2016-09-08','2017-09-07','2018-09-06','2019-09-05','2020-09-05'], format='%Y-%m-%d')
        yrs=[2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019]
        bins=pd.IntervalIndex.from_tuples([(strts[i],strts[i+1]) for i in range(len(strts)-1)], closed='left')

        main=pd.read_csv(fpath)
        main['game_date'] = pd.to_datetime(main['game_date'], format='%Y-%m-%d')
        main['year']=pd.cut(main['game_date'],bins).map(dict(zip(bins,yrs))).astype(int)
        main['ssn_start']=main['year'].map(dict(zip(yrs,strts[:-1])))
        main['week']=((main['game_date']-main['ssn_start']).astype(str).str.split(" ", expand=True)[0].astype(int)//7)+1
    
        self.datmain=main
        self.his=his

    def passing(self,incols,aggcols):
        #dat=ts_agg(self.datmain,self.his,'rush_attempt',['rusher_player_id','rusher_player_name'],['rusher_player_id','rusher_player_name','week','year','yards_gained','rush_attempt','rush_touchdown'],['yards_gained','rush_attempt','rus$
        #self.passer=dat
        pass

    def rushing(self):
        dat=ts_agg(self.datmain,self.his,'rush_attempt',['rusher_player_id','rusher_player_name'],['rusher_player_id','rusher_player_name','week','year','yards_gained','rush_attempt','rush_touchdown'],['yards_gained','rush_attempt','rush_touchdown'])
        self.rusher=dat

    def receiving(self):
        comp=ts_agg(self.datmain,self.his,'complete_pass',['receiver_player_id','receiver_player_name'],['receiver_player_id','receiver_player_name','week','year','complete_pass','air_yards','yards_after_catch','pass_touchdown'],['complete_pass','air_yards','yards_after_catch','pass_touchdown'])
        print(len(comp))
        att=ts_agg(self.datmain,self.his,'pass_attempt',['receiver_player_id','receiver_player_name'],['receiver_player_id','receiver_player_name','week','year','pass_attempt','air_yards'],['pass_attempt','air_yards'])
        print(len(att))
        main=att.merge(comp, how='left', on=['Game0','receiver_player_id'])
        self.receiving=main

    def kicking(self,incols,aggcols):
        pass

    def defense(self,incols,aggcols):
        pass

    def write(self):
        pass

if __name__=="__main__":
    run=nflsr()
    print(run.his)
    run.receiving()
    print(run.receiving)

