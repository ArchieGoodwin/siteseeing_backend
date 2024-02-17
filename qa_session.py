import os
import random
import numpy as np
import psycopg2
import openai
import json
import uuid
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv
import embedding
from psycopg2.extensions import register_adapter, AsIs

def addapt_numpy_float64(numpy_float64):
    return AsIs(numpy_float64)

#create embedding from question, then find 15 records in sc_vectors with the most similar embeddings. Then generate answer using OpenAI API using question and using content from result emddings as assistant role input
def find_embedding_vectors(question, namespace):
    # Generate embedding for the question
    register_adapter(np.float64, addapt_numpy_float64)
    emb = embedding.get_embedding(question)

    # Fetch the 15 most similar records
    embedding_array = addapt_numpy_float64(emb)
    # Register pgvector extension
    conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
    cur = conn.cursor()

    cur.execute("SELECT * FROM sc_vectors WHERE namespace = %s ORDER BY embedding <=> %s::vector LIMIT 10", (namespace, (emb, )))
    top3_docs = cur.fetchall()
    print("top10_docs = ", len(top3_docs))
    return top3_docs
    

def find_embedding_vectors_all(question):
    # Generate embedding for the question
    register_adapter(np.float64, addapt_numpy_float64)
    emb = embedding.get_embedding(question)

    # Fetch the 15 most similar records
    embedding_array = addapt_numpy_float64(emb)
    # Register pgvector extension
    conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
    cur = conn.cursor()

    cur.execute("SELECT * FROM sc_vectors ORDER BY embedding <=> %s::vector LIMIT 35", (emb, ))
    top3_docs = cur.fetchall()
    
    sites_list = []
    for record in top3_docs:
        #add only records which link field is not yet in sites_list
        if not any(d['link'].rstrip('/') == record[2].rstrip('/') for d in sites_list):
            site_dict = {
                "id": record[0],
                "content": record[1],
                "link": record[2].rstrip('/'),
                "userId": record[3],
                "namespace": record[4],
                "createdAt": record[6],
                "updatedAt": record[7],
            }
            sites_list.append(site_dict)
         

    print("top10_docs = ", len(sites_list))
    return sites_list



def generate_answer(question, top3_docs):
    # Generate the assistant role input
    assistant_array = []
    
    for doc in top3_docs:
        assistant_array.append({"role": "assistant", "content": f"content to look at: {doc[1]}"})
    # Generate the answer using OpenAI API
    assistant_array.append({"role": "system", "content": "You are a helpful assistant. You can analyze the content above and provide answer for user's question Use your knowledge and context provided with assistant's messages."})
    assistant_array.append({"role": "user", "content": question})
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=assistant_array,
        timeout=120
    )
    print("asnwer : ", response.choices[0].message.content)
    return response.choices[0].message.content


# embeddings_result = find_embedding_vectors("What services does this site provide?", "tinyseed.com/")
# generate_answer("What services does this site provide?", embeddings_result)
