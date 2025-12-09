from kivy.metrics import sp, dp
from kivy.core.window import Window
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.label import MDLabel
from kivy.uix.label import Label
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.widget import MDWidget
from kivymd.uix.card import MDCard
from kivy.clock import Clock
from kivy.graphics import Color, Line

from . import fonts

def toast(text):
    MDSnackbar(
        MDSnackbarText(text=text),
        y=sp(24),
        pos_hint={"center_x": 0.5},
        size_hint_x=0.3,
    ).open()

class CopyLabel(MDBoxLayout):
    def __init__(self, *args, message_role="assistant", on_double_tap_callback=None, **kwargs):
        # 移除text参数，避免冲突
        text_content = kwargs.pop('text', '')
        super().__init__(*args, **kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.adaptive_height = True
        self.message_role = message_role  # 添加角色标识："user" 或 "assistant"
        self._text_content = text_content  # 存储文本内容
        self._on_double_tap_callback = on_double_tap_callback  # 双击回调函数
        
        # 添加双击事件支持
        self.register_event_type('on_double_tap')
        self.register_event_type('on_selection')  # 添加选择事件支持
        self._last_touch_time = 0
        self._double_tap_time = 0.3  # 双击时间间隔（秒）
        
        # 获取主题信息
        from kivymd.app import MDApp
        theme_cls = MDApp.get_running_app().theme_cls
        
        # 创建卡片包装（自适应宽度）
        card = MDCard(
            size_hint=(None, None),
            padding=dp(12),
            radius=[8],  # 圆角
            elevation=1,  # 轻微阴影
        )
        
        # 根据角色设置不同的边框样式和对齐方式
        if self.message_role == "user":
            # 用户消息：使用主题主色调边框，右对齐
            card.theme_line_color = "Custom"
            card.line_color = theme_cls.primaryColor  # 使用主题主色调
            card.style = "outlined"  # 边框样式
            card.halign = "right"
            
            # 用户消息：右对齐，左边用弹性空间推进
            self.add_widget(MDWidget(size_hint_x=1))  # 弹性占位
            self.add_widget(card)
            
        else:
            # AI消息：使用主题边框色，左对齐
            card.theme_line_color = "Custom"
            card.line_color = theme_cls.outlineColor  # 使用主题边框颜色
            card.style = "outlined"  # 边框样式
            card.halign = "left"
            
            # AI消息：左对齐，右边用弹性空间
            self.add_widget(card)
            self.add_widget(MDWidget(size_hint_x=1))  # 弹性占位
        
        # 创建标签（使用Kivy原生Label，避免MDLabel的字体覆盖问题）
        label = Label(
            text="",  # 先为空
            font_name=fonts.FONT_NAME,
            font_size=sp(14),
            markup=True,
            size_hint_y=None,
            height=dp(20),
            # 不预设text_size，让短文字保持自然宽度
        )
        
        # 字体已成功设置（移除调试信息）
        
        # 设置文本颜色和对齐方式
        if self.message_role == "user":
            # 用户消息：使用深色字体，确保在浅色背景下可见
            label.color = (0.1, 0.1, 0.1, 1)  # 深灰色，接近黑色
            label.halign = "right"
        else:
            # AI消息：使用更深的颜色，提高对比度
            label.color = (0.05, 0.05, 0.05, 1)  # 深黑色，确保清晰可读
            label.halign = "left"
        
        card.add_widget(label)
        self.label = label
        self.card = card
        
        # 延迟设置文本和高度，确保字体加载完成
        Clock.schedule_once(self._setup_text_and_height, 0.1)
        
        # 立即绑定触摸事件，确保事件捕获
        print("正在绑定触摸事件...")
        self.bind(on_touch_down=self._on_touch_down)
        print("触摸事件绑定完成")
        
        # 监听窗口大小变化，动态调整消息卡片宽度
        Window.bind(on_resize=self._on_window_resize)
    
    def _on_touch_down(self, instance, touch):
        """处理触摸事件，检测双击"""
        print(f"触摸事件触发 - 位置: {touch.pos}, 组件位置: {self.pos}, 大小: {self.size}")
        if self.collide_point(*touch.pos):
            print(f"触摸点在组件内！消息角色: {self.message_role}, 内容: {self._text_content[:50]}...")
            import time
            current_time = time.time()
            print(f"当前时间: {current_time}, 上次触摸时间: {self._last_touch_time}, 双击时间间隔: {self._double_tap_time}")
            
            # 检查是否为双击
            if current_time - self._last_touch_time < self._double_tap_time:
                # 双击事件触发
                print(f"检测到双击事件！消息内容: {self._text_content[:50]}...")
                
                # 如果有特定的双击回调函数，优先使用它（用于用户和AI消息的特定处理）
                if self._on_double_tap_callback:
                    print(f"正在调用特定的双击回调函数: {self._on_double_tap_callback}")
                    self._on_double_tap_callback(self)
                    print("特定的双击回调函数调用完成")
                else:
                    # 如果没有特定回调，才触发通用的上下文菜单
                    print("触发通用的上下文菜单")
                    self.dispatch('on_selection', self)
                
                self.dispatch('on_double_tap', self)
                self._last_touch_time = 0  # 重置时间，避免连续触发
            else:
                # 单击事件 - 不执行任何操作，等待可能的第二次点击
                self._last_touch_time = current_time
                print(f"设置上次触摸时间: {self._last_touch_time}")
        return super().on_touch_down(touch)
    
    def on_double_tap(self, instance):
        """双击事件回调 - 供外部绑定使用"""
        pass
    
    def on_selection(self, instance):
        """选择事件回调 - 供外部绑定使用"""
        pass
    
    # 移除延迟绑定函数，改为立即绑定
    
    def _setup_text_and_height(self, dt):
        # 强制重新设置字体，确保自定义字体生效
        self.label.font_name = fonts.FONT_NAME
        
        # 设置文本内容
        self.label.text = self._text_content
        
        # 智能主题适配：根据主题模式调整字体颜色
        from kivymd.app import MDApp
        theme_cls = MDApp.get_running_app().theme_cls
        
        if theme_cls.theme_style == "Dark":
            # 深色模式：使用浅色字体确保可读性
            if self.message_role == "user":
                self.label.color = (0.9, 0.9, 0.9, 1)  # 浅灰色
            else:
                self.label.color = (0.95, 0.95, 0.95, 1)  # 更浅的灰色
        else:
            # 浅色模式：使用深色字体确保可读性
            if self.message_role == "user":
                self.label.color = (0.1, 0.1, 0.1, 1)  # 深灰色
            else:
                self.label.color = (0.05, 0.05, 0.05, 1)  # 更深的灰色
        
        # 更新纹理并获取实际尺寸
        self.label.texture_update()
        
        # 设置自适应宽度和高度
        text_width, text_height = self.label.texture_size
        
        # 计算卡片宽度：考虑完整布局约束，确保消息不会超出程序窗口边界
        # 1. 主容器左右padding：24dp + 24dp = 48dp (来自run.py)
        # 2. MDCard自身的左右padding：12dp + 12dp = 24dp
        # 3. 再留15%的安全边距
        total_margins = dp(48 + 24)  # 主容器边距 + MDCard内边距 = 72dp
        available_width = Window.width - total_margins
        max_width = available_width * 0.85  # 最终最大宽度限制
        card_width = min(text_width + dp(24), max_width)  # 24dp为MDCard左右内边距
        
        # 设置卡片和标签的宽度
        self.card.width = card_width
        self.label.width = card_width - dp(24)  # 减去内边距
        
        # 只有当文字需要换行时才设置text_size
        if text_width + dp(24) > max_width:
            # 长文字需要换行，重新计算高度
            self.label.text_size = (max_width - dp(24), None)
            self.label.valign = "top"
            # 重新获取换行后的实际高度
            self.label.texture_update()
            text_height = self.label.texture_size[1]
        else:
            # 短文字保持自然宽度，不强制换行
            self.label.text_size = (card_width - dp(24), None)
        
        # 设置高度 - 确保足够容纳所有文字
        self.label.height = text_height + dp(8)  # 增加垂直内边距
        self.card.height = self.label.height + dp(24)  # 卡片内边距
        self.height = self.card.height + dp(16)  # 整体间距
    
    def _on_window_resize(self, window, width, height):
        """窗口大小变化时重新计算消息卡片宽度"""
        if hasattr(self, 'label') and hasattr(self, 'card'):
            # 重新计算布局
            self._setup_text_and_height(0)
    
    def _update_height(self, dt):
        self.label.texture_update()
        
        # 获取文字实际尺寸
        text_width, text_height = self.label.texture_size
        
        # 计算自适应宽度：考虑完整布局约束
        # 1. 主容器左右padding：24dp + 24dp = 48dp (来自run.py)
        # 2. MDCard自身的左右padding：12dp + 12dp = 24dp
        # 3. 再留15%的安全边距
        total_margins = dp(48 + 24)  # 主容器边距 + MDCard内边距 = 72dp
        available_width = Window.width - total_margins
        max_width = available_width * 0.85  # 最终最大宽度限制
        card_width = min(text_width + dp(24), max_width)
        
        # 更新宽度和高度
        self.card.width = card_width
        self.label.width = card_width - dp(24)
        
        # 只有当文字需要换行时才设置text_size
        if text_width + dp(24) > max_width:
            # 长文字需要换行，重新计算高度
            self.label.text_size = (max_width - dp(24), None)
            self.label.valign = "top"
            # 重新获取换行后的实际高度
            self.label.texture_update()
            text_height = self.label.texture_size[1]
        else:
            # 短文字保持自然宽度，不强制换行
            self.label.text_size = (card_width - dp(24), None)
        
        # 设置高度 - 确保足够容纳所有文字
        self.label.height = text_height + dp(8)  # 增加垂直内边距
        self.card.height = self.label.height + dp(24)  # 卡片内边距
        self.height = self.card.height + dp(16)  # 整体间距
    
    @property
    def text(self):
        return self.label.text if hasattr(self, 'label') else self._text_content
    
    @text.setter
    def text(self, value):
        if hasattr(self, 'label'):
            self.label.text = value
            self._update_height(0)
        else:
            self._text_content = value

class ChatBubble(MDBoxLayout):
    
    """聊天气泡：左对齐（AI）或右对齐（用户）"""
    def __init__(self, text, is_user=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        # 调整padding确保消息不会超出窗口边界
        self.padding = [dp(8), dp(8), dp(8), dp(8)]  # 上下左右都有8dp间距
        self.spacing = dp(8)
        
        card_width = Window.width * 0.9
        
        # 获取主题信息，使用主题色而非固定颜色
        from kivymd.app import MDApp
        theme_cls = MDApp.get_running_app().theme_cls
        
        # 根据主题和角色设置背景色
        if is_user:
            # 用户消息：使用主题的主色调
            md_bg_color = theme_cls.primaryColor
        else:
            # AI消息：使用主题的卡片背景色
            md_bg_color = theme_cls.surfaceColor
        
        bubble = MDCard(
            size_hint=(None, None),
            padding=dp(12),
            radius=[12],
            elevation=1,
            md_bg_color=md_bg_color,
        )
        
        # 先创建空标签（支持主题适配）
        from kivymd.app import MDApp
        theme_cls = MDApp.get_running_app().theme_cls
        
        if theme_cls.theme_style == "Dark":
            # 深色模式：使用浅色字体
            text_color = (0.9, 0.9, 0.9, 1) if is_user else (0.95, 0.95, 0.95, 1)
        else:
            # 浅色模式：使用深色字体
            text_color = (0.1, 0.1, 0.1, 1) if is_user else (0.05, 0.05, 0.05, 1)
        
        label = MDLabel(
            text="",  # 先为空
            font_name=fonts.FONT_NAME,
            font_size=sp(14),
            color=text_color,  # 根据主题和角色设置颜色
            size_hint=(None, None),
            # 不预设width和text_size，让短文字保持自然宽度
        )
        
        bubble.add_widget(label)
        
        # 延迟 0.05 秒后设置文本（确保字体已加载）
        def set_text():
            label.text = text
            label.texture_update()
            
            # 获取文字实际尺寸
            text_width, text_height = label.texture_size
            
            # 计算自适应宽度：考虑完整布局约束
            # 1. 窗口总宽度
            # 2. 减去ChatBubble的左右padding：8dp + 8dp = 16dp
            # 3. 减去MDCard与弹性空间之间的spacing：8dp
            # 4. 减去MDCard自身的左右padding：12dp + 12dp = 24dp
            # 5. 再留15%的安全边距
            total_margins = dp(16 + 8 + 24)  # 48dp总边距
            available_width = Window.width - total_margins
            max_width = available_width * 0.85  # 最终最大宽度限制
            bubble_width = min(text_width + dp(24), max_width)
            
            # 设置宽度和高度
            bubble.width = bubble_width
            label.width = bubble_width - dp(24)
            
            # 只有当文字需要换行时才设置text_size
            if text_width + dp(24) > max_width:
                # 长文字需要换行，重新计算高度
                label.text_size = (max_width - dp(24), None)
                label.valign = "top"
                # 重新获取换行后的实际高度
                label.texture_update()
                text_height = label.texture_size[1]
            else:
                # 短文字保持自然宽度，不强制换行
                label.text_size = (bubble_width - dp(24), None)
            
            # 设置高度 - 确保足够容纳所有文字
            label.height = text_height + dp(8)  # 增加垂直内边距
            bubble.height = label.height + dp(24)  # 卡片内边距
            self.height = bubble.height + dp(16)  # 整体间距
        
        Clock.schedule_once(lambda dt: set_text(), 0.05)
        
        # 布局控制：用户消息右对齐，AI消息左对齐
        if is_user:
            # 用户消息：右对齐，左边用弹性空间推进
            self.add_widget(MDWidget(size_hint_x=1))  # 弹性占位
            self.add_widget(bubble)
        else:
            # AI消息：左对齐，右边用弹性空间
            self.add_widget(bubble)
            self.add_widget(MDWidget(size_hint_x=1))  # 弹性占位
        
        self.height = bubble.height + dp(16)  # 初始高度
        
        # 监听窗口大小变化，动态调整气泡宽度
        Window.bind(on_resize=self._on_window_resize)
    
    def _on_window_resize(self, window, width, height):
        """窗口大小变化时重新计算气泡宽度"""
        # 重新计算布局（延迟执行确保布局稳定）
        Clock.schedule_once(lambda dt: self._update_bubble_size(), 0.1)
    
    def _update_bubble_size(self):
        """重新计算气泡大小"""
        # 找到气泡和标签组件
        for child in self.children:
            if isinstance(child, MDCard):
                bubble = child
                for widget in bubble.children:
                    if isinstance(widget, MDLabel):
                        label = widget
                        
                        # 重新计算文字尺寸
                        label.texture_update()
                        text_width, text_height = label.texture_size
                        
                        # 重新计算自适应宽度：考虑完整布局约束
                        total_margins = dp(16 + 8 + 24)  # 48dp总边距
                        available_width = Window.width - total_margins
                        max_width = available_width * 0.85  # 最终最大宽度限制
                        bubble_width = min(text_width + dp(24), max_width)
                        
                        # 更新宽度和高度
                        bubble.width = bubble_width
                        label.width = bubble_width - dp(24)
                        
                        # 重新判断是否需要换行
                        if text_width + dp(24) > max_width:
                            label.text_size = (max_width - dp(24), None)
                            label.valign = "top"
                            label.texture_update()
                            text_height = label.texture_size[1]
                        else:
                            label.text_size = (bubble_width - dp(24), None)
                        
                        # 更新高度
                        label.height = text_height + dp(8)
                        bubble.height = label.height + dp(24)
                        self.height = bubble.height + dp(16)
                        break
                break