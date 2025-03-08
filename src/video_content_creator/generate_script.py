#!/usr/bin/env python3
"""
AI Script Generation Module
Generates content scripts based on given topics using OpenAI APIs.
"""
import os
import json
import logging
import openai
from pathlib import Path

logger = logging.getLogger(__name__)

def generate_content_script(topic, style='educational', length='medium', output_dir=None):
    """
    Generate a content script using OpenAI's GPT model.
    
    Args:
        topic (str): The main topic for the content
        style (str): Content style (educational, entertaining, narrative, etc.)
        length (str): Content length (short, medium, long)
        output_dir (str): Directory to save the output script
    
    Returns:
        str: Path to the generated script file
    """
    # Configure OpenAI
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    # Define length parameters in words
    length_mapping = {
        'short': 300,
        'medium': 600,
        'long': 1200
    }
    word_count = length_mapping.get(length, 600)
    
    # Prepare the prompt for script generation
    prompt = f"""
    Create a {style} script about {topic}.
    The script should be approximately {word_count} words and include:
    - An engaging introduction
    - Clear sections with appropriate headings
    - A conclusion that summarizes key points
    
    Format the script with:
    - Scene descriptions in [brackets]
    - Narration text as regular paragraphs
    - Visual cues or B-roll suggestions in (parentheses)
    """
    
    try:
        # Call the OpenAI API
        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert content creator who specializes in creating engaging scripts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        # Extract the generated script
        script_content = response.choices[0].message.content
        
        # Create metadata for the script
        metadata = {
            "topic": topic,
            "style": style,
            "target_length": length,
            "word_count": len(script_content.split()),
            "estimated_duration_seconds": len(script_content.split()) / 2.5  # Rough estimate: 150 words per minute
        }
        
        # Save the script and metadata
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
            # Save script
            script_path = os.path.join(output_dir, 'script.txt')
            with open(script_path, 'w', encoding='utf-8') as file:
                file.write(script_content)
            
            # Save metadata
            metadata_path = os.path.join(output_dir, 'script_metadata.json')
            with open(metadata_path, 'w', encoding='utf-8') as file:
                json.dump(metadata, file, indent=2)
            
            logger.info(f"Script generated and saved to {script_path}")
            return script_path
        else:
            logger.warning("No output directory specified, script not saved")
            return script_content
    
    except Exception as e:
        logger.error(f"Error generating script: {str(e)}", exc_info=True)
        raise

def extract_scenes_from_script(script_path):
    """
    Parse a script file and extract scene descriptions for video generation.
    
    Args:
        script_path (str): Path to the script file
        
    Returns:
        list: List of scene descriptions with text and visual cues
    """
    try:
        with open(script_path, 'r', encoding='utf-8') as file:
            script_content = file.read()
        
        # Split script into paragraphs
        paragraphs = script_content.split('\n\n')
        scenes = []
        
        for para in paragraphs:
            if para.strip():
                # Extract scene descriptions [in brackets]
                import re
                scene_desc = re.findall(r'\[(.*?)\]', para)
                scene_desc = scene_desc[0] if scene_desc else "General scene"
                
                # Extract visual cues (in parentheses)
                visual_cues = re.findall(r'\((.*?)\)', para)
                
                # Clean the paragraph text
                text = re.sub(r'\[(.*?)\]', '', para)
                text = re.sub(r'\((.*?)\)', '', text).strip()
                
                if text:
                    scenes.append({
                        "scene_description": scene_desc,
                        "narration": text,
                        "visual_cues": visual_cues
                    })
        
        return scenes
    
    except Exception as e:
        logger.error(f"Error extracting scenes from script: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    script_path = generate_content_script(
        topic="Artificial Intelligence in Healthcare",
        style="educational",
        length="medium",
        output_dir="output/test"
    )
    
    if os.path.exists(script_path):
        scenes = extract_scenes_from_script(script_path)
        print(f"Extracted {len(scenes)} scenes from the script.")
