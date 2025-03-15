"""
정렬 관련 유틸리티 함수 모음

이 모듈은 문자열 정렬과 관련된 유틸리티 함수들을 담고 있어요.
"""

import re  # 정규식 모듈을 가져와요 (문자열 패턴을 찾는 데 사용해요)


def atoi(text):
    """
    텍스트가 숫자로만 이루어져 있으면 정수로 변환하고, 아니면 그대로 반환해요.
    
    이 함수는 natural_keys 함수를 돕기 위해 사용돼요.
    
    매개변수:
        text (str): 변환할 텍스트
        
    반환값:
        int 또는 str: 텍스트가 숫자면 정수, 아니면 원래 텍스트
    """
    return int(text) if text.isdigit() else text


def natural_keys(text):
    """
    숫자가 포함된 문자열을 자연스럽게 정렬하기 위한 키 함수예요.
    
    일반 문자열 정렬은 '1, 10, 2'와 같이 정렬하지만,
    이 함수를 사용하면 '1, 2, 10'과 같이 사람이 기대하는 방식으로 정렬돼요.
    
    매개변수:
        text (str): 정렬할 텍스트
        
    반환값:
        list: 정렬 키로 사용할 리스트
        
    예시 사용법:
        >>> sorted(['z10.txt', 'z1.txt', 'z2.txt'], key=natural_keys)
        ['z1.txt', 'z2.txt', 'z10.txt']
    """
    # 숫자와 나머지 부분을 분리해요. 예: 'abc123def' -> ['abc', '123', 'def']
    return [atoi(c) for c in re.split('([0-9]+)', text)] 