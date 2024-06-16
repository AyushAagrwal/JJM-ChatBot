import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, render_template
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import warnings
from translate import Translator  # Assuming you have installed the 'translate' library
import google.generativeai as genai

warnings.filterwarnings("ignore")

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Load text file and return content
def get_text_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return None

# Split text into chunks
def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=300)
    return splitter.split_text(text)

# Get embeddings for each chunk
def get_vector_store(chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

# Create a conversational chain
def get_conversational_chain():
    prompt_template = """
    You are an expert on the JJM Operational Guidelines. Answer the question as detailed as possible from the provided context. 
    If the answer is not in the provided context, say "The answer is not available in the context." Do not provide a wrong answer.

    Context:\n{context}\n
    Question:\n{question}\n

    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", client=genai, temperature=0.8, max_tokens=1000, top_p=0.98, top_k=50, stop_sequences=["\n"])
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    return load_qa_chain(llm=model, chain_type="stuff", prompt=prompt)

# Global initialization flag
initialized = False

# Translation function using 'translate' library
def translate(text, target_language):
    translator = Translator(to_lang=target_language)
    try:
        translated_text = translator.translate(text)
        return translated_text
    except Exception as e:
        print(f"Translation error: {e}")
        return text

@app.before_request
def before_request():
    global initialized
    if not initialized:
        file_path = "JJM_Operational_Guidelines.txt"
        raw_text = get_text_content(file_path)
        if raw_text:
            text_chunks = get_text_chunks(raw_text)
            get_vector_store(text_chunks)
            initialized = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    user_question = data['question']
    selected_language = data['language']

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = vector_store.similarity_search(user_question)
    
    chain = get_conversational_chain()
    response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
    answer = response['output_text']
    
    translated_answer = translate(answer, selected_language)
    
    if "The answer is not available in the context." in answer:
        return jsonify({"answer": translated_answer, "available": False})
    else:
        return jsonify({"answer": translated_answer, "available": True})

@app.route('/google_search', methods=['POST'])
def google_search():
    data = request.get_json()
    query = data['query']
    selected_language = data['language']
    try:
        headers = {
            "User-Agent": "Chrome/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(f"https://www.google.com/search?q={query}", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = soup.find_all('div', class_='BNeawe s3v9rd AP7Wnd', limit=2)
        
        results_set = set()
        for result in search_results:
            text = result.text.strip()
            if text and text not in results_set:  # Ensure the result is unique
                translated_result = translate(text, selected_language)
                results_set.add(translated_result)
        
        results = list(results_set)
        
        if results:
            return jsonify({"answers": results})
        else:
            return jsonify({"answers": ["No results found."]})
    except Exception as e:
        return jsonify({"answer": f"Error occurred during search: {e}"})

# Error handling routes    
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('error.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
