"""
시간 관련 유틸리티 함수 모음

이 모듈은 시간 처리와 관련된 유틸리티 함수들을 담고 있어요.
"""


def format_time(seconds):
    """
    초를 'MM:SS' 형식으로 변환해요.
    
    매개변수:
        seconds (float): 변환할 시간(초)
        
    반환값:
        str: 'MM:SS' 형식의 시간 문자열
    
    예시:
        >>> format_time(65)
        '01:05'
    """
    minutes = int(seconds // 60)  # 분 부분을 계산해요 (60으로 나눈 몫)
    seconds = int(seconds % 60)   # 초 부분을 계산해요 (60으로 나눈 나머지)
    return f"{minutes:02}:{seconds:02}"  # 두 자리 숫자로 포맷팅해요 