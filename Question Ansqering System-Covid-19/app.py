from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import nltk
from nltk.tokenize import word_tokenize
from question_answer import get_answer
from question_similarity import load_questions, find_similar_questions  

nltk.download('punkt')

app = Flask(__name__)

all_questions = load_questions('COVID-QA.json')

# Define a route to serve the query_form.html file
@app.route('/')
def index():
    return send_from_directory('', 'query_form.html')

def process_query(query):
    tokens = word_tokenize(query)
    if len(tokens) >= 4:
        n_grams = [' '.join(tokens[i:i+4]) for i in range(len(tokens) - 3)]
    elif len(tokens) == 3:
        n_grams = [' '.join(tokens[i:i+3]) for i in range(len(tokens) - 2)]
    elif len(tokens) == 2:
        n_grams = [' '.join(tokens[i:i+2]) for i in range(len(tokens) - 1)]
    else:
        n_grams = tokens  # Use the single words if the query is very short
    return n_grams

def fetch_relevant_abstracts(db_path, n_grams):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            if len(n_grams) > 1:
                query_parts = ["abstract LIKE ?" for _ in n_grams]  # Use all n-grams
            else:
                query_parts = ["abstract LIKE ?" for _ in n_grams]  # Use all for shorter queries

            query = "SELECT DISTINCT abstract FROM metadata WHERE " + " OR ".join(query_parts) + " LIMIT 4"
            cursor.execute(query, ['%' + gram + '%' for gram in n_grams])

            abstracts = cursor.fetchall()

        return [a[0] for a in abstracts]
    except sqlite3.Error as e:
        app.logger.error('SQLite error: %s', str(e))
        return []  # Return an empty list if an error occurs

@app.route('/query', methods=['POST'])
def process_query_request():
    try:
        data = request.get_json()
        user_query = data['query']
        app.logger.info(f"Received query: {user_query}")

        # Find 3 similar questions to the user's query
        similar_questions = find_similar_questions(all_questions, user_query, 3)
        app.logger.info("Similar Questions: " + ", ".join(similar_questions))

        # Process the user query to get n-grams
        n_grams = process_query(user_query)
        app.logger.info(f"Processed n-grams: {n_grams}")

        # Fetch relevant abstracts from the database
        relevant_abstracts = fetch_relevant_abstracts('cord19_metadata.db', n_grams)
        app.logger.info(f"Fetched {len(relevant_abstracts)} relevant abstracts")

        # Check if there are any relevant abstracts and process the first one
        if relevant_abstracts:
            first_abstract = relevant_abstracts[0]
            app.logger.info(f"Processing first abstract: {first_abstract[:50]}...")

            answer = get_answer(user_query, first_abstract)
            app.logger.info(f"Generated answer: {answer}")

            answered_abstracts = [{'abstract': first_abstract, 'answer': answer}]
        else:
            app.logger.warning("No relevant abstracts found.")
            answered_abstracts = []

        return jsonify({'answered_abstracts': answered_abstracts, 'similar_questions': similar_questions}), 200

    except Exception as e:
        app.logger.error(f"An error occurred: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred while processing the request'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5003)

