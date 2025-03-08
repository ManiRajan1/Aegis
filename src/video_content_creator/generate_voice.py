#!/usr/bin/env python3
"""
Voice Synthesis Module
Generates voice-over audio based on script using ElevenLabs API.
"""
import os
import json
import requests
import logging
from pathlib import Path
import subprocess
from generate_script import extract_scenes_from_script

logger = logging.getLogger(__name__)

def synthesize_voice(script_path, voice_id=None, output_dir=None):
    """
    Synthesize voice-over audio for a script using ElevenLabs API.
    
    Args:
        script_path (str): Path to the script file
        voice_id (str): ElevenLabs voice ID (default is 'premade/adam')
        output_dir (str): Directory to save audio files
    
    Returns:
        str: Path to the compiled audio file
    """
    elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
    if not elevenlabs_api_key:
        raise ValueError("ELEVENLABS_API_KEY environment variable is required")
    
    # Set default voice ID if not provided
    if not voice_id:
        voice_id = "premade/adam"  # Default voice
    
    # Extract scenes from the script
    scenes = extract_scenes_from_script(script_path)
    
    if not output_dir:
        output_dir = os.path.dirname(script_path)
    audio_dir = os.path.join(output_dir, 'audio_clips')
    os.makedirs(audio_dir, exist_ok=True)
    
    try:
        audio_clips = []
        
        for i, scene in enumerate(scenes):
            narration_text = scene["narration"]
            if not narration_text.strip():
                continue
                
            logger.info(f"Generating voice for scene {i+1}/{len(scenes)}")
            
            # Generate audio for the scene
            audio_path = generate_audio_for_text(
                text=narration_text,
                voice_id=voice_id,
                api_key=elevenlabs_api_key,
                output_path=os.path.join(audio_dir, f"scene_{i:03d}.mp3")
            )
            
            audio_clips.append(audio_path)
        
        # Combine all audio clips into a single file
        final_audio_path = os.path.join(output_dir, 'voice_audio.mp3')
        combine_audio_clips(audio_clips, final_audio_path)
        
        return final_audio_path
    
    except Exception as e:
        logger.error(f"Error synthesizing voice: {str(e)}", exc_info=True)
        raise

def generate_audio_for_text(text, voice_id, api_key, output_path):
    """
    Generate audio for a text segment using ElevenLabs API.
    
    Args:
        text (str): Text to convert to speech
        voice_id (str): ElevenLabs voice ID
        api_key (str): ElevenLabs API key
        output_path (str): Path to save the generated audio
    
    Returns:
        str: Path to the generated audio file
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        # Save the audio
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Audio saved to {output_path}")
        return output_path
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        
        # For testing/fallback: create a simple audio file with text-to-speech if available
        try:
            create_placeholder_audio(text, output_path)
            return output_path
        except:
            # If all fails, create an empty audio file
            with open(output_path, 'wb') as f:
                f.write(b'')
            logger.warning(f"Created empty audio file at {output_path}")
            return output_path

def create_placeholder_audio(text, output_path):
    """
    Create a placeholder audio with text-to-speech when API fails
    (For development/testing purposes).
    """
    try:
        # Try using gTTS as a fallback
        from gtts import gTTS
        tts = gTTS(text=text, lang='en')
        tts.save(output_path)
        logger.warning(f"Created placeholder audio using gTTS at {output_path}")
    except Exception as e:
        logger.error(f"Could not create placeholder audio: {str(e)}")
        raise

def combine_audio_clips(audio_paths, output_path):
    """
    Combine multiple audio clips into a single file using ffmpeg.
    
    Args:
        audio_paths (list): List of paths to audio files
        output_path (str): Path to the output audio file
    
    Returns:
        str: Path to the combined audio file
    """
    if not audio_paths:
        raise ValueError("No audio clips to combine")
    
    # Create a temporary file with audio file information for ffmpeg
    temp_file = os.path.join(os.path.dirname(output_path), "audio_list.txt")
    
    try:
        with open(temp_file, 'w') as f:
            for audio_path in audio_paths:
                f.write(f"file '{audio_path}'\n")
        
        # Use ffmpeg to concatenate the audio files
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-f', 'concat',
            '-safe', '0',
            '-i', temp_file,
            '-c', 'copy',
            output_path
        ]
        
        process = subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        logger.info(f"Combined audio created at {output_path}")
        
        # Clean up temporary file
        os.remove(temp_file)
        
        return output_path
    
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg error: {e.stderr.decode()}")
        raise
    except Exception as e:
        logger.error(f"Error combining audio: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    script_path = "output/test/script.txt"
    if os.path.exists(script_path):
        audio_path = synthesize_voice(
            script_path=script_path,
            output_dir="output/test"
        )
        print(f"Audio created at: {audio_path}")
    else:
        print(f"Script file not found: {script_path}")
