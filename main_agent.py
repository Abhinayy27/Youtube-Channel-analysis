import os
import agentql
from openai import OpenAI
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()

XAI_API_KEY = os.getenv("XAI_API_KEY")
AGENTQL_API_KEY = os.getenv("AGENTQL_API_KEY")

if AGENTQL_API_KEY is None:
    raise ValueError("AGENTQL_API_KEY not found in environment variables")

os.environ["AGENTQL_API_KEY"] = AGENTQL_API_KEY
agentql.api_key = AGENTQL_API_KEY

# Initialize OpenAI client for Grok
client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1",
)


def scrape_youtube_channel(channel_url):
    try:
        print(f"\n[DEBUG] Initializing browser session...")
        with sync_playwright() as playwright, playwright.chromium.launch(
            headless=False
        ) as browser:
            page = agentql.wrap(browser.new_page())
            print(f"[DEBUG] Navigating to: {channel_url}")
            page.goto(channel_url)

            VIDEOS_QUERY = """
            {
                videos[] {
                    title
                    views
                    upload_date
                }
            }
            """

            print("[DEBUG] Executing AgentQL query...")
            response = page.query_data(VIDEOS_QUERY)
            print("[DEBUG] Query completed successfully")
            return response

    except Exception as e:
        print(f"[DEBUG] Error occurred: {str(e)}")
        return f"An error occurred during scraping: {str(e)}"


def get_formatted_analysis(scrape_data):
    try:
        completion = client.chat.completions.create(
            model="grok-beta",
            messages=[
                {
                    "role": "system",
                    "content": """You are an AI assistant specialized in analyzing YouTube channel data. 
                    Your task is to format scraped YouTube channel information into clean, readable markdown.
                    Focus on  presenting the video data in an organized way.
                   Use standard markdown formatting.""",
                },
                {
                    "role": "user",
                    "content": f"""Please analyze this YouTube channel's raw data with a focus on video performance and popularity. Create a detailed markdown report that includes:

                    1. Top 3 Most Viewed Videos
                    - List titles and view counts
                    - Analyze what made these videos successful (title analysis, topic appeal)
                    
                    2. Bottom 3 Least Viewed Videos  
                    - List titles and view counts
                    - Analyze potential reasons for lower performance
                    
                    3. View Count Distribution
                    - Overall view count patterns
                    - Identify any notable trends or anomalies
                    - Compare view counts across different types of content
                    
                    4. Performance Analysis
                    - What types of titles tend to perform better?
                    - Are there specific topics or approaches that consistently get more views?
                    - Recommendations for improving future video performance
                    
                    Here's the scraped data: {scrape_data}""",
                },
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"An error occurred during analysis: {str(e)}"


if __name__ == "__main__":
    print("[DEBUG] Starting YouTube scraper...")
    channel_url = "https://www.youtube.com/@mkbhd/videos"

    # Get scraped data
    videos_data = scrape_youtube_channel(channel_url)

    # Print first 100 characters of raw data
    print("\nFirst 100 characters of scraped data:")
    print(str(videos_data)[:100] + "...")

    # Get formatted analysis from Grok
    print("\n[DEBUG] Generating formatted analysis...")
    formatted_analysis = get_formatted_analysis(videos_data)

    # Save to markdown file
    print("[DEBUG] Saving analysis to markdown file...")
    with open("youtube_analysis.md", "w", encoding="utf-8") as f:
        f.write(formatted_analysis)

    print("[DEBUG] Analysis saved to youtube_analysis.md")
