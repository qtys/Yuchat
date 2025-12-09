import os
from kivy.uix.image import Image
from .platform_utils import get_storage_path

def load_background_image(filename="image.png"):
    """从 assets 文件夹加载背景图，返回 Image 组件；若不存在返回 None。"""
    storage_path = get_storage_path()
    image_path = os.path.join(storage_path, "assets", filename)
    
    if os.path.isfile(image_path):
        try:
            bg_image = Image(
                source=image_path,
                size_hint=(1, 1),
                pos_hint={"x": 0, "y": 0},
                allow_stretch=True,
                keep_ratio=False,
            )
            print(f"✓ 背景图已加载: {image_path}")
            return bg_image
        except Exception as e:
            print(f"✗ 背景图加载失败: {e}")
            return None
    else:
        print(f"⚠ 背景图不存在: {image_path}")
        return None