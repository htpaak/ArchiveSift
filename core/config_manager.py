"""
설정 관리 모듈

이 모듈은 프로그램 설정을 저장하고 불러오는 기능을 담당해요.
"""

import os  # 파일 경로 작업을 위한 모듈
import json  # 설정 파일을 JSON 형식으로 저장하고 불러오기 위한 모듈

# 설정 기본 경로는 core.utils.path_utils에서 가져와요
from core.utils.path_utils import get_user_data_directory


def load_settings(filename):
    """
    Load the settings file.
    
    Parameters:
        filename (str): Name of the settings file (e.g., 'key_settings.json')
        
    Returns:
        dict: A dictionary containing settings. Returns an empty dictionary if the file does not exist.
    """
    # Create the path to the settings file in the user data directory
    settings_path = os.path.join(get_user_data_directory(), filename)
    
    # Check if the file exists
    if os.path.exists(settings_path):
        try:
            # Open the file and read its contents
            with open(settings_path, 'r', encoding='utf-8') as file:
                # Convert the JSON-formatted settings into a Python dictionary
                return json.load(file)
        except Exception as e:
            # If an error occurs while reading the file, return an empty dictionary
            return {}
    else:
        # If the file does not exist, return an empty dictionary
        return {}


def save_settings(settings, filename):
    """
    Save the settings to a file.
    
    Parameters:
        settings (dict): A dictionary containing the settings to be saved
        filename (str): Name of the settings file (e.g., 'key_settings.json')
        
    Returns:
        bool: A boolean indicating whether the save was successful (True for success, False for failure)
    """
    # Create the path to the settings file in the user data directory
    settings_path = os.path.join(get_user_data_directory(), filename)
    
    try:
        # Create the user data directory if it does not exist
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        
        # Copy the settings dictionary for JSON serialization
        serializable_settings = {}
        
        # Convert each setting value into a JSON-serializable format
        for key, value in settings.items():
            # Save appropriately based on the type of the value (keyboard settings are integers, mouse settings can be strings or integers)
            if isinstance(value, (int, str, float, bool, list, dict, tuple)):
                # If it is already a JSON-serializable type, use it as is
                serializable_settings[key] = value
            else:
                # For other types, convert to a string and save
                try:
                    serializable_settings[key] = int(value)  # Attempt conversion to integer
                except (ValueError, TypeError):
                    serializable_settings[key] = str(value)  # If conversion to integer fails, save as a string
        
        # Open the file and save the settings
        with open(settings_path, 'w', encoding='utf-8') as file:
            # Convert the Python dictionary to JSON format and save it
            # indent=4 means the file will be formatted with an indentation of 4 spaces for readability
            json.dump(serializable_settings, file, indent=4, ensure_ascii=False)
        return True  # Save successful
    except Exception as e:
        # If an error occurs while saving the file, return False
        return False  # Save failed 