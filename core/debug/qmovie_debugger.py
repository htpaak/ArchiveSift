"""
QMovie 디버거 모듈

QMovie 객체의 상태 모니터링 및 메모리 누수 분석 기능을 제공합니다.
"""

import gc
import types
from PyQt5.QtGui import QMovie
from .debug_utils import DebugUtils
from .memory_profiler import MemoryProfiler

class QMovieDebugger:
    """
    QMovie 객체 디버깅을 위한 클래스
    
    이 클래스는 QMovie 객체의 상태를 모니터링하고 메모리 누수를 추적하는 기능을 제공합니다.
    """
    
    def __init__(self, parent=None):
        """
        QMovieDebugger 클래스를 초기화합니다.
        
        Args:
            parent: ArchiveSift 인스턴스 또는 None
        """
        self.parent = parent
        self.debug_utils = DebugUtils()
        self.memory_profiler = MemoryProfiler()
    
    def toggle_debug_mode(self):
        """
        디버깅 모드를 켜고 끕니다.
        
        Returns:
            bool: 변경된 디버깅 모드 상태
        """
        debug_mode = self.debug_utils.toggle_debug_mode()
        
        # 디버깅 모드가 켜진 경우 현재 QMovie 객체 상태 출력
        if debug_mode:
            self.debug_qmovie_status()
            
        return debug_mode
    
    def is_debug_mode(self):
        """현재 디버깅 모드 상태를 반환합니다."""
        return self.debug_utils.is_debug_mode()
    
    def debug_qmovie_status(self):
        """현재 QMovie 객체 상태를 출력합니다."""
        if not self.debug_utils.check_library_exists('objgraph'):
            print("objgraph 라이브러리가 설치되어 있지 않습니다.")
            print("pip install objgraph 명령으로 설치하세요.")
            return
            
        try:
            import objgraph
            
            self.debug_utils.print_debug_info("QMovie 객체 상태", "")
            
            # QMovie 객체 수 확인
            try:
                movie_count = objgraph.count('QMovie')
                print(f"QMovie 객체 수: {movie_count}")
            except Exception as e:
                print(f"objgraph로 QMovie 객체 수 확인 중 오류: {e}")
            
            # 모든 객체에서 QMovie 인스턴스 찾기
            qmovie_objects = []
            for obj in gc.get_objects():
                if isinstance(obj, QMovie):
                    qmovie_objects.append(obj)
                    
            print(f"gc에서 찾은 QMovie 객체 수: {len(qmovie_objects)}")
            
            # 각 QMovie 객체에 대한 참조 출력
            for i, movie in enumerate(qmovie_objects):
                print(f"\nQMovie 객체 #{i+1}:")
                try:
                    print(f"- 파일명: {movie.fileName() if movie.fileName() else '알 수 없음'}")
                    print(f"- 상태: {'실행 중' if movie.state() == QMovie.Running else '중지됨'}")
                except Exception as e:
                    print(f"QMovie 속성 접근 중 오류: {e}")
                
                # 이 객체를 참조하는 객체들 찾기
                try:
                    referrers = gc.get_referrers(movie)
                    print(f"- 참조하는 객체 수: {len(referrers)}")
                    
                    # 참조하는 객체 유형 분석
                    ref_types = {}
                    for ref in referrers:
                        ref_type = type(ref).__name__
                        if ref_type in ref_types:
                            ref_types[ref_type] += 1
                        else:
                            ref_types[ref_type] = 1
                            
                    print("- 참조 유형:")
                    for ref_type, count in ref_types.items():
                        print(f"  - {ref_type}: {count}개")
                    
                    # 중요 참조 자세히 출력 (모듈, 함수, 클래스 외의 참조)
                    print("- 중요 참조 상세:")
                    for ref in referrers:
                        # 함수, 모듈, 클래스, dict, list 등은 건너뛰기
                        if (isinstance(ref, (types.ModuleType, types.FunctionType, type)) or 
                                type(ref).__name__ in ['dict', 'list', 'tuple', 'set', 'frame']):
                            continue
                            
                        # LRUCache 객체인지 확인
                        if type(ref).__name__ == 'LRUCache' or 'Cache' in type(ref).__name__:
                            print(f"  - 캐시 객체 발견: {type(ref).__name__}")
                            if hasattr(ref, 'cache'):
                                print(f"    - 캐시 항목 수: {len(ref.cache)}")
                                # 캐시 내의 QMovie 객체 찾기
                                for k, v in ref.cache.items():
                                    if v is movie:
                                        print(f"    - 캐시 키: {k}")
                                        
                        elif hasattr(ref, 'image_label') and hasattr(ref, 'current_movie'):
                            print(f"  - AnimationHandler 의심 객체: {type(ref).__name__}")
                            print(f"    - current_movie: {ref.current_movie is movie}")
                            print(f"    - image_label.movie(): {ref.image_label.movie() is movie if hasattr(ref.image_label, 'movie') else 'N/A'}")
                        else:
                            print(f"  - 기타 객체: {type(ref).__name__}")
                            # 객체의 주요 속성 출력
                            for attr_name in dir(ref):
                                if attr_name.startswith('__'):
                                    continue
                                try:
                                    attr = getattr(ref, attr_name)
                                    if attr is movie:
                                        print(f"    - 속성: {attr_name} ({type(ref).__name__}.{attr_name} == QMovie)")
                                except:
                                    pass
                except Exception as e:
                    print(f"참조 분석 중 오류: {e}")
            
            # 메모리 상위 객체 출력
            self.memory_profiler.show_most_common_types(limit=10)
        
        except Exception as e:
            print(f"QMovie 상태 분석 중 오류 발생: {e}")
    
    def debug_qmovie_before_cleanup(self):
        """정리 전 QMovie 상태를 출력합니다."""
        self.debug_utils.print_debug_info("정리 전 QMovie 상태", "")
        self.debug_qmovie_status()
        
    def debug_qmovie_after_cleanup(self):
        """정리 후 QMovie 상태를 출력합니다."""
        # 가비지 컬렉션 강제 실행
        self.memory_profiler.perform_garbage_collection()
        self.debug_utils.print_debug_info("정리 후 QMovie 상태", "")
        self.debug_qmovie_status()
        
    def generate_qmovie_reference_graph(self):
        """QMovie 객체의 참조 그래프를 생성합니다."""
        if not self.debug_utils.check_library_exists('objgraph'):
            print("objgraph 라이브러리가 설치되어 있지 않습니다.")
            print("pip install objgraph 명령으로 설치하세요.")
            return
            
        try:
            import objgraph
            
            # 가비지 컬렉션 강제 실행
            self.memory_profiler.perform_garbage_collection()
            
            # QMovie 객체 찾기
            qmovie_objects = []
            for obj in gc.get_objects():
                if isinstance(obj, QMovie):
                    qmovie_objects.append(obj)
                    
            if not qmovie_objects:
                print("QMovie 객체를 찾을 수 없습니다.")
                return
                
            print(f"{len(qmovie_objects)}개의 QMovie 객체 발견, 참조 그래프 생성 중...")
            
            try:
                # 첫 번째 QMovie 객체에 대한 참조 그래프 생성
                objgraph.show_backrefs(
                    qmovie_objects[0], 
                    max_depth=5, 
                    filename='qmovie_refs.png',
                    filter=lambda x: not isinstance(x, dict)
                )
                print("참조 그래프가 'qmovie_refs.png' 파일로 저장되었습니다.")
            except Exception as e:
                print(f"참조 그래프 생성 중 오류: {e}")
                
        except Exception as e:
            print(f"QMovie 참조 그래프 생성 중 오류 발생: {e}") 