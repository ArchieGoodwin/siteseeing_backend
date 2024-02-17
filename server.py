import json
import os
from flask import Flask, request, jsonify, send_file
import subprocess
import threading
import random
import psycopg2
import os
import io


from dbmanager import add_qa, add_screen, delete_screen, fetch_data, fetch_qa, fetch_screen_by_link, fetch_site_by_id, fetch_site_by_link, fetch_sites_with_categories, fetch_sites_with_keywords, get_record_count, search_sc_sites
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from qa_session import find_embedding_vectors, find_embedding_vectors_all, generate_answer

app = Flask(__name__)

def run_script_in_background(script_name, websites, user_id):
    # Run the script as a subprocess
    subprocess.Popen(["python", script_name, websites, user_id])


@app.route('/execute', methods=['POST'])
def run_script():
    # Parse JSON from the request
    data = request.json

    # Extract values from JSON
    websites = data.get('websites', [])
    user_id = data.get('user_id')
    json_string = json.dumps(websites)
    # Start the script in a separate thread
    if websites and user_id:
        thread = threading.Thread(target=run_script_in_background, args=("main.py", json_string, user_id))
        thread.start()

        return jsonify({"message": "Script execution started."}), 200
    else:
        return jsonify({"error": "Invalid data provided."}), 400


#create GET request returning the records count using dbmanager function get_records_count
@app.route('/sites_count', methods=['GET'])
def get_sites_count():
    try:
        # Fetch the site details by id
        count = get_record_count()
        return jsonify({"count": count}), 200

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data", error)
        #return 200 with message
        return jsonify({"error": "not found"}), 500


#return the questions and answers for the site using link in request
@app.route('/qa/<site_link>', methods=['GET'])
def get_qa_by_link(site_link):
    try:
        # Fetch the site details by id
        qa_dict = fetch_qa(site_link, "ca16c64d-961a-498f-a856-62de7a083f6f")
        print("qa_dict = ", qa_dict)
        return jsonify(qa_dict), 200

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data", error)
        #return 200 with message
        return jsonify({"error": "not found"}), 404

#ask question for site using link in request
@app.route('/qa', methods=['POST'])
def ask_question():
    try:
        # Parse JSON from the request
        data = request.json

        # Extract values from JSON
        link = data.get('link', '')
        question = data.get('question', '')
        userId = data.get('userId', '')
        if not link or not question:
            return jsonify({"error": "Invalid data provided."}), 400
    
        embeddings_result = find_embedding_vectors(question, link)
        answer = generate_answer(question, embeddings_result)

        add_qa(link.rstrip('/').replace("http://", "").replace("https://", ""), question, answer, userId)
        return jsonify({"message": "success", "answer": answer}), 200
    except (Exception, psycopg2.Error) as error:
        print("Error while inserting data", error)
        return jsonify({"error": "can't answer"}), 500

#ask question for site using link in request
@app.route('/narrow/package', methods=['POST'])
def prepare_batch():
    try:
        # Parse JSON from the request
        data = request.json

        # Extract values from JSON
        question = data.get('question', '')
        userId = data.get('userId', '')
        if not question:
            return jsonify({"error": "Invalid data provided."}), 400
    
        embeddings_result = find_embedding_vectors_all(question)

        return jsonify({"message": "success", "results": embeddings_result}), 200
    except (Exception, psycopg2.Error) as error:
        print("Error while inserting data", error)
        return jsonify({"error": "can't answer"}), 500


#get screen by site link
@app.route('/screens/<site_link>', methods=['GET'])
def get_screen_by_link(site_link):
    try:
        print("site_link = ", site_link)
        # Fetch the site details by id
        screen_dict = fetch_screen_by_link(site_link)
        if screen_dict == None:
            return jsonify({"error": "not found"}), 200
        #print("screen_dict = ", screen_dict)
        return jsonify(screen_dict), 200

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data", error)
        #return 200 with message
        return jsonify({"error": "not found"}), 200

    

#add screen to site by link
@app.route('/screens', methods=['POST'])
def add_screen_to_site():
    try:
        # Parse JSON from the request
        data = request.json

        # Extract values from JSON
        link = data.get('link', '')
        screen = data.get('screen', '')
        if not link or not screen:
            return jsonify({"error": "Invalid data provided."}), 200
    
        result = fetch_screen_by_link(link)
        if result == None:
            add_screen(link, screen)
            return jsonify({"message": "success"}), 200
        if result['screen'] != None:
            delete_screen(link)
            add_screen(link, screen)
        

        return jsonify({"message": "success"}), 200
    except (Exception, psycopg2.Error) as error:
        print("Error while inserting data", error)
        return jsonify({"error": "can't insert"}), 200


@app.route('/sites', methods=['GET'])
def get_sites():
    try:
       # Default values
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        sort = request.args.get('sort', 'createdAt')


        # Convert the results to a list of dictionaries
        sites_list = fetch_data(page, page_size, sort)
        
        return jsonify(sites_list), 200

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data", error)
        return jsonify({"error": "Error while fetching data"}), 500


@app.route('/sites/by-keywords', methods=['GET'])
def get_sites_by_keywords():
    try:
        # Extract keywords from the query string
        keywords = request.args.get('keywords', '')

        # Fetch the sites with the specified keywords
        sites_list = fetch_sites_with_keywords(keywords)

        return jsonify(sites_list), 200

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data", error)
        return jsonify({"error": "Error while fetching data"}), 500
    

@app.route('/sites/by-categories', methods=['GET'])
def get_sites_by_categories():
    try:
        # Extract keywords from the query string
        categories = request.args.get('categories', '')

        # Fetch the sites with the specified keywords
        sites_list = fetch_sites_with_categories(categories)

        return jsonify(sites_list), 200

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data", error)
        return jsonify({"error": "Error while fetching data"}), 500

#load site details by site link
@app.route('/sites/<site_id>', methods=['GET'])
def get_site_by_id(site_id):
    try:
        # Fetch the site details by id
        site_dict = fetch_site_by_id(site_id)

        return jsonify(site_dict), 200

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data", error)
        return jsonify({"error": "Error while fetching data"}), 500


#load site details by site id
@app.route('/sites/link/<site_link>', methods=['GET'])
def get_site_by_link(site_link):
    try:
        
        # Fetch the site details by id
        site_dict = fetch_site_by_link(site_link)

        return jsonify(site_dict), 200

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data", error)
        return jsonify({"error": "Error while fetching data"}), 500
    


@app.route('/sites/search', methods=['GET'])
def get_sites_by_search():
    try:
        # Extract keywords from the query string
        keywords = request.args.get('terms', '')

        # Fetch the sites with the specified keywords
        sites_list = search_sc_sites(keywords)

        return jsonify(sites_list), 200

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data", error)
        return jsonify({"error": "Error while fetching data"}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 17995))
    app.run(host='0.0.0.0', port=port)




