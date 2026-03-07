import os
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found")

client = OpenAI(api_key=api_key)

def summarize(text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You summarize news in 2 sentences."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content


example_text = "OpenAI released a new AI model today that improves reasoning ability."
summary = summarize(example_text)
print(summary)