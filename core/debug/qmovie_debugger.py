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
            parent: MediaSorterPAAK 인스턴스 또는 None
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
        """Print the current QMovie object status."""
        if not self.debug_utils.check_library_exists('objgraph'):
            print("The objgraph library is not installed.")
            print("Install it using 'pip install objgraph'.")
            return
            
        try:
            import objgraph
            
            self.debug_utils.print_debug_info("QMovie Object Status", "")
            
            # Check the number of QMovie objects
            try:
                movie_count = objgraph.count('QMovie')
                print(f"Number of QMovie objects: {movie_count}")
            except Exception as e:
                print(f"Error while counting QMovie objects with objgraph: {e}")
            
            # Find QMovie instances from all objects
            qmovie_objects = []
            for obj in gc.get_objects():
                if isinstance(obj, QMovie):
                    qmovie_objects.append(obj)
                    
            print(f"Number of QMovie objects found in gc: {len(qmovie_objects)}")
            
            # Print references for each QMovie object
            for i, movie in enumerate(qmovie_objects):
                print(f"\nQMovie object #{i+1}:")
                try:
                    print(f"- File name: {movie.fileName() if movie.fileName() else 'Unknown'}")
                    print(f"- Status: {'Running' if movie.state() == QMovie.Running else 'Stopped'}")
                except Exception as e:
                    print(f"Error accessing QMovie property: {e}")
                
                # Find objects that reference this object
                try:
                    referrers = gc.get_referrers(movie)
                    print(f"- Number of referencing objects: {len(referrers)}")
                    
                    # Analyze types of referencing objects
                    ref_types = {}
                    for ref in referrers:
                        ref_type = type(ref).__name__
                        if ref_type in ref_types:
                            ref_types[ref_type] += 1
                        else:
                            ref_types[ref_type] = 1
                            
                    print("- Reference types:")
                    for ref_type, count in ref_types.items():
                        print(f"  - {ref_type}: {count} items")
                    
                    # Print detailed important references (excluding module, function, class references)
                    print("- Detailed important references:")
                    for ref in referrers:
                        # Skip functions, modules, classes, dict, list, etc.
                        if (isinstance(ref, (types.ModuleType, types.FunctionType, type)) or 
                                type(ref).__name__ in ['dict', 'list', 'tuple', 'set', 'frame']):
                            continue
                            
                        # Check if it's an LRUCache object
                        if type(ref).__name__ == 'LRUCache' or 'Cache' in type(ref).__name__:
                            print(f"  - Cache object found: {type(ref).__name__}")
                            if hasattr(ref, 'cache'):
                                print(f"    - Cache item count: {len(ref.cache)}")
                                # Find QMovie object in cache
                                for k, v in ref.cache.items():
                                    if v is movie:
                                        print(f"    - Cache key: {k}")
                                        
                        elif hasattr(ref, 'image_label') and hasattr(ref, 'current_movie'):
                            print(f"  - Suspected AnimationHandler object: {type(ref).__name__}")
                            print(f"    - current_movie: {ref.current_movie is movie}")
                            print(f"    - image_label.movie(): {ref.image_label.movie() is movie if hasattr(ref.image_label, 'movie') else 'N/A'}")
                        else:
                            print(f"  - Other object: {type(ref).__name__}")
                            # Print main attributes of the object
                            for attr_name in dir(ref):
                                if attr_name.startswith('__'):
                                    continue
                                try:
                                    attr = getattr(ref, attr_name)
                                    if attr is movie:
                                        print(f"    - Attribute: {attr_name} ({type(ref).__name__}.{attr_name} == QMovie)")
                                except:
                                    pass
                except Exception as e:
                    print(f"Error during reference analysis: {e}")
            
            # Print most common objects in memory
            self.memory_profiler.show_most_common_types(limit=10)
        
        except Exception as e:
            print(f"Error occurred during QMovie status analysis: {e}")
    
    def debug_qmovie_before_cleanup(self):
        """Print QMovie status before cleanup."""
        self.debug_utils.print_debug_info("QMovie Status Before Cleanup", "")
        self.debug_qmovie_status()
        
    def debug_qmovie_after_cleanup(self):
        """Print QMovie status after cleanup."""
        # Force garbage collection
        self.memory_profiler.perform_garbage_collection()
        self.debug_utils.print_debug_info("QMovie Status After Cleanup", "")
        self.debug_qmovie_status()
        
    def generate_qmovie_reference_graph(self):
        """Generate the reference graph for QMovie objects."""
        if not self.debug_utils.check_library_exists('objgraph'):
            print("The objgraph library is not installed.")
            print("Install it using 'pip install objgraph'.")
            return
            
        try:
            import objgraph
            
            # Force garbage collection
            self.memory_profiler.perform_garbage_collection()
            
            # Find QMovie objects
            qmovie_objects = []
            for obj in gc.get_objects():
                if isinstance(obj, QMovie):
                    qmovie_objects.append(obj)
                    
            if not qmovie_objects:
                print("No QMovie objects found.")
                return
                
            print(f"Found {len(qmovie_objects)} QMovie objects, generating reference graph...")
            
            try:
                # Generate reference graph for the first QMovie object
                objgraph.show_backrefs(
                    qmovie_objects[0], 
                    max_depth=5, 
                    filename='qmovie_refs.png',
                    filter=lambda x: not isinstance(x, dict)
                )
                print("Reference graph has been saved to 'qmovie_refs.png'.")
            except Exception as e:
                print(f"Error during reference graph generation: {e}")
                
        except Exception as e:
            print(f"Error occurred during QMovie reference graph generation: {e}") 