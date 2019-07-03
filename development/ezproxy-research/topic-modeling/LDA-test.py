import random
import json
import sqlite3
import spacy
import mysql.connector
from spacy.lang.en import English
import nltk
from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer
from gensim import corpora
import pickle
import gensim
import pyLDAvis.gensim

spacy.load('en')
parser = English()
nltk.download('wordnet')
nltk.download('stopwords')
en_stop = set(nltk.corpus.stopwords.words('english'))

def adapt_json(data):
    return (json.dumps(data, sort_keys=True)).encode()

def convert_json(blob):
    return json.loads(blob.decode())

def get_sierra_db():
	researchdb = mysql.connector.connect (
		host = "analytics.tc-library.org",
		user = "research",
		passwd = "S@YZfH",
		database = "research-sierra"
	)
	return researchdb

def tokenize(text):
	lda_tokens = []
	tokens = parser(text)
	for token in tokens:
		if token.orth_.isspace():
			continue
		elif token.like_url:
			lda_tokens.append('URL')
		elif token.orth_.startswith('@'):
			lda_tokens.append('SCREEN_NAME')
		else:
			lda_tokens.append(token.lower_)
	return lda_tokens

def get_lemma(word):
	lemma = wn.morphy(word)
	if lemma is None:
		return word
	else:
		return lemma

def get_lemma2(word):
	return WordNetLemmatizer().lemmatize(word)

def prepare_text_for_lda(text):
	tokens = tokenize(text)
	tokens = [token for token in tokens if len(token) > 4]
	tokens = [token for token in tokens if token not in en_stop]
	tokens = [get_lemma(token) for token in tokens]
	return tokens

researchdb = get_sierra_db()
mysql_cursor = researchdb.cursor()

sqlite3.register_adapter(dict, adapt_json)
sqlite3.register_adapter(list, adapt_json)
sqlite3.register_adapter(tuple, adapt_json)
sqlite3.register_converter('JSON', convert_json)

conn = sqlite3.connect("ezproxy-DOI.db")
sqlite_cursor = conn.cursor()

# mysql_cursor.execute("SELECT title FROM bib")
# f = mysql_cursor.fetchall()[::1]

# sqlite_cursor.execute("SELECT title FROM ezproxy_doi")
# f = sqlite_cursor.fetchall()[::1]

# text_data = []
# counter = 1
# for item in f:
# 	line = item[0]
# 	if not line:
# 		continue	
# 	tokens = prepare_text_for_lda(line)
# 	if tokens:
# 		#print(tokens)
# 		text_data.append(tokens)
# 	print(f"Completed {counter} of {len(f)}")
# 	counter += 1

# dictionary = corpora.Dictionary(text_data)
# corpus = [dictionary.doc2bow(text) for text in text_data]
# pickle.dump(corpus, open('corpus.pkl', 'wb'))
# dictionary.save('dictionary.gensim')

# NUM_TOPICS = 12
# ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics = NUM_TOPICS, id2word = dictionary, passes = 15)
# ldamodel.save('model12.gensim')

dictionary = gensim.corpora.Dictionary.load('dictionary.gensim')
corpus = pickle.load(open('corpus.pkl', 'rb'))
ldamodel = gensim.models.ldamodel.LdaModel.load('model12.gensim')

lda_display = pyLDAvis.gensim.prepare(ldamodel, corpus, dictionary, sort_topics=False)
pyLDAvis.show(lda_display)

topics = ldamodel.print_topics(num_words = 10)
for topic in topics:
	print(topic)

new_doc = 'Research Findings on Early First Language Attrition: Implications for the Discussion on Critical Periods in Language Acquisition'
new_doc = prepare_text_for_lda(new_doc)
new_doc_bow = dictionary.doc2bow(new_doc)
print(new_doc_bow)
print(ldamodel.get_document_topics(new_doc_bow))


