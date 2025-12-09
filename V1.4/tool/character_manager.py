#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色管理器模块
负责角色的加载、保存、选择和管理功能
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from kivymd.uix.button import MDIconButton, MDButton, MDButtonText, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogContentContainer,
    MDDialogButtonContainer
)
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivy.uix.label import Label
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import (
    MDListItem,
    MDListItemHeadlineText,
    MDListItemLeadingIcon,
    MDListItemSupportingText,
    MDListItemTrailingIcon
)
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.graphics import Line
from kivymd.uix.divider import MDDivider
from tool import fonts  # 导入字体模块
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.app import App


class CharacterManager:
    """角色管理器类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化角色管理器
        
        Args:
            config_path: 配置文件路径
        """
        from .platform_utils import get_storage_path
        self.config_path = config_path or os.path.join(get_storage_path(), "config", "config.json")
        self.characters: List[str] = []
        self.current_character: str = "默认角色"
        self.character_drawer = None
        self.character_list = None
        self.delete_character_btn = None
        self.callbacks = {}
        
    def load_characters_from_config(self) -> None:
        """从配置文件加载角色信息"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 获取角色列表
            if "characters" in config.get("app", {}) and config["app"]["characters"]:
                self.characters = [char["name"] for char in config["app"]["characters"]]
            else:
                # 如果配置文件中没有角色，使用默认值
                self.characters = ["默认角色", "AI助手", "翻译专家", "编程助手", "写作助手"]
            
            # 获取当前角色
            self.current_character = config.get("app", {}).get("current_character", "默认角色")
            
            # 如果当前角色不在角色列表中，使用第一个角色
            if self.current_character not in self.characters:
                self.current_character = self.characters[0] if self.characters else "默认角色"
                
            print(f"从配置文件加载角色: {self.characters}")
            print(f"当前角色: {self.current_character}")
            
        except Exception as e:
            print(f"从配置文件加载角色时出错: {e}")
            # 使用默认值
            self.characters = ["默认角色", "AI助手", "翻译专家", "编程助手", "写作助手"]
            self.current_character = "默认角色"
    
    def update_current_character_in_config(self, character_name: str) -> None:
        """更新配置文件中的当前角色"""
        try:
            # 读取当前配置文件
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新当前角色
            config["app"]["current_character"] = character_name
            
            # 更新元数据
            config["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 保存回文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
                
            print(f"配置文件中的当前角色已更新为: {character_name}")
            
        except Exception as e:
            print(f"更新当前角色配置时出错: {e}")
    
    def save_character_to_config(self, character_name: str) -> None:
        """将角色信息保存到配置文件并创建对应的对话记录文件"""
        try:
            # 读取当前配置文件
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 创建新角色配置
            new_character = {
                "name": character_name,
                "data_file": f"data/chat_history_{character_name}.json",
                "description": f"自定义角色: {character_name}",
                "icon": "account-circle-outline"  # 默认图标
            }
            
            # 添加到角色列表
            if "characters" not in config["app"]:
                config["app"]["characters"] = []
            
            # 检查是否已存在
            existing_chars = [char["name"] for char in config["app"]["characters"]]
            if character_name not in existing_chars:
                config["app"]["characters"].append(new_character)
                
                # 更新元数据
                config["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 保存回文件
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                
                # 创建对应的对话记录文件
                from .platform_utils import get_storage_path
                data_file_path = os.path.join(get_storage_path(), "data", f"chat_history_{character_name}.json")
                os.makedirs(os.path.dirname(data_file_path), exist_ok=True)
                
                # 创建空的对话记录文件
                with open(data_file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                
                print(f"角色 '{character_name}' 已添加到配置文件")
                print(f"对话记录文件已创建: {data_file_path}")
                
        except Exception as e:
            print(f"保存角色配置时出错: {e}")
    
    def remove_character_from_config(self, character_name: str) -> None:
        """从配置文件中移除角色并删除对应的对话记录文件"""
        try:
            # 读取当前配置文件
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 获取要删除的角色的数据文件路径
            data_file_path = None
            if "characters" in config.get("app", {}):
                for char in config["app"]["characters"]:
                    if char["name"] == character_name:
                        data_file_path = char.get("data_file")
                        break
                
                # 从角色列表中移除
                config["app"]["characters"] = [
                    char for char in config["app"]["characters"] 
                    if char["name"] != character_name
                ]
                
                # 更新元数据
                config["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 保存回文件
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                    
                print(f"角色 '{character_name}' 已从配置文件中移除")
                
                # 删除对应的对话记录文件
                if data_file_path:
                    try:
                        if os.path.exists(data_file_path):
                            os.remove(data_file_path)
                            print(f"对话记录文件已删除: {data_file_path}")
                    except Exception as e:
                        print(f"删除对话记录文件时出错: {e}")
                
        except Exception as e:
            print(f"删除角色配置时出错: {e}")
    
    def create_character_drawer_content(self, drawer_instance) -> None:
        """创建角色选择抽屉内容"""
        # 获取当前主题
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        theme_cls = app.theme_cls
        
        # 根据主题设置颜色
        if theme_cls.theme_style == "Dark":
            title_color = (0.9, 0.9, 0.9, 1)  # 浅色标题
            text_color_selected = theme_cls.primaryColor  # 主色调
            text_color_normal = (0.8, 0.8, 0.8, 1)  # 普通文本浅色
            bg_color_selected = (0.15, 0.15, 0.15, 1)  # 选中背景深色
            divider_color = (0.3, 0.3, 0.3, 0.5)  # 分隔线深色
        else:
            title_color = (0.2, 0.2, 0.2, 1)  # 深色标题
            text_color_selected = theme_cls.primaryColor  # 主色调
            text_color_normal = (0.2, 0.2, 0.2, 1)  # 普通文本深色
            bg_color_selected = (0.95, 0.98, 1, 1)  # 选中背景浅色
            divider_color = (0.8, 0.8, 0.8, 0.5)  # 分隔线浅色
        
        # 保存颜色供后续使用
        self.text_color_selected = text_color_selected
        self.text_color_normal = text_color_normal
        self.bg_color_selected = bg_color_selected
        self.divider_color = divider_color
        
        # 抽屉内容布局 - 使用MDBoxLayout并设置主题背景色
        from kivymd.uix.boxlayout import MDBoxLayout
        drawer_content = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16)],
            spacing=dp(12),
            md_bg_color=theme_cls.surfaceColor  # 使用主题表面颜色作为背景
        )
        
        # 抽屉标题 - 使用Kivy原生Label，适配KivyMD主题
        title_label = Label(
            text="角色选择",
            font_name=fonts.FONT_NAME,
            font_size=sp(18),  # 稍微减小字体大小
            color=title_color,  # 主题适配颜色
            size_hint_y=None,
            height=dp(28),  # 稍微减小高度
            text_size=(None, None),  # 移除固定text_size，让文字自然换行
            valign='center',
            halign='left',
            shorten=True,  # 如果文字太长，用省略号表示
            shorten_from='right'
        )
        drawer_content.add_widget(title_label)
        
        # 操作按钮区域 - 使用MDBoxLayout
        button_layout = MDBoxLayout(
            size_hint_y=None,
            height=dp(40),
            spacing=dp(8)
        )
        
         # 添加角色按钮 - 使用图标按钮
        add_btn = MDIconButton(
             icon="plus",
             on_release=lambda x: self.add_character(),
             size_hint=(1, None),
             height=dp(40),
             theme_icon_color="Custom",
             theme_text_color="Custom",
             text_color=theme_cls.primaryColor  # 使用主色调
         )
         
         # 删除角色按钮 - 使用图标按钮
        delete_btn = MDIconButton(
             icon="delete",
             on_release=lambda x: self.delete_current_character(),
             disabled=not self.current_character or self.current_character == "默认角色",
             size_hint=(1, None),
             height=dp(40),
             theme_icon_color="Custom",
             theme_text_color="Custom",
             text_color=(0.8, 0.2, 0.2, 1)  # 保持红色警告色
         )
        button_layout.add_widget(add_btn)
        button_layout.add_widget(delete_btn)
        drawer_content.add_widget(button_layout)
        
        # 分隔线 - 使用主题适配颜色
        divider = MDDivider()
        drawer_content.add_widget(divider)
        
        # 角色列表滚动区域 - 使用MDScrollView和MDBoxLayout
        scroll_view = MDScrollView()
        character_list = MDBoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        character_list.bind(minimum_height=character_list.setter('height'))
        scroll_view.add_widget(character_list)
        
        drawer_content.add_widget(scroll_view)
        
        # 添加到抽屉
        drawer_instance.add_widget(drawer_content)
        
        # 保存引用
        self.character_list = character_list
        self.delete_character_btn = delete_btn
        self.drawer_content = drawer_content
        self.theme_cls = theme_cls
        
        # 初始化角色列表
        self.refresh_character_list()
    
    def refresh_character_list(self) -> None:
        """刷新角色列表 - 使用主题适配颜色"""
        if not self.character_list:
            return
            
        # 清空现有列表
        self.character_list.clear_widgets()
        
        pass  # 移除调试信息
        
        # 获取主题颜色
        text_color_selected = getattr(self, 'text_color_selected', (0.2, 0.6, 1, 1))
        text_color_normal = getattr(self, 'text_color_normal', (0.2, 0.2, 0.2, 1))
        bg_color_selected = getattr(self, 'bg_color_selected', (0.95, 0.98, 1, 1))
        divider_color = getattr(self, 'divider_color', (0.8, 0.8, 0.8, 0.5))
        
        # 添加角色列表项 - 使用现代卡片设计
        for character in self.characters:
            # 创建角色卡片 - 使用MDCard
            character_card = MDCard(
                style="outlined" if character != self.current_character else "filled",
                padding=[dp(12), dp(8)],  # 减小内边距
                spacing=dp(8),  # 减小间距
                size_hint_y=None,
                height=dp(56),  # 适中的高度
                radius=[dp(10)],  # 稍微减小圆角
                on_release=lambda x, char=character: self.select_character(char),
                theme_bg_color="Custom",
                md_bg_color=bg_color_selected if character == self.current_character else (1, 1, 1, 0.8),
                theme_line_color="Custom",
                line_color=self.theme_cls.primaryColor if character == self.current_character else (0.8, 0.8, 0.8, 0.3),
                elevation=2 if character == self.current_character else 1
            )
            
            # 卡片内容布局 - 使用AnchorLayout确保完美垂直居中对齐
            card_content = AnchorLayout(anchor_x='left', anchor_y='center', size_hint_x=1, size_hint_y=1, padding=[dp(12), dp(8)])
            
            # 内部水平布局
            inner_layout = MDBoxLayout(orientation='horizontal', spacing=dp(12), size_hint_x=1, size_hint_y=None, height=dp(44))
            
            # 左侧图标 - 已移除，根据用户需求不显示图标
            
            # 角色信息区域 - 使用AnchorLayout确保文字垂直居中
            info_layout = AnchorLayout(anchor_x='left', anchor_y='center', size_hint_x=0.8, size_hint_y=None, height=dp(44))
            
            # 角色名称 - 使用Label并强制字体
            name_label = Label(
                text=character,
                font_name="LXGWWenKai",  # 直接使用字体名称
                font_size=sp(16),  # 适中的字体大小
                color=self.theme_cls.primaryColor if character == self.current_character else text_color_normal,
                halign="left",
                valign="center",  # 文字自身垂直居中
                shorten=True,  # 如果文字太长，用省略号表示
                shorten_from='right',
                bold=True,  # 加粗显示
                size_hint_x=1,
                size_hint_y=None,
                height=dp(24)  # 固定文字高度，确保居中效果
            )
            
            info_layout.add_widget(name_label)
            inner_layout.add_widget(info_layout)
            card_content.add_widget(inner_layout)
            character_card.add_widget(card_content)
            
            self.character_list.add_widget(character_card)
            
            # 添加间距而不是分隔线
            if character != self.characters[-1]:  # 不是最后一个项目
                spacing = Widget(size_hint_y=None, height=dp(8))
                self.character_list.add_widget(spacing)
    
    def _on_character_item_touch(self, instance, touch, character):
        """处理角色项点击事件"""
        if instance.collide_point(*touch.pos) and touch.button == 'left':
            self.select_character(character)
            return True
        return False
    
    def select_character(self, character: str) -> None:
        """选择角色"""
        self.current_character = character
        # 刷新列表显示
        self.refresh_character_list()
        
        # 触发回调
        if 'on_character_selected' in self.callbacks:
            self.callbacks['on_character_selected'](character)
        
        print(f"已切换到角色: {character}")
        
        # 更新配置文件中的当前角色
        self.update_current_character_in_config(character)
    
    def add_character(self) -> None:
        """添加新角色 - 使用KivyMD原生组件"""
        # 创建输入框 - 直接设置字体
        character_input = MDTextField(
            hint_text="请输入角色名称",
            mode="outlined",
            multiline=False,
            size_hint_x=1,
            font_size=sp(16)
        )
        
        # 直接设置输入框的字体属性
        character_input.font_name = "LXGWWenKai"
        
        # 调试信息：检查输入框字体设置
        print(f"添加角色输入框字体设置: {getattr(character_input, 'font_name', '未设置')}")
        print(f"LXGWWenKai字体是否注册: {'LXGWWenKai' in ['Roboto', 'RobotoThin', 'RobotoLight', 'RobotoMedium', 'RobotoBlack', 'Icons', 'LXGWWenKai']}")
        
        # 创建对话框 - 不显示标题，只显示内容
        dialog = MDDialog(
            MDDialogContentContainer(
                character_input,
                orientation="vertical",
                spacing=dp(16),
                padding=[dp(24), dp(24), dp(24), dp(16)]  # 调整内边距，顶部留出更多空间
            ),
            MDDialogButtonContainer(
                MDIconButton(
                    icon="close",
                    theme_icon_color="Custom",
                    icon_color=App.get_running_app().theme_cls.onSurfaceVariantColor,
                    md_bg_color=App.get_running_app().theme_cls.surfaceContainerHighColor,
                    on_release=lambda x: dialog.dismiss()
                ),
                MDIconButton(
                    icon="check",
                    theme_icon_color="Custom",
                    icon_color=App.get_running_app().theme_cls.primaryColor,
                    md_bg_color=App.get_running_app().theme_cls.primaryContainerColor,
                    on_release=lambda x: self._do_add_character(character_input.text, dialog)
                ),
                spacing="8dp"
            )
        )
        dialog.open()
    
    def _do_add_character(self, character_name: str, dialog: MDDialog) -> None:
        """执行添加角色"""
        character_name = character_name.strip()
        if character_name and character_name not in self.characters:
            self.characters.append(character_name)
            self.refresh_character_list()
            
            # 更新配置文件
            self.save_character_to_config(character_name)
            
            # 触发回调
            if 'on_character_added' in self.callbacks:
                self.callbacks['on_character_added'](character_name)
        
        dialog.dismiss()
    
    def delete_current_character(self) -> None:
        """删除当前角色"""
        if not self.current_character or self.current_character == "默认角色":
            return
        
        # 创建确认对话框 - 不显示标题，只显示内容
        dialog = MDDialog(
            MDDialogContentContainer(
                Label(
                    text=f"确定要删除角色 '{self.current_character}' 吗？",
                    font_name="LXGWWenKai",  # 使用自定义字体
                    font_size="16sp",
                    color=self.theme_cls.onSurfaceColor,
                    size_hint_y=None,
                    height=dp(40),
                    valign="center"
                ),
                orientation="vertical",
                spacing=dp(16),
                padding=[dp(24), dp(24), dp(24), dp(16)]  # 调整内边距，顶部留出更多空间
            ),
            MDDialogButtonContainer(
                MDIconButton(
                    icon="close",
                    theme_icon_color="Custom",
                    icon_color=App.get_running_app().theme_cls.onSurfaceVariantColor,
                    md_bg_color=App.get_running_app().theme_cls.surfaceContainerHighColor,
                    on_release=lambda x: dialog.dismiss()
                ),
                MDIconButton(
                    icon="delete",
                    theme_icon_color="Custom",
                    icon_color=App.get_running_app().theme_cls.errorColor,
                    md_bg_color=App.get_running_app().theme_cls.errorContainerColor,
                    on_release=lambda x: self._do_delete_character(dialog)
                ),
                spacing="8dp"
            )
        )
        dialog.open()
    
    def _do_delete_character(self, dialog: MDDialog) -> None:
        """执行删除角色"""
        character_to_delete = self.current_character
        
        if character_to_delete in self.characters:
            self.characters.remove(character_to_delete)
            
            # 如果删除的是当前角色，切换到第一个可用角色
            if self.current_character == character_to_delete:
                self.current_character = self.characters[0] if self.characters else "默认角色"
                
            self.refresh_character_list()
            
            # 从配置文件中移除
            self.remove_character_from_config(character_to_delete)
            
            # 触发回调
            if 'on_character_deleted' in self.callbacks:
                self.callbacks['on_character_deleted'](character_to_delete, self.current_character)
        
        dialog.dismiss()
    
    def set_callback(self, event_name: str, callback: callable) -> None:
        """设置事件回调"""
        self.callbacks[event_name] = callback
    
    def get_current_character(self) -> str:
        """获取当前角色"""
        return self.current_character
    
    def get_characters(self) -> List[str]:
        """获取所有角色列表"""
        return self.characters.copy()