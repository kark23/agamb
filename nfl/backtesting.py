from pls_filter import *
from customfunctions import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

if __name__=="__main__":
    main=pd.read_csv('data/trans1/defense.csv')
    main=main.fillna(0)
    mapdoc=pd.read_excel('data/mapping/team_map.xlsx')
    mapdic={}
    for idx, row in mapdoc.iterrows():
        mapdic[row['oddsteams']]=row['nflscrapr']
    odds=pd.read_excel('data/odds/nfl.xlsx')
    odds['Home Team']=odds['Home Team'].map(mapdic)
    odds['Away Team']=odds['Away Team'].map(mapdic)
    strts=pd.to_datetime(['2009-09-10','2010-09-09','2011-09-08','2012-09-05','2013-09-05','2014-09-04','2015-09-10','2016-09-08','2017-09-07','2018-09-06','2019-09-05','2020-09-05'], format='%Y-%m-%d')
    yrs=[2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019]
    bins=pd.IntervalIndex.from_tuples([(strts[i],strts[i+1]) for i in range(len(strts)-1)], closed='left')
    odds['Date'] = pd.to_datetime(odds['Date'], format='%Y-%m-%d')
    odds=odds[odds['Date']>='2009-09-10']
    odds['year']=pd.cut(odds['Date'],bins).map(dict(zip(bins,yrs))).astype(int)
    odds['ssn_start']=odds['year'].map(dict(zip(yrs,strts[:-1])))
    odds['week']=((odds['Date']-odds['ssn_start']).astype(str).str.split(" ", expand=True)[0].astype(int)//7)+1
    #print(mapdic)
    #print(odds)
    totp=0
    tota=0
    cap=0
    for yr in range(2017,2020):
        yrp=0
        for wk in range(1,18):
            wkp=0
            wka=0
            main1=main[((main['d_year']>=2011) & (main['d_year']<=yr-1))|((main['d_year']==yr) & (main['d_week']<wk))].reset_index()
            main2=main[((main['d_year']==yr) & (main['d_week']==wk))].reset_index()
            main3=odds[((odds['year']==yr) & (odds['week']==wk))].reset_index()
            main1.to_csv('data/trans2/deftrn.csv')
            main2.to_csv('data/trans2/deftst.csv')
            yskip=['pass_attempt','complete_pass','air_yards','yards_after_catch','pass_touchdown','complete_pass','air_yards','yards_after_catch','pass_touchdown','rush_attempt','yards_gained','rush_touchdown','sack','interception',
            'fumble_forced','qb_hit','return_touchdown''field_goal_attempt','fg','winpct','dif']
            skip=['o_'+col for col in yskip]
            skip+=['d_'+col for col in yskip]
            y=['d_dif']
            nstnd=['index','d_defteam','d_game_id','d_Game0','d_team','o_defteam','o_game_id','o_Game0','o_team','Unnamed: 0']
            x=[col for col in main.columns if (main[col].dtype==np.float64 or main[col].dtype==np.int64) and col not in nstnd and col not in skip and col not in y]
            #for inp in x:
                #print(inp)
            #stndf=STAND(main,main,stndcols)
            PLS_SAVE(5,'data/trans2/deftrn.csv',x,y,'models/pls/def_sv1.sav')
            trn=PLS_LTRANS('data/trans2/deftrn.csv','data/trans2/deftrn.csv',x,y,'models/pls/def_sv1.sav','data/plstrans/deftrn.csv')
            tst=PLS_LTRANS('data/trans2/deftst.csv','data/trans2/deftrn.csv',x,y,'models/pls/def_sv1.sav','data/plstrans/deftst.csv')
            tmp={}
            for i in range(len(tst)):
                #print(main2)
                #print(main2.loc[i,'d_team'])
                tmp[main2.loc[i,'d_team']]=REG_FILT('data/plstrans/deftrn.csv','data/trans2/deftrn.csv',tst.loc[[i]],1000,None,2,write=False)
            #print(main2['d_team'].value_counts())
            for idx,row in main3.iterrows():
                #print(row)
                try:
                    homedist=tmp[row['Home Team']]
                    awaydist=tmp[row['Away Team']]
                #print('ayy')
                #print(dectoprob(row['Home Odds Open']),.5*((len(homedist[homedist['d_dif']>0])/len(homedist))+(len(awaydist[awaydist['d_dif']<0])/len(awaydist))))
                    if dectoprob(row['Home Odds Open'])<.5*((len(homedist[homedist['d_dif']>0])/len(homedist))+(len(awaydist[awaydist['d_dif']<0])/len(awaydist))):
                        prob=dectoprob(row['Home Odds Open'])
                        #amt=-(cap/4)*(prob-.5*((len(homedist[homedist['d_dif']>0])/len(homedist))+(len(awaydist[awaydist['d_dif']<0])/len(awaydist))))
                        amt=(.5*((len(homedist[homedist['d_dif']>0])/len(homedist))+(len(awaydist[awaydist['d_dif']<0])/len(awaydist)))/prob)-1
                        win=row['Home Score']>row['Away Score']
                        print('a',row,prob,amt,betprofit(amt,prob,win))
                        wkp+=betprofit(amt,prob,win)
                        wka+=amt
                    if dectoprob(row['Away Odds Open'])<.5*((len(homedist[homedist['d_dif']<0])/len(homedist))+(len(awaydist[awaydist['d_dif']>0])/len(awaydist))):
                        prob=dectoprob(row['Away Odds Open'])
                        #amt=-(cap/4)*(prob-.5*((len(homedist[homedist['d_dif']<0])/len(homedist))+(len(awaydist[awaydist['d_dif']>0])/len(awaydist))))
                        amt=(.5*((len(homedist[homedist['d_dif']<0])/len(homedist))+(len(awaydist[awaydist['d_dif']>0])/len(awaydist)))/prob)-1
                        win=row['Home Score']<row['Away Score']
                        print('b',row,prob,amt,betprofit(amt,prob,win))
                        wkp+=betprofit(amt,prob,win)
                        wka+=amt
                    if dectoprob(row['Home Line Odds Open'])<.5*((len(homedist[homedist['d_dif']>row['Away Line Open']])/len(homedist))+(len(awaydist[awaydist['d_dif']<row['Away Line Open']])/len(awaydist))):
                        prob=dectoprob(row['Home Line Odds Open'])
                        #amt=-(cap/4)*(prob-.5*((len(homedist[homedist['d_dif']>row['Away Line Open']])/len(homedist))+(len(awaydist[awaydist['d_dif']<row['Away Line Open']])/len(awaydist))))
                        amt=(.5*((len(homedist[homedist['d_dif']>row['Away Line Open']])/len(homedist))+(len(awaydist[awaydist['d_dif']<row['Away Line Open']])/len(awaydist)))/prob)-1
                        win=row['Home Score']+row['Away Line Open']>row['Away Score']
                        print('c',row,prob,amt,betprofit(amt,prob,win))
                        wkp+=betprofit(amt,prob,win)
                        wka+=amt
                    if dectoprob(row['Away Line Odds Open'])<.5*((len(homedist[homedist['d_dif']<row['Away Line Open']])/len(homedist))+(len(awaydist[awaydist['d_dif']>row['Away Line Open']])/len(awaydist))):
                        prob=dectoprob(row['Away Line Odds Open'])
                        #amt=-(cap/4)*(prob-.5*((len(homedist[homedist['d_dif']<row['Away Line Open']])/len(homedist))+(len(awaydist[awaydist['d_dif']>row['Away Line Open']])/len(awaydist))))
                        amt=(.5*((len(homedist[homedist['d_dif']<row['Away Line Open']])/len(homedist))+(len(awaydist[awaydist['d_dif']>row['Away Line Open']])/len(awaydist)))/prob)-1
                        win=row['Home Score']+row['Away Line Open']<row['Away Score']
                        print('d',row,prob,amt,betprofit(amt,prob,win))
                        wkp+=betprofit(amt,prob,win)
                        wka+=amt
                except Exception as e:
                    print(e)
                    #print(new['d_dif'].mean(),new['d_dif'].std())
                    #print(main2.loc[[i]][['d_dif','o_team','d_team','o_winpct','d_winpct','d_year','d_week']])
                #new['d_dif'].hist()
                #plt.savefig("plot{0}.pdf".format(str(i)))
                #plt.close()
            print(yr,wk,wkp,'wkprof')
            print(yr,wk,wkp/wka,'wkret')
            cap+=wkp
            print(yr,wk,cap/1000,cap,'netret')
            #totp+=wkp
            #tota+=wka
            #print(yr,wk,totp,'totprof')
            #print(yr,wk,totp/tota,'totret')
        #print(yr,yrp)
        #totp+=yrp
        #print('cum',totp)
