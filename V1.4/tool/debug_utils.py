"""
调试工具模块：提供运行时信息收集和调试功能
"""
import os
import sys
import time
import gc
import psutil
from datetime import datetime
from kivy import platform

class DebugInfoCollector:
    """调试信息收集器"""
    
    def __init__(self, log_dir=None):
        """初始化调试信息收集器"""
        if log_dir is None:
            if platform == 'android':
                self.log_dir = "/sdcard/YuChat/debug_logs"
            else:
                self.log_dir = "debug_logs"
        else:
            self.log_dir = log_dir
        
        os.makedirs(self.log_dir, exist_ok=True)
        self.start_time = time.time()
        self.log_file = None
        self.start_logging()
    
    def start_logging(self):
        """开始记录调试信息"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"debug_{timestamp}.log")
        
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(f"=== YuChat Debug Information ===\n")
            f.write(f"开始时间: {datetime.now().isoformat()}\n")
            f.write(f"Python版本: {sys.version}\n")
            f.write(f"平台: {platform}\n")
            f.write(f"工作目录: {os.getcwd()}\n")
            f.write(f"进程ID: {os.getpid()}\n")
    
    def collect_system_info(self):
        """收集系统信息"""
        return {
            'platform': sys.platform,
            'python_version': sys.version,
            'executable': sys.executable,
            'cwd': os.getcwd(),
            'timestamp': datetime.now().isoformat()
        }

    def collect_memory_info(self):
        """收集内存使用信息"""
        try:
            import psutil
            process = psutil.Process()
            return {
                'rss': process.memory_info().rss,
                'vms': process.memory_info().vms,
                'percent': process.memory_percent(),
                'available': psutil.virtual_memory().available
            }
        except ImportError:
            return {'error': 'psutil not available'}

    def collect_thread_info(self):
        """收集线程信息"""
        import threading
        return {
            'active_threads': threading.active_count(),
            'current_thread': threading.current_thread().name,
            'threads': [t.name for t in threading.enumerate()]
        }

    def log_system_info(self):
        """记录系统信息到日志"""
        sys_info = self.collect_system_info()
        self.log_custom_info("系统信息", str(sys_info))
        return sys_info

    def log_memory_info(self, label="内存信息"):
        """记录内存使用信息"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n=== {label} ===\n")
                f.write(f"时间: {datetime.now().isoformat()}\n")
                f.write(f"运行时长: {time.time() - self.start_time:.2f}秒\n")
                f.write(f"物理内存: {memory_info.rss / 1024 / 1024:.2f} MB\n")
                f.write(f"虚拟内存: {memory_info.vms / 1024 / 1024:.2f} MB\n")
                f.write(f"内存百分比: {process.memory_percent():.2f}%\n")
                
                # Python内存信息
                f.write(f"Python对象数量: {len(gc.get_objects())}\n")
                f.write(f"垃圾回收计数: {gc.get_count()}\n")
                
        except Exception as e:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n=== {label} (错误) ===\n")
                f.write(f"获取内存信息失败: {e}\n")
    
    def log_thread_info(self, label="线程信息"):
        """记录线程信息"""
        try:
            import threading
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n=== {label} ===\n")
                f.write(f"时间: {datetime.now().isoformat()}\n")
                f.write(f"活动线程数: {threading.active_count()}\n")
                f.write(f"当前线程: {threading.current_thread().name}\n")
                
                for thread in threading.enumerate():
                    f.write(f"  - {thread.name}: {'活动' if thread.is_alive() else '非活动'}\n")
                    
        except Exception as e:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n=== {label} (错误) ===\n")
                f.write(f"获取线程信息失败: {e}\n")

    def log_thread_info(self):
        """记录线程信息到日志"""
        thread_info = self.collect_thread_info()
        self.log_custom_info("线程信息", str(thread_info))
        return thread_info
    
    def log_exception(self, exception, label="异常信息"):
        """记录异常信息"""
        import traceback
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"\n=== {label} ===\n")
            f.write(f"时间: {datetime.now().isoformat()}\n")
            f.write(f"异常类型: {type(exception).__name__}\n")
            f.write(f"异常消息: {str(exception)}\n")
            f.write("详细堆栈:\n")
            traceback.print_exception(type(exception), exception, exception.__traceback__, file=f)
    
    def log_custom_info(self, title, content):
        """记录自定义信息"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"\n=== {title} ===\n")
            f.write(f"时间: {datetime.now().isoformat()}\n")
            f.write(f"运行时长: {time.time() - self.start_time:.2f}秒\n")
            f.write(f"{content}\n")
    
    def get_log_file_path(self):
        """获取日志文件路径"""
        return self.log_file

# 全局调试收集器实例
debug_collector = None

def init_debug_collector(log_dir=None):
    """初始化全局调试收集器"""
    global debug_collector
    debug_collector = DebugInfoCollector(log_dir)
    return debug_collector

def get_debug_collector():
    """获取调试收集器实例"""
    global debug_collector
    if debug_collector is None:
        debug_collector = DebugInfoCollector()
    return debug_collector

def log_startup_debug_info():
    """记录启动时的调试信息"""
    collector = get_debug_collector()
    
    # 基础系统信息
    collector.log_custom_info("启动调试信息", f"""
Python路径: {sys.executable}
系统路径: {sys.path}
环境变量: {dict(os.environ)}
命令行参数: {sys.argv}
""")
    
    # 模块信息
    modules_info = f"已加载模块数: {len(sys.modules)}\n"
    builtin_modules = [name for name in sys.modules.keys() if not hasattr(sys.modules[name], '__file__')]
    modules_info += f"内置模块数: {len(builtin_modules)}\n"
    modules_info += f"外部模块数: {len(sys.modules) - len(builtin_modules)}\n"
    
    collector.log_custom_info("模块信息", modules_info)
    
    # 内存信息
    collector.log_memory_info("启动时内存使用")
    
    # 线程信息
    collector.log_thread_info("启动时线程状态")

# 便捷函数
def log_memory(label="内存信息"):
    """记录内存信息"""
    return get_debug_collector().log_memory_info(label)

def log_threads(label="线程信息"):
    """记录线程信息"""
    return get_debug_collector().log_thread_info(label)

def log_exception_debug(exception, label="异常信息"):
    """记录异常信息"""
    return get_debug_collector().log_exception(exception, label)

def log_custom(title, content):
    """记录自定义信息"""
    return get_debug_collector().log_custom_info(title, content)