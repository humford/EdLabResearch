#Diffbot ezproxy Results Database
library(RSQLite)

conn <- dbConnect(RSQLite::SQLite(), "~/Documents/ezproxy-diffbot.db")

ezproxy_records <- dbReadTable(conn, "ezproxy_records")
tags <- dbReadTable(conn, "tags")
record_tags <- dbReadTable(conn, "record_tags")

scorehist <- function(record_tags) {
  hist(record_tags$score, breaks = 25, main = paste("Histogram of ezproxy Tag Scores (n = ", toString(nrow(ezproxy_records)), ")", sep = ""), xlab = "Tag Score")
}

counthist <- function(record_tags) {
  hist(record_tags$count, breaks = 10, main = paste("Histogram of ezproxy Tag Count (n = ", toString(nrow(ezproxy_records)), ")", sep = ""), xlab = "Tag Count", col = "lightblue")
}

countdot <- function(record_tags) {
  dotchart(record_tags$count, main = paste("Dot Chart of ezproxy Tag Count (n = ", toString(nrow(ezproxy_records)), ")", sep = ""), xlab = "Tag Count")
}

#categorypiechart <- function(gbooks) {
#  piedata <- sort(table(gbooks$google_category), decreasing = T)
#  pie(piedata, labels = row.names(head(piedata, 15)))
#}

tagfreqpiedotchart <- function(record_tags) {
  piedata <- sort(table(record_tags$tag_id), decreasing = T)
  pie(head(piedata, 25), labels = head(tags[row.names(piedata),"label"], 25))
  dotchart(head(piedata,50), labels = head(tags[row.names(piedata),"label"], 50), cex = 0.8)
}

avgscoreplot <- function(record_tags) {
  
}

tagfreqpiedotchart(record_tags)
