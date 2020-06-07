import os
import numpy as np
import pandas as pd
import scipy.optimize as spo

def ovrlap_corr(xvar, yvar, zvar):
	return zvar/((xvar+zvar)**.5 *(yvar+zvar)**.5)

def adj_sharpe(w, mu, q, n=.5):
	return -np.matmul(mu, w)/np.matmul(np.matmul(w.transpose(), q), w)**n

def brute_opt(df, nm, pos, seed=1):
	np.random.seed(seed)
	#for file in os.listdir("optdf"):
		#if file.endswith(".csv"):
			#fl=os.path.join("optdf/", file)
	#df=pd.read_csv(fl)
	#preds=pd.read_pickle('../data/pred/predictions.pkl')
	#df=df.merge(preds, left_on='Name', right_on='name')
	#print(df[['name', 'AvgPointsPerGame', 'fpts', 'fpts_100']])
	shape=[]
	tiers=list(df[pos].unique())
	vals=[]
	avals=[]
	names=[]
	sds=[]
	pdict={}
	for tier in tiers:
		shape.append((df[pos]==tier).sum())
		vals.append(list(df[df[pos]==tier]['fpts']))
		avals.append(list(df[df[pos]==tier]['scr']))
		names.append(list(df[df[pos]==tier][nm]))
		sds.append(list(df[df[pos]==tier]['fpts_100']))
	fp=np.zeros(shape)
	fpv=np.zeros(shape)
	for i in range(len(tiers)):
		#b=np.array(vals[i])
		dim_array=np.ones(len(shape), int)
		dim_array[i]=-1
		#b_reshaped=b.reshape(dim_array)
		fp+=np.array(vals[i]).reshape(dim_array) #b_reshaped
		#b=np.array(sds[i])
		#b_reshaped=b.reshape(dim_array)
		fpv+=np.array(sds[i]).reshape(dim_array)
	opt=fp/fpv
	lineupmax=1000
	inds= np.flip(np.unravel_index(fp.flatten().argsort()[-lineupmax:], fp.shape), 1)
	lineup=[]
	score=[]
	actual=[]
	for i in range(lineupmax):
		lineup.append([])
		score.append(0.)
		actual.append(0.)
		for j in range(len(tiers)):
			lineup[i].append(names[j][inds[j][i]])
			score[i]+=vals[j][inds[j][i]]
			actual[i]+=avals[j][inds[j][i]]
		#print(i, score[i], lineup[i])

	for i in range(len(names)):
		for j in range(len(names[i])):
			pdict[names[i][j]]=(vals[i][j], sds[i][j])
	#print(len(pdict))
	#corrs=np.zeros((lineupct, lineupct))
	lineupct=100
	s_fwd=.05
	s_lag=.01
	while s_fwd/s_lag>1.07 and lineupct*1.5<=lineupmax:
		lineupct=int(lineupct*1.5)
		s_lag=s_fwd
		covmat=np.zeros((lineupct, lineupct))
		for i in range(lineupct):
			for j in range(lineupct):
				covmat[i][j]=sum([pdict[nm][1] for nm in lineup[i] if nm in lineup[j]])

		result=spo.minimize(adj_sharpe, lineupct*[1./lineupct],args=(np.array(score[:lineupct]), covmat, 1, ), method='SLSQP', bounds=tuple((0, 1) for _ in range(lineupct)), \
			constraints=({'type':'eq','fun': lambda inputs: np.sum(inputs)-1}), options={'disp':True} )

		w=result.x
		#print(w)
		ret=np.matmul(np.array(score[:lineupct]), w)
		pvar=np.matmul(np.matmul(w.transpose(), covmat), w)
		s_fwd=ret/pvar
		#print(s_fwd)
		print(lineupct)
	results=[(",".join(lineup[i]), w[i], actual[i]) for i in range(lineupct-1) if w[i]>=.01]
	#pd.DataFrame(data={'lineup':[x[0] for x in results], 'allocation':[x[1] for x in results]}).to_csv('allocations/allocations.csv')
	return pd.DataFrame(data={'lineup':[x[0] for x in results], 'allocation':[x[1] for x in results], 'real_scr':[x[2] for x in results] })
