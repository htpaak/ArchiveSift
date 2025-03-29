# 메모리 캐시 관리 기능
# 최근에 사용한 이미지를 기억해두는 기능이에요. 
# 이미지를 다시 보면 빠르게 불러올 수 있어요.

from collections import OrderedDict  # 순서가 있는 사전 자료형

class LRUCache:
    """
    최근에 사용한 항목을 기억하는 캐시 클래스예요.
    
    LRU는 'Least Recently Used'의 약자로, 가장 오래된 항목부터
    지워서 메모리를 관리해요. 이미지나 다른 큰 파일을 
    임시로 저장해두는 용도로 사용해요.
    
    속성:
        capacity: 저장할 수 있는 항목의 최대 개수
        memory_usage: 현재 사용 중인 메모리 크기 (MB)
        max_memory: 최대 사용 가능한 메모리 크기 (MB)
    """
    def __init__(self, capacity):
        """
        LRUCache 초기화 함수
        
        매개변수:
            capacity: 저장할 수 있는 항목의 최대 개수
        """
        self.cache = OrderedDict()
        self.capacity = capacity
        self.memory_usage = 0  # 메모리 사용량 추적 (MB)
        self.max_memory = 300  # 최대 메모리 사용량 (MB) 500MB→300MB로 조정
        
    def get(self, key):
        """
        키(key)에 해당하는 항목을 캐시에서 가져와요.
        
        이 함수는 키를 이용해 저장된 값을 찾고, 
        그 항목을 '최근에 사용함'으로 표시해요.
        
        매개변수:
            key: 찾으려는 항목의 키
            
        반환값:
            찾은 항목 또는 None (항목이 없을 때)
        """
        if key not in self.cache:
            return None
        # 사용된 항목을 맨 뒤로 이동 (최근 사용)
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key, value, size_mb=0):
        """
        새 항목을 캐시에 추가하거나 기존 항목을 업데이트해요.
        
        메모리 사용량을 추적하고, 용량을 초과하면
        가장 오래된 항목을 제거해요.
        
        매개변수:
            key: 항목의 키
            value: 저장할 값
            size_mb: 항목의 크기 (MB)
        """
        # 이미 있는 항목이면 먼저 메모리 사용량에서 제외
        if key in self.cache:
            old_item = self.cache[key]
            if hasattr(old_item, 'cached_size'):
                self.memory_usage -= old_item.cached_size
            
            # QMovie 객체인 경우 리소스 정리
            self._cleanup_item(old_item)
            
            self.cache.move_to_end(key)
        
        # 메모리 사용량 업데이트
        self.memory_usage += size_mb
        
        # 새 항목에 크기 정보 저장
        if hasattr(value, 'cached_size') == False:
            value.cached_size = size_mb
            
        # 새로운 항목 추가
        self.cache[key] = value
        
        # 메모리 제한 또는 용량 제한 초과 시 오래된 항목 제거
        while (len(self.cache) > self.capacity or 
               self.memory_usage > self.max_memory) and len(self.cache) > 0:
            oldest_key, oldest_item = self.cache.popitem(last=False)
            
            # QMovie 객체인 경우 리소스 정리
            self._cleanup_item(oldest_item)
            
            if hasattr(oldest_item, 'cached_size'):
                self.memory_usage -= oldest_item.cached_size
    
    def _cleanup_item(self, item):
        """
        캐시 항목을 정리합니다. 특히 QMovie 객체의 경우 특별한 정리 작업을 수행합니다.
        
        매개변수:
            item: 정리할 캐시 항목
        """
        try:
            # QMovie 객체 확인
            from PyQt5.QtGui import QMovie
            from PyQt5.QtWidgets import QApplication
            
            if isinstance(item, QMovie):
                # 애니메이션 중지
                item.stop()
                
                # 모든 시그널 연결 해제
                try:
                    item.frameChanged.disconnect()
                    item.stateChanged.disconnect()
                    item.error.disconnect()
                    item.finished.disconnect()
                    item.started.disconnect()
                except:
                    pass  # 연결된 시그널이 없거나 이미 해제된 경우
                
                # 삭제 요청
                item.deleteLater()
                
                # 이벤트 처리를 강제로 수행하여 삭제 요청 처리
                QApplication.processEvents()
        except Exception as e:
            pass    
    
    def __len__(self):
        """
        캐시에 저장된 항목의 개수를 반환해요.
        """
        return len(self.cache)
    
    def clear(self):
        """
        캐시의 모든 항목을 제거하고 메모리 사용량을 0으로 초기화해요.
        특별히 QMovie 객체를 포함하는 항목의 경우 리소스를 확실히 정리합니다.
        """
        # 항목을 제거하기 전에 QMovie 객체가 있는지 확인하고 정리
        try:
            from PyQt5.QtGui import QMovie
            from PyQt5.QtWidgets import QApplication
            
            # 캐시에 있는 모든 항목을 순회하며 QMovie 객체 확인
            for key, item in list(self.cache.items()):
                # QMovie 객체인 경우 리소스 정리
                if isinstance(item, QMovie):
                    try:
                        # 애니메이션 중지
                        item.stop()
                        
                        # 모든 시그널 연결 해제
                        try:
                            item.frameChanged.disconnect()
                            item.stateChanged.disconnect()
                            item.error.disconnect()
                            item.finished.disconnect()
                            item.started.disconnect()
                        except:
                            pass  # 연결된 시그널이 없거나 이미 해제된 경우
                        
                        # 삭제 요청
                        item.deleteLater()
                        
                        # 이벤트 처리를 강제로 수행하여 삭제 요청 처리
                        QApplication.processEvents()
                    except Exception as e:
                        pass
        except Exception as e:
            pass
        
        # 메모리 정리를 위한 가비지 컬렉션 호출
        try:
            import gc
            gc.collect()
            # 이벤트 처리
            QApplication.processEvents()
        except:
            pass
            
        # 모든 항목 제거
        self.cache.clear()
        self.memory_usage = 0