#!/usr/bin/env python3
"""
Media Merger Module
Combines generated video and audio content into a final video.
"""
import os
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

def combine_audio_video(video_path, audio_path, output_dir=None):
    """
    Combine video and audio into a final video file using ffmpeg.
    
    Args:
        video_path (str): Path to the video file
        audio_path (str): Path to the audio file
        output_dir (str): Directory to save the output file
    
    Returns:
        str: Path to the final video file
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    if not output_dir:
        output_dir = os.path.dirname(video_path)
    
    final_video_path = os.path.join(output_dir, 'final_video.mp4')
    
    try:
        # Get audio duration
        audio_duration = get_media_duration(audio_path)
        
        # Get video duration
        video_duration = get_media_duration(video_path)
        
        logger.info(f"Audio duration: {audio_duration}s, Video duration: {video_duration}s")
        
        # If audio is longer than video, we need to slow down the video
        if audio_duration > video_duration:
            temp_video_path = os.path.join(output_dir, 'temp_adjusted_video.mp4')
            adjustment_factor = audio_duration / video_duration
            
            # Use ffmpeg setpts filter to adjust video speed
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',
                '-i', video_path,
                '-filter:v', f'setpts={adjustment_factor}*PTS',
                temp_video_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            video_path = temp_video_path
        
        # Combine video with audio
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            final_video_path
        ]
        
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        logger.info(f"Final video created at {final_video_path}")
        
        # Clean up temporary files
        if os.path.exists('temp_adjusted_video.mp4'):
            os.remove('temp_adjusted_video.mp4')
        
        return final_video_path
    
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error combining audio and video: {str(e)}")
        raise

def get_media_duration(file_path):
    """
    Get the duration of a media file using ffprobe.
    
    Args:
        file_path (str): Path to the media file
    
    Returns:
        float: Duration in seconds
    """
    try:
        cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        return duration
    
    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe error: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Error getting media duration: {str(e)}")
        raise

def add_subtitles(video_path, script_path, output_path=None):
    """
    Add subtitles to the video based on the script.
    
    Args:
        video_path (str): Path to the video file
        script_path (str): Path to the script file
        output_path (str, optional): Path for the output video with subtitles
        
    Returns:
        str: Path to the video with subtitles
    """
    if not output_path:
        filename = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(os.path.dirname(video_path), f"{filename}_with_subs.mp4")
    
    # First, create an SRT file from the script
    srt_path = os.path.join(os.path.dirname(video_path), "subtitles.srt")
    
    try:
        # Extract script content
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # Create a very simple SRT file (in a real app, you'd use proper timing)
        with open(srt