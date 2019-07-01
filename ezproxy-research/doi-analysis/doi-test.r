#Diffbot ezproxy Results Database
library(RSQLite)
library(topicmodels)
library(tidytext)
library(dplyr)
library(ggplot2)

conn <- dbConnect(RSQLite::SQLite(), "~/Git/EdLabResearch/ezproxy-research/ezproxy-DOI-old.db")

ezproxy_doi <- dbReadTable(conn, "ezproxy_doi")
subjects <- dbReadTable(conn, "subjects")
doi_subjects <- dbReadTable(conn, "doi_subjects")
users <- dbReadTable(conn, "ezproxy_users")
access_records <- dbReadTable(conn, "access_records")

userdata <- users[which(users$uni == "dnm2133"), "ezproxy_user_id"]
l <- ezproxy_doi[access_records[which(access_records$ezproxy_user_id == 14), "ezproxy_doi_id"], "title"]

subjectfreqpiedotchart <- function(doi_subjects) {
  piedata <- sort(table(doi_subjects$subject_id), decreasing = T)
  pie(piedata, labels = head(subjects[row.names(piedata),"subject"], 15))
  dotchart(head(piedata,50), labels = head(subjects[row.names(piedata),"subject"], 50), cex = 0.8)
}

get_dois_for_user <- function(user) {
  records <- access_records[which(access_records$ezproxy_user_id == which(users$uni == user)), "ezproxy_doi_id"]
  for (record in records) {
    i <- doi_subjects[which(doi_subjects$ezproxy_doi_id == record), "subject_id"]
    i
  }
}

library(janeaustenr)
book_words <- austen_books() %>%
  unnest_tokens(word, text) %>%
  count(book, word, sort = TRUE)

#subjectfreqpiedotchart(doi_subjects)

title_df <- tibble(text = ezproxy_doi$title, item = ezproxy_doi$ezproxy_doi_id)

title_words <- title_df %>%
  unnest_tokens(word, text) %>%
  count(item, word, sort = TRUE)

total_words <- title_words %>%
  group_by(item) %>%
  summarize(total = sum(n))

title_words <- left_join(title_words, total_words)

title_words <- title_words %>%
  bind_tf_idf(word, item, n) %>%
  filter(tf_idf > 0.4)

title_dtm <- title_words %>%
  cast_dtm(item, word, n)

title_LDA <- LDA(title_dtm, k=5, control = list(seed = 1234))

ezproxy_topics <- tidy(title_LDA, matrix = "beta")

ezproxy_top_terms <- ezproxy_topics %>%
  group_by(topic) %>%
  top_n(10, beta) %>%
  ungroup() %>%
  arrange(topic, -beta)

ezproxy_top_terms %>%
  mutate(term = reorder(term, beta)) %>%
  ggplot(aes(term, beta, fill = factor(topic))) +
  geom_col(show.legend = FALSE) +
  facet_wrap(~ topic, scales = "free") +
  coord_flip()

#count(text, sort = TRUE)
