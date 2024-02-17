import os
import openai
import json
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.

def get_embedding(text):
    client = openai.OpenAI()

    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )

    return response.data[0].embedding

def insert_record(userId, content, link, namespace, embedding):
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
    conn.autocommit = True

    # Create a cursor object
    cur = conn.cursor()

    # SQL query to insert data
    insert_query = f"""
    INSERT INTO sc_vectors (id, userId, content, link, namespace, embedding, createdAt, updatedAt)
    VALUES (uuid_generate_v4(), %s, %s, %s, %s, %s, NOW(), NOW());
    """

    try:
        if isinstance(embedding, list) and all(isinstance(x, float) for x in embedding):
            record_to_insert = (str(userId), content, link, namespace, embedding)
        else:
            raise ValueError("Embedding is not a list of floats")
        
        # Execute the query
        cur.execute(insert_query, record_to_insert)

        print("Record inserted successfully.")

    except (Exception, psycopg2.Error) as error:
        print("Error while inserting data into PostgreSQL", error)

    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()

import psycopg2

def delete_vector_records(userId, namespace):
    print("Deleting records for: ", namespace)
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
    conn.autocommit = True  # Enable auto commit for the transaction
    cur = conn.cursor()

    try:
        # SQL query to delete records from the table
        delete_query = f"DELETE FROM sc_vectors WHERE userId = %s AND namespace = %s;"
        
        # Execute the query
        cur.execute(delete_query, (userId, namespace))

        print("Records deleted successfully for: ", namespace)

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)

    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()


def delete_site_records(userId, namespace):
    print("Deleting records for sites for: ", namespace)
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
    conn.autocommit = True  # Enable auto commit for the transaction
    cur = conn.cursor()

    try:
        # SQL query to delete records from the table
        delete_query = f"DELETE FROM sc_sites WHERE userId = %s AND link = %s;"
        
        # Execute the query
        cur.execute(delete_query, (userId, namespace))

        print("Records from sites deleted successfully for: ", namespace)

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)

    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()



# # Example usage
# text = "Your text to embed"
# embedding = get_embedding(text)

# insert_record('your_dbname', 'your_username', 'your_password', 'your_host', 'your_table_name', 'Example content', 'https://example.com', 'example_namespace', embedding)
