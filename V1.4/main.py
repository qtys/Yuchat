#!/usr/bin/env python3
"""
YuChat Android Application Entry Point
Simple and clean main entry point
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Simple crash logging
def simple_crash_logger(exc_type, exc_value, exc_traceback):
    """Simple crash logger - just print to console"""
    print(f"应用崩溃: {exc_type.__name__}: {exc_value}")
    import traceback
    traceback.print_exception(exc_type, exc_value, exc_traceback)

# Set exception handler
sys.excepthook = simple_crash_logger

# Import and run the main app
try:
    from run import Example
    Example().run()
except ImportError as e:
    print(f"导入失败: {e}")
    print("请检查run.py文件是否存在")
except Exception as e:
    print(f"应用启动失败: {e}")
    import traceback
    traceback.print_exc()