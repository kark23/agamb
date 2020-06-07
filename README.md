# Automated Gambling Strategy Pipeline

## Overview
The goal of this project is to utilize advanced ml/prtfolio diversification methods in order to build a stable/profitable gambling strategy. The first iteration of this project is designed for fantasy basketball, but should be largely reapplicable toward other sports/gambling channels. The general structuring of the project will follow the asset management framework outlined in [Advances in Financial Machine Learning (Lopez de Prado 2018).](https://www.amazon.com/Advances-Financial-Machine-Learning-Marcos/dp/1119482089)

## Data Curation
* Scrape 20 years of historical play-by-play game data for training the base model
* Develop automated pipeline to append data daily for purpose of updating player time series and eventual model retrain
* Scrape fantasy competition data for strategy backtesting purposes/competition evaluation
## Feature Analysis
* Transform raw play-by-play data to usable structure for player/team time series modeling
* Evaluate feature importance to various model components to condense necessary input
## Strategy
* Model each component of fantasy score separately using the catboost regressor model
* Develop bet diversification optimization system, across teams/players/game type/competition (game types with flexibility on player slotting will require [MIP,](https://github.com/coin-or/python-mip) but otherwise basic continuous optimization methods can be used)

<div align="center">
  
![alt text](https://github.com/kark23/agamb/blob/master/figs/fig1.PNG?raw=true)
Figure 1: Optimization Outline

![alt text](https://github.com/kark23/agamb/blob/master/figs/fig2.PNG?raw=true)
Figure 2: Simplifying Equation for Bet Covariance Matrix

</div>

## Backtesting
* Evaluate historical in-sample/out=of-sample model accuracy v. actual and v. host site predictions
* Strategy can be backtested/adjusted through scraped competition data
## Deployment
* Wrapper script ties together data update, model prediction, ingestion of daily player pricing, and optimized bet allocation
* Injury disqualification and final bet placement will be done manually for first round of implementation
## Portfolio Oversight
* Quality of competition, model stability through regime change, and strategy comparative performance v. other investment strategies will be actively tracked
