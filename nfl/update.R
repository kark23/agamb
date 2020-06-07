library(nflscrapR)
args <- commandArgs(trailingOnly = TRUE)
upd <- scrape_season_play_by_play(args[1], "reg", weeks=args[2])
write.csv(upd, file = "data/update/update.csv")
