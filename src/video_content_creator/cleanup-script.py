#!/usr/bin/env python3
"""
Cleanup Module
Handles cleanup of temporary files after pipeline completion.
"""
import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def cleanup_temp_files(output_dir, keep_final=True):
    """
    Clean up temporary files created during the content generation process.
    
    Args:
        output_dir (str): Directory containing files to clean up
        keep_final (bool): Whether to keep the final video and script
    
    Returns:
        bool: True if cleanup was successful
    """
    try:
        # Directories to clean up
        temp_dirs = ['video_frames', 'audio_clips']
        
        # Files to keep if keep_final is True
        keep_patterns = ['final_video.mp4', 'script.txt', 'script_metadata.json']
        
        # Remove temporary directories
        for temp_dir in temp_dirs:
            dir_path = os.path.join(output_dir, temp_dir)
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                shutil.rmtree(dir_path)
                logger.info(f"Removed directory: {dir_path}")
        
        # Clean up temporary files in the output directory
        if not keep_final:
            # Remove all files except the ones matching keep_patterns
            for file_path in Path(output_dir).glob('*'):
                if file_path.is_file():
                    if not any(pattern in file_path.name for pattern in keep_patterns):
                        os.remove(file_path)
                        logger.info(f"Removed file: {file_path}")
        else:
            # Keep only the final files defined in keep_patterns
            for file_path in Path(output_dir).glob('*'):
                if file_path.is_file():
                    # Check if this is one of the files we want to keep
                    should_keep = any(pattern in file_path.name for pattern in keep_patterns)
                    # If it's not a file we want to keep and isn't the final file, remove it
                    if not should_keep and "final_video" not in file_path.name:
                        os.remove(file_path)
                        logger.info(f"Removed file: {file_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    test_dir = "output/test"
    if os.path.exists(test_dir):
        cleanup_temp_files(test_dir, keep_final=True)
        print("Cleanup completed.")
    else:
        print(f"Directory not found: {test_dir}")
