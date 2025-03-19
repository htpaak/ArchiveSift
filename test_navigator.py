"""
FileNavigator 클래스 테스트 스크립트
"""

from file.navigator import FileNavigator

def test_navigator():
    # 테스트용 가상 부모 클래스
    class MockParent:
        def __init__(self):
            self.last_message = ""
            
        def show_message(self, message):
            self.last_message = message
            print(f"메시지: {message}")
    
    # 테스트용 부모 객체 생성
    parent = MockParent()
    
    # FileNavigator 인스턴스 생성
    nav = FileNavigator(parent)
    
    # 초기 상태 테스트
    print("\n==== 초기 상태 테스트 ====")
    print(f"파일 개수: {nav.get_file_count()}")
    print(f"현재 인덱스: {nav.get_current_index()}")
    print(f"현재 파일: {nav.get_current_file()}")
    
    # 테스트용 파일 목록
    test_files = [
        "test1.jpg",
        "test2.png",
        "test3.gif",
        "test4.webp",
        "test5.mp4"
    ]
    
    # 파일 목록 설정
    print("\n==== 파일 목록 설정 테스트 ====")
    result = nav.set_files(test_files)
    print(f"set_files 결과: {result}")
    print(f"파일 개수: {nav.get_file_count()}")
    print(f"현재 인덱스: {nav.get_current_index()}")
    print(f"현재 파일: {nav.get_current_file()}")
    
    # 다음 파일 테스트
    print("\n==== 다음 파일 테스트 ====")
    for _ in range(6):  # 파일 개수(5)보다 많이 반복해서 경계 조건 테스트
        success, file_path = nav.next_file()
        print(f"next_file 결과: {success}, 파일: {file_path}")
        print(f"현재 인덱스: {nav.get_current_index()}")
    
    # 이전 파일 테스트
    print("\n==== 이전 파일 테스트 ====")
    for _ in range(6):  # 파일 개수(5)보다 많이 반복해서 경계 조건 테스트
        success, file_path = nav.previous_file()
        print(f"previous_file 결과: {success}, 파일: {file_path}")
        print(f"현재 인덱스: {nav.get_current_index()}")

if __name__ == "__main__":
    test_navigator() 