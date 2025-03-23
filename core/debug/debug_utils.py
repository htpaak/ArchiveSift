"""
일반 디버깅 유틸리티

디버깅에 유용한 일반적인 유틸리티 함수들을 제공합니다.
"""

class DebugUtils:
    """
    일반적인 디버깅 유틸리티 기능을 제공하는 클래스
    """
    
    def __init__(self):
        """
        DebugUtils 클래스를 초기화합니다.
        """
        self.debug_mode = False
    
    def toggle_debug_mode(self):
        """
        디버깅 모드를 켜고 끕니다.
        
        Returns:
            bool: 변경된 디버깅 모드 상태
        """
        self.debug_mode = not self.debug_mode
        print(f"디버깅 모드: {'켜짐' if self.debug_mode else '꺼짐'}")
        return self.debug_mode
    
    def is_debug_mode(self):
        """
        현재 디버깅 모드 상태를 반환합니다.
        
        Returns:
            bool: 디버깅 모드 활성화 여부
        """
        return self.debug_mode
    
    @staticmethod
    def print_debug_info(title, info):
        """
        디버깅 정보를 포맷팅하여 출력합니다.
        
        Args:
            title (str): 정보 제목
            info (str): 출력할 정보
        """
        print(f"\n===== {title} =====")
        print(info)
        print("=" * (len(title) + 12))
    
    @staticmethod
    def check_library_exists(library_name):
        """
        지정된 라이브러리가 설치되어 있는지 확인합니다.
        
        Args:
            library_name (str): 확인할 라이브러리 이름
            
        Returns:
            bool: 라이브러리 설치 여부
        """
        try:
            __import__(library_name)
            return True
        except ImportError:
            return False 