import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

# Set API keys from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
BOT_ID = os.getenv("BOT_ID")
ATTENDEE_API_TOKEN = os.getenv("ATTENDEE_API_TOKEN")

# Set environment variables explicitly for langchain
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
os.environ["NOTION_API_KEY"] = NOTION_API_KEY

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2)

# Function to fetch transcript
def fetch_transcript(bot_id=BOT_ID, api_token=ATTENDEE_API_TOKEN):
    url = f"https://app.attendee.dev/api/v1/bots/{bot_id}/transcript"
    headers = {
        'Authorization': f'Token {api_token}',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else f"Error: {response.status_code}"

# Trim to first n words
def get_first_n_words(text, n=100):
    words = text.split()
    return ' '.join(words[:n])

# Append content to Notion
def append_to_notion_page(title, summary, key_points):
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    blocks = [
        {"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"type": "text", "text": {"content": title}}]}},
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Summary"}}]}},
        {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": summary}}]}},
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Key Points"}}]}},
        {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": key_points}}]}},
        {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}}]}}
    ]
    response = requests.patch(
        f"https://api.notion.com/v1/blocks/{NOTION_PAGE_ID}/children",
        headers=headers,
        json={"children": blocks}
    )
    return "Content successfully added to Notion page" if response.status_code == 200 else f"Error: {response.status_code} - {response.text}"

# Define summarizer agent
summarizer = Agent(
    role="CS Lecture Summarizer",
    goal="Create concise summaries of CS lectures",
    backstory="You are an expert in computer science education with deep knowledge of algorithms, data structures, programming languages, and software engineering principles. You excel at distilling complex technical concepts into clear, organized summaries.",
    verbose=True,
    llm=llm
)

# Placeholder task
summarize_task = Task(
    description="PLACEHOLDER",
    expected_output="A summary followed by a list of key points from the lecture",
    agent=summarizer
)

# Define the crew
lecture_crew = Crew(
    agents=[summarizer],
    tasks=[summarize_task],
    process=Process.sequential,
    verbose=True
)

def main():
    print("Fetching transcript from Attendee API...")
    transcript_data = fetch_transcript()

    if isinstance(transcript_data, dict) and "transcript" in transcript_data:
        transcript_entries = transcript_data.get("transcript", [])
        transcript_text = "\n\n".join(
            f"{entry.get('speaker', 'Unknown')}: {entry.get('text', '')}" for entry in transcript_entries
        )
    else:
        transcript_text = str(transcript_data)

    # Limit to first 100 words
    trimmed_transcript = get_first_n_words(transcript_text, 100)

    print(f"Transcript trimmed to 100 words.")
    print(f"Sample:\n{trimmed_transcript[:200]}...\n")

    # Update task with trimmed transcript
    lecture_crew.tasks[0].description = f"""
    This is a transcript from a computer science class:

    \"\"\"{trimmed_transcript}\"\"\"

    Based on this, do the following:
    1. Summarize the lecture in 3–5 paragraphs.
    2. Extract 5–10 key technical points.
    """

    print("Generating summary with CrewAI...")
    result = lecture_crew.kickoff()
    print("Summary generated!")

    result_parts = result.split("\n\n") if result else []

    if len(result_parts) >= 2:
        summary = result_parts[0]
        key_points = "\n\n".join(result_parts[1:])
    else:
        lines = result.split("\n") if result else []
        summary = "\n".join(lines[:5])
        key_points = "\n".join(lines[5:]) if len(lines) > 5 else "No additional key points extracted."

    title = "CS Lecture Summary - " + datetime.now().strftime("%Y-%m-%d")
    print("Adding content to Notion page...")
    result = append_to_notion_page(title, summary, key_points)
    print(result)

if __name__ == "__main__":
    main()