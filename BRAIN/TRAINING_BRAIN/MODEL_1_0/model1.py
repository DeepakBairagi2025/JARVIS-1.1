import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from FUNCTION.JARVIS_SPEAK.speak import speak # Make sure your Mouth.py has a valid speak() function

# Load your Q&A dataset from a text file
def load_dataset(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        qna_pairs = [line.strip().split(':') for line in lines if ':' in line]
        dataset = [{'question': q.strip(), 'answer': a.strip()} for q, a in qna_pairs]
    return dataset

# Preprocess the text
def preprocess_text(text):
    stop_words = set(stopwords.words('english'))
    ps = PorterStemmer()
    tokens = word_tokenize(text.lower(), preserve_line=True)

    tokens = [ps.stem(token) for token in tokens if token.isalnum() and token not in stop_words]
    return ' '.join(tokens)

# Train the TF-IDF vectorizer
def train_tfidf_vectorizer(dataset):
    corpus = [preprocess_text(qa['question']) for qa in dataset]
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(corpus)
    return vectorizer, X

# Retrieve the most relevant answer
def get_answer(question, vectorizer, X, dataset):
    question = preprocess_text(question)
    question_vec = vectorizer.transform([question])
    similarities = cosine_similarity(question_vec, X)
    best_match_index = similarities.argmax()
    return dataset[best_match_index]['answer']

# Main function
def mind(text):
    # Replace 'your_dataset.txt' with the path to you Q&A dataset
    dataset_path = r"C:\Users\Deepak Bairagi\Desktop\JARVIS 1.1\DATA\BRAIN_DATA\QNA_DATA\qna.txt"  # Make sure this file exists
    dataset = load_dataset(dataset_path)

    vectorizer, X = train_tfidf_vectorizer(dataset)
    user_question = text
    answer = get_answer(user_question, vectorizer, X, dataset)
    speak(answer)

x = mind("hello")
print(x)