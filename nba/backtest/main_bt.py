import numpy as np
import pandas as pd
import pickle
import catboost
import dateutil
import sys
sys.path.insert(0, '../optimization')
from brute import *
import os
import os.path

def prz_cln(slate):
	for cont in slate['contests']:
		cont['prizes'].append({'cash': 0, 'rank': cont['maxEntries'], 'score': 0})
		cont['pz_df']=pd.DataFrame(cont['prizes']).sort_values('rank')
		cont['pz_df']['ppl']=cont['pz_df']['rank']- cont['pz_df']['rank'].shift()
		cont['pz_df'].loc[0, 'ppl']= cont['pz_df'].loc[0, 'rank']
		cont['pz_df']['cash']*= cont['pz_df']['ppl']
		cont['pz_df']=cont['pz_df'].groupby('score')[['cash','ppl']].sum().reset_index()
		cont['pz_df']['pz']= cont['pz_df']['cash']/ cont['pz_df']['ppl']
		cont['pz_df']= cont['pz_df'][['score', 'pz']]
		cont['entries']=0
	return slate

def read_fpt(dir):
	df=[]
	for dirpath, dirnames, filenames in os.walk(dir):
		print(dirpath, dirnames, filenames)
		for filename in [f for f in filenames if f.endswith(".pkl")]:
			with open(os.path.join(dirpath, filename), 'rb') as handle:
				df.append(pickle.load(handle))
	return df

bt_main=read_fpt('../data/fantasy_data')
with open('../modeling/invars.pickle', 'rb') as handle:
	xvars= pickle.load(handle)


vars=['p_ast', 'p_blk', 'p_dreb', 'p_fg2', 'p_fg3', 'p_ft', 'p_oreb', 'p_stl', 'p_tov']
dnames=['ast', 'blk', 'drb', 'fg2', 'fg3', 'ft', 'orb', 'stl', 'tov']
pscale={'p_ast':1.5, 'p_blk':2, 'dubdub':1.5, 'p_dreb':1.25, 'p_fg2':2, 'p_fg3':3.5, 'p_ft':1, 'p_oreb':1.25, 'p_stl':2, 'tridub':3, 'p_tov':-.5}

cb=catboost.CatBoostRegressor(iterations=20000, learning_rate=.1, depth=3, od_type='Iter', od_wait=2000)
varl=[]
first=True
for var, dname in zip (vars, dnames):
	plyvar=pd.read_pickle(f'../data/trans2/df_{dname}.pkl')
	print(dname, plyvar)
	xvars[var]=[i for i in xvars[var] if i in list(plyvar.columns)]
	mod=cb.load_model('../modeling/catmods/'+dname)
	varl.append('pred_'+var)
	plyvar['pred_'+var]=cb.predict(plyvar[xvars[var]])
	if first:
		hist=plyvar[['name', 'game_id', var, 'pred_'+var, 'fpts_100']].copy()
		tm=pd.read_pickle('../data/trans1/fullteam.pkl')[['game_id', 'wct']].drop_duplicates('game_id')
		tm['wct']=pd.to_datetime(pd.to_datetime(tm['wct']).dt.date)
		hist=hist.merge(tm, on='game_id')
		hist['scr']=0
		hist['fpts']=0
		first=False
	else:
		hist=hist.merge(plyvar[['name', 'game_id', var, 'pred_'+var]], on=['name', 'game_id'])
	hist['fpts']+=hist['pred_'+var]*pscale[var]
	hist['scr']+=hist[var]*pscale[var]
mod=cb.load_model('../modeling/catmods/dd')
hist=hist.merge(pd.read_pickle('../data/trans2/df_dd.pkl')[['name', 'game_id', 'dubdub']], on=['name', 'game_id']).merge(pd.read_pickle('../data/trans2/df_td.pkl')[['name', 'game_id', 'tridub']], on=['name', 'game_id'])
hist['pred_dubdub']=mod.predict(hist[varl])
hist['fpts']+=hist['pred_dubdub']*pscale['dubdub']
hist['scr']+=hist['dubdub']*pscale['dubdub']
mod=cb.load_model('../modeling/catmods/td')
hist['pred_tridub']=mod.predict(hist[varl])
hist['fpts']+=hist['pred_tridub']*pscale['tridub']
hist['scr']+=hist['tridub']*pscale['tridub']

prof=0
for bt_dat in bt_main:
	dtref=bt_dat['date']
	for slate in [prz_cln(x) for x in bt_dat['slates'] if x['slateTypeName']=='Tiers']:
		print(pd.DataFrame(slate['slatePlayers']))
		sal=pd.DataFrame(slate['slatePlayers'])
		sal['date']=pd.to_datetime(dtref)
		sal=sal.merge(hist, left_on=['name', 'date'], right_on=['name', 'wct'])
		print(sal)
		sal['fpts']=sal['projectedFpts']
		allocs=brute_opt(sal, 'name', 'slatePosition').sort_values('allocation')
		allocs['allocation']/=sum(allocs['allocation'])
		cap=100
		allocs['allocation']*=cap
		for ind, row in allocs.iterrows():
			inv=row['allocation']
			tmp= [cont for cont in slate['contests'] if cont['entryFee']<=inv and cont['entries']< cont['maxEntriesPerUser']]
			while len(tmp)>0 and inv>0:
				comp= tmp[np.random.randint(len(tmp))]
				comp['entries']+=1
				inv+= -comp['entryFee']
				prof+= -comp['entryFee']+ comp['pz_df'][comp['pz_df']['score']<= row['real_scr']]['pz'].max()
				print(prof)
				tmp= [cont for cont in slate['contests'] if cont['entryFee']<=inv and cont['entries']< cont['maxEntriesPerUser']]
