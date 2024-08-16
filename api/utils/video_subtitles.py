import os

def save_subtitles_to_file(subtitles: str, file_path: str) -> None:
    """Saves subtitles to a file.
    
    Args:
        subtitles (str): The subtitle content to be saved.
        file_path (str): The path where the subtitle file should be saved.
    """
    try:
        with open(file_path, 'w') as file:
            file.write(subtitles)
    except Exception as e:
        raise Exception(f"Error saving subtitles to file: {str(e)}")

def delete_file(file_path: str) -> None:
    """Deletes a file from the file system.
    
    Args:
        file_path (str): The path of the file to delete.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error deleting file: {str(e)}")
