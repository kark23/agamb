from pls_filter import *
import pandas as pd
import numpy as np

if __name__=="__main__":
    main=pd.read_csv('data/trans1/defense.csv')
    main=main.fillna(0)
    #main=main[main['d_year']>=2011]
    main1=main[(main['d_year']>=2011) & (main['d_year']<=2017)].reset_index()
    main2=main[main['d_year']>=2018].reset_index()
    main1.to_csv('data/trans2/deftrn.csv')
    main2.to_csv('data/trans2/deftst.csv')
    yskip=['pass_attempt','complete_pass','air_yards','yards_after_catch','pass_touchdown','complete_pass','air_yards','yards_after_catch','pass_touchdown','rush_attempt','yards_gained','rush_touchdown','sack','interception',
        'fumble_forced','qb_hit','return_touchdown''field_goal_attempt','fg','winpct','dif']
    skip=['o_'+col for col in yskip]
    skip+=['d_'+col for col in yskip]
    y=['d_dif']
    nstnd=['index','d_defteam','d_game_id','d_Game0','d_team','o_defteam','o_game_id','o_Game0','o_team','Unnamed: 0']
    x=[col for col in main.columns if (main[col].dtype==np.float64 or main[col].dtype==np.int64) and col not in nstnd and col not in skip and col not in y]
    for inp in x:
        print(inp)
    #stndf=STAND(main,main,stndcols)
    PLS_SAVE(5,'data/trans2/deftrn.csv',x,y,'models/pls/def_sv1.sav')
    trn=PLS_LTRANS('data/trans2/deftrn.csv','data/trans2/deftrn.csv',x,y,'models/pls/def_sv1.sav','data/plstrans/deftrn.csv')
    tst=PLS_LTRANS('data/trans2/deftst.csv','data/trans2/deftrn.csv',x,y,'models/pls/def_sv1.sav','data/plstrans/deftst.csv')
    for i in range(100,110):
        new=REG_FILT('data/plstrans/deftrn.csv','data/trans2/deftrn.csv',tst.loc[[i]],1000,None,2,write=False)
        print(tst.loc[[i]])
        print(new['d_dif'].value_counts())
        print(new['d_dif'].mean(),new['d_dif'].std())
        print(main2.loc[[i]][['d_dif','o_team','d_team','o_winpct','d_winpct','d_year','d_week']])
        import matplotlib.pyplot as plt
        new['d_dif'].hist()
        plt.savefig("plot{0}.pdf".format(str(i)))
        plt.close()
