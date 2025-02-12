from transformers import pipeline
import tensorflow as tf

local_model_directory = '.'

# Initialize the question-answering pipeline with your local model
question_answerer = pipeline("question-answering", model=local_model_directory)

def get_answer(question, context):
    try:
        print(f"Question: {question}")
        print(f"Context: {context[:50]}...")  # Print a portion if context is long
        result = question_answerer(question=question, context=context)
        print(f"Answer: {result['answer']}")
        return result['answer']
    except Exception as e:
        print(f"Error in get_answer: {e}")
        return "Error processing the answer."

#question = "What is COVID-19?"
#context = "COVID-19 is caused by a coronavirus called SARS-CoV-2."
#answer = get_answer(question, context)
#print(answer)
