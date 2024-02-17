import json
import sys
from completions import analyze_contents_with_chat_completion
from processing import process_json_files
from scrapper import scrape_website
from urllib.parse import urlparse


def main():

    def get_base_url(url):
        parsed_url = urlparse(url)
        base_url = f"https://{parsed_url.netloc}/"
        return base_url

    def ensure_trailing_slash(s):
        """Ensure the string ends with a forward slash."""
        if not s.endswith('/'):
            return s + '/'
        return s
    # Print all command line arguments
    if len(sys.argv) < 3:
        print("Error: Not all arguments provided.")
        sys.exit(1)  # Exit the script with an error code, e.g., 1
    # Get the 2nd and 3rd arguments
    websites = sys.argv[1]
    json_array = json.loads(websites)
    user_id = sys.argv[2]

    print(f"Website: {json_array}")
    print(f"user_id: {user_id}")

    for json_object in json_array:
        website_cleaned = get_base_url(json_object)
        #scrape website
        scrape_website(website_cleaned)
        website = ensure_trailing_slash(website_cleaned).replace("http://", "").replace("https://", "").replace("/", "_")
        print("start processing", website_cleaned)
        process_json_files(website, user_id)
        print("start summarizing", website)
        analyze_contents_with_chat_completion(website.replace("_", "/"), user_id)
        print("done processing", website_cleaned)


if __name__ == "__main__":
    main()