#!/usr/bin/env python3
"""
Main orchestration file for AI content generation and publishing pipeline.
This script coordinates the entire workflow from script generation to YouTube upload.
"""
import os
import json
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Import individual modules
from generate_script import generate_content_script
from generate_video import create_video_content
from generate_voice import synthesize_voice
from merge_media import combine_audio_video
from upload_youtube import upload_to_youtube
from cleanup import cleanup_temp_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from .env file"""
    load_dotenv()
    required_vars = [
        'OPENAI_API_KEY', 
        'ELEVENLABS_API_KEY',
        'GOOGLE_API_KEY',
        'YOUTUBE_CLIENT_ID',
        'YOUTUBE_CLIENT_SECRET',
        'STABILITY_API_KEY'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return False
    return True

def load_prompt_from_file(file_path, index=None):
    """
    Load a prompt from a JSON file based on index or date.
    
    Args:
        file_path (str): Path to the JSON file containing prompts
        index (int, optional): Specific index to use (1-based). 
                              If None, uses day of year for chronological ordering.
    
    Returns:
        dict: Prompt data with topic, style, and length
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        
        if not prompts or not isinstance(prompts, list):
            raise ValueError("Prompts file must contain a list of prompt objects")
        
        # If no index specified, use the day of year
        if index is None:
            day_of_year = datetime.now().timetuple().tm_yday
            index = day_of_year
        
        # Convert index to 0-based for array access
        # Use modulo to cycle through prompts if we have more days than prompts
        prompt_index = (int(index) - 1) % len(prompts)
        
        prompt_data = prompts[prompt_index]
        logger.info(f"Loaded prompt #{prompt_index + 1}: {prompt_data.get('topic', 'No topic specified')}")
        
        return prompt_data
        
    except Exception as e:
        logger.error(f"Error loading prompt from file: {str(e)}", exc_info=True)
        # Return a default prompt as fallback
        return {
            "topic": "Artificial Intelligence",
            "style": "educational",
            "length": "medium"
        }

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='AI Content Generation Pipeline')
    
    # Add argument group for direct topic specification
    topic_group = parser.add_argument_group('Direct Topic Specification')
    topic_group.add_argument('--topic', type=str, help='Topic for content generation')
    topic_group.add_argument('--style', type=str, default='educational', 
                          help='Content style (educational, entertaining, etc.)')
    topic_group.add_argument('--length', type=str, default='medium', 
                          help='Content length (short, medium, long)')
    
    # Add argument group for prompt file
    prompt_group = parser.add_argument_group('Prompt File')
    prompt_group.add_argument('--from-prompt-file', type=str, 
                           help='Path to JSON file with prompts')
    prompt_group.add_argument('--prompt-index', type=int,
                           help='Index of prompt to use (defaults to day of year)')
    
    # General arguments
    parser.add_argument('--skip-upload', action='store_true', help='Skip YouTube upload step')
    
    return parser.parse_args()

def run_pipeline(topic, style='educational', length='medium', skip_upload=False):
    """Execute the full content generation pipeline"""
    logger.info(f"Starting content generation pipeline for topic: {topic}")
    
    # Create output directory
    output_dir = os.path.join("output", topic.replace(" ", "_"))
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Generate script
        logger.info("Generating content script...")
        script_path = generate_content_script(
            topic=topic,
            style=style,
            length=length,
            output_dir=output_dir
        )
        
        # Generate video content
        logger.info("Creating video content...")
        video_path = create_video_content(
            script_path=script_path,
            style=style,
            output_dir=output_dir
        )
        
        # Generate voice-over
        logger.info("Synthesizing voice-over...")
        audio_path = synthesize_voice(
            script_path=script_path,
            output_dir=output_dir
        )
        
        # Combine audio and video
        logger.info("Merging audio and video...")
        final_video_path = combine_audio_video(
            video_path=video_path,
            audio_path=audio_path,
            output_dir=output_dir
        )
        
        # Upload to YouTube if not skipped
        if not skip_upload:
            logger.info("Uploading to YouTube...")
            video_url = upload_to_youtube(
                video_path=final_video_path,
                script_path=script_path,
                topic=topic
            )
            logger.info(f"Video uploaded successfully: {video_url}")
        
        # Clean up temporary files
        logger.info("Cleaning up temporary files...")
        cleanup_temp_files(output_dir, keep_final=True)
        
        logger.info("Pipeline completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    if not load_environment():
        exit(1)
    
    args = parse_arguments()
    
    # Determine if we're using a prompt file or direct topic specification
    if args.from_prompt_file:
        # Load prompt from JSON file
        prompt_data = load_prompt_from_file(args.from_prompt_file, args.prompt_index)
        topic = prompt_data.get('topic')
        style = prompt_data.get('style', 'educational')
        length = prompt_data.get('length', 'medium')
    else:
        # Use directly specified arguments
        if not args.topic:
            logger.error("Error: Either --topic or --from-prompt-file must be specified")
            exit(1)
        topic = args.topic
        style = args.style
        length = args.length
    
    # Run the pipeline
    success = run_pipeline(
        topic=topic,
        style=style,
        length=length,
        skip_upload=args.skip_upload
    )
    
    exit(0 if success else 1)
