import os
from kivy.core.text import LabelBase

# 字体名称常量
FONT_NAME = "LXGWWenKai"

# 字体文件路径常量
# 使用相对路径，假设从项目根目录运行
FONT_PATH = os.path.join("assets", "LXGWWenKai.ttf")

# 如果文件不存在，尝试使用绝对路径（兼容不同运行方式）
if not os.path.isfile(FONT_PATH):
    # 获取当前文件所在目录的上一级目录（tool文件夹的父目录）
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FONT_PATH = os.path.join(base_dir, "assets", "LXGWWenKai.ttf")

# Android特殊处理：检查多个可能的路径
if not os.path.isfile(FONT_PATH):
    try:
        from kivy import platform
        if platform == 'android':
            # Android上尝试多个可能的路径
            possible_paths = [
                FONT_PATH,  # 原始路径
                os.path.join('/data/data/com.yuchat.yuchat/files', 'assets', 'LXGWWenKai.ttf'),  # 应用私有目录
                os.path.join('/sdcard/Yuchat', 'assets', 'LXGWWenKai.ttf'),  # 外部存储
                os.path.join(os.getcwd(), 'assets', 'LXGWWenKai.ttf'),  # 当前工作目录
            ]
            
            for path in possible_paths:
                if os.path.isfile(path):
                    FONT_PATH = path
                    print(f"[手机] Android找到字体文件: {path}")
                    break
            else:
                print("[警告] Android上未找到字体文件，将使用系统默认字体")
    except Exception as e:
        print(f"[警告] Android路径检测失败: {e}")

def register_fonts():
    """注册项目中 assets 文件夹内的自定义字体（延迟注册以加快启动）。"""
    # 若需快速启动，可先返回，后续首次使用时再注册
    # 或使用后台线程注册
    #from threading import Thread
    
    def _register():
        print(f"[检查] 正在检查字体文件: {FONT_PATH}")
        
        # 检查平台信息
        try:
            from kivy import platform
            print(f"[手机] 当前平台: {platform}")
        except:
            print("[系统] 无法检测平台")
            platform = "unknown"
            
        if os.path.isfile(FONT_PATH):
            print(f"[成功] 字体文件存在，大小: {os.path.getsize(FONT_PATH)} 字节")
            try:
                # 检查字体是否已经注册
                from kivy.core.text import LabelBase
                if FONT_NAME in LabelBase._fonts:
                    print(f"字体 {FONT_NAME} 已经注册，跳过注册")
                    return
                    
                LabelBase.register(name=FONT_NAME, fn_regular=FONT_PATH)
                print(f"[成功] 字体已注册: {FONT_NAME} -> {FONT_PATH}")
                print(f"当前注册的字体: {list(LabelBase._fonts.keys())}")
                
                # 注册Kivy默认字体别名，解决SourceHanSerifCN-Light.ttf找不到的问题
                try:
                    LabelBase.register(name="Roboto", fn_regular=FONT_PATH)
                    LabelBase.register(name="Arial", fn_regular=FONT_PATH)
                    print("[成功] 字体别名注册成功，应该能解决字体找不到的问题啦～")
                except Exception as alias_error:
                    print(f"[警告] 字体别名注册失败（但主字体已注册成功）: {alias_error}")
                
            except Exception as e:
                print(f"[错误] 字体注册失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[警告] 字体文件不存在: {FONT_PATH}")
            # Android上找不到字体是常见问题，给出更友好的提示
            if platform == 'android':
                print("[手机] Android设备上找不到字体文件，将使用系统默认字体")
                print("[建议] 建议: 确保字体文件已正确打包到APK中")
            else:
                # 列出assets目录下的文件
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                assets_dir = os.path.join(base_dir, "assets")
                if os.path.isdir(assets_dir):
                    print(f"assets目录内容: {os.listdir(assets_dir)}")
    
    # 若要后台注册，可改为：
    # thread = Thread(target=_register, daemon=True)
    # thread.start()
    # 但大多数情况直接调用足够快
    try:
        _register()
    except Exception as e:
        print(f"[错误] 字体注册过程出错: {e}")
        print("[建议] 应用将继续使用默认字体运行")