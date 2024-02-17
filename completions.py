import os
import random
import psycopg2
import openai
import json
import uuid
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv

from embedding import delete_site_records
load_dotenv()  # take environment variables from .env.


def summarize_content(content):
    """ Summarize the content using OpenAI's Chat Completion API. """
    client = openai.OpenAI()
    
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Ypu can analyze the content below and provide insights on what content is about. Summary should be compehehensive and be rather long."},
            {"role": "user", "content": f"Summarize the following content:\n\n{content}"}
        ]
    )

    return response.choices[0].message.content.strip()

def select_part_randomly(result_set, count):
    # Shuffle the result set
    random.shuffle(result_set)
    return result_set[:count]


def split_list_into_sublists(lst, count):
    # Split 'lst' into sublists of length 'count'
    return [lst[i:i + count] for i in range(0, len(lst), count)]

def filter_json_array(json_array):
    if len(json_array) <= 100:
        return json_array
    filtered_array = []
    alternate = False  # Flag to add every second JSON with more than one underscore

    for json_obj in json_array:
        link = json_obj[0].replace("http://", "").replace("https://", "").replace("/", "_")
        #print("link: ", link)
        underscore_count = link.count('_')
        #print("underscore_count: ", underscore_count)
        if underscore_count == 1:
            filtered_array.append(json_obj)
        elif underscore_count > 1:
            if alternate:
                filtered_array.append(json_obj)
            alternate = not alternate
    #print("filtered_array: ", len(filtered_array))
    return filtered_array



def insert_record(userId, content, link, description, keywords, categories, services, rawdata):
    # Create a connection to the database
    conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
    conn.autocommit = True  # Auto commit the changes
    cur = conn.cursor()

    # Prepare the INSERT statement
    insert_query = """
    INSERT INTO sc_sites (id, userId, content, link, description, keywords, categories, services, rawdata, createdAt, updatedAt) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    # Generate a new UUID for the id and get the current timestamp
    record_id = str(uuid.uuid4())
    current_time = datetime.now()

    try:
        # Execute the INSERT statement
        cur.execute(insert_query, (record_id, userId, content, link, description, keywords, categories, services,  psycopg2.extras.Json(rawdata), current_time, current_time))

        print("Record inserted successfully.")

    except (Exception, psycopg2.Error) as error:
        print("Error while inserting data into PostgreSQL", error)

    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()


def analyze_contents_with_chat_completion(namespace, user_id, max_tokens=32000):
    # Connect to the database
    conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("DBUSER"), password=os.getenv("DBPASSWORD"), host=os.getenv("DBHOST"))
    cur = conn.cursor()

    # Query to select records from the database
    select_query = """
    SELECT link, content FROM sc_vectors WHERE namespace = %s AND userId = %s;
    """

    try:
        # Fetch data from the database
        cur.execute(select_query, (namespace, user_id))
        records = cur.fetchall()

        if cur:
            cur.close()
        if conn:
            conn.close()

        client = openai.OpenAI()

        print("records found ",len(records))
        # Combine records into a conversation prompt
        prompt = "I have compiled content from various links for one website. Please analyze them and provide summary of what is the whole content is about.  Summary should be compehehensive and be rather long and use key content for summary in result json. Also provide 5-7 basic keywords describing the content. Also give me 3-4 categories in which the whole website content is rely on. And also describe the website description in one sentence. Also provide the list of services this website is providing. Take into account the content from assistants. Provide answer in json:\n\n"
        results = []
        filtered_records = filter_json_array(records)
        print("filtered records: ", len(filtered_records))
        splitted_records = split_list_into_sublists(filtered_records, 25)
        print("splitted records before cut: ", len(splitted_records))
        if len(splitted_records) > 25:
            splitted_records = select_part_randomly(splitted_records, 25)
        print("splitted records after cut: ", len(splitted_records))
        for records in splitted_records:
            content = ""
            content_description = ""
            for record in records:
                content = record[1]                
                content_description += f"Content from {record[0]}: {content}\n"
                            
            prompt_inside = content_description

            # Use OpenAI Chat Completion API to generate analysis
            print("OPENAI_MODEL: ", os.getenv("OPENAI_MODEL"))

            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL"),
                messages=[
                    {"role": "assistant", "content": "provide answer in json form. Sample: {'content': 'This is a sample content', 'keywords': ['keyword1', 'keyword2'], 'categories': ['category1', 'category2'], 'description': 'This is a sample description', 'services': ['service1', 'service2']}"},
                    {"role": "system", "content": "You are a helpful assistant. Ypu can analyze the website content below and provide insights on what each content is about."},
                    {"role": "user", "content": prompt_inside}
                ],
                response_format={ "type":"json_object" }
            )
            print("preliminary result: ", response.choices[0].message.content)
            results.append(response.choices[0].message.content)
        print("results: ", len(results))
        assistant_array = []
      
        for result in results:
            assistant_array.append({"role": "assistant", "content": f"Summarized content: {result}"})

        # Use OpenAI Chat Completion API to generate analysis
        client = openai.OpenAI()

        messages=[
                {"role": "assistant", "content": "provide answer in json form. Sample: {'content': 'This is a sample content', 'keywords': ['keyword1', 'keyword2'], 'categories': ['category1', 'category2'], 'description': 'This is a sample description', 'services': ['service1', 'service2']}"},
                {"role": "system", "content": "You are a helpful assistant. You can analyze the website content below and provide insights on what each content is about."}
            ]
        messages.extend(assistant_array)
        messages.append({"role": "user", "content": prompt})
        print("OPENAI_MODEL: ", os.getenv("OPENAI_MODEL"))
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            messages=messages,
            response_format={ "type":"json_object" }
        )

        content_json = json.loads(response.choices[0].message.content)
        print("content_json: ", content_json)
        content = ""
        if 'content' not in content_json:
            if 'summary' not in content_json:
                if 'content_summary' not in content_json:
                    if 'website_summary' not in content_json:
                        content = ""
                    else:
                        content = content_json['website_summary']
                else:
                    content = content_json['content_summary']
            else:
                content = content_json['summary']
        else:
            content = content_json['content']
        
        print("content: ", content)

        keywords = ""
        if 'keywords' not in content_json:
            keywords = ""
        else:
            string_list = content_json['keywords']
            keywords = ", ".join(string_list)
        print("keywords: ", keywords)

        categories = ""
        if 'categories' not in content_json:
            categories = ""
        else:
            string_list = content_json['categories']
            categories = ", ".join(string_list)
        print("categories: ", categories)

        description = ""
        if 'description' not in content_json:
            if 'content_description' not in content_json:
                    if 'website_description' not in content_json:
                        description = content
                    else:
                        description = content_json['website_description']
            else:
                description = content_json['content_description']
        else:
            description = content_json['description']
        print("description: ", description)

        services = ""
        if 'services' not in content_json:
            services = ""
        else:
            string_list = content_json['services']
            services = ", ".join(string_list)
        print("services: ", services)

        #delete previous record
        delete_site_records(user_id, "https://" + namespace)

        #insert result into sc_sites 
        insert_record(user_id, content, "https://" + namespace, description, keywords, categories, services, content_json)

        #return response.choices[0].message.content

    except Exception as e:
        print("Error:", e)
    finally:
        cur.close()
        conn.close()

# Example usage
# print(os.environ)
# namespace = "tech.eu/"
# user_id = "ca16c64d-961a-498f-a856-62de7a083f6f"
# analysis_result = analyze_contents_with_chat_completion(namespace, user_id)
# print(analysis_result)
