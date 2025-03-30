"""
MPV 라이브러리 래퍼 모듈
PyInstaller로 패키징할 때 발생하는 DLL 검색 문제 해결
"""
import os
import sys
import platform

def configure_mpv_path():
    """
    MPV DLL 파일 경로를 환경 변수에 설정
    """
    print("Configuring MPV path...")
    
    # PyInstaller로 패키징된 경우
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        print(f"Running in packaged mode, base path: {base_path}")
        
        # 시스템별 라이브러리 파일명
        if platform.system() == 'Windows':
            dll_names = ['libmpv-2.dll', 'mpv-2.dll', 'mpv-1.dll']
            
            # 현재 실행 파일 경로를 PATH에 추가
            os.environ["PATH"] = base_path + os.pathsep + os.environ["PATH"]
            print(f"Updated PATH: {os.environ['PATH']}")
            
            # 모든 가능한 DLL 파일 검색
            for dll in dll_names:
                dll_path = os.path.join(base_path, dll)
                if os.path.exists(dll_path):
                    os.environ["MPV_DYLIB_PATH"] = dll_path
                    print(f"Found MPV DLL: {dll_path}")
                    return True
        
        elif platform.system() == 'Darwin':  # macOS
            lib_path = os.path.join(base_path, "libmpv.dylib")
            if os.path.exists(lib_path):
                os.environ["MPV_DYLIB_PATH"] = lib_path
                return True
        
        else:  # Linux
            lib_path = os.path.join(base_path, "libmpv.so")
            if os.path.exists(lib_path):
                os.environ["MPV_DYLIB_PATH"] = lib_path
                return True
    
    print("MPV library not found in package, using system paths")
    return False

# MPV 모듈을 임포트하기 전에 경로 설정
configure_mpv_path()

# 실제 MPV 모듈 임포트
try:
    import mpv
    print("MPV module imported successfully")
except Exception as e:
    print(f"Error importing MPV: {e}")
    # 객체를 생성할 수 없을 경우 더미 클래스 제공
    class DummyMPV:
        def __init__(self, *args, **kwargs):
            print("WARNING: Using dummy MPV implementation")
            self.dummy = True
        
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    
    mpv.MPV = DummyMPV

# mpv 모듈 재내보내기
__all__ = ['mpv'] 