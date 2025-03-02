from openai import OpenAI
import httpx
from dotenv import load_dotenv

def openAI_API(prompt:str):

    load_dotenv()
    client = OpenAI(http_client = httpx.Client(verify=False))
    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system", 
            "content": "You are a creative children's story writer."
        },
        {
            "role": "user",
            "content": prompt
        }
    ])

    return(completion.choices[0].message.content)


if __name__ == "__main__":
    out = openAI_API("Give me a haiku saying API connection is up")
    print (out)