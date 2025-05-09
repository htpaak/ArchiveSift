# 경로를 찾는 기능
# 프로그램 폴더와 사용자 데이터 폴더의 위치를 알려주는 함수들이 있어요.
import os  # 파일과 폴더를 다루는 도구
import sys  # 컴퓨터 시스템과 관련된 도구

def get_app_directory():
    """
    프로그램이 설치된 폴더를 찾아주는 함수예요.
    
    이 함수는 우리 프로그램이 어느 폴더에 있는지 알려줘요.
    프로그램이 설치 파일로 만들어졌을 때와 그냥 파이썬 코드로 
    실행할 때 다르게 동작해요.
    
    반환값:
        프로그램이 설치된 폴더의 경로
    """
    if getattr(sys, 'frozen', False):
        # 프로그램이 설치 파일로 만들어졌을 때
        return os.path.dirname(sys.executable)
    else:
        # 그냥 파이썬 코드로 실행할 때
        # core 폴더 안에 있으니까 바깥쪽 폴더를 찾아요
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_user_data_directory():
    """
    사용자의 정보를 저장할 폴더를 만들고 알려주는 함수예요.
    
    이 함수는 프로그램에서 사용자 정보(북마크, 설정 등)를 
    %LOCALAPPDATA%/MediaSorterPAAK/UserData 폴더(Windows) 또는
    ~/MediaSorterPAAK/UserData 폴더(macOS, Linux)에 저장합니다.
    만약 그 폴더가 없다면 새로 만들어줘요.
    
    반환값:
        사용자 데이터를 저장하는 폴더의 경로
    """
    # 운영체제별 적절한 앱 데이터 경로 사용
    if os.name == 'nt':  # Windows
        # %LOCALAPPDATA%/MediaSorterPAAK 경로 사용 (권한 문제 방지)
        local_app_data = os.environ.get('LOCALAPPDATA')
        if not local_app_data:  # 환경 변수가 없는 경우 대체 경로
            local_app_data = os.path.join(os.path.expanduser('~'), 'AppData', 'Local')
        data_dir = os.path.join(local_app_data, 'MediaSorterPAAK', 'UserData')
    else:  # macOS, Linux 등
        # 홈 디렉토리의 MediaSorterPAAK 폴더 사용
        home = os.path.expanduser("~")
        data_dir = os.path.join(home, 'MediaSorterPAAK', 'UserData')
    
    # 만약 그 폴더가 아직 없다면 새로 만들어요
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        
    return data_dir  # 폴더 경로를 알려줌