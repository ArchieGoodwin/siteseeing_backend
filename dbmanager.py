import html
import json
import os
from flask import Flask, request, jsonify
import subprocess
import threading
import random
import psycopg2

def fetch_data(page, page_size, sort):
    # Connect to your PostgreSQL database
    conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
    cur = conn.cursor()

    # Calculate OFFSET
    offset = (page - 1) * page_size

    # Build the SQL query for sorting
    if sort == 'createdAt':
        order_sql = 'ORDER BY createdAt DESC'
    elif sort == 'random':
        order_sql = 'ORDER BY RANDOM()'

    # Create the SQL query with LIMIT and OFFSET for pagination
    query = f"SELECT * FROM sc_sites {order_sql} LIMIT %s OFFSET %s"

    # Execute the query
    cur.execute(query, (page_size, offset))

    # Fetch the results
    rows = cur.fetchall()

     # Convert the results to a list of dictionaries
    sites_list = []
    for site in rows:
        site_dict = {
            "id": site[0],
            "userId": site[1],
            "content": site[2],
            "link": site[3],
            "description": site[4],
            "keywords": site[5],
            "categories": site[6],
            "services": site[7],
            "rawdata": site[8],
            "createdAt": site[9],
            "updatedAt": site[10]
        }
        sites_list.append(site_dict)

    # Close the connection
    cur.close()
    conn.close()

    return sites_list

def fetch_sites_with_keywords(keywords):
    # Connect to your PostgreSQL database
    conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
    cur = conn.cursor()

    # Create the base SQL query
    query = "SELECT * FROM sc_sites WHERE "

    # HTML decode the string
    decoded_keywords = html.unescape(keywords)

    # Split the string by comma to get a list of keywords
    keyword_list = decoded_keywords.split(',')
    
    # Add conditions for each keyword
    keyword_conditions = [f"LOWER(keywords) LIKE LOWER('%{keyword}%')" for keyword in keyword_list]
    query += ' OR '.join(keyword_conditions)
    query += " ORDER BY createdAt DESC" # Sort by createdAt in descending order
    print("query = ", query)
    # Execute the query
    cur.execute(query)

    # Fetch the results
    rows = cur.fetchall()

     # Convert the results to a list of dictionaries
    sites_list = []
    for site in rows:
        site_dict = {
            "id": site[0],
            "userId": site[1],
            "content": site[2],
            "link": site[3],
            "description": site[4],
            "keywords": site[5],
            "categories": site[6],
            "services": site[7],
            "rawdata": site[8],
            "createdAt": site[9],
            "updatedAt": site[10]
        }
        sites_list.append(site_dict)
    # Close the connection
    cur.close()
    conn.close()

    return sites_list


def fetch_sites_with_categories(categories):
    # Connect to your PostgreSQL database
    conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
    cur = conn.cursor()

    # Create the base SQL query
    query = "SELECT * FROM sc_sites WHERE "

    # HTML decode the string
    decoded_keywords = html.unescape(categories)

    # Split the string by comma to get a list of keywords
    keyword_list = decoded_keywords.split(',')

    # Add conditions for each keyword
    keyword_conditions = [f"LOWER(categories) LIKE LOWER('%{keyword}%')" for keyword in keyword_list]
    query += ' OR '.join(keyword_conditions)
    query += " ORDER BY createdAt DESC" # Sort by createdAt in descending order

    # Execute the query
    cur.execute(query)

    # Fetch the results
    rows = cur.fetchall()

    # Convert the results to a list of dictionaries
    sites_list = []
    for site in rows:
        site_dict = {
            "id": site[0],
            "userId": site[1],
            "content": site[2],
            "link": site[3],
            "description": site[4],
            "keywords": site[5],
            "categories": site[6],
            "services": site[7],
            "rawdata": site[8],
            "createdAt": site[9],
            "updatedAt": site[10]
        }
        sites_list.append(site_dict)
    # Close the connection
    cur.close()
    conn.close()

    return sites_list


def add_screen(link, screen):
    try:
        # Connect to your PostgreSQL database
        conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # SQL query to insert a new screen
        query = "INSERT INTO sc_screens (id, link, screen, createdAt, updatedAt) VALUES (uuid_generate_v4(), %s, %s, NOW(), NOW()) RETURNING id"

        # Execute the query
        cur.execute(query, (link, screen))

        # Fetch the result
        screen_id = cur.fetchone()[0]

        return screen_id
    except (Exception, psycopg2.Error) as error:
        print("Error while inserting data", error)
        return None
    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def delete_screen(link):
    try:
        # Connect to your PostgreSQL database
        conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # SQL query to delete a screen
        query = "DELETE FROM sc_screens WHERE link = %s"

        # Execute the query
        cur.execute(query, (link,))

    except (Exception, psycopg2.Error) as error:
        print("Error while deleting data", error)
    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()

#add question and answer for user and link in sc_qa 
def add_qa(link, question, answer, userId):
    try:
        # Connect to your PostgreSQL database
        conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # SQL query to insert a new question and answer
        query = "INSERT INTO sc_qa (id, link, question, answer, userId, createdAt, updatedAt) VALUES (uuid_generate_v4(), %s, %s, %s, %s, NOW(), NOW()) RETURNING id"

        # Execute the query
        cur.execute(query, (link, question, answer, userId))

        # Fetch the result
        qa_id = cur.fetchone()[0]

        return qa_id
    except (Exception, psycopg2.Error) as error:
        print("Error while inserting data", error)
        return None
    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()


#return records from sc_qa for link and user
def fetch_qa(link, userId):
    try:
        # Connect to your PostgreSQL database
        conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
        cur = conn.cursor()

        # SQL query to fetch the question and answer by link and user
        query = "SELECT * FROM sc_qa WHERE link = %s AND userId = %s ORDER BY createdAt DESC"

        # Execute the query
        cur.execute(query, (link, userId))

        # Fetch the results
        qa = cur.fetchall()
        # Convert the results to a list of dictionaries
        qa_list = []
        for qa in qa:
            qa_dict = {
                "id": qa[0],
                "link": qa[1],
                "question": qa[2],
                "answer": qa[3],
                "userId": qa[4],
                "createdAt": qa[5],
                "updatedAt": qa[6]
            }
            qa_list.append(qa_dict)      

        return qa_list
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data", error)
    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def fetch_screen_by_link(link):
    try:
        # Connect to your PostgreSQL database
        conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
        cur = conn.cursor()

        # SQL query to fetch the screen details by link
        query = "SELECT * FROM sc_screens WHERE link = %s"

        # Execute the query
        cur.execute(query, (link,))

        # Fetch the results
        screen = cur.fetchone()

        if screen is not None:
            screen_dict = {
                "id": screen[0],
                "link": screen[1],
                "screen": screen[2],
                "createdAt": screen[3],
                "updatedAt": screen[4]
            }
            return screen_dict
        

        return None
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data", error)
    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_record_count():
    try:
        # Connect to your PostgreSQL database
        conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
        cur = conn.cursor()

        # SQL query to count the number of records
        query = "SELECT COUNT(*) FROM sc_sites"

        # Execute the query
        cur.execute(query)

        # Fetch the result, which is the number of records in sc_sites
        result = cur.fetchone()
        print("result count = ", result)
        if result is not None:
            record_count = result[0]
            return record_count

        else:
            raise Exception("Query returned no result.")

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data for count ", error)
        return None
    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()
    


def fetch_site_by_id(site_id):
    try:
       # Connect to your PostgreSQL database
        conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
        cur = conn.cursor()

        # SQL query to fetch the site details by id
        query = "SELECT * FROM sc_sites WHERE id = %s"

        # Execute the query
        cur.execute(query, (site_id,))

        # Fetch the results
        site = cur.fetchone()

        # Convert the results to a dictionary
        site_dict = {
            "id": site[0],
            "userId": site[1],
            "content": site[2],
            "link": site[3],
            "description": site[4],
            "keywords": site[5],
            "categories": site[6],
            "services": site[7],
            "rawdata": site[8],
            "createdAt": site[9],
            "updatedAt": site[10]
        }

       
        return site_dict
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data", error)
        return None
    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def ensure_trailing_slash(s):
    """Ensure the string ends with a forward slash."""
    if not s.endswith('/'):
        return s + '/'
    return s

def fetch_site_by_link(link):
    try:
       # Connect to your PostgreSQL database
        conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
        cur = conn.cursor()

        sitelink = ensure_trailing_slash(link)
        sitelink = "https://" + sitelink
        # SQL query to fetch the site details by id
        query = "SELECT * FROM sc_sites WHERE link = %s"

        # Execute the query
        cur.execute(query, (sitelink,))

        # Fetch the results
        site = cur.fetchone()

        # Convert the results to a dictionary
        site_dict = {
            "id": site[0],
            "userId": site[1],
            "content": site[2],
            "link": site[3],
            "description": site[4],
            "keywords": site[5],
            "categories": site[6],
            "services": site[7],
            "rawdata": site[8],
            "createdAt": site[9],
            "updatedAt": site[10]
        }

       
        return site_dict
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data", error)
        return None
    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def search_sc_sites(search_term):
    # Connect to your PostgreSQL database
    conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
    cur = conn.cursor()

    # HTML decode the string
    decoded_keywords = html.unescape(search_term)

    # Split the search term into words
    words = decoded_keywords.split()

    # Start building the SQL query
    query = "SELECT *, ("
    query_conditions = []

    for word in words:
        # For each word, check if it's in any of the four fields
        word_condition = f"(LOWER(keywords) LIKE LOWER('%{word}%') OR LOWER(categories) LIKE LOWER('%{word}%') OR LOWER(services) LIKE LOWER('%{word}%') OR LOWER(content) LIKE LOWER('%{word}%'))"
        query_conditions.append(word_condition)

    # Combine conditions with OR and count matches for relevance
    query += " + ".join([f"CASE WHEN {condition} THEN 1 ELSE 0 END" for condition in query_conditions])
    query += ") as relevance FROM sc_sites WHERE ("
    query += " + ".join([f"CASE WHEN {condition} THEN 1 ELSE 0 END" for condition in query_conditions])
    query += ") > 0 ORDER BY relevance DESC"

    # Execute the query
    cur.execute(query)

    # Fetch the results
    rows = cur.fetchall()

    # Close the connection
    cur.close()
    conn.close()

    # Convert the results to a list of dictionaries
    sites_list = []
    for site in rows:
        site_dict = {
            "id": site[0],
            "userId": site[1],
            "content": site[2],
            "link": site[3],
            "description": site[4],
            "keywords": site[5],
            "categories": site[6],
            "services": site[7],
            "rawdata": site[8],
            "createdAt": site[9],
            "updatedAt": site[10]
        }
        sites_list.append(site_dict)

    return sites_list