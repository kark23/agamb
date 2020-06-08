import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
import shap
import xgboost as xgb
import catboost
from sklearn import metrics

datadir='../data/trans2/'
figdir='figs/'
modeldir='catmods/'
modeldir2='xmods/'

def model(var, dname, action, iter=5000, dct=None):
	print(var)
	base=pd.read_pickle(datadir+'df_'+dname+'.pkl')
	#base['rest']=base['rest'].dt.total_seconds()
	trn=(base['game_id']<=21900500)
	#dct[var]=[i for i in dct[var] if i in list(base.columns)]
	x=base[dct[var]] #.drop(columns=['game_id', 'player_id', 'name', 'team', 'opp', 'pop', var])
	cat_inds=[x.columns.get_loc(c) for c in ['home', 'stadium'] if c in x]
	#for col in x.columns:
	#	print(col)
	y=base[var]
	cb=catboost.CatBoostRegressor(iterations=iter, learning_rate=.1, depth=3, od_type='Iter', od_wait=2000) #, task_type="GPU", devices='1')
	if action=='train':
		cb=cb.fit(x[trn], y[trn], cat_inds, eval_set=(x[~trn], y[~trn]))
		cb.save_model(modeldir+dname)
		#cv_params= cb.get_params()
		#cv_params.update({'loss_function': 'RMSE'})
		#cv_data = catboost.cv(catboost.Pool(x[trn], y[trn], cat_inds), cv_params)
		##explainer=shap.TreeExplainer(cb)
		#shapvals=explainer.shap_values(x[~msk_trn])
		shap.initjs()
		shap_values= cb.get_feature_importance(catboost.Pool(x[~trn], label=y[~trn], cat_features=cat_inds), type="ShapValues")
		shap.summary_plot(shap_values[:,:-1], x[~trn], show=False, plot_size=(16,16), max_display=50)
		plt.savefig(figdir+dname+'shap1.png')
		plt.close()
		return cb.predict(x)
	#if action=='train2':
		#
	elif action=='xtrain':
		param = {'max_depth':3, 'learning_rate':.1}
		xdf=xgb.DMatrix(data=x[trn].drop(columns='stadium'), label=y[trn])
		xtst= xgb.DMatrix(data=x[~trn].drop(columns='stadium'), label=y[~trn])
		watchlist= [(xtst, 'eval'), (xdf, 'train')]
		bst = xgb.train(param, xdf, iter, watchlist)
		bst.dump_model(modeldir2+dname+'.model')
	elif action=='test':
		pscale={'p_ast':1.5, 'p_blk':2, 'dubdub':1.5, 'p_dreb':1.25, 'p_fg2':2, 'p_fg3':3.5, 'p_ft':1, 'p_oreb':1.25, 'p_stl':2, 'tridub':3, 'p_tov':-.5}
		cb=cb.load_model(modeldir+dname)
		preds=cb.predict(x[~trn])
		avg=x[~trn][var+'_10']
		print(dname)
		print('r2', metrics.r2_score(y[~trn], preds))
		print('mse', metrics.mean_squared_error(y[~trn], preds))
		print('mae', metrics.mean_absolute_error(y[~trn], preds))
		print('explained var', metrics.explained_variance_score(y[~trn], preds))
		print('avg comp')
		avg=avg.fillna(avg.mean())
		print('r2', metrics.r2_score(y[~trn], avg))
		print('mse', metrics.mean_squared_error(y[~trn], avg))
		print('mae', metrics.mean_absolute_error(y[~trn], avg))
		print('explained var', metrics.explained_variance_score(y[~trn], avg))
		return pscale[var]*np.stack((y[~trn], preds, avg))
	elif action=='xgtest':
		bst=xgb.XGBRegressor(max_depth=3, learning_rate=.1)
		bst=bst.load_model(modeldir2+dname+'.model')
		preds=bst.predict(x[~trn])
		avg=x[~trn][var+'_10']
		print(dname)
		print('r2', metrics.r2_score(y[~trn], preds))
		print('mse', metrics.mean_squared_error(y[~trn], preds))
		print('mae', metrics.mean_absolute_error(y[~trn], preds))
		print('explained var', metrics.explained_variance_score(y[~trn], preds))
		print('avg comp')
		print('r2', metrics.r2_score(y[~trn], avg))
		print('mse', metrics.mean_squared_error(y[~trn], avg))
		print('mae', metrics.mean_absolute_error(y[~trn], avg))
		print('explained var', metrics.explained_variance_score(y[~trn], avg))
		return pscale[var]*np.stack((y[~trn], preds, avg))

vars=['p_ast', 'p_blk', 'p_dreb', 'p_fg2', 'p_fg3', 'p_ft', 'p_oreb', 'p_stl', 'p_tov']
dnames=['ast', 'blk', 'drb', 'fg2', 'fg3', 'ft', 'orb', 'stl', 'tov']
vars2=['dubdub', 'tridub']
dnames2=['dd', 'td']

xvars={
'p_ast':
['dreb_100', 'p_ast_10', 'p_usg_pct_20', 'pct2_20', 'p_time_2', 'ast_20', 'home', 'p_ft_pct_100', 'fg3_20', 'p_ast_50', 'p_ast_pct_100', 'p_flr_pct_5', 'blk_100', 'p_ft_100', 'p_usg_pct_5', 'game_num', 'p_ast_2', 
'p_ast_5', 'p_flr_pct_20', 'poss_20', 'dreb_20', 'ast_100', 'tov_20', 'stadium', 'p_ast_20', 'p_ast_pct_20', 'p_time_10', 'd_paga_20', 'p_tov_100', 'poss_100', 'p_time_100', 'p_pct3_100', 'p_ast_pct_5', 'fg2_100', 
'dreb_pct_100', 'p_ast_100', 'p_usg_pct_100', 'fg3_100', 'p_fg2_20', 'p_ft_20', 'p_fg2_100', 'fg2_20', 'p_pct2_100', 'pfor_100', 'season', 'p_fg3_20', 'p_time_50', 'pfor_5', 'd_paga_100', 'p_flr_pct_100', 'pfor_20', 
'p_ast_pct_50', 'p_fg3_100', 'pct2_100', 'tov_100', 'dreb_pct_20', 'p_tov_50', 'stl_100'],
'p_blk':
['pfor_50', 'd_poss_2', 'p_drtg_100', 'p_usg_pct_20', 'home', 'p_stops_50', 'p_blk_100', 'blk_100', 'p_stop_pct_100', 'd_tov_100', 'p_flr_pct_10', 'p_stl_50', 'p_flr_pct_20', 'p_time_20', 'd_pfor_20', 'paga_50', 
'd_poss_50', 'p_fouls_20', 'p_stop_pct_10', 'stadium', 'p_stops_5', 'p_blk_20', 'paga_100', 'p_time_10', 'poss_50', 'p_usg_pct_50', 'poss_100', 'p_time_100', 'p_stl_10', 'd_pfor_50', 'p_usg_pct_100', 'p_stl_5', 
'p_drtg_50', 'd_poss_20', 'p_usg_pct_10', 'pfor_100', 'd_tov_50', 'p_drtg_20', 'p_blk_50', 'p_stl_100', 'season', 'p_stl_20', 'p_time_50', 'p_time_5', 'p_fouls_50', 'blk_50', 'p_flr_pct_50', 'p_stop_pct_50', 
'p_flr_pct_100', 'p_drtg_10', 'p_stops_10', 'p_stops_100', 'd_poss_100', 'p_fouls_100', 'p_stop_pct_20', 'd_poss_10'],
'p_dreb':
['dreb_100', 'p_oreb_pct_50', 'dreb_10', 'd_oreb_20', 'p_oreb_100', 'd_dreb_50', 'p_dreb_pct_100', 'p_time_2', 'home', 'p_stops_50', 'oreb_pct_100', 'd_oreb_pct_50', 'd_pfor_5', 'p_ft_100', 'game_num', 'fg2_50', 
'p_oreb_pct_20', 'p_ft_pct_20', 'd_pfor_20', 'p_time_20', 'paga_50', 'd_poss_50', 'p_fg2_50', 'dreb_50', 'poss_20', 'p_pct3_10', 'dreb_2', 'p_pct2_50', 'p_dreb_50', 'paga_100', 'poss_50', 'd_pfor_100', 'p_usg_pct_50', 
'poss_100', 'p_time_100', 'oreb_50', 'p_oreb_pct_100', 'dreb_pct_100', 'paga_10', 'fg3_100', 'p_usg_pct_100', 'p_drtg_50', 'p_ft_20', 'p_fg2_100', 'p_ft_pct_50', 'fg2_20', 'd_poss_5', 'p_pct2_100', 'p_dreb_100', 
'p_oreb_20', 'dreb_pct_5', 'season', 'd_oreb_pct_100', 'p_oreb_50', 'p_dreb_pct_50', 'p_flr_pct_50', 'p_time_50', 'd_oreb_5', 'p_dreb_pct_10', 'p_flr_pct_100', 'p_stop_pct_50', 'tov_100', 'dreb_pct_20', 'd_poss_100', 
'p_ft_50', 'd_oreb_pct_20', 'p_dreb_10'],
'p_fg2':
['p_oreb_pct_50', 'pfor_50', 'dreb_pct_50', 'fg2_10', 'p_oreb_100', 'p_usg_pct_20', 'home', 'p_ft_pct_100', 'ast_50', 'p_ast_50', 'p_ast_pct_100', 'p_ft_100', 'p_usg_pct_5', 'game_num', 'fg2_50', 'p_flr_pct_10', 'p_stl_50', 
'p_fg2_50', 'p_fg2_5', 'ast_100', 'fg2_5', 'p_pct2_50', 'p_ast_20', 'p_ast_pct_20', 'p_fg3_50', 'd_paga_20', 'p_fg2_10', 'p_usg_pct_50', 'poss_50', 'p_tov_100', 'p_usg_pct_2', 'poss_100', 'p_time_100', 'p_pct3_100', 
'p_oreb_pct_100', 'fg2_100', 'dreb_pct_100', 'p_ast_100', 'p_tov_20', 'p_usg_pct_100', 'rest', 'p_fg2_20', 'p_fg2_100', 'fg2_20', 'd_paga_10', 'p_pct2_100', 'p_pct3_5', 'pfor_100', 'p_pct2_5', 'p_flr_pct_2', 'p_stl_100', 
'season', 'p_oreb_50', 'p_time_5', 'p_time_50', 'p_flr_pct_50', 'd_paga_100', 'p_flr_pct_100', 'pfor_20', 'p_ast_pct_50', 'p_fg3_100', 'p_pct3_50', 'p_ft_50', 'd_poss_100', 'p_tov_50', 'pct2_100', 'tov_100', 'stl_100'],
'p_fg3':
['p_oreb_pct_50', 'dreb_pct_50', 'p_fg3_5', 'oreb_pct_50', 'fg3_20', 'p_oreb_100', 'fg3_5', 'p_usg_pct_20', 'home', 'p_ft_pct_100', 'ast_50', 'p_ast_50', 'p_ast_pct_100', 'oreb_pct_100', 'p_flr_pct_5', 'p_ft_100', 
'p_usg_pct_5', 'game_num', 'p_oreb_pct_20', 'p_stl_50', 'd_paga_50', 'p_flr_pct_20', 'p_fg2_50', 'poss_20', 'p_pct3_10', 'ast_100', 'p_pct2_50', 'p_ast_pct_20', 'p_fg3_50', 'd_paga_20', 'poss_50', 'p_tov_100', 'p_usg_pct_2', 
'poss_100', 'p_time_100', 'p_pct3_100', 'p_pct3_20', 'oreb_50', 'p_oreb_pct_100', 'p_fg3_2', 'dreb_pct_100', 'fg3_50', 'p_tov_20', 'fg3_100', 'p_usg_pct_100', 'p_fg2_20', 'p_fg2_100', 'p_ft_pct_50', 'd_paga_10', 
'p_pct2_100', 'p_pct2_20', 'p_stl_100', 'season', 'd_dreb_pct_50', 'd_paga_5', 'p_fg3_20', 'p_stl_20', 'p_pct3_2', 'p_time_5', 'p_time_50', 'd_paga_100', 'p_flr_pct_100', 'pfor_20', 'p_ast_pct_50', 'p_fg3_100', 
'p_pct3_50', 'poss_10', 'fg3_2', 'p_fg3_10', 'fg3_10'],
'p_ft':
['ft_100', 'p_oreb_pct_50', 'pfor_50', 'ft_10', 'ast_pct_50', 'p_oreb_100', 'p_usg_pct_20', 'home', 'p_ft_pct_100', 'ast_50', 'p_ast_pct_100', 'blk_100', 'oreb_pct_100', 'p_tov_50', 'p_ft_100', 'game_num', 'p_pct2_10', 
'ft_20', 'p_flr_pct_20', 'p_time_20', 'ft_pct_50', 'd_fouls_50', 'p_fg2_50', 'ast_pct_100', 'ast_100', 'd_fouls_20', 'p_ast_pct_20', 'p_fg3_50', 'p_usg_pct_50', 'p_tov_100', 'p_usg_pct_2', 'poss_100', 'p_time_100', 
'p_pct3_100', 'p_oreb_pct_100', 'p_ast_100', 'p_usg_pct_100', 'p_fg2_20', 'p_ft_20', 'p_fg2_100', 'p_ft_pct_50', 'ft_50', 'p_pct2_100', 'p_usg_pct_10', 'd_fouls_10', 'pfor_100', 'd_fouls_100', 'p_stl_100', 'season', 
'p_oreb_50', 'p_time_5', 'p_time_50', 'p_flr_pct_50', 'p_flr_pct_100', 'tov_100', 'p_ast_pct_50', 'p_fg3_100', 'p_pct3_50', 'p_ft_50', 'ft_pct_100'],
'p_oreb':
['dreb_100', 'p_oreb_pct_50', 'pfor_50', 'd_poss_2', 'd_dreb_pct_100', 'dreb_pct_50', 'oreb_20', 'oreb_pct_50', 'p_oreb_100', 'd_dreb_50', 'oreb_5', 'dreb_5', 'home', 'p_ft_pct_100', 'p_usg_pct_20', 'blk_100', 
'oreb_pct_100', 'p_ft_100', 'game_num', 'oreb_pct_20', 'oreb_100', 'p_time_20', 'oreb_pct_5', 'd_poss_50', 'p_fg2_50', 'dreb_20', 'poss_20', 'p_pct2_50', 'stadium', 'd_dreb_20', 'd_dreb_100', 'p_dreb_50', 'p_time_10', 
'p_dreb_pct_20', 'p_usg_pct_50', 'p_dreb_20', 'poss_50', 'poss_100', 'tov_50', 'p_time_100', 'oreb_50', 'p_oreb_pct_100', 'dreb_pct_100', 'p_usg_pct_100', 'p_fg2_20', 'p_fg2_100', 'p_ft_pct_50', 'd_poss_20', 'd_poss_5', 
'p_pct2_100', 'pfor_100', 'season', 'd_dreb_pct_50', 'p_oreb_50', 'd_dreb_pct_20', 'p_dreb_pct_50', 'p_flr_pct_50', 'p_time_50', 'p_flr_pct_100', 'tov_100', 'dreb_pct_20', 'd_poss_100', 'p_ft_50', 'd_oreb_pct_20', 'stl_100'],
'p_stl':
['d_poss_2', 'p_drtg_100', 'p_stops_50', 'd_tov_5', 'p_blk_100', 'game_num', 'p_stop_pct_100', 'd_tov_100', 'p_flr_pct_10', 'd_ast_10', 'd_tov_20', 'p_stl_50', 'p_flr_pct_20', 'p_time_20', 'paga_50', 'stl_20', 'd_poss_50', 
'p_stop_pct_10', 'stl_5', 'p_stops_20', 'stadium', 'p_stops_5', 'paga_100', 'stl_50', 'p_time_10', 'p_usg_pct_50', 'poss_100', 'p_time_100', 'stl_2', 'd_tov_2', 'p_stl_10', 'rest', 'p_usg_pct_100', 'p_stl_5', 'p_drtg_50', 
'pfor_10', 'd_tov_10', 'd_poss_20', 'd_poss_5', 'p_drtg_20', 'pfor_100', 'd_tov_50', 'p_blk_50', 'p_stl_100', 'season', 'p_stl_20', 'p_time_50', 'd_ast_50', 'p_flr_pct_50', 'stl_10', 'p_stop_pct_50', 'p_flr_pct_100', 
'pfor_20', 'poss_10', 'p_stops_10', 'p_stops_100', 'p_stop_pct_20', 'p_fouls_100', 'p_stop_pct_5', 'd_poss_10', 'stl_100'],
'p_tov':
['d_poss_2', 'd_dreb_pct_100', 'dreb_pct_50', 'oreb_pct_50', 'ast_pct_50', 'p_oreb_100', 'p_usg_pct_20', 'home', 'p_ast_50', 'oreb_pct_100', 'd_stl_2', 'p_ft_100', 'p_tov_50', 'game_num', 'p_flr_pct_10', 'p_flr_pct_20', 
'p_time_20', 'tov_10', 'd_poss_50', 'p_fg2_50', 'ast_pct_100', 'poss_20', 'tov_20', 'p_ast_20', 'p_dreb_50', 'p_fg3_50', 'p_time_10', 'p_fg2_10', 'poss_50', 'p_usg_pct_50', 'tov_50', 'p_tov_100', 'poss_100', 'p_time_100', 
'poss_5', 'dreb_pct_100', 'p_ast_100', 'p_tov_20', 'p_usg_pct_100', 'p_fg2_20', 'd_stl_100', 'd_poss_20', 'p_dreb_100', 'pfor_100', 'season', 'p_fg3_20', 'p_oreb_50', 'p_time_5', 'p_time_50', 'p_flr_pct_50', 'd_stl_10', 
'd_stl_20', 'p_flr_pct_100', 'pfor_20', 'poss_10', 'p_fg3_100', 'tov_100', 'p_ft_50', 'd_stl_50', 'd_stl_5']
}



with open('invars.pickle', 'wb') as handle:
    pickle.dump(xvars, handle, protocol=pickle.HIGHEST_PROTOCOL)

"""
first=True
predvars=[]
cb=catboost.CatBoostRegressor(iterations=20000, learning_rate=.1, depth=3, od_type='Iter', od_wait=2000)
#dd=pd.read_pickle(datadir+'df_dd.pkl')
#td=pd.read_pickle(datadir+'df_td.pkl')
#train

for var, dname in zip (vars, dnames):
	print(var)
	tmp=model(var, dname, 'train', 20000, xvars)
	#base=pd.read_pickle(datadir+'df_'+dname+'.pkl').dropna()
	#x=base[xvars[var]]
	#print(var)
	#print(xvars[var])
	#print(x.iloc[:, 11])
	#cat_inds=[x.columns.get_loc(c) for c in ['home', 'stadium'] if c in x]
	#cb=catboost.CatBoostRegressor(iterations=iter, learning_rate=.1, depth=3, od_type='Iter', cat_features=cat_inds, od_wait=1500)
	#mod=cb.load_model(modeldir+dname)
	predvars.append('pred_'+var)
	#dd['pred_'+var]=mod.predict(x)
	#td['pred_'+var]=mod.predict(x)
	#dd['pred_'+var]=tmp
	#td['pred_'+var]=tmp

#dd[['game_id', 'player_id', 'name', 'team', 'pop', 'fpts_100', 'dubdub']+predvars].to_pickle('../data/trans2/df_dd1.pkl')
#td[['game_id', 'player_id', 'name', 'team', 'pop', 'fpts_100', 'tridub']+predvars].to_pickle('../data/trans2/df_td1.pkl')
"""
"""
dd=pd.read_pickle(datadir+'df_dd1.pkl')
td=pd.read_pickle(datadir+'df_td1.pkl')
trn=(dd['game_id']<=21900500)
print(dd, dd[trn][predvars], dd[trn]['dubdub'])
ddm=cb.fit(dd[trn][predvars], y=dd[trn]['dubdub'], eval_set=(dd[~trn][predvars], dd[~trn]['dubdub']))
ddm.save_model(modeldir+'dd')
tdm=cb.fit(td[trn][predvars], td[trn]['tridub'], eval_set=(td[~trn][predvars], td[~trn]['tridub']))
tdm.save_model(modeldir+'td')
"""
"""
#test
for var, dname in zip (vars, dnames):
	if first:
		fpts=model(var, dname, 'test', 10000, xvars)
		first=False
	else:
		fpts+=model(var, dname, 'test', 10000, xvars)

print(fpts)
print('fantasypts preds')
print('r2', metrics.r2_score(fpts[0], fpts[1]))
print('mse', metrics.mean_squared_error(fpts[0], fpts[1]))
print('mae', metrics.mean_absolute_error(fpts[0], fpts[1]))
print('explained var', metrics.explained_variance_score(fpts[0], fpts[1]))
print('fantasypts avg')
print('r2', metrics.r2_score(fpts[0], fpts[2]))
print('mse', metrics.mean_squared_error(fpts[0], fpts[2]))
print('mae', metrics.mean_absolute_error(fpts[0], fpts[2]))
print('explained var', metrics.explained_variance_score(fpts[0], fpts[2]))
"""
