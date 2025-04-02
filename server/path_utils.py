import os

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