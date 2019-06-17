#Google Books Sierra Database
library(RSQLite)

conn <- dbConnect(RSQLite::SQLite(), "~/Documents/sierra-checkout-book.db")

sierrabooks_checkout <- dbReadTable(conn, "sierrabooks")

d <- sort(table(sierrabooks_checkout[,13]), decreasing = T)

hist(sierrabooks_checkout$partial_title_sim, breaks = 75, main = paste("Histogram of Title Fuzzy Matching Scores TEST 6 (n = ", toString(nrow(sierrabooks_checkout)), ")", sep = ""), xlab = "Fuzzy Matching Score")
hist(sierrabooks_checkout$partial_author_sim, breaks = 75, main = paste("Histogram of Author Fuzzy Matching Scores TEST 6 (n = ", toString(nrow(sierrabooks_checkout)), ")", sep = ""), xlab = "Fuzzy Matching Score")

#Research Sierra Database
library(RMariaDB)

dbpassword = "S@YZfH"

researchDb <- dbConnect(RMariaDB::MariaDB(), user = "research", password = dbpassword, dbname = "research-sierra", host = "analytics.tc-library.org")

rb = dbSendQuery(researchDb, "SELECT * FROM bib")
sierrabooks <- dbFetch(rb)

rs = dbSendQuery(researchDb, "SELECT * FROM checkout")
sierrarecords <- dbFetch(rs)

ri = dbSendQuery(researchDb, "SELECT * FROM items")
sierraitems <- dbFetch(ri)

categorypiechart <- function(gbooks) {
  piedata <- sort(table(gbooks$google_category), decreasing = T)
  pie(piedata, labels = row.names(head(piedata, 15)))
}

categorypiechart(sierrabooks_checkout)

#d <- sort(table(sierrarecords[,3]), decreasing = T)

#d <- sort(table(sierraitems[,5]), decreasing = T)

#d <- sort(table(sierrabooks[,11]), decreasing = T)

#pie(d, labels = row.names(head(d, 15)))

#for (id in as.integer(row.names(d))) {
#  print(which(sierrabooks$sierra_id == id))
#  print(sierrabooks[which(sierrabooks$sierra_id == id), ])
#}

