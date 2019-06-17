library(RMariaDB)

dbpassword = "S@YZfH"

researchDb <- dbConnect(RMariaDB::MariaDB(), user = "research", password = dbpassword, dbname = "ezproxy-logs-oclc", host = "analytics.tc-library.org")

query = "SELECT * FROM ezporxy_spu"

rs = dbSendQuery(researchDb, query)
dbRows <- dbFetch(rs)

dbRows$datetime <- as.Date(dbRows$datetime)

t <- as.data.frame(table(dbRows$datetime))

#dbRows$CatelogDate <- as.Date(dbRows$CatelogDate)

d <- sort(table(dbRows[,5]), decreasing = T)

#d <- sort(table(sierraitems[,5]))

#t <- as.data.frame(table(dbRows$CatelogDate))

t$Var1 <- as.Date(t$Var1)

pct <- round(d / sum(d)*100)
lbls <- paste(row.names(d), pct)
lbls <- paste(lbls, "%", sep = "")

pie(d, labels = head(lbls, 15))

#dotchart(head(d,50), cex = 1)

dbListTables(researchDb)
dbDisconnect(researchDb)