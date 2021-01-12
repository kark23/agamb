import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import catboost as cb
import os
import pickle
import copy
from sklearn.metrics import mean_absolute_error
from itertools import product
from pymoo.algorithms.nsga2 import NSGA2
from pymoo.model.problem import Problem
from pymoo.optimize import minimize
from pymoo.visualization.scatter import Scatter
from pymoo.util.termination.f_tol import MultiObjectiveSpaceToleranceTermination
from pymoo.factory import get_problem, get_termination
from mip import Model, xsum, maximize, BINARY, INTEGER
from itertools import permutations
import time

def uniform_split(shape, axis, seed=0):
    np.random.seed(seed)
    arr= np.random.uniform(np.zeros(shape), np.ones(shape))
    arr/= arr.sum(axis=axis).reshape(-1,1)
    return arr

class Lineup_Diversification(Problem):
    def __init__(self, slate, c_pts, c_var, lineupct,  capital, seed=0):
        self.capital= capital
        self.slate= slate
        self.lineups= self.get_lineups(slate, c_pts, lineupct)
        self.exp_val= self.get_expval(self.lineups, c_pts)
        self.covmat= self.get_covmat(self.lineups, c_var)
        lowest_bet= min([cont['entryFee'] for cont in slate['contests']])
        
        super().__init__(n_var= len(self.lineups),
                         n_obj= 2,
                         n_constr= 2,
                         xl=np.zeros(len(self.lineups)),
                         xu=np.ones(len(self.lineups)))
    
    def get_lineups(self, slate, ptcol, lineups, salcap=50000):
        positions= slate['positions']
        pool= pd.concat(slate['players'].values(),ignore_index='True').drop(columns='position')\
            .drop_duplicates().reset_index(drop=True)
        #Establish positions eligibility data structure
        elig= [[1 if plyr['name'] in list(slate['players'][pos]['name']) else 0 for 
            i, pos in enumerate(positions)] for skip, plyr in pool.iterrows()]
        pts= list(pool[ptcol])
        #Set up player salary list
        sal= list(pool['salary'])
        #Set up range just for short reference
        I= range(len(pts))
        J= range(len(positions))
        #Set up results
        results= []
        m = Model()
        m.verbose=False
        x = [[m.add_var(var_type=BINARY) for j in J] for i in I]
        m.objective = maximize(xsum(x[i][j]*elig[i][j]*pts[i] for i in I for j in J))
        #Apply salary cap constraint
        m += xsum((x[i][j]*sal[i] for i in I for j in J)) <= salcap
        #Apply one player per position constraint
        for j in J:
            m+= xsum(x[i][j] for i in I)== 1
        #apply max one position per player constraint
        for i in I:
            m+= xsum(x[i][j] for j in J)<= 1        
        for lineup in range(lineups):
            print(lineup)
            m.optimize()
            #Add lineup to results
            idx= [(i, j) for i in I for j in J if x[i][j].x >= 0.99]
            results.append(pd.concat([pool.iloc[i:i+1] for i, j in idx], ignore_index=True))
            results[-1]['position']= [positions[j] for i, j in idx]
            #Apply constraint to ensure this player combination will not be repeated (cannot have three overlapping players for diversity)
            m+= xsum(x[i][j] for i, skip in idx for j in J)<= len(positions)-3
        return results
    
    def get_expval(self, lineups, ptcol):
        #Simply sum predicted points for each lineup df and convert to len lineups array
        return np.array([lineup[ptcol].sum() for lineup in lineups])
    
    def get_covmat(self, lineups, varcol):
        #Get reference variance df with primary key player
        plyr_var= pd.concat(lineups)[['name', varcol]].drop_duplicates().reset_index(drop=True)
        #Set up lineups x players variance array with player variance filled if included in lineup, else 0
        vrnce= np.array([plyr_var[['name']].merge(lineup[['name', varcol]], how='left')[varcol].fillna(0) 
            for lineup in lineups]) 
        #Initialize lineups x lineups x players covariance matrix empty structure 
        covmat= np.zeros((vrnce.shape[0], vrnce.shape[0], vrnce.shape[1]))
        #Cross add (not correct word) the variance array into the covariance matrix structure, then sum across 3rd axis
        #for true lineup x lineup output covariance matrix
        return (vrnce*(covmat+vrnce==covmat+vrnce.reshape(vrnce.shape[0], -1, vrnce.shape[1]))).sum(axis=2)

    def _evaluate(self, X, out, *args, **kwargs):
        #Optimize lineup allocation for pareto front minimizing portfolio expected pts variance and maximizing 
        #expected pts  
        
        #Define avg lineup expected pts objective (minimize)
        avg_exp_pts= -np.matmul(X, self.exp_val)
        #Define lineup portfolio pt variance objective (minimize)
        port_var= np.matmul(np.matmul(X, self.covmat), X.transpose()).diagonal()
        #Define constraints (allocations sum to approx 1, need upper/lower bounds or it will break)
        hi= X.sum(axis=1)- 1.001
        low= .999- X.sum(axis=1)

        out["F"] = np.column_stack([avg_exp_pts, port_var])
        out["G"] = np.column_stack([hi, low])
