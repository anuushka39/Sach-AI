import string
import re
import nltk
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

try:
    nltk.data.find("corpora/wordnet")
except LookupError:
    nltk.download("wordnet")

# nltk.download('stopwords')
# nltk.download('wordnet')
# nltk.download('averaged_perceptron_tagger')
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


#helper func
stop_words = nltk.corpus.stopwords.words('english')
def tokenization(text):
    return re.findall(r'\b\w+\b', text)
def remove_stopwords(text):
    output= [i for i in text if i not in stop_words]
    return output
wordnet_lemmatizer = WordNetLemmatizer()
def lemmatizer(text):
    lemm_text = [wordnet_lemmatizer.lemmatize(word) for word in text]
    return lemm_text

#preprocedd func
def preprocess_text(text):
  text = text.lower()
  # text= ''.join([char for char in text if char not in string.punctuation])
  text = text.translate(str.maketrans(string.punctuation, ' '*len(string.punctuation)))
  tokens = tokenization(text)
  tokens = remove_stopwords(tokens)
  tokens = lemmatizer(tokens)
  return " ".join(tokens)

