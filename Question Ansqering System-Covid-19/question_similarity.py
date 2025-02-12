import json
import Levenshtein

# Function to load questions from the JSON file
def load_questions(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    questions = []
    for section in data['data']:
        for paragraph in section['paragraphs']:
            for qa in paragraph['qas']:
                questions.append(qa['question'])
    return questions

# Function to find similar questions
def find_similar_questions(questions, base_question, num_similar=3):
    distances = []
    for question in questions:
        if question != base_question:
            distance = Levenshtein.distance(base_question, question)
            distances.append((question, distance))
    # Sort by distance
    distances.sort(key=lambda x: x[1])
    # Return the questions with the smallest distances
    return [question for question, _ in distances[:num_similar]]
