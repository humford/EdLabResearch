#Network ezproxy Results Database
library(RSQLite)
library(topicmodels)
library(tidytext)
library(dplyr)
library(ggplot2)

conn <- dbConnect(RSQLite::SQLite(), "~/Documents/Ezproxy/ezproxy-DOI.db")

ezproxy_doi <- dbReadTable(conn, "ezproxy_doi")
subjects <- dbReadTable(conn, "subjects")
doi_subjects <- dbReadTable(conn, "doi_subjects")