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
    설정 파일을 불러와요.
    
    매개변수:
        filename (str): 설정 파일의 이름 (예: 'key_settings.json')
        
    반환값:
        dict: 설정 정보가 담긴 사전. 파일이 없으면 빈 사전을 반환해요.
    """
    # 사용자 데이터 디렉토리 안의 설정 파일 경로를 만들어요
    settings_path = os.path.join(get_user_data_directory(), filename)
    
    # 파일이 존재하는지 확인해요
    if os.path.exists(settings_path):
        try:
            # 파일을 열고 내용을 읽어요
            with open(settings_path, 'r', encoding='utf-8') as file:
                # JSON 형식으로 된 설정을 파이썬 사전으로 변환해요
                return json.load(file)
        except Exception as e:
            # 파일을 읽는 중 오류가 발생하면 오류 메시지를 출력하고 빈 사전을 반환해요
            print(f"설정 파일 '{filename}'을 읽는 중 오류가 발생했어요: {e}")
            return {}
    else:
        # 파일이 없으면 빈 사전을 반환해요
        return {}


def save_settings(settings, filename):
    """
    설정을 파일에 저장해요.
    
    매개변수:
        settings (dict): 저장할 설정 정보가 담긴 사전
        filename (str): 설정 파일의 이름 (예: 'key_settings.json')
        
    반환값:
        bool: 저장 성공 여부 (성공: True, 실패: False)
    """
    # 사용자 데이터 디렉토리 안의 설정 파일 경로를 만들어요
    settings_path = os.path.join(get_user_data_directory(), filename)
    
    try:
        # 사용자 데이터 디렉토리가 없다면 만들어요
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        
        # JSON으로 직렬화할 수 있도록 설정 사전을 복사해요
        serializable_settings = {}
        
        # 각 설정 값을 직렬화할 수 있는 형식으로 변환해요
        for key, value in settings.items():
            # 값의 타입에 따라 적절히 저장 (키보드 설정은 정수, 마우스 설정은 문자열 또는 정수)
            if isinstance(value, (int, str, float, bool, list, dict, tuple)):
                # 이미 JSON 직렬화 가능한 타입이면 그대로 사용
                serializable_settings[key] = value
            else:
                # 다른 타입은 문자열로 변환하여 저장
                try:
                    serializable_settings[key] = int(value)  # 정수로 변환 시도
                except (ValueError, TypeError):
                    serializable_settings[key] = str(value)  # 정수 변환 실패 시 문자열로 저장
        
        # 파일을 열고 설정을 저장해요
        with open(settings_path, 'w', encoding='utf-8') as file:
            # 파이썬 사전을 JSON 형식으로 변환해서 저장해요
            # indent=4는 들여쓰기를 4칸 간격으로 예쁘게 저장한다는 뜻이에요
            json.dump(serializable_settings, file, indent=4, ensure_ascii=False)
        return True  # 저장 성공
    except Exception as e:
        # 파일을 저장하는 중 오류가 발생하면 오류 메시지를 출력하고 False를 반환해요
        print(f"설정 파일 '{filename}'을 저장하는 중 오류가 발생했어요: {e}")
        return False  # 저장 실패 