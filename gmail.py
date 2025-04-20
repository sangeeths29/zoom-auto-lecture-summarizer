import os
import base64
import textwrap
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI

# Set API keys via environment variable placeholders for GitHub safety
os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

# Email settings
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_RECIPIENT = "recipient_email@gmail.com"
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2)

# Gmail API authentication
def authenticate_gmail_api():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

# Trim to first n words
def get_first_n_words(text, n=100):
    words = text.split()
    return ' '.join(words[:n])

# Send summary via Gmail API
def send_email_notification(subject, summary, key_points):
    service = authenticate_gmail_api()

    message = MIMEMultipart()
    message['To'] = EMAIL_RECIPIENT
    message['From'] = EMAIL_SENDER
    message['Subject'] = subject

    body = f"Upcoming Assignment Notification\n\nSummary:\n{summary}\n\nKey Details:\n{key_points}"
    message.attach(MIMEText(body, 'plain'))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}

    try:
        service.users().messages().send(userId='me', body=body).execute()
        return "Email sent successfully via Gmail API"
    except Exception as e:
        return f"Failed to send email: {e}"

# Define summarizer agent
summarizer = Agent(
    role="CS Assignment Reminder Agent",
    goal="Scan transcripts and notify students about upcoming assignments",
    backstory="You are a proactive assistant that highlights deadlines and key announcements from class discussions to help students stay on track.",
    verbose=True,
    llm=llm
)

# Placeholder task
summarize_task = Task(
    description="PLACEHOLDER",
    expected_output="A reminder summary of upcoming assignments with clear academic actions",
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
    sample_transcript = textwrap.dedent("""
        Today’s lecture covered the core principles of machine learning. We began with a recap of supervised vs. unsupervised learning, noting that supervised learning relies on labeled datasets, whereas unsupervised learning detects patterns without labeled data.
        Key examples of supervised learning included decision trees and support vector machines (SVMs), each with their own tradeoffs in interpretability and performance. We delved into the mathematics behind SVMs and margin maximization.
        The class also learned about unsupervised methods like k-means clustering and Principal Component Analysis (PCA), both useful in dimensionality reduction and exploratory analysis.
        A brief overview of neural networks was introduced, highlighting the role of activation functions and backpropagation. Students were encouraged to explore frameworks like TensorFlow or PyTorch.
        Assignment 4 is due next Friday and covers implementing a basic regression model. The next class will review performance metrics like RMSE and classification accuracy.
    """ * 20)

    trimmed_transcript = get_first_n_words(sample_transcript, 100)
    print("Transcript trimmed to 100 words.")
    print(f"Sample:\n{trimmed_transcript[:300]}...\n")

    lecture_crew.tasks[0].description = f"""
    This is a transcript from a computer science class:

    \"\"\"{trimmed_transcript}\"\"\"

    Your task:
    1. Identify and summarize any upcoming assignment announcements or due dates mentioned.
    2. Clearly explain what the student is expected to do next.
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

    title = "Upcoming Assignment Reminder - " + datetime.now().strftime("%Y-%m-%d")
    print("Sending email notification...")
    email_result = send_email_notification(title, summary, key_points)
    print(email_result)

if __name__ == "__main__":
    main()