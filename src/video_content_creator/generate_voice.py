from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import save
import os


def ElLabs (script:str):
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API")
    client = ElevenLabs(api_key=api_key)
    audio = client.text_to_speech.convert(
        text=script,
        voice_id="XrExE9yKIg1WjnnlVkGX",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )

    save(audio, "/data/voice.mp3")

if __name__ == "__main__":
    ElLabs(script ="The first move is what sets everything in motion.")

