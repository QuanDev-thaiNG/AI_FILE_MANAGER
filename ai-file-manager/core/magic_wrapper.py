import os
import mimetypes

def detect_mime_type(file_path):
    """
    Detect MIME type of a file using Python's built-in mimetypes module.
    This is a fallback for when python-magic is not available.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: MIME type of the file
    """
    # Initialize mimetypes database
    mimetypes.init()
    
    # Get file extension
    _, ext = os.path.splitext(file_path)
    
    # Get MIME type based on extension
    mime_type, _ = mimetypes.guess_type(file_path)
    
    # Default to application/octet-stream if MIME type is not found
    if mime_type is None:
        mime_type = 'application/octet-stream'
    
    return mime_type