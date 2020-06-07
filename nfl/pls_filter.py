import pandas as pd
import numpy as np
import random
from sklearn.cross_decomposition import PLSRegression
from scipy.spatial import distance
from sklearn.neighbors import NearestNeighbors
import pickle
import copy
import time

def STAND(df,ref,cols):
    tmp=df.copy()
    for col in cols:
        if tmp[col].std()>0:
            tmp[col]=(tmp[col]-ref[col].mean())/ref[col].std()
        else:
            tmp[col]=0
    return tmp

def REVSTAND(df,ref,cols):
    tmp=df.copy()
    for col in cols:
        if ref[col].std()>0:
            tmp[col]=tmp[col]*ref[col].std()+ref[col].mean()
        else:
            tmp[col]=0
    return tmp

def PLS_SAVE(comp,dfdir,xcol,ycol,save,dropna=True,write=True):
    df=pd.read_csv(dfdir)
    if dropna:
        df.dropna(inplace=True)
    df=STAND(df,df,xcol+ycol)
    mod=PLSRegression(n_components=comp)
    mod.fit(df[xcol], df[ycol])
    if write:
        pickle.dump(mod, open(save, 'wb'))
    return mod

def PLS_LTRANS(dirdf,dirref,xcol,ycol,dirpls,save,dropna=True,write=True):
    df=pd.read_csv(dirdf)
    ref=pd.read_csv(dirref)
    if dropna:
        df.dropna(inplace=True)
        ref.dropna(inplace=True)
    pls=pickle.load(open(dirpls, 'rb'))
    df=STAND(df,ref,xcol+ycol)
    xtrans=pls.transform(df[xcol])
    transdf=pd.DataFrame(data=xtrans,columns=['dim'+str(i) for i in range(len(xtrans[0]))])
    for col in ycol:
        transdf[col]=df[col]
    if write:
        transdf.to_csv(save)
    return transdf

def D_RESAMP(dists,parts,exp=2):
    imp=1/(np.array(dists)**exp)
    #print(imp)
    w=list(imp/imp.sum())
    N = len(w)
    new_particles = []
    index = int(random.random() * N)
    beta = 0.0
    mw = max(w)
    for i in range(N):
        beta += random.random() * 2.0 * mw
        while beta > w[index]:
            beta -= w[index]
            index = (index + 1) % N
        new_particles.append(index)
    return [new_particles[i] for i in list(np.random.randint(N, size=parts))]

def REG_FILT(dircomp,dirref,pred,parts,save,exp=2,samp=None,write=True):
    comp=pd.read_csv(dircomp)
    ref=pd.read_csv(dirref)
    xcols=[col for col in comp.columns if 'dim' in col]
    ycols=[col for col in comp.columns if 'dim' not in col]
    if samp is not None and samp<len(comp):
        comp=comp[np.random.rand(len(tmp)) < samp/len(comp)]
    distances=distance.cdist(pred[xcols], comp[xcols], 'euclidean')[0]
    #print(distances)
    out=comp.ix[D_RESAMP(distances,parts,exp)][ycols]
    out=REVSTAND(out,ref,ycols)
    if write:
        out.to_csv(save)
    return out
