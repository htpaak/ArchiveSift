"""
메모리 프로파일러 모듈

메모리 사용량 분석 및 가비지 컬렉션 관련 기능을 제공합니다.
"""

import gc
from .debug_utils import DebugUtils

class MemoryProfiler:
    """
    메모리 사용량 모니터링 및 프로파일링 기능을 제공하는 클래스
    """
    
    def __init__(self):
        """
        MemoryProfiler 클래스를 초기화합니다.
        """
        self.debug_utils = DebugUtils()
        
    def perform_garbage_collection(self):
        """
        Explicitly execute garbage collection.
        명시적으로 가비지 컬렉션을 실행합니다.
        
        Returns:
            int: Number of objects collected
            int: 수집된 객체 수
        """
        try:
            count = gc.collect()
            return count
        except Exception as e:
            return -1
    
    def show_most_common_types(self, limit=10):
        """
        Display the most frequently used object types in memory.
        메모리에서 가장 많이 사용되는 객체 유형을 표시합니다.
        
        Args:
            limit (int): Number of object types to display
            limit (int): 표시할 객체 유형 수
            
        Returns:
            bool: Success flag
            bool: 성공 여부
        """
        if self.debug_utils.check_library_exists('objgraph'):
            try:
                import objgraph
                objgraph.show_most_common_types(limit=limit)
                return True
            except Exception as e:
                pass
        else:
            pass
        return False
    
    def count_by_type(self, type_name):
        """
        Calculate the count of objects for a specific type.
        특정 유형의 객체 수를 계산합니다.
        
        Args:
            type_name (str): Name of the object type to count
            type_name (str): 계산할 객체 유형 이름
            
        Returns:
            int: Object count, or -1 on error
            int: 계산된 객체 수 또는 -1 (오류)
        """
        if self.debug_utils.check_library_exists('objgraph'):
            try:
                import objgraph
                count = objgraph.count(type_name)
                return count
            except Exception as e:
                pass
        else:
            pass
        return -1
    
    def find_object_referrers(self, obj, max_depth=1):
        """
        특정 객체를 참조하는 객체들을 찾습니다.
        
        Args:
            obj: 검사할 객체
            max_depth (int): 최대 참조 깊이
            
        Returns:
            list: 참조하는 객체 목록
        """
        referrers = gc.get_referrers(obj)
        
        if max_depth <= 1:
            return referrers
            
        all_referrers = []
        all_referrers.extend(referrers)
        
        for ref in referrers:
            # 표준 타입 (dict, list 등)은 건너뜁니다
            if isinstance(ref, (dict, list, tuple, set, type, gc.frame)):
                continue
                
            # 재귀적으로 참조 탐색
            refs = self.find_object_referrers(ref, max_depth - 1)
            all_referrers.extend(refs)
            
        return all_referrers 