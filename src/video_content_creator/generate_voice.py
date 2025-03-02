from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import save
import os


def ElLabs (script:str):
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API")
    client = ElevenLabs(api_key=api_key, timeout=300)
    audio = client.generate(
        text=script,
        voice="Matilda"
    )

    if not os.path.exists ("./generated_files"):
        os.mkdir ("./generated_files")

    save (audio, "./generated_files/generated_audio.mp3")
    # with open ("./generated_files/generated_audio.mp3", "w+") as f:
    #     f.write (audio)

if __name__ == "__main__":
    ElLabs(script ="The first move is what sets everything in motion.")

