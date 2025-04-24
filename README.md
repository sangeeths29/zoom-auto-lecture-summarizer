# Zoom Classmate Buddy

This project automates the processing of lecture transcripts. It fetches Zoom bot transcripts from the **Attendee API**, summarizes them using **Gemini 1.5 Pro**, and delivers the output to both a **Notion page** and through **Gmail notifications** for upcoming assignments.

---

## Features

- Fetches transcript from Attendee bot API  
- Uses CrewAI with Gemini Pro (Google GenAI) to generate summaries  
- Extracts key technical points from computer science lectures  
- Appends the results to a Notion page  
- Sends assignment reminders via Gmail API  

---

## How It Works

1. The transcript is pulled from the Attendee Zoom bot (or provided manually).
2. The first 100–1000 words are passed to a summarization agent.
3. The agent produces:
   - A **3–5 paragraph summary**
   - A **list of technical key points**
   - Any **assignment reminders**
4. The result is:
   - Pushed to Notion (via Notion API)
   - Sent as an email (via Gmail API)

---

## Technologies Used

- **Python**
- **CrewAI** – agent coordination
- **Gemini Pro (Google GenAI)** – LLM summarization
- **Notion API** – append summary content
- **Gmail API** – send email reminders
- **Google OAuth 2.0** – email authentication
