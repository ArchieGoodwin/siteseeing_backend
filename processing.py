import os
import json
import uuid
import re
import embedding


def process_json_files(folder_path, user_id):
    namespace = os.path.basename(folder_path).replace("_", "/")
    print("Processing files in folder:", folder_path)

    embedding.delete_vector_records(user_id, namespace)
    
    # Function to split text into segments of up to 8000 tokens
    def split_text(text, max_tokens=8000):
        tokens_count = 1000 #count_tokens(text)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        segments = []
        current_segment = ""

        for sentence in sentences:
            if (len(current_segment.split()) + len(sentence.split())) <= tokens_count:
                current_segment += sentence + " "
            else:
                segments.append(current_segment.strip())
                current_segment = sentence + " "
        
        if current_segment:
            segments.append(current_segment.strip())
        print("Segments count:", len(segments))
        return segments

    # Iterate over .json files in the folder
    #check if dir exists 
    if not os.path.exists(folder_path):
        print("Error: Folder does not exist.")
        return
    for filename in os.listdir(folder_path):
        print("Processing file:", filename)
        #check if filename is not data.json
        if filename.endswith('.json') and filename != "data.json":
            file_path = os.path.join(folder_path, filename)

            # Read JSON file
            with open(file_path, 'r') as file:
                data = json.load(file)
                link = data['link']
                text = data['text']

                # Split text if necessary
                text_segments = split_text(text)

                for segment in text_segments:
                    # Generate embedding
                    try:
                        emb = embedding.get_embedding(segment)
                        # Insert record into database
                        folder = os.path.basename(folder_path).replace("_", "/")
                        embedding.insert_record(user_id, segment, link.replace("_", "/"), folder, emb)
                    except:
                        print("Error generating embedding for segment:", segment)
                        continue

                   

    print("All files processed.")

# Example usage
# user_id = "ca16c64d-961a-498f-a856-62de7a083f6f"
# process_json_files('tech.eu_', user_id)
