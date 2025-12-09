# 添加启动日志
import os
print("[火箭] YuChat应用启动中...")
print(f"[手机] 平台: {__import__('kivy.utils').platform}")
print(f"📂 工作目录: {os.getcwd()}")

# 字体注册 - 添加错误处理
try:
    from tool import fonts
    fonts.register_fonts()
    print("[成功] 字体注册完成")
except Exception as e:
    print(f"[警告] 字体注册失败: {e}")
    print("[建议] 应用将继续使用默认字体")

from kivy.metrics import dp, sp
from kivy.core.clipboard import Clipboard

from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
#from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText  # 底部短提示
from kivymd.app import MDApp  # 应用基类
from kivymd.uix.screen import MDScreen  # 屏幕组件
from kivymd.uix.label import MDLabel  # 文本控件
from kivymd.uix.menu import MDDropdownMenu  # 下拉菜单/上下文菜单
from kivymd.uix.textfield import MDTextField  # 输入框
from kivymd.uix.scrollview import MDScrollView  # 滚动视图
from kivymd.uix.button import MDIconButton, MDButton, MDButtonText, MDButtonIcon  # 图标按钮和按钮组件
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogContentContainer,
    MDDialogHeadlineText,
    MDDialogSupportingText,
)  # 对话框
from kivymd.uix.card import MDCard  # 卡片组件
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.list import MDListItem, MDListItemLeadingIcon, MDListItemHeadlineText
#from kivymd.uix.widget import MDWidget  # 占位通用控件
from threading import Thread
import threading
import queue
import weakref

# 导入 tool 模块
from tool.async_api_client import get_async_api_client, stop_async_api_client
from tool.image_loader import load_background_image
from tool.data_loader import load_data_from_folder
from tool.ui_helpers import toast, CopyLabel
from tool.character_manager import CharacterManager  # 导入角色管理器
from tool.platform_utils import fix_window_size_for_desktop, ensure_dir, get_storage_path, request_android_storage_permission, is_android
import json
import os

# 立即初始化全局变量和锁
character_data_lock = threading.Lock()
data = []

# 配置管理器类
class ConfigManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.config_path = os.path.join(get_storage_path(), "config", "config.json")
            self._config = None
            self.load_config()
            self._initialized = True
    
    def load_config(self):
        with self._lock:
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        self._config = json.load(f)
                except (json.JSONDecodeError, Exception) as e:
                    print(f"加载配置文件失败: {e}")
                    self._config = self._get_default_config()
            else:
                self._config = self._get_default_config()
                self.save_config()
    
    def save_config(self):
        with self._lock:
            try:
                ensure_dir(os.path.dirname(self.config_path))
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"保存配置文件失败: {e}")
    
    def _get_default_config(self):
        return {
            "openai": {
                "base_url": "",
                "api_key": "",
                "model": "gemini-2.5-flash"
            },
            "app": {
                "context_length": 50,
                "available_models": ["gemini-2.5-pro", "gemini-2.5-flash", "gpt-4.1", "deepseek-v3", "deepseek-r1"]
            },
            "theme": {
                "current_theme_index": 0,
                "theme_style": "Light",
                "primary_palette": "Blue",
                "accent_palette": "LightBlue"
            }
        }
    
    def get(self, key, default=None):
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key, value):
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()

# 全局配置管理器实例
config_manager = ConfigManager()

# 设置全局异常处理器
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    print(f"[错误] 未捕获的异常: {exc_type.__name__}: {exc_value}")
    import traceback
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    # 尝试显示错误信息给用户
    try:
        from kivy.clock import Clock
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.boxlayout import BoxLayout
        
        def show_error_popup(dt):
            layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
            error_label = Label(
                text=f"应用发生错误:\n{exc_value}",
                text_size=(400, None),
                halign='center',
                valign='middle'
            )
            close_button = Button(text='关闭', size_hint_y=None, height=50)
            
            layout.add_widget(error_label)
            layout.add_widget(close_button)
            
            popup = Popup(
                title='应用错误',
                content=layout,
                size_hint=(0.8, 0.4),
                auto_dismiss=False
            )
            
            close_button.bind(on_release=popup.dismiss)
            popup.open()
        
        Clock.schedule_once(show_error_popup, 0)
    except:
        print("无法显示错误弹窗")

import sys
sys.excepthook = global_exception_handler

# 安卓权限申请移到应用启动后，避免启动时崩溃
# 权限申请将在Example类的on_start方法中进行

# 仅桌面固定窗口大小
fix_window_size_for_desktop()

# 主应用类
class Example(MDApp):
    """主应用类"""
    context_menu = None  # 存放当前打开的上下文菜单引用
    loading_popup = None  # 加载指示器弹窗
    async_client = None  # 异步API客户端
    model_menu = None
    current_model = "deepseek-v3"  # 默认AI模型
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 主题配置
        self.themes = [
            {"name": "经典蓝白", "style": "Light", "palette": "Blue", "accent": "LightBlue", "icon": "weather-sunny"},
            {"name": "深蓝夜色", "style": "Dark", "palette": "Indigo", "accent": "BlueGray", "icon": "moon-waning-crescent"},
            {"name": "樱花粉白", "style": "Light", "palette": "Pink", "accent": "Red", "icon": "flower"},
            {"name": "森林绿野", "style": "Light", "palette": "Green", "accent": "LightGreen", "icon": "tree"},
            {"name": "神秘紫夜", "style": "Dark", "palette": "Purple", "accent": "DeepPurple", "icon": "star"},
            {"name": "橙色活力", "style": "Light", "palette": "Orange", "accent": "Amber", "icon": "weather-sunny-alert"},
            {"name": "科技青蓝", "style": "Dark", "palette": "Teal", "accent": "Cyan", "icon": "atom"},
            {"name": "温暖棕木", "style": "Light", "palette": "Brown", "accent": "Orange", "icon": "home"},
            {"name": "极简黑白", "style": "Dark", "palette": "Gray", "accent": "BlueGray", "icon": "circle-half-full"},
            {"name": "清新薄荷", "style": "Light", "palette": "LightGreen", "accent": "Teal", "icon": "leaf"}
        ]
        
        # 从配置管理器加载主题设置
        self.current_theme_index = config_manager.get("theme.current_theme_index", 0)
        
        # 防抖调度器引用
        self._debounce_schedules = {}
        
        # 中央卡片输入框（初始隐藏）
        self.center_card_input = None
        self.center_input_field = None
        self.is_center_input_visible = False
        
        # 存储最后发送的用户消息（用于API失败时重试）
        self._last_user_message = None

    def get_application_name(self):
        """设置应用程序标题"""
        return "Yuchat"  # 宝贝可以改成你喜欢的标题喔～
    
    def get_application_icon(self):
        """设置应用程序图标"""
        from tool.platform_utils import get_storage_path
        import os
        icon_path = os.path.join(get_storage_path(), "assets", "lightball.ico")
        return icon_path  # 使用可爱的光球图标～

    def on_start(self):
        # 安卓权限申请 - 移到应用启动后，避免启动时崩溃
        if __import__('kivy.utils').platform == 'android':
            try:
                print("[Android] 开始申请存储权限...")
                from tool.platform_utils import request_android_storage_permission
                request_android_storage_permission()
                print("[Android] 存储权限申请完成")
            except Exception as e:
                print(f"[Android] 权限申请失败: {e}")
                # 权限申请失败也不影响应用继续运行
        
        # 安卓设备上确保目录存在
        if hasattr(self, 'check_android_storage'):
            self.check_android_storage()
        
        # 立即启动数据加载线程（比 build 返回后更早执行）
        thread = Thread(target=self._load_data_async, daemon=True)
        thread.start()
        
        # 初始化异步API客户端
        self.async_client = get_async_api_client()
        
        # 从配置管理器读取默认模型
        self.current_model = config_manager.get("openai.model", "gemini-2.5-flash")
        available_models = config_manager.get("app.available_models", [])
        
        # 如果默认模型在可用模型列表中，使用它；否则使用第一个可用模型
        if available_models and self.current_model in available_models:
            self.current_model = self.current_model
        elif available_models:
            self.current_model = available_models[0]
        else:
            self.current_model = "gemini-2.5-flash"
        
        # 应用保存的主题颜色到界面
        Clock.schedule_once(self._apply_saved_theme_colors, 0.5)
        
        # 确保输入框使用中文字体
        if hasattr(self, 'message_input'):
            self.message_input.font_name = fonts.FONT_NAME
            self.message_input.font_size = '16sp'
            print(f"输入框字体已设置为: {self.message_input.font_name}")
        else:
            print("输入框还未创建，将在build方法中设置字体")

    def build(self):
        # 1) 内部的垂直 box（用于放多个 CopyLabel）
        # 2) 一个多行输入框（MDTextField）
        # 3) 一个占位 MDWidget（用于填充/布局）
        # 注意：这里使用 id="box" 的方式在纯 python 构建时不会自动生成 kv 的 ids，
        # 原代码中后来通过 self.root.get_ids() 访问会出问题（需改为保存引用）。

        # 初始化主题配置（必须在创建主题按钮之前）
        self.theme_cls.theme_style = config_manager.get("theme.theme_style", "Light")
        self.theme_cls.primary_palette = config_manager.get("theme.primary_palette", "Blue")
        self.theme_cls.accent_palette = config_manager.get("theme.accent_palette", "LightBlue")
        
        # 预热主题（避免首次使用时卡顿）
        self.theme_cls.primary_palette = "Blue"
        
        # 添加主题切换功能
        self.theme_cls.theme_style = "Light"  # 默认浅色模式
        
        # 初始化角色管理器
        self.character_manager = CharacterManager()
        self.character_manager.load_characters_from_config()
        self.character_chat_files = {}  # 角色对应的聊天记录文件路径
        
        # 设置角色管理器回调
        self.character_manager.set_callback('on_character_selected', self.on_character_selected)
        self.character_manager.set_callback('on_character_added', self.on_character_added)
        self.character_manager.set_callback('on_character_deleted', self.on_character_deleted)
        
        # 初始化角色选择抽屉（使用ModalView实现）
        from kivy.uix.modalview import ModalView
        self.character_drawer = ModalView(
            size_hint=(0.5, 1),  # 宽度改为50%
            pos_hint={'right': 1},
            background_color=self.theme_cls.surfaceColor,  # 使用主题表面颜色
            overlay_color=(0, 0, 0, 0.5)
        )
        self.character_manager.create_character_drawer_content(self.character_drawer)

        # 初始化设置抽屉（使用ModalView实现，显示在左侧，占据1/2宽度）
        self.settings_drawer = ModalView(
            size_hint=(0.5, 1),  # 宽度1/2（50%）
            pos_hint={'x': 0, 'top': 1},  # 左侧对齐，顶部对齐
            background_color=self.theme_cls.surfaceColor,  # 使用主题表面颜色
            overlay_color=(0, 0, 0, 0.5),
            auto_dismiss=True  # 点击外部区域自动关闭
        )
        self._build_settings_drawer_content()

        # 主屏幕内容
        self.main_layout = MDBoxLayout(
            orientation="vertical",
            padding=0,
            spacing=0
        )

        # 顶部功能栏
        self.top_bar = MDBoxLayout(
            adaptive_height=True,
            padding=[dp(16), dp(8)],
            spacing=dp(12)
        )

        # 主题切换按钮
        self.theme_button = MDIconButton(
            icon=self.themes[self.current_theme_index]["icon"] if hasattr(self, 'themes') else "weather-sunny",
            on_release=lambda x: self.open_theme_menu(x),  # 弹出主题选择菜单
            pos_hint={"center_y": 0.5}
        )

        # 占位符
        self.spacer = Widget(size_hint_x=1)

        # 角色选择按钮
        self.character_button = MDIconButton(
            icon="account-multiple",
            on_release=lambda x: self.toggle_character_drawer(),
            pos_hint={"center_y": 0.5}
        )

        # 设置按钮
        self.settings_button = MDIconButton(
            icon="cog",
            on_release=lambda x: self.toggle_settings_drawer(),
            pos_hint={"center_y": 0.5}
        )

        # 模型选择区域
        self.model_container = MDBoxLayout(
            adaptive_width=True,
            spacing=dp(2),
            pos_hint={"center_y": 0.5}
        )

        # 当前模型显示标签
        self.model_label = Label(
            text=f"当前模型: {self.current_model}",
            font_size=sp(11),
            color=(0.5, 0.5, 0.5, 1),
            halign="right",
            valign="center",
            size_hint_x=None,
            width=dp(100),
            font_name=fonts.FONT_NAME
        )

        # 模型选择按钮
        self.model_button = MDIconButton(
            icon="card-multiple-outline",
            on_release=lambda x: self.open_model_menu(x),
            pos_hint={"center_y": 0.5}
        )

        # 组装顶部栏
        self.model_container.add_widget(self.model_label)
        self.model_container.add_widget(self.model_button)

        self.top_bar.add_widget(self.theme_button)
        self.top_bar.add_widget(self.settings_button)  # 设置按钮移到主题切换右边
        self.top_bar.add_widget(self.spacer)
        self.top_bar.add_widget(self.character_button)
        self.top_bar.add_widget(self.model_container)

        # 将顶部栏加入主布局
        self.main_layout.add_widget(self.top_bar)

        # 聊天区域
        self.chat_layout = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(8), dp(16), dp(16)],
            spacing=dp(12)
        )

        # 聊天历史显示区域
        self.chat_history = ScrollView(
            size_hint=(1, 1),
            bar_width=dp(8),
            bar_color=(0.5, 0.5, 0.5, 0.8),
            bar_inactive_color=(0.5, 0.5, 0.5, 0.3),
            scroll_type=["bars", "content"],
            smooth_scroll_end=10
        )

        self.chat_history_layout = MDBoxLayout(
            orientation="vertical",
            padding=[dp(12), dp(16), dp(12), dp(16)],
            spacing=dp(12),
            size_hint_y=None,
            height=dp(100)
        )
        self.chat_history_layout.bind(minimum_height=self.chat_history_layout.setter('height'))
        self.chat_history.add_widget(self.chat_history_layout)

        # 输入区域
        self.input_layout = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(56),
            padding=[dp(8), dp(8), dp(8), dp(8)]
        )

        self.message_input = MDTextField(
            hint_text="输入消息...",
            mode="filled",
            multiline=False,
            size_hint=(1, 1),
            font_size=sp(16),
            on_text_validate=lambda x: self.send_message()
        )
        # 绑定焦点事件
        self.message_input.bind(focus=self._on_message_input_focus)
        # 绑定触摸事件作为备选方案
        self.message_input.bind(on_touch_down=self._on_message_input_touch)
        
        # 安全地设置字体 - 如果字体不存在则使用默认字体
        try:
            # 检查字体是否已注册
            from kivy.core.text import LabelBase
            if fonts.FONT_NAME in LabelBase._fonts:
                self.message_input.font_name = fonts.FONT_NAME
                print("[成功] 输入框字体设置为 fonts.FONT_NAME")
            else:
                print("[警告] fonts.FONT_NAME字体未注册，使用默认字体")
        except Exception as e:
            print(f"[警告] 字体设置失败，使用默认字体: {e}")
            # 不设置字体名称，使用默认字体
        
        # 绑定输入框焦点事件（移动端键盘适配）
        # self.message_input.bind(focus=self._on_message_input_focus)  # 已移除上移方法

        self.send_button = MDIconButton(
            icon="send",
            on_release=lambda x: self.send_message(),
            size_hint=(None, None),
            size=(dp(48), dp(48))
        )

        self.input_layout.add_widget(self.message_input)
        self.input_layout.add_widget(self.send_button)

        self.chat_layout.add_widget(self.chat_history)
        self.chat_layout.add_widget(self.input_layout)
        
        # 将聊天区域加入主布局
        self.main_layout.add_widget(self.chat_layout)

        # 创建主屏幕（使用MDScreen以支持主题背景色）
        main_screen = MDScreen()
        main_screen.md_bg_color = self.theme_cls.backgroundColor
        main_screen.add_widget(self.main_layout)
        
        # 角色抽屉将手动控制显示
        
        # 添加键盘监听（移动端适配）
        if hasattr(Window, 'bind'):
            # Window.bind(on_keyboard_height=self._on_keyboard_height)  # 已移除上移方法
            # Window.bind(on_textinput=self._on_textinput_focus)  # 已移除上移方法
            # 启用软键盘模式
            if hasattr(Window, 'set_vkeyboard_class'):
                Window.set_vkeyboard_class(None)  # 禁用虚拟键盘，使用系统键盘
            
            # 移动端优化：设置键盘模式
            from kivy import platform
            if platform == 'android' or platform == 'ios':
                # 设置窗口软输入模式
                if hasattr(Window, 'set_softinput_mode'):
                    Window.set_softinput_mode('resize')  # 调整窗口大小以适应键盘
        
        return main_screen

    def _load_data_async(self):
        """在后台线程中加载当前角色的聊天记录，然后回到主线程更新 UI。"""
        global data
        
        # 使用锁确保线程安全 - 解决手机端角色切换数据污染问题
        character_data_lock.acquire()
        
        try:
            # 获取当前角色的聊天记录文件路径
            current_character = self.character_manager.current_character
            character_data_file = None
            
            try:
                config = config_manager._config
                
                if "characters" in config.get("app", {}):
                    for char in config["app"]["characters"]:
                        if char['name'] == current_character:
                            data_file = char.get('data_file', f"data/chat_history_{current_character}.json")
                            # 确保使用完整路径，特别是在移动端
                            if not os.path.isabs(data_file):
                                character_data_file = os.path.join(get_storage_path(), data_file)
                            else:
                                character_data_file = data_file
                            break
            except Exception as e:
                print(f"读取角色配置时出错: {e}")
            
            if not character_data_file:
                if current_character and current_character != "默认角色":
                    character_data_file = os.path.join(get_storage_path(), "data", f"chat_history_{current_character}.json")
                else:
                    character_data_file = os.path.join(get_storage_path(), "data", "chat_data.json")
            
            print(f"正在加载角色 '{current_character}' 的聊天记录文件: {character_data_file}")
            
            # 只加载当前角色的聊天记录文件
            try:
                from tool.data_saver import load_chat_data
                # 为每个角色维护独立的数据副本，避免全局变量污染
                character_data = load_chat_data(character_data_file)
                data = character_data.copy()  # 使用副本避免异步竞争
                print(f"成功加载 {len(data)} 条聊天记录")
            except Exception as e:
                print(f"加载角色聊天记录时出错: {e}")
                data = []
        finally:
            # 确保锁被释放
            character_data_lock.release()

        # 回到主线程添加 UI 控件（批量添加可减少重排）
        Clock.schedule_once(self._add_ui_items, 0)

    def _add_ui_items(self, dt):
        """在主线程中逐个添加 CopyLabel 到 box（限制初始数量加快显示）。"""
        limit = 50  # 只初始显示前 50 条
        for i, item in enumerate(data[:limit]):
            # 检查数据结构，提取角色信息和内容
            if isinstance(item, dict):
                # 如果是字典格式，提取 role 和 content
                role = item.get('role', 'assistant')
                content = item.get('content', '')
                text = content
            else:
                # 如果是纯文本格式，默认为 assistant 角色
                role = 'assistant'
                text = str(item)
            
            # 创建 CopyLabel 时传入角色信息
            if role == 'user':
                copy_label = CopyLabel(text=text, message_role=role, on_double_tap_callback=self._handle_user_message_double_tap)
            elif role == 'assistant':
                copy_label = CopyLabel(text=text, message_role=role, on_double_tap_callback=self._handle_ai_message_double_tap)
            else:
                copy_label = CopyLabel(text=text, message_role=role)
            copy_label.bind(on_selection=self.open_context_menu)
            self.chat_history_layout.add_widget(copy_label)

        # 若有更多数据，可在用户滚动时按需加载（这里先不实现）
        
        # 延迟滚动到底部
        Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)
    
    def _scroll_to_bottom(self):
        """滚动到底部"""
        if hasattr(self, 'chat_history'):
            # 更准确的滚动方法
            self.chat_history.scroll_y = 0
    
    def open_model_menu(self, button):
        """打开AI模型选择菜单"""
        # 从配置管理器读取可用模型列表
        available_models = config_manager.get("app.available_models", ["deepseek-v3"])
        
        model_items = []
        for model_name in available_models:
            model_items.append({
                "text": model_name,
                "on_release": lambda x=model_name: self.select_model(x),
                "font_name": fonts.FONT_NAME,
            })
        
        # 每次都重新创建菜单，确保显示最新的模型列表
        self.model_menu = MDDropdownMenu(
            caller=button, 
            items=model_items, 
            position="bottom",
            width_mult=4,
        )
        
        self.model_menu.open()
    
    def select_model(self, model_name):
        """选择AI模型"""
        self.current_model = model_name
        # 直接使用已保存的model_label引用，避免硬编码索引
        self.model_label.text = f"当前模型: {model_name}"
        if hasattr(self, 'model_menu') and self.model_menu:
            self.model_menu.dismiss()
        # 使用打印语句代替toast
        print(f"已选择模型: {model_name}")

    def _build_character_drawer_content(self):
        """构建角色选择抽屉内容 - 使用美观的KivyMD组件"""
        from kivymd.uix.navigationdrawer import MDNavigationDrawer
        from kivymd.uix.card import MDCard
        from kivymd.uix.list import MDListItem, MDListItemLeadingIcon, MDListItemHeadlineText, MDListItemSupportingText
        from kivymd.uix.button import MDButton, MDButtonText
        from kivymd.uix.divider import MDDivider
        
        # 创建现代导航抽屉
        drawer_content = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16)],
            spacing=dp(12)
        )
        
        # 抽屉头部卡片 - 使用主题色
        header_card = MDCard(
            style="filled",
            padding=[dp(16)],
            spacing=dp(8),
            size_hint_y=None,
            height=dp(80),
            radius=[dp(12)]
        )
        
        # 头部图标和标题
        header_content = MDBoxLayout(orientation="vertical", spacing=dp(4))
        header_icon = MDIconButton(
            icon="account-multiple",
            pos_hint={"center_x": 0.5},
            theme_icon_color="Custom",
            icon_color=self.theme_cls.primaryColor
        )
        header_title = MDLabel(
            text="角色选择",
            halign="center",
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=self.theme_cls.primaryColor
        )
        header_content.add_widget(header_icon)
        header_content.add_widget(header_title)
        header_card.add_widget(header_content)
        drawer_content.add_widget(header_card)
        
        # 操作按钮区域 - 使用主题按钮
        button_layout = MDBoxLayout(
            adaptive_height=True,
            spacing=dp(8)
        )
        
        # 添加角色按钮 - 使用图标按钮
        add_btn = MDIconButton(
            icon="plus",
            on_release=lambda x: self.add_character(),
            size_hint=(1, None),
            height=dp(48),
            style="filled",
            theme_icon_color="Custom",
            icon_color=self.theme_cls.onPrimaryColor,
            md_bg_color=self.theme_cls.primaryColor
        )
        
        # 删除角色按钮 - 使用图标按钮
        delete_btn = MDIconButton(
            icon="delete",
            on_release=lambda x: self.delete_current_character(),
            disabled=not self.current_character or self.current_character == "默认角色",
            size_hint=(1, None),
            height=dp(48),
            style="outlined",
            theme_icon_color="Custom",
            icon_color=self.theme_cls.primaryColor
        )
        
        button_layout.add_widget(add_btn)
        button_layout.add_widget(delete_btn)
        drawer_content.add_widget(button_layout)
        
        # 分隔线 - 使用主题色
        divider = MDDivider()
        drawer_content.add_widget(divider)
        
        # 角色列表区域 - 使用现代列表组件
        scroll_view = ScrollView(
            bar_width=dp(4),
            bar_color=self.theme_cls.primaryColor,
            bar_inactive_color=(0.5, 0.5, 0.5, 0.3)
        )
        
        character_list_layout = MDBoxLayout(
            orientation='vertical', 
            spacing=dp(8), 
            size_hint_y=None,
            padding=[dp(4)]
        )
        character_list_layout.bind(minimum_height=character_list_layout.setter('height'))
        scroll_view.add_widget(character_list_layout)
        drawer_content.add_widget(scroll_view)
        
        # 添加到抽屉
        self.character_drawer.add_widget(drawer_content)
        
        # 保存引用
        self.character_list = character_list_layout
        self.delete_character_btn = delete_btn
        
        # 初始化角色列表 - 使用新的美观样式
        self.refresh_character_list()

    def _build_settings_drawer_content(self):
        """构建设置抽屉内容 - 参考角色抽屉的设计风格"""
        from kivymd.uix.card import MDCard
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
        from kivymd.uix.divider import MDDivider
        from kivymd.uix.label import MDLabel
        from kivy.uix.widget import Widget
        
        # 创建设置抽屉内容 - 使用主题背景色
        drawer_content = MDBoxLayout(
            orientation="vertical",
            padding=[dp(8), dp(8), dp(8), dp(0)],  # 减少整体内边距，底部无间距
            spacing=dp(8),  # 减少间距
            md_bg_color=self.theme_cls.surfaceColor  # 使用主题表面颜色作为背景
        )
        
        # 抽屉头部卡片 - 使用与角色抽屉相同的样式
        header_card = MDCard(
            style="filled",
            padding=[dp(16)],
            spacing=dp(8),
            size_hint_y=None,
            height=dp(80),
            radius=[dp(12)]
        )
        
        header_content = MDBoxLayout(orientation="vertical", spacing=dp(4))
        header_icon = MDIconButton(
            icon="cog",
            pos_hint={"center_x": 0.5},
            theme_icon_color="Custom",
            icon_color=self.theme_cls.primaryColor
        )
        header_title = Label(
            text="设置",
            halign="center",
            font_name=fonts.FONT_NAME,
            font_size="20sp",
            color=self.theme_cls.primaryColor
        )
        header_content.add_widget(header_icon)
        header_content.add_widget(header_title)
        header_card.add_widget(header_content)
        drawer_content.add_widget(header_card)
        
        # 设置项区域 - 调整间距让界面更紧凑
        settings_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),  # 从8减小到6，让内容更紧凑
            padding=[dp(6), dp(6), dp(6), dp(6)]  # 保持内边距不变
        )
        drawer_content.add_widget(settings_layout)
        
        # 加载当前配置
        self._load_current_config()
        
        # API基础URL - 调整高度让界面更紧凑
        self.base_url_field = MDTextField(
            text=self.current_base_url,
            hint_text="API基础URL",
            mode="outlined",
            size_hint_y=None,
            height=dp(40)  # 从默认48dp减小到40dp
        )
        settings_layout.add_widget(self.base_url_field)
        
        # API密钥 - 调整高度让界面更紧凑
        self.api_key_field = MDTextField(
            text=self.current_api_key,
            hint_text="API密钥",
            mode="outlined",
            # 取消password=True，让密钥正常显示
            size_hint_y=None,
            height=dp(40)  # 从默认48dp减小到40dp
        )
        settings_layout.add_widget(self.api_key_field)
        
        # 上下文长度 - 调整高度让界面更紧凑
        self.context_length_field = MDTextField(
            text=str(self.current_context_length),
            hint_text="上下文长度",
            mode="outlined",
            size_hint_y=None,
            height=dp(40)  # 从默认48dp减小到40dp
        )
        settings_layout.add_widget(self.context_length_field)
        
        # 添加分隔区域 - 让可用模型部分视觉上更独立
        section_spacer = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(4),  # 轻微的空间分隔
            md_bg_color=(0.95, 0.95, 0.95, 0.3)  # 极浅的背景色
        )
        settings_layout.add_widget(section_spacer)
        
        # 可用模型区域 - 添加轻微背景让区域更独立
        models_section = MDBoxLayout(
            orientation="vertical",
            spacing=dp(2),  # 稍微增加到2，让区域内部更透气
            padding=[dp(2), dp(2), dp(2), dp(2)],  # 添加轻微内边距
            md_bg_color=(0.98, 0.98, 0.98, 0.5),  # 极浅的背景色
            radius=[dp(4)]  # 轻微圆角
        )
        
        # 模型头部区域 - 使用垂直居中对齐
        models_header = MDBoxLayout(
            orientation="horizontal", 
            spacing=dp(1),  # 从2减小到1
            padding=[dp(2), dp(0), dp(2), dp(0)],  # 从[2,1,2,0]减小到[2,0,2,0]
            size_hint_y=None,
            height=dp(32)  # 设置固定高度，确保垂直居中对齐
        )
        
        models_label = Label(
            text="可用模型",
            font_name=fonts.FONT_NAME,
            font_size="14sp",  # 从16sp减小到14sp，让标题更低调
            color=(0.6, 0.6, 0.6, 1),  # 使用灰色，降低视觉权重
            halign="left",
            valign="center",
            size_hint_x=0.8,
            size_hint_y=None,
            height=dp(32),  # 与容器相同高度，确保垂直居中
            text_size=(None, dp(32))  # 设置文本区域高度与容器一致
        )
        
        # 添加模型按钮 - 使用固定尺寸确保垂直居中对齐
        add_model_button = MDIconButton(
            icon="plus",
            style="filled",
            theme_icon_color="Custom",
            icon_color=self.theme_cls.onPrimaryColor,
            md_bg_color=self.theme_cls.primaryColor,
            size_hint=(None, None),
            size=(dp(28), dp(28)),  # 设置固定尺寸，便于垂直居中
            pos_hint={"center_y": 0.5},  # 垂直居中
            on_release=lambda x: self._show_add_model_dialog()
        )
        
        models_header.add_widget(models_label)
        models_header.add_widget(Widget())  # 占位符
        models_header.add_widget(add_model_button)
        models_section.add_widget(models_header)
        
        # 创建可滚动的模型列表容器 - 移除固定高度，让内容自然流动
        scroll_view = ScrollView(
            bar_width=dp(4),  # 滚动条宽度
            bar_color=(0.5, 0.5, 0.5, 0.8),  # 滚动条颜色
            bar_inactive_color=(0.5, 0.5, 0.5, 0.3)  # 非活跃滚动条颜色
        )
        
        # 模型列表区域 - 放在ScrollView中，增加卡片间距
        self.models_list_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(4),  # 从0增加到4，增加模型卡片之间的间距
            size_hint_y=None,  # 重要：必须设置为None才能让ScrollView正常工作
            height=dp(0),  # 初始高度为0，会根据内容自动调整
            padding=[dp(1), dp(2), dp(1), dp(2)]  # 稍微增加垂直内边距
        )
        # 绑定高度调整函数
        self.models_list_layout.bind(minimum_height=self.models_list_layout.setter('height'))
        
        scroll_view.add_widget(self.models_list_layout)
        models_section.add_widget(scroll_view)
        
        settings_layout.add_widget(models_section)
        
        # 保存当前模型列表引用
        self.current_models_widgets = []
        
        # 在UI组件创建完成后刷新模型列表
        if hasattr(self, 'current_available_models'):
            self._refresh_models_list()
        
        # 分隔线
        divider = MDDivider()
        settings_layout.add_widget(divider)
        
        # 保存按钮 - 使用默认尺寸，让布局更自然
        save_button = MDIconButton(
            icon="content-save",
            style="filled",
            theme_icon_color="Custom",
            icon_color=self.theme_cls.onPrimaryColor,
            md_bg_color=self.theme_cls.primaryColor,
            on_release=lambda x: self._save_settings(),
            pos_hint={"center_x": 0.5}
        )
        settings_layout.add_widget(save_button)
        
        # 添加到抽屉
        self.settings_drawer.add_widget(drawer_content)
    
    def _refresh_settings_fields(self):
        """刷新设置界面的字段值"""
        # 更新各个字段的文本
        if hasattr(self, 'base_url_field'):
            self.base_url_field.text = self.current_base_url
        if hasattr(self, 'api_key_field'):
            self.api_key_field.text = self.current_api_key
        if hasattr(self, 'context_length_field'):
            self.context_length_field.text = str(self.current_context_length)
        # 刷新模型列表
        if hasattr(self, 'current_available_models'):
            self._refresh_models_list()

    def _refresh_models_list(self):
        """刷新模型列表显示"""
        # 清空现有列表
        self.models_list_layout.clear_widgets()
        self.current_models_widgets.clear()
        
        # 添加每个模型卡片 - 正序添加，让第一个模型显示在最上方
        for model in self.current_available_models:
            # 处理新旧数据结构兼容性
            if isinstance(model, dict):
                model_name = model.get('name', 'Unknown')
            else:
                model_name = str(model)
            
            model_card = self._create_model_card(model_name)
            self.models_list_layout.add_widget(model_card)
            self.current_models_widgets.append(model_card)
    
    def _create_model_card(self, model_name):
        """创建单个模型卡片 - 参考角色抽屉的角色卡片样式"""
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel
        from kivy.uix.widget import Widget
        
        card = MDCard(
            style="outlined",
            padding=[dp(2), dp(2)],  # 增加内边距
            spacing=dp(2),  # 增加间距
            size_hint_y=None,
            height=dp(36),  # 从28增加到36，让卡片更大一些
            radius=[dp(4)],  # 增加圆角
            elevation=1,  # 添加轻微阴影效果
            theme_bg_color="Custom",
            md_bg_color=(1, 1, 1, 0.8),  # 轻微透明背景
            theme_line_color="Custom",
            line_color=(0.8, 0.8, 0.8, 0.3)  # 浅色边框
        )
        
        card_layout = MDBoxLayout(orientation="horizontal", spacing=dp(8), padding=[dp(8), dp(4)])  # 增加间距和内边距
        
        # 模型名称标签 - 左对齐，占据大部分空间，为删除按钮留出位置
        from kivy.uix.label import Label
        model_label = Label(
            text=model_name,
            font_name=fonts.FONT_NAME,
            font_size=sp(14),
            color=self.theme_cls.primaryColor,
            halign="left",
            valign="center",
            shorten=True,  # 如果文字太长，用省略号表示
            shorten_from="right",
            text_size=(None, None),
            size_hint_x=0.85,  # 占85%宽度，为删除按钮留出空间
            padding=[dp(4), dp(0)]  # 增加左边距
        )
        
        # 删除按钮 - 放在最右边，固定宽度避免超出
        delete_button = MDIconButton(
            icon="delete",
            size_hint=(None, None),
            size=(dp(22), dp(22)),  # 保持22尺寸
            style="standard",
            theme_icon_color="Custom",
            icon_color=self.theme_cls.errorColor,
            on_release=lambda x, name=model_name: self._delete_model(name),
            pos_hint={"center_y": 0.5}  # 垂直居中对齐
        )
        
        # 先添加模型名称（左对齐，占大部分空间），再添加删除按钮（右对齐，固定宽度）
        card_layout.add_widget(model_label)
        card_layout.add_widget(delete_button)
        card.add_widget(card_layout)
        
        return card
    
    def _show_add_model_dialog(self):
        """显示添加模型对话框"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.button import MDButton, MDButtonText
        
        # 创建模型名称输入框（只保留这一个输入框）
        self.new_model_field = MDTextField(
            hint_text="输入模型名称",
            mode="outlined"
        )
        
        # 创建取消按钮 - 使用图标按键
        from kivymd.uix.button import MDIconButton
        cancel_button = MDIconButton(
            icon="close",
            style="standard",
            on_release=lambda x: self._close_add_model_dialog()
        )
        
        # 创建确认按钮 - 使用图标按键
        confirm_button = MDIconButton(
            icon="check",
            style="filled",
            on_release=lambda x: self._add_model()
        )
        
        # 创建对话框 - 使用自定义标题布局替代MDDialogHeadlineText
        from kivy.uix.label import Label
        from kivymd.uix.boxlayout import MDBoxLayout
        
        # 创建自定义标题
        title_label = Label(
            text="添加新模型",
            font_name=fonts.FONT_NAME,
            font_size="18sp",
            color=self.theme_cls.primaryColor,
            halign="center",
            valign="center",
            size_hint_y=None,
            height=dp(40),
            text_size=(None, dp(40))
        )
        
        # 创建对话框内容容器（只包含标题和模型名称输入框）
        content_container = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            padding=[dp(24), dp(16), dp(24), dp(16)],
            size_hint_y=None,
            height=dp(120)  # 减少高度，只容纳一个输入框
        )
        content_container.add_widget(title_label)
        content_container.add_widget(self.new_model_field)
        
        # 创建按钮容器
        from kivymd.uix.boxlayout import MDBoxLayout
        button_container = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            padding=[dp(24), dp(16), dp(24), dp(24)],
            size_hint_y=None,
            height=dp(56),
            pos_hint={"right": 1}
        )
        button_container.add_widget(Widget())  # 占位符
        button_container.add_widget(cancel_button)
        button_container.add_widget(confirm_button)
        
        # 创建对话框
        self.add_model_dialog = MDDialog(
            content_container,
            button_container
        )
        
        self.add_model_dialog.open()
    
    def _close_add_model_dialog(self):
        """关闭添加模型对话框"""
        if hasattr(self, 'add_model_dialog') and self.add_model_dialog:
            self.add_model_dialog.dismiss()
            self.add_model_dialog = None
    
    def _add_model(self):
        """添加新模型"""
        new_model = self.new_model_field.text.strip()
        
        if new_model:
            # 检查模型是否已存在
            model_exists = False
            for existing_model in self.current_available_models:
                if existing_model == new_model:
                    model_exists = True
                    break
            
            if not model_exists:
                # 添加模型名称字符串到列表
                self.current_available_models.append(new_model)
                
                # 只添加新模型卡片，不刷新整个列表
                model_card = self._create_model_card(new_model)
                # 将新模型添加到列表底部（最后），这样不会推动现有卡片
                self.models_list_layout.add_widget(model_card)
                self.current_models_widgets.append(model_card)
                
                # 同步保存到配置文件，确保模型选择菜单能立即看到新模型
                self._save_settings()
        
        # 关闭对话框
        self._close_add_model_dialog()
    
    def _delete_model(self, model_name):
        """删除模型"""
        # 从字符串列表中删除模型
        if model_name in self.current_available_models:
            self.current_available_models.remove(model_name)
            self._refresh_models_list()
            # 同步保存到配置文件，确保模型选择菜单能立即看到变化
            self._save_settings()

    def toggle_character_drawer(self):
        """切换角色选择抽屉"""
        if self.character_drawer.parent:
            self.character_drawer.dismiss()
        else:
            # 重新加载角色配置
            self.character_manager.load_characters_from_config()
            self.character_manager.refresh_character_list()
            self.character_drawer.open()

    def toggle_settings_drawer(self):
        """切换设置抽屉"""
        if self.settings_drawer.parent:
            self.settings_drawer.dismiss()
        else:
            # 重新加载配置并刷新UI
            self._load_current_config()
            self._refresh_settings_fields()
            self.settings_drawer.open()
    
    def _load_character_chat_history(self, character: str) -> None:
        """加载指定角色的聊天记录"""
        global data
        
        # 使用锁确保线程安全 - 解决手机端角色切换数据污染问题
        character_data_lock.acquire()
        
        try:
            # 清空当前聊天记录显示
            self.chat_history_layout.clear_widgets()
            
            # 获取角色对应的数据文件路径
            character_data_file = None
            try:
                config = config_manager._config
                
                if "characters" in config.get("app", {}):
                    for char in config["app"]["characters"]:
                        if char['name'] == character:
                            data_file = char.get('data_file', os.path.join(get_storage_path(), "data", f"chat_history_{character}.json"))
                            # 确保使用完整路径，特别是在移动端
                            if not os.path.isabs(data_file):
                                character_data_file = os.path.join(get_storage_path(), data_file)
                            else:
                                character_data_file = data_file
                            break
            except Exception as e:
                print(f"读取角色配置时出错: {e}")
            
            if not character_data_file:
                if character and character != "默认角色":
                    character_data_file = os.path.join(get_storage_path(), "data", f"chat_history_{character}.json")
                else:
                    character_data_file = os.path.join(get_storage_path(), "data", "chat_data.json")
            
            print(f"正在加载角色 '{character}' 的聊天记录文件: {character_data_file}")
            
            # 加载聊天记录
            from tool.data_saver import load_chat_data
            chat_history = load_chat_data(character_data_file)
            
            # 更新全局数据 - 使用角色专属的数据副本
            data = chat_history.copy() if chat_history else []
            
            # 显示聊天记录
            if chat_history:
                print(f"找到 {len(chat_history)} 条聊天记录")
                for message in chat_history:
                    role = message.get('role', 'assistant')
                    content = message.get('content', '')
                    
                    if content:  # 只显示有内容的消息
                        # 根据角色绑定双击事件
                        if role == 'user':
                            message_label = CopyLabel(text=content, message_role=role, on_double_tap_callback=self._handle_user_message_double_tap)
                        elif role == 'assistant':
                            message_label = CopyLabel(text=content, message_role=role, on_double_tap_callback=self._handle_ai_message_double_tap)
                        else:
                            message_label = CopyLabel(text=content, message_role=role)
                        message_label.bind(on_selection=self.open_context_menu)
                        self.chat_history_layout.add_widget(message_label)
            else:
                print("该角色暂无聊天记录")
            
            # 滚动到底部
            Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)
            
        except Exception as e:
            print(f"加载角色聊天记录时出错: {e}")
            # 出错时显示默认数据
            data = []
        finally:
            # 确保锁被释放
            character_data_lock.release()
    
    def on_character_selected(self, character: str) -> None:
        """角色选择回调"""
        global data
        
        # 关闭抽屉
        self.character_drawer.dismiss()
        print(f"主程序收到角色切换: {character}")
        
        # 立即清空当前数据，避免异步加载时的数据污染
        character_data_lock.acquire()
        try:
            data = []  # 清空全局数据，确保不会显示旧角色的数据
            self._clear_chat_display()  # 立即清空UI显示
        finally:
            character_data_lock.release()
        
        # 重新加载对应角色的聊天记录
        self._load_character_chat_history(character)
    
    def on_character_added(self, character: str) -> None:
        """角色添加回调"""
        print(f"主程序收到角色添加: {character}")
    
    def on_character_deleted(self, deleted_character: str, new_current_character: str) -> None:
        """角色删除回调"""
        global data
        
        print(f"主程序收到角色删除: {deleted_character}，新当前角色: {new_current_character}")
        
        # 立即清空当前数据，避免异步加载时的数据污染
        character_data_lock.acquire()
        try:
            data = []  # 清空全局数据，确保不会显示旧角色的数据
            self._clear_chat_display()  # 立即清空UI显示
        finally:
            character_data_lock.release()
        
        # 重新加载新角色的聊天记录
        if new_current_character:
            self._load_character_chat_history(new_current_character)

    def delete_current_character(self):
        """删除当前角色"""
        if self.character_manager:
            self.character_manager.delete_current_character()
    
    def _clear_chat_display(self):
        """清空聊天显示区域"""
        if hasattr(self, 'chat_history_layout') and self.chat_history_layout:
            self.chat_history_layout.clear_widgets()
            # 重置布局高度
            self.chat_history_layout.height = dp(100)
    
    def _on_message_input_focus(self, instance, value):
        """原输入框焦点事件处理"""
        print(f"输入框焦点事件: value={value}, is_center_input_visible={self.is_center_input_visible}")
        if value and not self.is_center_input_visible:  # 获得焦点且中央输入框未显示
            print("显示中央卡片输入框")
            self._debounced_show_center_input()
    
    def _on_message_input_touch(self, instance, touch):
        """原输入框触摸事件处理"""
        print(f"输入框触摸事件: instance={instance}, touch={touch}")
        if instance.collide_point(*touch.pos) and not self.is_center_input_visible:
            print("触摸显示中央卡片输入框")
            self._debounced_show_center_input()
            return True
        return False
    
    def _debounced_show_center_input(self):
        """防抖显示中央输入框"""
        # 取消之前的调度
        if 'show_center_input' in self._debounce_schedules:
            Clock.unschedule(self._debounce_schedules['show_center_input'])
        
        # 重新调度
        self._debounce_schedules['show_center_input'] = Clock.schedule_once(
            lambda dt: self._actually_show_center_input(), 0.1
        )
    
    def _actually_show_center_input(self):
        """实际显示中央卡片输入框"""
        if self.is_center_input_visible:
            return
            
        self.is_center_input_visible = True
        print("开始创建中央卡片输入框")
        
        # 创建中央卡片输入框
        from kivymd.uix.card import MDCard
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.button import MDIconButton
        from kivymd.uix.boxlayout import MDBoxLayout
        
        # 创建卡片布局
        card_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            padding=[dp(24), dp(24), dp(24), dp(24)],
            size_hint=(None, None),
            size=(dp(320), dp(200)),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        
        # 创建输入框 - 使用MDScrollView包裹MDTextField以支持滚动
        self.center_input_field = MDTextField(
            hint_text="在这里输入消息...",
            mode="filled",
            multiline=True,
            size_hint=(1, None),
            height=dp(100),  # 固定高度以启用滚动
            font_size=sp(16),
            text=self.message_input.text,  # 同步原输入框的内容
        )
        
        # 创建滚动视图包裹输入框
        scroll_view = MDScrollView(
            size_hint=(1, None),
            height=dp(100),
            do_scroll_x=False,  # 禁用水平滚动
            do_scroll_y=True,   # 启用垂直滚动
        )
        scroll_view.add_widget(self.center_input_field)
        
        # 创建按钮布局
        button_layout = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(48),
            padding=[0, dp(16), 0, 0]
        )
        
        # 取消按钮
        cancel_button = MDIconButton(
            icon="close",
            on_release=lambda x: self.hide_center_card_input()
        )
        
        # 发送按钮
        send_button = MDIconButton(
            icon="send",
            on_release=lambda x: self.send_message_from_center(),
            theme_icon_color="Custom",
            icon_color=self.theme_cls.primaryColor
        )
        
        button_layout.add_widget(cancel_button)
        button_layout.add_widget(MDBoxLayout())  # 空白填充
        button_layout.add_widget(send_button)
        
        card_layout.add_widget(scroll_view)
        card_layout.add_widget(button_layout)
        
        # 创建卡片
        self.center_card_input = MDCard(
            style="elevated",
            elevation=8,
            size_hint=(None, None),
            size=(dp(320), dp(200)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            opacity=0
        )
        self.center_card_input.add_widget(card_layout)
        
        # 添加到主屏幕
        if hasattr(self, 'root') and self.root:
            print(f"正在添加中央卡片到root: {self.root}")
            self.root.add_widget(self.center_card_input)
            print(f"中央卡片已添加，子部件数量: {len(self.root.children)}")
            
            # 动画显示
            from kivy.animation import Animation
            anim = Animation(opacity=1, duration=0.3)
            anim.start(self.center_card_input)
            
            # 聚焦到输入框
            self.center_input_field.focus = True
            
            # 绑定文本变化事件以实现同步
            self.center_input_field.bind(text=self._on_center_input_text_change)
            
            # 绑定触摸事件，用于检测点击卡片外部
            self.center_card_input.bind(on_touch_down=self._on_center_card_touch)
            
            print("中央卡片输入框创建完成")
    
    def _on_center_card_touch(self, instance, touch):
        """处理卡片触摸事件，检测是否点击在卡片外部"""
        # 如果卡片不可见，不处理
        if not self.is_center_input_visible or not self.center_card_input:
            return False
            
        # 获取卡片在窗口中的实际位置
        card_pos = self.center_card_input.to_window(*self.center_card_input.pos)
        card_size = self.center_card_input.size
        
        # 检查触摸点是否在卡片区域外
        if (touch.x < card_pos[0] or touch.x > card_pos[0] + card_size[0] or
            touch.y < card_pos[1] or touch.y > card_pos[1] + card_size[1]):
            # 点击在卡片外部，隐藏卡片
            self.hide_center_card_input()
            # 消费掉这个触摸事件，防止事件冒泡
            return True
        
        # 点击在卡片内部，正常处理，不消费事件
        return False
    
    def hide_center_card_input(self):
        """隐藏中央卡片输入框"""
        if not self.is_center_input_visible or not self.center_card_input:
            return
            
        # 动画隐藏
        from kivy.animation import Animation
        anim = Animation(opacity=0, duration=0.2)
        anim.bind(on_complete=lambda *args: self._remove_center_card())
        anim.start(self.center_card_input)
    
    def _remove_center_card(self):
        """移除中央卡片"""
        if self.center_card_input and self.center_card_input.parent:
            self.center_card_input.parent.remove_widget(self.center_card_input)
            self.center_card_input = None
            self.center_input_field = None
            self.is_center_input_visible = False
    
    def _on_center_input_text_change(self, instance, value):
        """中央输入框文本变化时同步到原输入框"""
        self.message_input.text = value
    
    def send_message_from_center(self):
        """从中央输入框发送消息"""
        if self.center_input_field and self.center_input_field.text.strip():
            # 同步文本到原输入框
            self.message_input.text = self.center_input_field.text
            # 隐藏中央卡片
            self.hide_center_card_input()
            # 发送消息
            self.send_message()

    def open_theme_menu(self, button):
        """打开主题选择菜单"""
        theme_items = []
        for i, theme in enumerate(self.themes):
            theme_items.append({
                "text": theme["name"],
                "on_release": lambda x=i: self.set_theme(x),
                "font_name": fonts.FONT_NAME,
            })
        
        self.theme_menu = MDDropdownMenu(
            caller=button,
            items=theme_items,
            width_mult=4,
            max_height=dp(300)
        )
        self.theme_menu.open()
    
    def set_theme(self, theme_index):
        """设置指定主题"""
        if 0 <= theme_index < len(self.themes):
            self.current_theme_index = theme_index
            theme = self.themes[theme_index]
            
            # 应用主题设置
            self.theme_cls.theme_style = theme["style"]
            self.theme_cls.primary_palette = theme["palette"]
            self.theme_cls.accent_palette = theme["accent"]
            
            # 更新主题按钮图标
            if hasattr(self, 'theme_button'):
                self.theme_button.icon = theme["icon"]
            
            # 关闭菜单
            if hasattr(self, 'theme_menu'):
                self.theme_menu.dismiss()
            
            # 更新界面颜色
            self._update_theme_colors()
            
            # 保存主题配置到config.json
            config_manager.set("theme.current_theme_index", theme_index)
            config_manager.set("theme.theme_style", theme["style"])
            config_manager.set("theme.primary_palette", theme["palette"])
            config_manager.set("theme.accent_palette", theme["accent"])
            
            print(f"[成功] 主题配置已保存: {theme['name']}")
    
    def switch_theme(self):
        """切换到下一个主题（循环）"""
        self.current_theme_index = (self.current_theme_index + 1) % len(self.themes)
        self.set_theme(self.current_theme_index)
    
    def _apply_saved_theme_colors(self, dt=None):
        """应用保存的主题颜色到界面（在界面构建完成后调用）"""
        try:
            # 获取保存的主题索引
            saved_theme_index = config_manager.get("theme.current_theme_index", 0)
            
            # 确保索引有效
            if 0 <= saved_theme_index < len(self.themes):
                self.current_theme_index = saved_theme_index
                theme = self.themes[self.current_theme_index]
                
                # 应用主题样式、调色板和强调色
                theme_style = config_manager.get("theme.theme_style", theme["style"])
                primary_palette = config_manager.get("theme.primary_palette", theme["palette"])
                accent_palette = config_manager.get("theme.accent_palette", theme["accent"])
                
                self.theme_cls.theme_style = theme_style
                self.theme_cls.primary_palette = primary_palette
                self.theme_cls.accent_palette = accent_palette
                
                # 使用KivyMD的主题颜色系统
                if hasattr(self, 'root') and hasattr(self.root, 'md_bg_color'):
                    self.root.md_bg_color = self.theme_cls.backgroundColor
                
                # 更新图标按钮颜色
                if hasattr(self, 'add_character_button'):
                    self.add_character_button.icon_color = self.theme_cls.onPrimaryColor
                    self.add_character_button.md_bg_color = self.theme_cls.primaryColor
                
                if hasattr(self, 'delete_character_button'):
                    self.delete_character_button.icon_color = self.theme_cls.primaryColor
                
                # 更新主题按钮图标
                if hasattr(self, 'theme_button'):
                    self.theme_button.icon = theme['icon']
                
                # 重新渲染所有消息以应用新的颜色主题
                Clock.schedule_once(self._refresh_messages, 0.1)
                
                print(f"[成功] 已应用保存的主题: {theme['name']}")
            else:
                print(f"[警告] 保存的主题索引无效: {saved_theme_index}")
                
        except Exception as e:
            print(f"[错误] 应用保存主题失败: {e}")
            # 如果失败，使用默认主题
            self._update_theme_colors()
    
    def _update_theme_colors(self):
        """更新界面颜色主题"""
        # 更新主屏幕背景色
        if hasattr(self, 'root') and hasattr(self.root, 'md_bg_color'):
            self.root.md_bg_color = self.theme_cls.backgroundColor
        
        # 更新图标按钮颜色
        if hasattr(self, 'add_character_button'):
            self.add_character_button.icon_color = self.theme_cls.onPrimaryColor
            self.add_character_button.md_bg_color = self.theme_cls.primaryColor
        
        if hasattr(self, 'delete_character_button'):
            self.delete_character_button.icon_color = self.theme_cls.primaryColor
        
        # 重新渲染所有消息以应用新的颜色主题
        Clock.schedule_once(self._refresh_messages, 0.1)
    
    def _refresh_messages(self, dt):
        """重新渲染所有消息以应用新的主题颜色"""
        for child in self.chat_history_layout.children:
            if isinstance(child, CopyLabel):
                child._setup_text_and_height(dt)  # 重新设置文本和颜色
    
    def send_message(self):
        """发送消息功能"""
        text = self.message_input.text.strip()
        
        # 调试信息：检查输入框字体
        print(f"输入框当前字体: {self.message_input.font_name}")
        print(f"输入框当前文本: {text}")
        
        if not text:
            return
        
        # 获取当前角色的数据文件路径
        current_character = self.character_manager.get_current_character()
        if current_character and current_character != "默认角色":
            # 查找角色对应的数据文件 - 从配置文件获取完整角色信息
            character_data_file = None
            try:
                config = config_manager._config
                
                if "characters" in config.get("app", {}):
                    for char in config["app"]["characters"]:
                        if char['name'] == current_character:
                            data_file = char.get('data_file', f"data/chat_history_{current_character}.json")
                            # 确保使用完整路径，特别是在移动端
                            if not os.path.isabs(data_file):
                                character_data_file = os.path.join(get_storage_path(), data_file)
                            else:
                                character_data_file = data_file
                            break
            except Exception as e:
                print(f"读取角色配置时出错: {e}")
            
            if not character_data_file:
                character_data_file = os.path.join(get_storage_path(), "data", f"chat_history_{current_character}.json")
        else:
            # 如果没有角色或默认角色，使用默认文件
            character_data_file = os.path.join(get_storage_path(), "data", "chat_data.json")
        
        print(f"使用数据文件: {character_data_file}")
        
        # 创建用户消息
        user_message = {
            'role': 'user',
            'content': text
        }
        
        # 添加到全局数据
        global data
        data.append(user_message)
        
        # 保存到角色对应的聊天记录文件
        from tool.data_saver import save_message_to_chat_data
        save_message_to_chat_data(text, 'user', character_data_file)
        
        # 创建并添加用户消息卡片
        user_label = CopyLabel(text=text, message_role='user', on_double_tap_callback=self._handle_user_message_double_tap)
        user_label.bind(on_selection=self.open_context_menu)
        self.chat_history_layout.add_widget(user_label)
        
        # 清空输入框
        self.message_input.text = ""
        
        # 保存最后发送的用户消息（用于API失败时重试）
        self._last_user_message = text
        
        # 滚动到底部显示新消息
        Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)
        
        # 使用异步API调用获取AI回复
        self._get_ai_response_async(text)


    # 处理上下文菜单点击：复制或剪切
    def click_item_context_menu(
            self, type_click: str, instance_label: CopyLabel
    ) -> None:
        Clipboard.copy(instance_label.text)  # 先把文本复制到剪贴板

        if type_click == "copy":
            print("已复制到剪贴板")  # 使用打印代替toast
        elif type_click == "cut":
            # 从界面中移除该标签（剪切）
            self.chat_history_layout.remove_widget(instance_label)
            print("已剪切到剪贴板")  # 使用打印代替toast
        if self.context_menu:
            self.context_menu.dismiss()  # 关闭菜单

    def _show_loading_indicator(self, message="AI正在思考中..."):
        """显示加载指示器"""
        if self.loading_popup:
            return
            
        # 创建加载布局
        loading_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(20),
            padding=dp(30),
            size_hint=(None, None),
            size=(dp(250), dp(150))
        )
        
        # 添加加载标签
        loading_label = Label(
            text=message,
            font_size='16sp',
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(30)
        )
        
        # 创建不确定进度条（循环动画）
        progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(10)
        )
        
        # 添加动画效果
        from kivy.animation import Animation
        anim = Animation(value=100, duration=2.0) + Animation(value=0, duration=0.1)
        anim.repeat = True
        anim.start(progress_bar)
        
        loading_layout.add_widget(loading_label)
        loading_layout.add_widget(progress_bar)
        
        # 创建模态弹窗
        self.loading_popup = ModalView(
            size_hint=(None, None),
            size=(dp(300), dp(200)),
            background_color=(0.2, 0.2, 0.2, 0.9),
            auto_dismiss=False
        )
        self.loading_popup.add_widget(loading_layout)
        self.loading_popup.open()
        
        # 禁用输入框
        self.message_input.disabled = True
    
    def _show_chat_loading_indicator(self):
        """在聊天区域显示加载圈"""
        # 创建加载指示器布局
        self.loading_indicator = BoxLayout(
            orientation='horizontal',
            spacing=dp(10),
            size_hint_y=None,
            height=dp(50),
            padding=[dp(20), dp(10), dp(20), dp(10)]
        )
        
        # 创建自定义圆形加载器
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, Ellipse, Line
        from kivy.animation import Animation
        from kivy.clock import Clock
        
        class CircularLoader(Widget):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.size_hint = (None, None)
                self.size = (dp(30), dp(30))
                self.rotation = 0
                self.draw_circle()
                self.start_animation()
            
            def draw_circle(self):
                with self.canvas:
                    Color(0.3, 0.3, 0.3, 0.3)  # 背景圆圈
                    Ellipse(pos=self.pos, size=self.size)
                    Color(0.2, 0.6, 1, 1)  # 进度颜色
                    Line(circle=(self.center_x, self.center_y, self.width/2 - 2), 
                         width=3, cap='round', dash_length=8, dash_offset=0)
            
            def start_animation(self):
                # 旋转动画
                anim = Animation(rotation=self.rotation + 360, duration=1.0)
                anim.bind(on_complete=lambda *args: self.start_animation())
                anim.start(self)
                
                # 更新画布
                self.clock_event = Clock.schedule_interval(self.update_canvas, 0.1)
            
            def update_canvas(self, dt):
                self.canvas.clear()
                with self.canvas:
                    Color(0.3, 0.3, 0.3, 0.3)  # 背景圆圈
                    Ellipse(pos=self.pos, size=self.size)
                    Color(0.2, 0.6, 1, 1)  # 进度颜色
                    # 创建旋转的进度圆圈
                    Line(circle=(self.center_x, self.center_y, self.width/2 - 2), 
                         width=3, cap='round', dash_length=8, dash_offset=self.rotation/10)
        
        # 创建加载器实例
        self.circular_loader = CircularLoader()
        
        # 添加加载文字
        loading_label = Label(
            text="AI正在思考中... ",
            font_size='14sp',
            color=(0.4, 0.6, 0.9, 1),  # 柔和的蓝色
            size_hint_y=None,
            height=dp(30),
            font_name=fonts.FONT_NAME  # 使用常量引用字体
        )
        
        self.loading_indicator.add_widget(self.circular_loader)
        self.loading_indicator.add_widget(loading_label)
        
        # 添加到聊天区域
        self.chat_history_layout.add_widget(self.loading_indicator)
        
        # 滚动到底部
        Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)
        
        # 禁用输入框
        self.message_input.disabled = True
    
    def _hide_loading_indicator(self):
        """隐藏加载指示器"""
        if hasattr(self, 'loading_indicator') and self.loading_indicator:
            # 停止动画和清理资源
            if hasattr(self, 'circular_loader') and self.circular_loader:
                # 停止动画
                from kivy.animation import Animation
                Animation.cancel_all(self.circular_loader)
                if hasattr(self.circular_loader, 'clock_event'):
                    Clock.unschedule(self.circular_loader.clock_event)
            self.chat_history_layout.remove_widget(self.loading_indicator)
            self.loading_indicator = None
            self.circular_loader = None
        
        # 重新启用输入框
        self.message_input.disabled = False
    
    def _show_error_message(self, message):
        """显示错误提示消息"""
        # 隐藏加载指示器（如果有）
        self._hide_loading_indicator()
        
        # 创建错误消息
        error_message = {
            'role': 'system',
            'content': f"[错误] {message}"
        }
        
        # 添加到全局数据
        global data
        data.append(error_message)
        
        # 创建并添加错误消息卡片（系统错误消息不需要双击删除功能）
        error_label = CopyLabel(text=f"[错误] {message}", message_role='system')
        error_label.bind(on_selection=self.open_context_menu)
        self.chat_history_layout.add_widget(error_label)
        
        # 滚动到底部
        Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)
    
    def _get_ai_response_async(self, user_message):
        """异步获取AI回复"""
        if not self.async_client:
            # 如果没有异步客户端，显示提示信息
            self._show_error_message("AI服务未配置，请检查配置")
            return
        
        # 在聊天区域显示加载圈
        self._show_chat_loading_indicator()
        
        # 准备历史消息上下文
        message_history = []
        context_length = getattr(self, 'current_context_length', 50)  # 从配置读取，默认50
        for item in data[-context_length:]:  # 使用配置文件中的context_length值
            if isinstance(item, dict) and 'role' in item and 'content' in item:
                message_history.append({
                    'role': item['role'],
                    'content': item['content']
                })
        
        # 使用弱引用避免循环引用
        app_ref = weakref.ref(self)
        
        def message_callback(success, response, error_msg=None):
            # 在主线程中处理结果
            app = app_ref()
            if app:
                Clock.schedule_once(lambda dt: app._handle_ai_response(success, response, error_msg), 0)
        
        # 异步调用API - 传入当前选择的模型
        try:
            self.async_client.send_message_async(
                user_message, 
                message_history, 
                message_callback,
                model=self.current_model  # 使用当前选择的模型
            )
        except Exception as error:
            error_msg = str(error)
            Clock.schedule_once(lambda dt: self._handle_ai_response(False, "", error_msg), 0)
    
    def _handle_ai_response(self, success, response, error_msg):
        """处理AI回复结果"""
        print(f"处理AI回复结果 - success: {success}, response长度: {len(response) if response else 0}, error_msg: {error_msg}")
        
        # 隐藏加载指示器
        self._hide_loading_indicator()
        
        if success and response:
            # 过滤AI回复，移除markdown和emoji
            try:
                from tool.simple_text_filter import SimpleTextFilter
                response = SimpleTextFilter.clean_text(response, remove_markdown=True, remove_emoji=True)
                print(f"AI回复已过滤 - 过滤后长度: {len(response)}")
            except Exception as e:
                print(f"过滤AI回复时出错: {e}")
                # 如果过滤失败，仍然使用原始回复
            # 获取当前角色的数据文件路径
            current_character = self.character_manager.get_current_character()
            if current_character and current_character != "默认角色":
                # 查找角色对应的数据文件 - 从配置文件获取完整角色信息
                character_data_file = None
                try:
                    config = config_manager._config
                    
                    if "characters" in config.get("app", {}):
                        for char in config["app"]["characters"]:
                            if char['name'] == current_character:
                                data_file = char.get('data_file', f"data/chat_history_{current_character}.json")
                                # 确保使用完整路径，特别是在移动端
                                if not os.path.isabs(data_file):
                                    character_data_file = os.path.join(get_storage_path(), data_file)
                                else:
                                    character_data_file = data_file
                                break
                except Exception as e:
                    print(f"读取角色配置时出错: {e}")
                
                if not character_data_file:
                    character_data_file = os.path.join(get_storage_path(), f"data/chat_history_{current_character}.json")
            else:
                # 如果没有角色或默认角色，使用默认文件
                character_data_file = os.path.join(get_storage_path(), "data/chat_data.json")
            
            # 创建AI回复消息
            ai_message = {
                'role': 'assistant',
                'content': response
            }
            
            # 添加到全局数据
            global data
            data.append(ai_message)
            
            # 保存到角色对应的聊天记录文件
            from tool.data_saver import save_message_to_chat_data
            save_message_to_chat_data(response, 'assistant', character_data_file)
            
            # 创建并添加AI回复卡片
            ai_label = CopyLabel(text=response, message_role='assistant', on_double_tap_callback=self._handle_ai_message_double_tap)
            ai_label.bind(on_selection=self.open_context_menu)
            self.chat_history_layout.add_widget(ai_label)
            
            # 滚动到底部
            Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)
            
        else:
            # 更友好的错误提示
            if error_msg and "None" not in str(error_msg):
                error_text = f"AI暂时无法回复: {error_msg}"
            else:
                error_text = "AI服务暂时不可用，请稍后再试～"
            
            # 显示错误提示

            
            # 创建一个友好的错误消息显示在聊天中
            error_message = {
                'role': 'system',
                'content': f"[警告] {error_text}"
            }
            
            # 添加到聊天界面（系统错误消息支持双击重发功能）
            error_label = CopyLabel(text=error_message['content'], message_role='system', on_double_tap_callback=self._handle_error_message_double_tap)
            error_label.bind(on_selection=self.open_context_menu)
            self.chat_history_layout.add_widget(error_label)
            
            # 滚动到底部
            Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)

    # 打开上下文菜单（当文本被选中时调用）
    def open_context_menu(self, instance_label: CopyLabel, *args) -> None:
        instance_label.text_color = "black"  # 选中后把文本颜色设为黑色
        menu_items = [
            {
                "text": "Copy text",
                "on_release": lambda: self.click_item_context_menu(
                    "copy", instance_label
                ),
            },
            {
                "text": "Cut text",
                "on_release": lambda: self.click_item_context_menu(
                    "cut", instance_label
                ),
            },
        ]
        # 创建并打开 MDDropdownMenu，caller 为被选中的标签
        self.context_menu = MDDropdownMenu(
            caller=instance_label, items=menu_items, width_mult=3
        )
        self.context_menu.open()


    def _handle_user_message_double_tap(self, instance, *args):
        """处理用户消息双击事件 - 弹出确认对话框后撤回本回合对话"""
        print(f"用户消息被双击: {instance.text}")
        print(f"实例类型: {type(instance)}")
        print(f"是否有message_role属性: {hasattr(instance, 'message_role')}")
        if hasattr(instance, 'message_role'):
            print(f"message_role值: {instance.message_role}")
        print("处理函数被调用！")
        
        # 创建确认对话框
        from kivy.uix.label import Label
        dialog = MDDialog(
            MDDialogHeadlineText(
                text="",
            ),
            MDDialogContentContainer(
                Label(
                    text="确定要撤回这条对话吗？\n这将删除您的问题和AI的回复。",
                    font_name=fonts.FONT_NAME,
                    font_size="16sp",
                    halign="center",
                    color=(0.2, 0.2, 0.2, 1),
                    size_hint_y=None,
                    height="60dp"
                )
            ),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonIcon(icon="content-copy"),
                    on_release=lambda x: self._copy_user_message(instance, dialog),
                    style="text"
                ),
                MDButton(
                    MDButtonIcon(icon="delete"),
                    on_release=lambda x: self._confirm_withdraw_dialog(instance, dialog),
                    style="text"
                ),
                MDButton(
                    MDButtonIcon(icon="close"),
                    on_release=lambda x: dialog.dismiss(),
                    style="text"
                )
            )
        )
        dialog.open()
    
    def _copy_user_message(self, instance, dialog):
        """复制用户消息到剪贴板"""
        dialog.dismiss()
        Clipboard.copy(instance.text)
        
        # 显示复制成功的提示
        from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
        
        snackbar = MDSnackbar(
            MDSnackbarText(
                text="用户消息已复制到剪贴板",
            ),
            y=dp(24),
            pos_hint={'center_x': 0.5},
            size_hint_x=0.8,
            duration=0.5,  # 缩短显示时间为1.5秒
        )
        snackbar.open()
        print(f"用户消息已复制: {instance.text[:50]}...")

    def _confirm_withdraw_dialog(self, instance, dialog):
        """确认撤回对话框"""
        dialog.dismiss()
        
        # 找到该用户消息在聊天布局中的索引
        children = list(self.chat_history_layout.children)
        try:
            user_index = children.index(instance)
            print(f"找到用户消息在索引位置: {user_index}")
            
            # 查找对应的AI回复（在用户消息之后）
            ai_reply = None
            ai_index = None
            for i in range(user_index - 1, -1, -1):  # 从用户消息的前一个开始查找
                child = children[i]
                if isinstance(child, CopyLabel) and hasattr(child, 'message_role') and child.message_role == 'assistant':
                    ai_reply = child
                    ai_index = i
                    break
            
            # 从界面移除用户消息和AI回复
            self.chat_history_layout.remove_widget(instance)
            if ai_reply:
                self.chat_history_layout.remove_widget(ai_reply)
                print(f"移除了用户消息和AI回复")
            else:
                print(f"只移除了用户消息，未找到对应的AI回复")
            
            # 从数据中也移除
            global data
            # 找到对应的数据索引并移除
            user_found = False
            ai_found = False
            new_data = []
            
            for item in data:
                if (item.get('role') == 'user' and item.get('content') == instance.text and not user_found):
                    user_found = True
                    continue  # 跳过该用户消息
                elif (user_found and item.get('role') == 'assistant' and not ai_found and ai_reply):
                    ai_found = True
                    continue  # 跳过对应的AI回复
                new_data.append(item)
            
            data = new_data
            
            # 保存更新后的数据到文件
            current_character = self.character_manager.get_current_character()
            if current_character and current_character != "默认角色":
                # 获取角色的完整数据文件路径
                character_data_file = None
                try:
                    config = config_manager._config
                    
                    if "characters" in config.get("app", {}):
                        for char in config["app"]["characters"]:
                            if char['name'] == current_character:
                                data_file = char.get('data_file', f"data/chat_history_{current_character}.json")
                                # 确保使用完整路径，特别是在移动端
                                if not os.path.isabs(data_file):
                                    character_data_file = os.path.join(get_storage_path(), data_file)
                                else:
                                    character_data_file = data_file
                                break
                except Exception as e:
                    print(f"获取角色数据文件路径时出错: {e}")
                
                if not character_data_file:
                    character_data_file = os.path.join(get_storage_path(), f"data/chat_history_{current_character}.json")
            else:
                character_data_file = os.path.join(get_storage_path(), "data/chat_data.json")
            
            import json
            with open(character_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print("对话回合已撤回")
            
        except ValueError:
            print("未找到用户消息在布局中的位置")
    
    def _handle_ai_message_double_tap(self, instance, *args):
        """处理AI消息双击事件 - 弹出重新加载选项对话框"""
        print(f"AI消息被双击: {instance.text}")
        print(f"实例类型: {type(instance)}")
        print(f"是否有message_role属性: {hasattr(instance, 'message_role')}")
        if hasattr(instance, 'message_role'):
            print(f"message_role值: {instance.message_role}")
        print("处理函数被调用！")
        
        # 添加更多调试信息
        print(f"所有参数: {args}")
        print(f"chat_history_layout中的子组件数量: {len(self.chat_history_layout.children)}")
        print(f"instance的父组件: {instance.parent}")
        print(f"instance的父组件类型: {type(instance.parent) if instance.parent else 'None'}")
        
        # 找到该AI消息在聊天布局中的索引
        children = list(self.chat_history_layout.children)
        
        # 打印所有子组件的详细信息
        print("所有子组件详情:")
        for i, child in enumerate(children):
            if hasattr(child, 'message_role'):
                print(f"  索引 {i}: 角色={child.message_role}, 内容={child.text[:50]}...")
            else:
                print(f"  索引 {i}: 无message_role属性, 类型={type(child)}")
        try:
            ai_index = children.index(instance)
            print(f"找到AI消息在索引位置: {ai_index}")
            
            # 直接创建编辑选项对话框（不需要查找用户问题）
            from kivy.uix.label import Label
            dialog = MDDialog(
                MDDialogHeadlineText(
                    text="",
                ),
                MDDialogContentContainer(
                    Label(
                        text="您想要如何操作这条AI回复？",
                        font_name=fonts.FONT_NAME,
                        font_size="16sp",
                        halign="center",
                        color=(0.2, 0.2, 0.2, 1),
                        size_hint_y=None,
                        height="40dp"
                    )
                ),
                MDDialogButtonContainer(
                    MDButton(
                        MDButtonIcon(icon="content-copy"),
                        on_release=lambda x: self._copy_ai_response(instance, dialog),
                        style="text"
                    ),
                    MDButton(
                        MDButtonIcon(icon="pencil"),
                        on_release=lambda x: self._edit_ai_response(instance, dialog),
                        style="text"
                    ),
                    MDButton(
                        MDButtonIcon(icon="close"),
                        on_release=lambda x: dialog.dismiss(),
                        style="text"
                    )
                )
            )
            dialog.open()
                
        except ValueError:
            print("未找到AI消息在布局中的位置")
    
    def _regenerate_ai_response(self, instance, user_question, dialog):
        """重新生成AI回复"""
        dialog.dismiss()
        
        # 从界面移除旧的AI回复
        self.chat_history_layout.remove_widget(instance)
        
        # 从数据中移除旧的AI回复
        global data
        # 找到对应的数据索引并移除AI回复
        user_found = False
        new_data = []
        
        for item in data:
            if (item.get('role') == 'user' and item.get('content') == user_question.text and not user_found):
                user_found = True
                new_data.append(item)  # 保留用户消息
            elif user_found and item.get('role') == 'assistant' and item.get('content') == instance.text:
                # 跳过旧的AI回复，不添加到新数据中
                continue
            else:
                new_data.append(item)
        
        data = new_data
        
        # 让AI重新思考这个问题
        self._get_ai_response_async(user_question.text)
        
        print("AI正在重新思考该回合对话")
    
    def _copy_ai_response(self, instance, dialog):
        """复制AI回复内容"""
        dialog.dismiss()
        
        # 复制AI回复到剪贴板
        Clipboard.copy(instance.text)
        
        # 显示提示
        from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
        
        snackbar = MDSnackbar(
            MDSnackbarText(
                text="AI回复已复制到剪贴板",
            ),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.8,
            duration=0.5,  # 缩短显示时间为1.5秒
        )
        snackbar.open()
        
        print("AI回复已复制到剪贴板")
    
    def _edit_ai_response(self, instance, dialog):
        """编辑AI回复内容"""
        dialog.dismiss()
        
        # 创建编辑对话框
        from kivy.uix.textinput import TextInput
        from kivymd.uix.dialog import MDDialog, MDDialogButtonContainer, MDDialogContentContainer, MDDialogHeadlineText
        
        # 创建文本输入框
        text_input = TextInput(
            text=instance.text,
            multiline=True,
            size_hint_y=None,
            height=dp(200),
            font_name=fonts.FONT_NAME,
            font_size="16sp"
        )
        
        edit_dialog = MDDialog(
            MDDialogHeadlineText(
                text="",
            ),
            MDDialogContentContainer(
                text_input
            ),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonIcon(icon="close"),
                    on_release=lambda x: edit_dialog.dismiss(),
                    style="text"
                ),
                MDButton(
                    MDButtonIcon(icon="check"),
                    on_release=lambda x: self._save_edited_response(instance, text_input.text, edit_dialog),
                    style="text"
                )
            )
        )
        edit_dialog.open()
        
        print("打开AI回复编辑对话框")
    
    def _save_edited_response(self, instance, new_text, dialog):
        """保存编辑后的AI回复"""
        dialog.dismiss()
        
        if not new_text.strip():
            # 显示空内容提示
            from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
            snackbar = MDSnackbar(
                MDSnackbarText(
                    text="回复内容不能为空",
                ),
                y=dp(24),
                pos_hint={"center_x": 0.5},
                size_hint_x=0.8,
                duration=2.0,  # 错误提示稍微长一点
            )
            snackbar.open()
            return
        
        # 更新界面上的文本
        old_text = instance.text
        instance.text = new_text
        
        # 更新数据
        global data
        for item in data:
            if item.get('role') == 'assistant' and item.get('content') == old_text:
                item['content'] = new_text
                break
        
        # 保存到文件
        current_character = self.character_manager.get_current_character()
        if current_character and current_character != "默认角色":
            # 获取角色的完整数据文件路径
            character_data_file = None
            try:
                config = config_manager._config
                
                if "characters" in config.get("app", {}):
                    for char in config["app"]["characters"]:
                        if char['name'] == current_character:
                            data_file = char.get('data_file', f"data/chat_history_{current_character}.json")
                            # 确保使用完整路径，特别是在移动端
                            if not os.path.isabs(data_file):
                                character_data_file = os.path.join(get_storage_path(), data_file)
                            else:
                                character_data_file = data_file
                            break
            except Exception as e:
                print(f"获取角色数据文件路径时出错: {e}")
            
            if not character_data_file:
                character_data_file = os.path.join(get_storage_path(), f"data/chat_history_{current_character}.json")
        else:
            character_data_file = os.path.join(get_storage_path(), "data/chat_data.json")
        
        import json
        with open(character_data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 显示成功提示
        from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
        snackbar = MDSnackbar(
            MDSnackbarText(
                text="AI回复已更新并保存",
            ),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.8,
            duration=0.5,  # 缩短显示时间为1.5秒
        )
        snackbar.open()
        
        print(f"AI回复已更新: {old_text[:50]}... -> {new_text[:50]}...")

    def _load_current_config(self):
        """加载当前配置到变量中"""
        try:
            # 获取配置项
            self.current_base_url = config_manager.get("openai.base_url", "")
            self.current_api_key = config_manager.get("openai.api_key", "")
            self.current_context_length = config_manager.get("app.context_length", 4096)
            self.current_available_models = config_manager.get("app.available_models", [])
            
            # 刷新模型列表显示（仅当UI组件已创建时）
            if hasattr(self, 'models_list_layout') and hasattr(self, '_refresh_models_list'):
                self._refresh_models_list()
            
        except Exception as e:
            print(f"加载配置文件时出错: {e}")
            # 设置默认值
            self.current_base_url = ""
            self.current_api_key = ""
            self.current_context_length = 4096
            self.current_available_models = []
            
            # 刷新模型列表显示（仅当UI组件已创建时）
            if hasattr(self, 'models_list_layout') and hasattr(self, '_refresh_models_list'):
                self._refresh_models_list()

    def _save_settings(self):
        """保存设置到config.json"""
        try:
            # 更新配置项
            config_manager.set("openai.base_url", self.base_url_field.text.strip())
            config_manager.set("openai.api_key", self.api_key_field.text.strip())
            
            # 解析上下文长度
            try:
                context_length = int(self.context_length_field.text.strip())
                config_manager.set("app.context_length", context_length)
            except ValueError:
                # 显示错误提示
                from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
                snackbar = MDSnackbar(
                    MDSnackbarText(
                        text="上下文长度必须是数字",
                    ),
                    y=dp(24),
                    pos_hint={"center_x": 0.5},
                    size_hint_x=0.8,
                    duration=2.0,  # 错误提示稍微长一点
                )
                snackbar.open()
                return
            
            # 直接从current_available_models获取模型列表（卡片列表中的模型）
            config_manager.set("app.available_models", self.current_available_models.copy())
            
            # 删除保存成功提示，不再显示小tip
            pass
            
            # 关闭设置抽屉
            self.settings_drawer.dismiss()
            
            print("设置已保存到config.json")
            
        except Exception as e:
            print(f"保存设置时出错: {e}")
    
    def _handle_error_message_double_tap(self, instance, *args):
        """处理错误消息双击事件 - 重新发送之前的失败消息"""
        print(f"错误消息被双击: {instance.text}")
        print(f"最后发送的用户消息: {self._last_user_message}")
        
        if self._last_user_message:
            # 移除错误消息卡片
            self.chat_history_layout.remove_widget(instance)
            
            # 重新发送之前的消息
            print(f"正在重新发送消息: {self._last_user_message}")
            self._get_ai_response_async(self._last_user_message)
            
            # 显示重新发送的提示
            from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
            snackbar = MDSnackbar(
                MDSnackbarText(
                    text="正在重新发送消息...",
                ),
                y=dp(24),
                pos_hint={"center_x": 0.5},
                size_hint_x=0.8,
                duration=0.5,  # 缩短显示时间为1.5秒
            )
            snackbar.open()
        else:
            print("没有可重新发送的消息")
            # 显示错误提示
            from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
            snackbar = MDSnackbar(
                MDSnackbarText(
                    text="保存设置失败",
                ),
                y=dp(24),
                pos_hint={"center_x": 0.5},
                size_hint_x=0.8,
                duration=2.0,  # 错误提示稍微长一点
            )
            snackbar.open()

    def on_stop(self):
        """应用关闭时清理资源"""
        self.cleanup_resources()

    def cleanup_resources(self):
        """统一清理所有资源"""
        print("开始清理应用资源...")
        
        # 关闭所有打开的对话框
        if hasattr(self, 'add_model_dialog') and self.add_model_dialog:
            self.add_model_dialog.dismiss()
            self.add_model_dialog = None
        
        # 关闭菜单
        if hasattr(self, 'context_menu') and self.context_menu:
            self.context_menu.dismiss()
            self.context_menu = None
        
        if hasattr(self, 'theme_menu') and self.theme_menu:
            self.theme_menu.dismiss()
            self.theme_menu = None
        
        if hasattr(self, 'model_menu') and self.model_menu:
            self.model_menu.dismiss()
            self.model_menu = None
        
        # 停止所有动画
        if hasattr(self, 'circular_loader') and self.circular_loader:
            from kivy.animation import Animation
            Animation.cancel_all(self.circular_loader)
            if hasattr(self.circular_loader, 'clock_event'):
                Clock.unschedule(self.circular_loader.clock_event)
        
        # 取消所有防抖调度
        for schedule_name, schedule in self._debounce_schedules.items():
            if schedule:
                Clock.unschedule(schedule)
        self._debounce_schedules.clear()
        
        # 关闭抽屉
        if hasattr(self, 'character_drawer') and self.character_drawer.parent:
            self.character_drawer.dismiss()
        
        if hasattr(self, 'settings_drawer') and self.settings_drawer.parent:
            self.settings_drawer.dismiss()
        
        # 清理中央输入框
        if hasattr(self, 'center_card_input') and self.center_card_input:
            self._remove_center_card()
        
        # 清理异步客户端
        if self.async_client:
            stop_async_api_client()
            self.async_client = None
        
        print("应用资源清理完成")

    def check_android_storage(self):
        """检查安卓存储权限并确保目录存在"""
        try:
            if is_android():
                # 安卓平台获取存储路径
                storage_path = get_storage_path()
                data_dir = os.path.join(storage_path, "data")
                
                # 确保目录存在
                ensure_dir(data_dir)
                print(f"安卓存储检查完成: {storage_path}")
                
                # 申请存储权限
                request_android_storage_permission()
                
        except Exception as e:
            print(f"安卓存储检查出错: {e}")



def main():
    """应用主入口函数"""
    Example().run()

# 启动应用
if __name__ == '__main__':
    main()