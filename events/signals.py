"""
애플리케이션 이벤트 신호 모듈

이 모듈은 애플리케이션 전체에서 사용할 수 있는 이벤트 신호를 정의합니다.
Observer 패턴의 구현을 위한 PyQt 신호들을 포함합니다.
"""
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, Any, List, Optional


class MediaSignals(QObject):
    """미디어 관련 이벤트 신호"""
    
    # 미디어 로드 관련 신호
    media_loaded = pyqtSignal(str)  # 미디어 로드 완료 (경로)
    media_loading_failed = pyqtSignal(str, str)  # 미디어 로드 실패 (경로, 오류 메시지)
    media_loading_progress = pyqtSignal(int, int)  # 미디어 로드 진행 상황 (현재, 전체)
    
    # 미디어 정보 관련 신호
    media_info_updated = pyqtSignal(dict)  # 미디어 정보 업데이트 (정보 딕셔너리)
    
    # 미디어 표시 관련 신호
    media_displayed = pyqtSignal(str)  # 미디어 표시 완료 (경로)
    media_display_changed = pyqtSignal(dict)  # 미디어 표시 상태 변경 (상태 딕셔너리)


class NavigationSignals(QObject):
    """탐색 관련 이벤트 신호"""
    
    # 파일 탐색 관련 신호
    navigation_index_changed = pyqtSignal(int)  # 내비게이션 인덱스 변경 (새 인덱스)
    file_list_changed = pyqtSignal(list)  # 파일 목록 변경 (새 파일 목록)
    directory_changed = pyqtSignal(str)  # 디렉토리 변경 (새 디렉토리 경로)
    
    # 폴더 탐색 관련 신호
    folder_selected = pyqtSignal(str)  # 폴더 선택 (폴더 경로)
    base_folder_changed = pyqtSignal(str)  # 기준 폴더 변경 (새 기준 폴더 경로)


class UISignals(QObject):
    """UI 관련 이벤트 신호"""
    
    # UI 상태 관련 신호
    ui_visibility_changed = pyqtSignal(dict)  # UI 가시성 변경 (컴포넌트별 가시성 딕셔너리)
    ui_state_changed = pyqtSignal(str, object)  # UI 상태 변경 (상태 키, 새 상태값)
    
    # 테마 관련 신호
    theme_changed = pyqtSignal(str)  # 테마 변경 (새 테마 이름)
    
    # UI 잠금 관련 신호
    ui_lock_changed = pyqtSignal(bool)  # UI 잠금 상태 변경 (잠금 여부)
    ui_title_lock_changed = pyqtSignal(bool)  # 타이틀바 잠금 상태 변경 (잠금 여부)


class FeatureSignals(QObject):
    """기능 관련 이벤트 신호"""
    
    # 북마크 관련 신호
    bookmark_added = pyqtSignal(str, str)  # 북마크 추가 (경로, 이름)
    bookmark_removed = pyqtSignal(str)  # 북마크 제거 (경로)
    bookmark_list_changed = pyqtSignal(list)  # 북마크 목록 변경 (새 북마크 목록)
    
    # 회전 관련 신호
    rotation_changed = pyqtSignal(int)  # 회전 상태 변경 (각도)
    
    # 비디오 관련 신호
    video_playback_state_changed = pyqtSignal(bool)  # 비디오 재생 상태 변경 (재생 중 여부)
    video_position_changed = pyqtSignal(float)  # 비디오 위치 변경 (진행률 0.0-1.0)
    video_volume_changed = pyqtSignal(int)  # 비디오 볼륨 변경 (볼륨 0-100)
    video_mute_changed = pyqtSignal(bool)  # 비디오 음소거 상태 변경 (음소거 여부)


class FileOperationSignals(QObject):
    """파일 작업 관련 이벤트 신호"""
    
    # 파일 작업 관련 신호
    file_operation_started = pyqtSignal(str, str, str)  # 파일 작업 시작 (작업 유형, 소스, 대상)
    file_operation_progress = pyqtSignal(str, int, int)  # 파일 작업 진행 (작업 유형, 현재, 전체)
    file_operation_completed = pyqtSignal(str, bool, str)  # 파일 작업 완료 (작업 유형, 성공 여부, 결과 메시지)
    
    # 파일 변경 감지 신호
    file_changed_externally = pyqtSignal(str)  # 외부에서 파일 변경 감지 (경로)
    directory_changed_externally = pyqtSignal(str)  # 외부에서 디렉토리 변경 감지 (경로)


class ApplicationSignals(QObject):
    """애플리케이션 관련 이벤트 신호"""
    
    # 애플리케이션 상태 관련 신호
    application_start = pyqtSignal()  # 애플리케이션 시작
    application_exit = pyqtSignal()  # 애플리케이션 종료
    
    # 설정 관련 신호
    settings_changed = pyqtSignal(str, object)  # 설정 변경 (설정 키, 새 설정값)
    settings_loaded = pyqtSignal(dict)  # 설정 로드 완료 (설정 딕셔너리)
    
    # 오류 관련 신호
    error_occurred = pyqtSignal(str, str, dict)  # 오류 발생 (오류 유형, 오류 메시지, 오류 세부 정보)


class MediaViewerSignals(QObject):
    """전체 이미지 뷰어 애플리케이션 신호 통합"""
    
    def __init__(self):
        super().__init__()
        
        # 각 카테고리별 신호 객체 인스턴스 생성
        self.media = MediaSignals()
        self.navigation = NavigationSignals()
        self.ui = UISignals()
        self.feature = FeatureSignals()
        self.file_operation = FileOperationSignals()
        self.application = ApplicationSignals()


# 전역 신호 인스턴스 (싱글톤)
_signals_instance = None

def get_signals() -> MediaViewerSignals:
    """
    전역 신호 인스턴스 반환 (싱글톤 패턴)
    
    Returns:
        MediaViewerSignals 인스턴스
    """
    global _signals_instance
    if _signals_instance is None:
        _signals_instance = MediaViewerSignals()
    return _signals_instance 