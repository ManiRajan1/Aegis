from openai import OpenAI
import httpx
from dotenv import load_dotenv

def openAI_API(prompt:str):

    load_dotenv()
    #client = OpenAI(http_client = httpx.Client(verify=False))
    client = OpenAI()
    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system", 
            "content": "You are a creative children's story writer.\
                        Donot exceed 200 words in the story.\
                        Create the story in a scene by scene\
                        manner such that the script can be played."
        },
        {
            "role": "user",
            "content": prompt
        }
    ])

    return(completion.choices[0].message.content)


if __name__ == "__main__":
    out = openAI_API("In a world where robots follow strict instructions, a tiny robot named R1X wishes to dream like humans. With the help of a curious child, R1X embarks on an adventure to discover what dreams are and whether a robot can have them too.")
    print (out)