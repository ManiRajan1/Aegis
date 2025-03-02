import json
import datetime
import generate_script, generate_voice

# Load prompts from JSON file
with open("data/prompts.json", "r") as f:
    prompts = json.load(f)["prompts"]

# todays_prompt = prompts[day_of_year - 1]  # Adjust index (0-based)
todays_prompt = prompts[0]

# Generate the script for video
script = generate_script.openAI_API(prompt=todays_prompt["prompt"])

generate_voice.ElevenLabs(script)