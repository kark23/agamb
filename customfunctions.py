import numpy as np

def oddtoprob(sign,val):
    ref={'-': val,'+': 100}
    return ref[sign]/(100+val)

def build_dist(odds):
    prts=[]
    for odd in odds:
        prts+=odd[:2]
    prts=sorted(list(set(prts)))
    mainmat=np.zeros((len(odds),len(prts)-1))
    cond=np.zeros(len(odds))
    print(prts)
    for i in range(len(odds)):
        ind1,ind2=(prts.index(odds[i][0]),prts.index(odds[i][1]))
        inds=np.linspace(ind1,ind2-1,ind2-ind1)
        for ind in inds:
            mainmat[i,int(ind)]=1
        cond[i]=odds[i][2]
    approx=np.matmul(np.linalg.inv(mainmat),cond)
    print(approx)
    def int_dist(lo,hi):
        prob=0.
        strt=False
        for i in range(len(prts)):
            if strt:
                prob+=approx[i]
            if lo>=prts[i] and lo<=prts[i+1]:
                prob+=approx[i]*(prts[i+1]-lo)/(prts[i+1]-prts[i])
                strt=True
            if hi>=prts[i] and hi<=prts[i+1]:
                prob-=approx[i]*(prts[i+1]-hi)/(prts[i+1]-prts[i])
                return prob
    return int_dist
