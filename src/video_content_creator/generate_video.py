#!/usr/bin/env python3
"""
Video Generation Module
Creates video content based on script scenes using Stability AI API.
"""
import os
import time
import json
import requests
import logging
from pathlib import Path
import subprocess
from generate_script import extract_scenes_from_script

logger = logging.getLogger(__name__)

def create_video_content(script_path, style='educational', output_dir=None):
    """
    Create video content based on script using Stability AI.
    
    Args:
        script_path (str): Path to the script file
        style (str): Visual style for the video
        output_dir (str): Directory to save output files
    
    Returns:
        str: Path to the compiled video file
    """
    stability_api_key = os.getenv('STABILITY_API_KEY')
    if not stability_api_key:
        raise ValueError("STABILITY_API_KEY environment variable is required")
    
    # Extract scenes from the script
    scenes = extract_scenes_from_script(script_path)
    
    if not output_dir:
        output_dir = os.path.dirname(script_path)
    video_dir = os.path.join(output_dir, 'video_frames')
    os.makedirs(video_dir, exist_ok=True)
    
    # Map content style to visual style for Stability AI
    style_prompts = {
        'educational': "professional, clean, informative, high quality, detailed illustration",
        'entertaining': "vibrant, dynamic, engaging, colorful, high-energy visuals",
        'narrative': "cinematic, atmospheric, storytelling, emotional, dramatic lighting",
        'technical': "detailed, precise, diagrams, blueprints, technical illustrations"
    }
    
    style_prompt = style_prompts.get(style, style_prompts['educational'])
    
    try:
        scene_images = []
        
        for i, scene in enumerate(scenes):
            # Combine scene description with visual cues
            visual_description = scene["scene_description"]
            if scene["visual_cues"]:
                visual_description += ". " + ". ".join(scene["visual_cues"])
            
            # Create prompt for image generation
            prompt = f"{visual_description}. {style_prompt}"
            logger.info(f"Generating image for scene {i+1}/{len(scenes)}: {prompt[:50]}...")
            
            # Generate image for the scene using Stability AI API
            image_path = generate_image_for_scene(
                prompt=prompt,
                api_key=stability_api_key,
                output_path=os.path.join(video_dir, f"scene_{i:03d}.png")
            )
            
            scene_images.append({
                "image_path": image_path,
                "duration": len(scene["narration"].split()) / 2.5  # Estimate 150 words per minute
            })
            
            # Rate limiting to avoid API throttling
            time.sleep(1)
        
        # Create a video from the images using ffmpeg
        video_path = os.path.join(output_dir, 'video_without_audio.mp4')
        create_video_from_images(scene_images, video_path)
        
        return video_path
    
    except Exception as e:
        logger.error(f"Error creating video content: {str(e)}", exc_info=True)
        raise

def generate_image_for_scene(prompt, api_key, output_path):
    """
    Generate an image for a scene using Stability AI API.
    
    Args:
        prompt (str): The image description prompt
        api_key (str): Stability AI API key
        output_path (str): Path to save the generated image
    
    Returns:
        str: Path to the generated image
    """
    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    body = {
        "text_prompts": [
            {
                "text": prompt,
                "weight": 1.0
            }
        ],
        "cfg_scale": 7,
        "height": 1024,
        "width": 1024,
        "samples": 1,
        "steps": 30
    }
    
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        
        data = response.json()
        
        # Save the image
        if "artifacts" in data and len(data["artifacts"]) > 0:
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(data["artifacts"][0]["base64"]))
            logger.info(f"Image saved to {output_path}")
            return output_path
        else:
            raise ValueError("No image data in API response")
    
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        
        # For testing/fallback: create a blank image with text
        create_placeholder_image(prompt, output_path)
        return output_path

def create_placeholder_image(text, output_path):
    """
    Create a placeholder image with text when API fails
    (For development/testing purposes).
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a blank image
        img = Image.new('RGB', (1024, 1024), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        
        # Add text
        font = ImageFont.load_default()
        d.text((10, 10), text[:500], fill=(255, 255, 255), font=font)
        
        img.save(output_path)
        logger.warning(f"Created placeholder image at {output_path}")
    
    except Exception as e:
        logger.error(f"Could not create placeholder image: {str(e)}")

def create_video_from_images(scene_images, output_path):
    """
    Create a video from a series of images using ffmpeg.
    
    Args:
        scene_images (list): List of dictionaries with image_path and duration
        output_path (str): Path to the output video file
    
    Returns:
        str: Path to the created video file
    """
    # Create a temporary file with frame information for ffmpeg
    temp_file = os.path.join(os.path.dirname(output_path), "frames.txt")
    
    try:
        with open(temp_file, 'w') as f:
            for scene in scene_images:
                # Each image appears for its calculated duration
                f.write(f"file '{scene['image_path']}'\n")
                f.write(f"duration {max(1.0, scene['duration'])}\n")
            
            # Write the last image without duration (required by ffmpeg)
            if scene_images:
                f.write(f"file '{scene_images[-1]['image_path']}'\n")
        
        # Use ffmpeg to create the video
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-f', 'concat',
            '-safe', '0',
            '-i', temp_file,
            '-vsync', 'vfr',
            '-pix_fmt', 'yuv420p',
            '-c:v', 'libx264',
            '-r', '24',
            output_path
        ]
        
        process = subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        logger.info(f"Video created at {output_path}")
        
        # Clean up temporary file
        os.remove(temp_file)
        
        return output_path
    
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg error: {e.stderr.decode()}")
        raise
    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    import base64  # Add import for base64 decoding
    
    logging.basicConfig(level=logging.INFO)
    
    script_path = "output/test/script.txt"
    if os.path.exists(script_path):
        video_path = create_video_content(
            script_path=script_path,
            style="educational",
            output_dir="output/test"
        )
        print(f"Video created at: {video_path}")
    else:
        print(f"Script file not found: {script_path}")
