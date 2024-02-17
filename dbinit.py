import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import uuid
from datetime import datetime
load_dotenv()  # take environment variables from .env.




def create_table_with_vector_support():
    # Connect to the PostgreSQL server
    conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    # Create a cursor object
    cur = conn.cursor()

    # SQL query to create a table
    #create extension vector with schema extensions;  -- Adjust based on the actual extension name
    create_table_query = """
    CREATE TABLE IF NOT EXISTS sc_vectors (
        id UUID PRIMARY KEY,
        userId UUID,
        content TEXT,
        link TEXT,
        namespace TEXT,
        embedding vector(1536),  -- Replace 'vectordb_type' with the actual vector data type
        createdAt TIMESTAMP,
        updatedAt TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS sc_sites (
        id UUID PRIMARY KEY,
        userId UUID,
        content TEXT,
        link TEXT,
        description TEXT,
        keywords TEXT,
        categories TEXT,
        services TEXT,
        rawdata JSONB,
        createdAt TIMESTAMP,
        updatedAt TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS sc_screens (
        id UUID PRIMARY KEY,
        link TEXT,
        screen TEXT,
        createdAt TIMESTAMP,
        updatedAt TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS sc_qa (
        id UUID PRIMARY KEY,
        link TEXT,
        question TEXT,
        answer TEXT,
        userId UUID,
        createdAt TIMESTAMP,
        updatedAt TIMESTAMP
    );
    """

    try:
        # Execute the query
        cur.execute(create_table_query)
        print("Tables were created successfully.")

    except (Exception, psycopg2.Error) as error:
        print("Error while creating PostgreSQL tables", error)

    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()


create_table_with_vector_support()