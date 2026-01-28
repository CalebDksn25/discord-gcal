from dotenv import load_dotenv
from openai import AsyncOpenAI
import os
from lib.prompts import get_user_prompt, OPENAI_SYSTEM_PROMPT


# Load environment variables from .env file
load_dotenv()

# Create the OpenAI client instance
client = AsyncOpenAI()

# Create a function to get response from OpenAI asynchronously
async def get_openai_response(user_input: str):
    # Prepare the user prompt with current LA date
    user_prompt = get_user_prompt(user_input)

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