import os
import json
import tempfile
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def upload_to_youtube(video_path, script_path, topic):
    """
    Upload a video to YouTube with metadata from the script.
    
    Args:
        video_path (str): Path to the video file to upload
        script_path (str): Path to the script file (used for description)
        topic (str): Topic of the video (used for title and tags)
        
    Returns:
        str: URL of the uploaded video or None if upload failed
    """
    try:
        # Check if files exist
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return None
            
        if not os.path.exists(script_path):
            logger.error(f"Script file not found: {script_path}")
            return None
            
        # Read script content for description
        with open(script_path, 'r', encoding='utf-8') as file:
            script_content = file.read()
            
        # Prepare description (first 5000 chars max)
        description = f"Video about {topic}\n\n{script_content[:5000]}"
        
        # Prepare video title
        title = f"{topic} - Automated Educational Video"
        
        # Generate tags from topic
        tags = [topic] + topic.split()
        
        # Get API key from environment variables
        api_key = os.environ.get('GOOGLE_API_KEY')
        
        # Get client credentials from environment variables
        client_id = os.environ.get('YOUTUBE_CLIENT_ID')
        client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            logger.error("YouTube API credentials not found in environment variables")
            return None
            
        # Create a temporary client_secret.json file from environment variables
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
            }
        }
        
        # Create a temporary file to store client config
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(client_config, temp_file)
            client_secrets_file = temp_file.name
        
        try:
            # Authentication
            # Get credentials and create API client
            scopes = ["https://www.googleapis.com/auth/youtube.upload"]
            
            # Get credentials and create an API client
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes)
            credentials = flow.run_local_server(port=8080)
            
            # Use API key alongside OAuth credentials for quota management
            youtube = googleapiclient.discovery.build(
                "youtube", 
                "v3", 
                credentials=credentials,
                developerKey=api_key if api_key else None
            )
            
            # Define video metadata
            request_body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': '27'  # Education category
                },
                'status': {
                    'privacyStatus': 'private',  # Start as private, can be changed later
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Prepare the media file
            media_file = MediaFileUpload(video_path, 
                                        mimetype='video/*',
                                        resumable=True)
            
            # Execute the upload
            logger.info(f"Starting upload for video: {title}")
            upload_request = youtube.videos().insert(
                part="snippet,status",
                body=request_body,
                media_body=media_file
            )
            
            # Execute the upload and handle the response
            response = upload_request.execute()
            video_id = response.get('id')
            
            if video_id:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"Upload successful! Video URL: {video_url}")
                return video_url
            else:
                logger.error("Upload failed - no video ID returned")
                return None
                
        finally:
            # Clean up the temporary file
            if os.path.exists(client_secrets_file):
                os.unlink(client_secrets_file)
                
    except Exception as e:
        logger.error(f"Error uploading video to YouTube: {str(e)}")
        return None

if __name__ == "__main__":
    # Example usage
    video_url = upload_to_youtube(
        video_path="path/to/your/video.mp4",
        script_path="path/to/your/script.txt",
        topic="Python Programming"
    )
    
    if video_url:
        print(f"Video uploaded successfully: {video_url}")
    else:
        print("Video upload failed")
