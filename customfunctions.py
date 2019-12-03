import numpy as np

def oddtoprob(sign,val):
    ref={'-': val,'+': 100}
    return ref[sign]/(100+val)

def distri(odds):
    prts=[]
    for odd in odds:
        prts+=odd[:2]
    prts=sorted(list(set(prts)))
    #mainmatrix=matrix(len(odds),len(prts)-1)
    for i in len(odds):
        ind1,ind2=(prts.index(odds[i][0]),prts.index(odds[i][1]))
        inds=np.linspace(ind1,ind2,1+abs(ind1-ind2))
        for ind in inds:
            #mainmatrix[i][int(ind)]=1
        #cond[i]=odds[i][2]
        #solve matrix
