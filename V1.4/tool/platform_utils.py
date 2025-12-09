"""
跨平台工具箱：判断平台、申请权限、获取安全路径
"""
import os
import sys
from kivy import platform

def is_android():
    return platform == "android"

def get_storage_path():
    """返回安卓外部存储根目录，桌面返回项目根目录"""
    if is_android():
        # 安卓10+使用应用私有目录，避免存储权限问题
        try:
            from android.storage import app_storage_path
            # 使用应用私有存储路径
            app_path = app_storage_path()
            result = os.path.join(app_path, "Yuchat")
            print(f"[手机] Android私有存储路径: {result}")
            return result
        except ImportError as e:
            print(f"[警告] 无法获取Android私有路径，降级使用外部存储: {e}")
            # 降级使用外部存储
            return "/sdcard/Yuchat"
    # 返回项目根目录（tool目录的父目录）
    result = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"[系统] 桌面存储路径: {result}")
    return result

def ensure_dir(path: str):
    """确保目录存在，安卓下自动申请权限"""
    if is_android():
        # 安卓10+不需要手动申请权限访问私有目录
        if not path.startswith("/sdcard"):
            os.makedirs(path, exist_ok=True)
            return
        # 外部存储需要权限
        if not os.path.exists(path):
            request_android_storage_permission()
    os.makedirs(path, exist_ok=True)

def request_android_storage_permission():
    """安卓动态申请存储权限 - 适配Android 11+"""
    if not is_android():
        print("[手机] 非Android平台，跳过权限申请")
        return
    
    import time
    start_time = time.time()
    
    try:
        print("[权限] 开始申请Android存储权限...")
        print(f"[位置] 当前函数: request_android_storage_permission()")
        print(f"⏰ 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 检查权限模块是否存在
        try:
            from android.permissions import Permission, request_permissions, check_permission
            print("[成功] android.permissions 模块导入成功")
        except ImportError as e:
            elapsed = time.time() - start_time
            print(f"[错误] android.permissions 模块导入失败 (耗时: {elapsed:.2f}秒): {e}")
            print("[建议] 可能的原因:")
            print("  - buildozer.spec中未添加android-permissions依赖")
            print("  - 模块未正确安装")
            print("  - Python路径问题")
            return
        
        # 获取Android API级别
        try:
            from android import api_version
            api_level = api_version
            print(f"[信息] Android API级别: {api_level}")
        except:
            api_level = 21  # 默认最低支持版本
            print(f"[警告] 无法获取API级别，使用默认值: {api_level}")
        
        # Android 11+ (API 30+) 使用新的权限模型
        if api_level >= 30:
            print("[信息] Android 11+ 检测，使用Scoped Storage模式")
            # Android 11+ 主要使用私有目录，不需要传统存储权限
            # 只需要申请基本权限
            permissions = [Permission.READ_EXTERNAL_STORAGE]
            print("[日志] Android 11+ 权限列表: 仅申请读取权限")
        else:
            # Android 10及以下需要完整的存储权限
            permissions = [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
            print(f"[日志] Android 10及以下权限列表: 读取和写入权限")
        
        # 检查是否已有权限
        has_permissions = True
        for permission in permissions:
            try:
                if not check_permission(permission):
                    has_permissions = False
                    print(f"[需要] 缺少权限: {permission}")
                else:
                    print(f"[已有] 已拥有权限: {permission}")
            except Exception as e:
                print(f"[警告] 检查权限失败: {e}")
                has_permissions = False
        
        if has_permissions:
            print("[成功] 已有所需权限，跳过申请")
            return
        
        # 申请权限
        print("[刷新] 正在调用request_permissions...")
        
        # 使用异步方式申请权限，避免阻塞UI线程
        def permission_callback(permissions, results):
            elapsed = time.time() - start_time
            if all(results):
                print(f"[成功] 权限申请成功 (耗时: {elapsed:.2f}秒)")
            else:
                failed_perms = [p for p, r in zip(permissions, results) if not r]
                print(f"[警告] 部分权限申请失败: {failed_perms}")
        
        request_permissions(permissions, permission_callback)
        
        # 给权限申请一些时间
        time.sleep(0.5)
        
    except ImportError as e:
        elapsed = time.time() - start_time
        print(f"[错误] 权限申请ImportError (耗时: {elapsed:.2f}秒): {e}")
        print(f"[记录] 详细错误信息: {type(e).__name__}: {e}")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[错误] 权限申请失败 (耗时: {elapsed:.2f}秒): {e}")
        print(f"[记录] 异常类型: {type(e).__name__}")
        print(f"[记录] 异常详情: {e}")
        
        # 尝试获取更详细的异常信息
        import traceback
        print("[图表] 异常堆栈:")
        traceback.print_exc()

def fix_window_size_for_desktop():
    """仅桌面设置窗口大小，避免安卓强制分辨率"""
    if is_android():
        return
    from kivy.core.window import Window
    from kivy.metrics import dp
    Window.size = (dp(300), dp(533))
    Window.minimum_height = dp(480)