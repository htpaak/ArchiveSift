"""
애플리케이션 버전 관리 모듈

이 모듈은 애플리케이션의 버전 정보를 관리하고 제공합니다.
시맨틱 버전 관리 원칙을 따릅니다.
"""
import datetime
from typing import Dict, Tuple, Any


# 애플리케이션 버전 (메이저, 마이너, 패치)
VERSION: Tuple[int, int, int] = (1, 0, 0)

# 빌드 날짜 (자동 생성)
BUILD_DATE = datetime.datetime.now().strftime("%Y-%m-%d")

# 코드명 (선택 사항)
CODENAME = ""


def get_version_string() -> str:
    """
    버전 문자열 반환 (x.y.z 형식)
    
    Returns:
        버전 문자열
    """
    return '.'.join(map(str, VERSION))


def get_full_version_string() -> str:
    """
    전체 버전 문자열 반환 (버전 + 코드명)
    
    Returns:
        전체 버전 문자열
    """
    if CODENAME:
        return f"{get_version_string()} ({CODENAME})"
    else:
        return get_version_string()


def get_version_info() -> Dict[str, Any]:
    """
    버전 정보를 딕셔너리로 반환
    
    Returns:
        버전 정보를 포함한 딕셔너리
    """
    return {
        'major': VERSION[0],
        'minor': VERSION[1],
        'patch': VERSION[2],
        'version': get_version_string(),
        'full_version': get_full_version_string(),
        'codename': CODENAME,
        'build_date': BUILD_DATE,
    }


def is_development_version() -> bool:
    """
    개발 버전인지 확인
    
    Returns:
        개발 버전 여부 (0.x.y 버전은 개발 버전으로 간주)
    """
    return VERSION[0] == 0


def check_version_upgrade(previous_version: str) -> Tuple[bool, str]:
    """
    이전 버전에서 업그레이드 여부 확인
    
    Args:
        previous_version: 이전 버전 문자열 (x.y.z 형식)
        
    Returns:
        (업그레이드 여부, 업그레이드 유형)
        업그레이드 유형은 'major', 'minor', 'patch', 'none' 중 하나
    """
    if not previous_version:
        return True, 'new_install'
    
    try:
        prev_parts = list(map(int, previous_version.split('.')))
        
        # 버전 부분 개수 맞추기
        while len(prev_parts) < 3:
            prev_parts.append(0)
        
        # 메이저 버전 업그레이드
        if VERSION[0] > prev_parts[0]:
            return True, 'major'
        
        # 마이너 버전 업그레이드
        if VERSION[0] == prev_parts[0] and VERSION[1] > prev_parts[1]:
            return True, 'minor'
        
        # 패치 버전 업그레이드
        if VERSION[0] == prev_parts[0] and VERSION[1] == prev_parts[1] and VERSION[2] > prev_parts[2]:
            return True, 'patch'
        
        # 버전 다운그레이드 (더 낮은 버전 사용 중)
        if (VERSION[0] < prev_parts[0] or 
            (VERSION[0] == prev_parts[0] and VERSION[1] < prev_parts[1]) or
            (VERSION[0] == prev_parts[0] and VERSION[1] == prev_parts[1] and VERSION[2] < prev_parts[2])):
            return True, 'downgrade'
        
        # 동일 버전
        return False, 'none'
    
    except (ValueError, IndexError):
        # 버전 형식 오류
        return True, 'invalid_previous' 