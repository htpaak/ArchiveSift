"""
파일 내비게이터 모듈

이 모듈은 파일 목록을 탐색하고 이전/다음 이미지로 이동하는 기능을 제공합니다.
"""

import os


class FileNavigator:
    """
    파일 내비게이터 클래스
    
    이 클래스는 파일 목록을 관리하고 다음/이전 파일로 이동하는 기능을 제공합니다.
    """
    
    def __init__(self, parent=None):
        """
        FileNavigator 클래스 초기화
        
        매개변수:
            parent: 부모 객체 (일반적으로 메인 어플리케이션 창)
        """
        self.parent = parent
        self.files = []  # 현재 파일 목록
        self.current_index = -1  # 현재 인덱스 (-1은 유효한 파일이 없음을 의미)
        self.loop_navigation = False  # 순환 탐색 옵션 기본값 (마지막 파일에서 처음으로 돌아가기)
        
    def set_files(self, files, start_index=0):
        """
        파일 목록을 설정하고 현재 인덱스를 지정합니다.
        
        매개변수:
            files (list): 파일 경로 목록
            start_index (int): 시작 인덱스 (기본값: 0)
            
        반환값:
            bool: 성공 여부
        """
        if not files:
            self.files = []
            self.current_index = -1
            return False
            
        self.files = files
        
        # 유효한 인덱스 범위 확인
        if 0 <= start_index < len(files):
            self.current_index = start_index
        else:
            self.current_index = 0
            
        return True
    
    def set_current_index(self, index):
        """
        현재 파일 인덱스를 직접 설정합니다.
        
        매개변수:
            index (int): 설정할 인덱스
            
        반환값:
            bool: 성공 여부
        """
        if not self.files:
            return False
            
        # 유효한 인덱스 범위 확인
        if 0 <= index < len(self.files):
            self.current_index = index
            return True
        else:
            return False
    
    def get_current_file(self):
        """
        현재 선택된 파일 경로를 반환합니다.
        
        반환값:
            str: 현재 파일 경로 또는 None
        """
        if not self.files or self.current_index < 0 or self.current_index >= len(self.files):
            return None
            
        return self.files[self.current_index]
    
    def get_current_index(self):
        """
        현재 파일 인덱스를 반환합니다.
        
        반환값:
            int: 현재 인덱스
        """
        return self.current_index
    
    def get_file_count(self):
        """
        전체 파일 개수를 반환합니다.
        
        반환값:
            int: 파일 개수
        """
        return len(self.files)
    
    def get_files(self):
        """
        현재 파일 목록을 반환합니다.
        
        반환값:
            list: 파일 경로 목록
        """
        return self.files.copy()  # 복사본 반환하여 외부에서 변경되지 않도록 함
    
    def next_file(self, show_message=True):
        """
        Move to the next file.
        이동할 다음 파일.
        
        Parameters:
            show_message (bool): Whether to display a message when the boundary is reached.
            show_message (bool): 경계에 도달했을 때 메시지 표시 여부.
            
        Returns:
            tuple: (success status, file path)
            tuple: (성공 여부, 파일 경로)
        """
        if not self.files:
            return False, None
            
        # If last file
        # 마지막 파일인 경우
        if self.current_index >= len(self.files) - 1:
            if show_message and self.parent and hasattr(self.parent, 'show_message'):
                self.parent.show_message("This is the last image.")
            return False, None
            
        # Move to the next file
        # 다음 파일로 이동
        self.current_index += 1
        return True, self.files[self.current_index]
    
    def previous_file(self, show_message=True):
        """
        Move to the previous file.
        이전 파일로 이동.
        
        Parameters:
            show_message (bool): Whether to display a message when the boundary is reached.
            show_message (bool): 경계에 도달했을 때 메시지 표시 여부.
            
        Returns:
            tuple: (success status, file path)
            tuple: (성공 여부, 파일 경로)
        """
        if not self.files:
            return False, None
            
        # If first file
        # 첫 번째 파일인 경우
        if self.current_index <= 0:
            if show_message and self.parent and hasattr(self.parent, 'show_message'):
                self.parent.show_message("This is the first image.")
            return False, None
            
        # Move to the previous file
        # 이전 파일로 이동
        self.current_index -= 1
        return True, self.files[self.current_index]
        
    def delete_current_file(self):
        """
        현재 파일을 목록에서 삭제합니다.
        실제 파일은 삭제하지 않고 목록에서만 제거합니다.
        
        반환값:
            tuple: (성공 여부, 다음 파일 경로)
        """
        if not self.files or self.current_index < 0 or self.current_index >= len(self.files):
            return False, None
            
        # 현재 파일 경로 저장
        deleted_path = self.files[self.current_index]
        
        # 파일 목록에서 현재 파일 제거
        self.files.pop(self.current_index)
        
        # 파일 목록이 비어있게 되면
        if not self.files:
            self.current_index = -1
            return True, None
            
        # 현재 인덱스가 파일 목록 끝을 초과하면 마지막 파일로 조정
        if self.current_index >= len(self.files):
            self.current_index = len(self.files) - 1
            
        # 다음에 표시할 파일 경로 반환
        return True, self.files[self.current_index]
        
    def add_file(self, file_path):
        """
        파일 목록에 파일을 추가합니다.
        
        이 메서드는 지정된 파일을 파일 목록에 추가하고, 원래 위치에 가장 가까운 인덱스를 찾아 파일을 배치합니다.
        파일이 이미 목록에 있으면 아무 작업도 수행하지 않습니다.
        
        Args:
            file_path (str): 추가할 파일 경로
            
        Returns:
            bool: 파일 추가 성공 여부
        """
        # 파일이 이미 목록에 있으면 건너뛰기
        if file_path in self.files:
            return True
            
        # 파일이 실제로 존재하는지 확인
        if not os.path.exists(file_path):
            return False
            
        # 먼저 파일 디렉토리 확인
        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        
        # 현재 목록의 파일 디렉토리와 비교
        if self.files and os.path.dirname(self.files[0]) != file_dir:
            # 디렉토리가 다르면 적절한 위치 결정 어려움 - 맨 끝에 추가
            self.files.append(file_path)
            # 현재 인덱스를 추가된 파일로 설정
            self.current_index = len(self.files) - 1
            return True
            
        # 알파벳 순서로 삽입할 위치 찾기
        insert_index = 0
        for i, path in enumerate(self.files):
            if os.path.basename(path) > file_name:
                insert_index = i
                break
            # 이미 모든 파일이 현재 파일보다 알파벳 순서가 앞서면 맨 끝에 추가
            insert_index = i + 1
            
        # 파일 삽입
        self.files.insert(insert_index, file_path)
        
        # 현재 인덱스를 추가된 파일로 설정
        self.current_index = insert_index
        
        return True
    
    def go_to_index(self, index, show_message=True):
        """
        Move to a specific index.
        
        Parameters:
            index (int): Index to move to
            show_message (bool): Whether to display a message when boundaries are reached
            
        Returns:
            tuple: (success status, file path)
        """
        if not self.files:
            return False, None
            
        # Check index range
        if index < 0:
            if show_message and self.parent and hasattr(self.parent, 'show_message'):
                self.parent.show_message("This is the first image.")
            index = 0
        elif index >= len(self.files):
            if show_message and self.parent and hasattr(self.parent, 'show_message'):
                self.parent.show_message("This is the last image.")
            index = len(self.files) - 1
            
        # If index is unchanged, return current file
        if index == self.current_index:
            return False, self.files[self.current_index]
            
        # Update index
        self.current_index = index
        return True, self.files[self.current_index]
        
    def find_file_index(self, file_path):
        """
        특정 파일의 인덱스를 찾습니다.
        
        매개변수:
            file_path (str): 찾을 파일 경로
            
        반환값:
            int: 파일 인덱스 또는 -1 (파일이 없는 경우)
        """
        try:
            return self.files.index(file_path)
        except ValueError:
            return -1
            
    def go_to_file(self, file_path, show_message=True):
        """
        Navigate to a specific file.  
        특정 파일로 이동합니다.  
        
        Parameters:  
        매개변수:  
            file_path (str): file path to navigate to  
            file_path (str): 이동할 파일 경로  
            show_message (bool): whether to display a message when the boundary is reached  
            show_message (bool): 경계에 도달했을 때 메시지 표시 여부
            
        Returns:  
        반환값:  
            tuple: (success status, file path)  
            tuple: (성공 여부, 파일 경로)
        """
        index = self.find_file_index(file_path)
        if index == -1:
            if show_message and self.parent and hasattr(self.parent, 'show_message'):
                self.parent.show_message("File not found.")
            return False, None
            
        return self.go_to_index(index, show_message)
    
    def peek_next_file(self):
        """다음 파일 정보를 조회합니다 (실제로 이동하지 않음).
        
        반환값:
            (성공 여부, 다음 파일 경로)
        """
        if not self.files:  # 파일 목록이 비어 있는 경우
            return False, None
            
        if self.current_index >= len(self.files) - 1:  # 이미 마지막 파일인 경우
            # 순환 옵션이 켜져 있으면 첫 번째 파일 반환
            if self.loop_navigation:
                return True, self.files[0]
            # 그렇지 않으면 실패
            return False, None
            
        # 다음 파일 경로 반환
        return True, self.files[self.current_index + 1]
    
    def peek_previous_file(self):
        """이전 파일 정보를 조회합니다 (실제로 이동하지 않음).
        
        반환값:
            (성공 여부, 이전 파일 경로)
        """
        if not self.files:  # 파일 목록이 비어 있는 경우
            return False, None
            
        if self.current_index <= 0:  # 이미 첫 번째 파일인 경우
            # 순환 옵션이 켜져 있으면 마지막 파일 반환
            if self.loop_navigation:
                return True, self.files[-1]
            # 그렇지 않으면 실패
            return False, None
            
        # 이전 파일 경로 반환
        return True, self.files[self.current_index - 1] 