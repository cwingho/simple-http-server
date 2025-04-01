import os
import posixpath
from urllib.parse import unquote

def normalize_path(path):
    """
    Normalize and sanitize a path to prevent directory traversal attacks.
    
    Args:
        path (str): The path to normalize
        
    Returns:
        str: A normalized and sanitized path
    """
    # Unquote URL-encoded characters
    path = unquote(path)
    
    # Convert separators to native OS format
    path = path.replace('/', os.sep)
    
    # Normalize the path (resolve '..' and '.')
    normalized_path = posixpath.normpath(path)
    
    # Ensure the path doesn't start with '..' to prevent directory traversal
    if normalized_path.startswith('..'):
        normalized_path = ''
    
    return normalized_path

def is_path_safe(base_path, requested_path):
    """
    Check if the requested path is safe (within the base directory).
    
    Args:
        base_path (str): The base directory path
        requested_path (str): The requested path
        
    Returns:
        bool: True if the path is safe, False otherwise
    """
    # Get absolute paths
    base_abs = os.path.abspath(base_path)
    requested_abs = os.path.abspath(os.path.join(base_path, requested_path))
    
    # Check if the requested path is within the base path
    return requested_abs.startswith(base_abs)

def get_file_info(path):
    """
    Get file information (size, modification time).
    
    Args:
        path (str): Path to the file
        
    Returns:
        tuple: (size, last_modified_time)
    """
    stat_info = os.stat(path)
    return (stat_info.st_size, stat_info.st_mtime) 