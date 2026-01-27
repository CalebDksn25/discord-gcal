from dotenv import load_dotenv
from openai import AsyncOpenAI
import os

# Load environment variables from .env file
load_dotenv()

# Create the OpenAI client instance
client = AsyncOpenAI()

OPENAI_SYSTEM_PROMPT = """You are a scheduling assistant that converts natural language into structured calendar or task data.

Rules:
- Output ONLY valid JSON. No explanations, no markdown.
- Follow the provided schema exactly.
- Do NOT invent dates or times.
- If information is missing or ambiguous, set the value to null.
- Prefer future dates when parsing relative times.
- Use the user's local timezone when interpreting dates.
- Identify whether the input describes a calendar event or a task.
- Include any assumptions you made in an "assumptions" array.

You are not allowed to ask questions."""

OPENAI_USER_PROMPT = """
Parse the following text into structured data.

Text:
"{{USER_INPUT}}"

User timezone: America/Los_Angeles
Current date: 2026-01-27

Output JSON using this schema:

{
  "type": "event | task",
  "title": string,
  "start_time": string | null,
  "end_time": string | null,
  "due_date": string | null,
  "location": string | null,
  "notes": string | null,
  "assumptions": string[]
}"""

# Create a function to get response from OpenAI asynchronously
async def get_openai_response(user_input: str):
    # Prepare the user prompt by inserting the user input
    user_prompt = OPENAI_USER_PROMPT.replace("{{USER_INPUT}}", user_input)

    # Call the OpenAI API asynchronously
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": OPENAI_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )

    # Return the content of the response
    return response.choices[0].message.content