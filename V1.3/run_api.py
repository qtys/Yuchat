import tkinter as tk
from tkinter import scrolledtext, Checkbutton, messagebox, ttk
from PIL import Image, ImageTk, ImageOps
import json
import os
import threading
from pathlib import Path
import sys
import time
import webbrowser

class ConfigManager:
    """配置管理器 - 仅支持JSON格式"""
    def __init__(self):
        self.config_path = "config/config.json"
        self.config = self.load_config()
    
    def load_config(self):
        """加载JSON配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print("成功加载JSON配置文件")
                    return config
            except Exception as e:
                print(f"加载JSON配置失败: {e}")
                return self.create_default_config()
        else:
            return self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置"""
        default_config = {
            "openai": {
                "api_key": "your_api_key_here",
                "base_url": "https://api.yuegle.com/v1",
                "model": "gemini-2.5-pro"
            },
            "baidu_tts": {
                "api_key": "your_baidu_api_key",
                "secret_key": "your_baidu_secret"
            },
            "app": {
                "data_file": "chat_history.json",
                "max_history": 100,
                "available_models": ["gemini-2.5-pro","gemini-2.5-flash","gpt-4.1","deepseek-v3","deepseek-r1"],
                "background_image": "background.jpg",  # 新增背景图片配置
                "current_character": "AI",
                "characters": [
                    {
                        "name": "AI",
                        "data_file": "chat_history_AI.json",
                        "description": "默认AI助手"
                    }
                ]
            }
        }
        
        os.makedirs("config", exist_ok=True)
        self.save_config(default_config)
        messagebox.showinfo("首次运行", "已创建默认配置文件\n\n请编辑: config/config.json")
        return default_config
    
    def save_config(self, config):
        """保存配置到JSON文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get(self, *keys, default=None):
        """安全获取配置值"""
        current = self.config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

class ChatHistoryManager:
    """聊天历史管理器"""
    def __init__(self, data_file, max_history=100):
        self.data_file = f"data/{data_file}"
        self.max_history = max_history
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """确保数据文件存在"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def load_history(self):
        """加载聊天历史"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
                if len(history) > self.max_history:
                    history = history[-self.max_history:]
                return history
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            return []
    
    def save_message(self, role, content):
        """保存单条消息 - 无限制保存聊天信息"""
        try:
            # 直接从文件读取完整历史，不进行截断
            history = []
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                pass
                
            message = {
                "role": role,
                "content": content,
                "timestamp": time.time()
            }
            history.append(message)
            
            # 不再限制保存的历史记录数量，实现无限制保存
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存消息失败: {e}")
    
    def clear_history(self):
        """清空聊天历史"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"清空历史记录失败: {e}")
            return False

class ChatApp:
    def __init__(self):
        self.setup_directories()
        self.config_manager = ConfigManager()
        
        # 初始化角色相关属性
        self.characters = self.config_manager.get("app", "characters", default=[
            {"name": "AI", "data_file": "chat_history_AI.json", "description": "默认AI助手"}
        ])
        self.current_character = self.config_manager.get("app", "current_character", default="AI")
        
        # 自动扫描data文件夹中的聊天历史文件，添加为角色
        self.scan_data_folder_for_characters()
        
        # 获取当前角色的数据文件
        data_file = self.get_current_character_data_file()
        max_history = self.config_manager.get("app", "max_history", default=100)
        self.history_manager = ChatHistoryManager(data_file, max_history)
        
        self.messages = self.history_manager.load_history()
        self.is_processing = False
        self.available_models = self.config_manager.get("app", "available_models", default=["gemini-2.5-pro"])
        
        self.setup_ui()
        self.test_api_connection()
    
    def get_current_character_data_file(self):
        """获取当前角色的数据文件"""
        for char in self.characters:
            if char["name"] == self.current_character:
                return char["data_file"]
        # 如果找不到当前角色，返回默认文件名
        return f"chat_history_{self.current_character}.json"
    
    def setup_directories(self):
        """创建必要的目录"""
        os.makedirs("config", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        os.makedirs("voice", exist_ok=True)
        os.makedirs("image", exist_ok=True)
    
    def test_api_connection(self):
        """测试API连接"""
        api_key = self.config_manager.get("openai", "api_key", default="")
        if not api_key or api_key.startswith("your_api_key"):
            messagebox.showwarning("配置提醒", "请先配置有效的API密钥")
    
    def setup_ui(self):
        """设置用户界面"""
        self.window = tk.Tk()
        self.window.title("YuChat")
        
        # 设置窗口最小大小和初始大小
        self.window.minsize(450, 550)
        self.window.geometry("500x600")
        self.window.resizable(True, True)
        self.window.attributes("-alpha", 0.97)
        
        # 注意：暂时移除窗口大小变化事件监听以确保程序稳定运行
        
        try:
            self.window.iconbitmap("image/lightball.ico")
        except:
            pass
        
        # 设置背景图片
        self.setup_background()
        
        self.create_widgets()
        self.bind_events()
        self.setup_text_tags()
        self.add_welcome_message()
        self.update_model_button()
    

    
    def setup_background(self):
        """设置背景图片"""
        try:
            # 获取背景图片路径
            bg_image_path = self.config_manager.get("app", "background_image", default="")
            if not bg_image_path:
                # 如果没有配置背景图片，使用默认背景色
                self.window.configure(bg="#f5f5f5")
                return
            
            # 构建完整路径
            if not os.path.isabs(bg_image_path):
                bg_image_path = os.path.join("image", bg_image_path)
            
            if os.path.exists(bg_image_path):
                # 加载并调整背景图片大小
                original_image = Image.open(bg_image_path)
                
                # 调整图片大小以适应窗口
                window_width, window_height = 500, 700
                resized_image = ImageOps.fit(original_image, (window_width, window_height), Image.LANCZOS)
                
                # 创建PhotoImage对象
                self.bg_image = ImageTk.PhotoImage(resized_image)
                
                # 创建背景标签
                self.bg_label = tk.Label(self.window, image=self.bg_image)
                self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                
                print(f"成功加载背景图片: {bg_image_path}")
            else:
                print(f"背景图片不存在: {bg_image_path}")
                self.window.configure(bg="#f5f5f5")
                
        except Exception as e:
            print(f"加载背景图片失败: {e}")
            self.window.configure(bg="#f5f5f5")
    
    def setup_text_tags(self):
        """预先配置文本标签样式 - 修复颜色格式"""
        # 使用十六进制颜色代码，而不是RGBA
        self.chat_display.tag_configure("user_prefix", 
                                      foreground="#FFFFFF",
                                      font=("微软雅黑", 11, "bold"),
                                      background="#2980B9",  # 使用纯色而不是RGBA
                                      relief="raised",
                                      borderwidth=1)
        self.chat_display.tag_configure("user_content",
                                      font=("微软雅黑", 11),
                                      foreground="#2C3E50",
                                      background="#E8F4FD",  # 浅蓝色背景
                                      lmargin1=10,
                                      lmargin2=10,
                                      rmargin=10)
        
        self.chat_display.tag_configure("assistant_prefix", 
                                      foreground="#FFFFFF",
                                      font=("微软雅黑", 11, "bold"),
                                      background="#27AE60",  # 使用纯色而不是RGBA
                                      relief="raised",
                                      borderwidth=1)
        self.chat_display.tag_configure("assistant_content",
                                      font=("微软雅黑", 11),
                                      foreground="#2C3E50",
                                      background="#E8F8F0",  # 浅绿色背景
                                      lmargin1=10,
                                      lmargin2=10,
                                      rmargin=10)
        
        self.chat_display.tag_configure("system_prefix", 
                                      foreground="#FFFFFF",
                                      font=("微软雅黑", 11, "bold"),
                                      background="#E74C3C")  # 使用纯色而不是RGBA
        self.chat_display.tag_configure("system_content",
                                      font=("微软雅黑", 11),
                                      foreground="#2C3E50",
                                      background="#FDEDEC")  # 浅红色背景
        
        self.chat_display.tag_configure("warning_prefix", 
                                      foreground="#FFFFFF",
                                      font=("微软雅黑", 11, "bold"),
                                      background="#F39C12")  # 使用纯色而不是RGBA
        self.chat_display.tag_configure("warning_content",
                                      font=("微软雅黑", 11),
                                      foreground="#2C3E50",
                                      background="#FEF5E7")  # 浅橙色背景
    
    def create_widgets(self):
        """创建界面控件 - 使用更严格的布局管理"""
        # 标题区域容器
        title_frame = tk.Frame(self.window, bg="#2C3E50", pady=10)
        title_frame.pack(fill=tk.X)
        
        # 设置grid布局权重，确保标题完美居中
        title_frame.grid_columnconfigure(0, weight=1)
        title_frame.grid_columnconfigure(1, weight=0)
        title_frame.grid_columnconfigure(2, weight=1)
        
        # 左侧占位符
        tk.Label(title_frame, bg="#2C3E50").grid(row=0, column=0, sticky="nsew")
        
        # 中间标题标签 - 放置在第一行中间列
        title_label = tk.Label(
            title_frame, text="YuChat",
            font=("微软雅黑", 16, "bold"), bg="#2C3E50", fg="white"
        )
        title_label.grid(row=0, column=1)
        
        # 右侧占位符 - 放置在第一行右侧
        tk.Label(title_frame, bg="#2C3E50").grid(row=0, column=2, sticky="nsew")
        
        # 可点击网址标签 - 放置在右侧列的底部，与标题底部对齐
        url_label = tk.Label(
            title_frame, text="yushne.xyz",
            font=("微软雅黑", 9), bg="#2C3E50", fg="white", cursor="hand2"
        )
        url_label.grid(row=0, column=2, sticky="se", padx=(0, 10))
        url_label.bind("<Button-1>", self.open_website)
        
        # 状态栏 - 纯色背景
        self.status_var = tk.StringVar(value="就绪")
        status_bar = tk.Label(
            self.window, textvariable=self.status_var,
            font=("微软雅黑", 9), bg="#ECF0F1", fg="#7F8C8D", anchor=tk.W, padx=10
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 创建标签页控件
        self.tab_control = tk.ttk.Notebook(self.window)
        self.tab_control.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 聊天标签页 - 使用grid布局管理内部组件
        self.chat_tab = tk.Frame(self.tab_control, bg="#FFFFFF")
        self.tab_control.add(self.chat_tab, text="💬 聊天")
        
        # 设置grid布局权重，确保中间区域可以扩展
        self.chat_tab.grid_rowconfigure(1, weight=1)
        self.chat_tab.grid_columnconfigure(0, weight=1)
        
        # 控制面板 - 纯色背景
        control_frame = tk.Frame(self.chat_tab, bg="#34495E", pady=5)
        control_frame.grid(row=0, column=0, sticky="ew", padx=10)
        
        # 语音复选框 - 纯色背景
        self.tts_var = tk.IntVar(value=0)
        tts_check = Checkbutton(
            control_frame, text="🔊 语音播报", variable=self.tts_var,
            bg="#34495E", fg="white", font=("微软雅黑", 10), 
            selectcolor="#34495E", activebackground="#34495E"
        )
        tts_check.pack(side=tk.LEFT, padx=10)
        
        # 模型切换按钮 - 纯色背景
        self.model_btn = tk.Button(
            control_frame, text="🔄 切换模型", command=self.switch_model,
            bg="#9B59B6", fg="white", font=("微软雅黑", 9), 
            relief=tk.FLAT, activebackground="#8E44AD"
        )
        self.model_btn.pack(side=tk.RIGHT, padx=5)
        
        # 清空历史按钮 - 纯色背景
        clear_btn = tk.Button(
            control_frame, text="🗑️ 清空", command=self.clear_history,
            bg="#E74C3C", fg="white", font=("微软雅黑", 9), 
            relief=tk.FLAT, activebackground="#C0392B"
        )
        clear_btn.pack(side=tk.RIGHT, padx=5)
        
        # 聊天显示区域 - 使用严格的布局
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_tab, wrap=tk.WORD, font=("微软雅黑", 11),
            bg="#FFFFFF", fg="#2C3E50", 
            padx=10, pady=10, relief=tk.FLAT, borderwidth=1,
            insertbackground="#2C3E50"  # 光标颜色
        )
        # 使用grid布局并设置sticky使其填充可用空间
        self.chat_display.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.chat_display.config(state=tk.DISABLED)
        
        # 输入区域 - 使用grid布局确保固定在底部
        input_frame = tk.Frame(self.chat_tab, bg="#ECF0F1", pady=5, padx=5)
        input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        input_frame.grid_columnconfigure(0, weight=1)  # 让输入框区域可扩展
        
        # 输入框
        self.input_entry = tk.Entry(
            input_frame, font=("微软雅黑", 12), 
            bg="#FFFFFF", fg="#2C3E50",
            relief=tk.FLAT, borderwidth=1, insertbackground="#2C3E50"
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=0, ipady=5)
        self.input_entry.focus()
        
        # 发送按钮 - 固定大小
        self.send_btn = tk.Button(
            input_frame, text="发送", command=self.on_send,
            font=("微软雅黑", 10, "bold"), bg="#3498DB", 
            fg="white", relief=tk.FLAT, width=8,
            activebackground="#2980B9"
        )
        self.send_btn.grid(row=0, column=1, padx=(5, 0))
        
        # 角色管理标签页
        self.character_tab = tk.Frame(self.tab_control, bg="#F5F5F5")
        self.tab_control.add(self.character_tab, text="👤 角色")
        self.create_character_tab()
        
        # 配置标签页
        self.config_tab = tk.Frame(self.tab_control, bg="#F5F5F5")
        self.tab_control.add(self.config_tab, text="⚙️ 配置")
        self.create_config_tab()
    
    def update_model_button(self):
        """更新模型按钮显示当前模型"""
        current_model = self.config_manager.get("openai", "model", default="未知")
        self.model_btn.config(text=f"🔄 {current_model}")
    
    def open_website(self, event):
        """点击网址标签时打开浏览器访问网站"""
        webbrowser.open("https://yushne.xyz")
    
    def switch_model(self):
        """切换模型"""
        current_model = self.config_manager.get("openai", "model", default="gemini-2.5-pro")
        
        try:
            current_index = self.available_models.index(current_model)
            next_index = (current_index + 1) % len(self.available_models)
            new_model = self.available_models[next_index]
        except ValueError:
            new_model = self.available_models[0]
        
        self.config_manager.config["openai"]["model"] = new_model
        self.config_manager.save_config(self.config_manager.config)
        self.update_model_button()
        self.display_message("系统", f"已切换模型为: {new_model}", "system")
    
    def add_welcome_message(self):
        """添加欢迎消息"""
        current_model = self.config_manager.get("openai", "model", default="未知")
        
        welcome_text = f"""欢迎使用 YuChat AI助手！

当前角色: {self.current_character}
当前模型: {current_model}
可用模型: {', '.join(self.available_models)}
功能特点：
• 支持连续对话
• 可选语音播报  
• 自动保存历史记录
• 可点击"切换模型"按钮更换AI模型
• 可点击"👤 {self.current_character}"按钮切换角色

请在上方输入您的问题，然后点击发送或按Enter键。"""

        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, welcome_text + "\n\n")
        self.chat_display.config(state=tk.DISABLED)
        
        self.display_history_messages()
    
    def display_history_messages(self):
        """显示历史消息"""
        if not self.messages:
            return
            
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "--- 历史对话 ---\n", "system_prefix")
        
        for msg in self.messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                self.display_message("您", content, "user", update_display=False)
            elif role == "assistant":
                self.display_message(self.current_character, content, "assistant", update_display=False)
        
        self.chat_display.insert(tk.END, "--- 当前对话 ---\n", "system_prefix")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def bind_events(self):
        """绑定事件"""
        self.input_entry.bind("<Return>", lambda e: self.on_send())
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_send(self):
        """发送消息"""
        if self.is_processing:
            return
            
        user_input = self.input_entry.get().strip()
        if not user_input:
            return
        
        self.input_entry.delete(0, tk.END)
        self.is_processing = True
        self.send_btn.config(state=tk.DISABLED, text="思考中...")
        self.status_var.set(f"{self.current_character} 正在思考...")
        
        self.display_message("您", user_input, "user")
        self.history_manager.save_message("user", user_input)
        
        threading.Thread(target=self.process_ai_response, args=(user_input,), daemon=True).start()
    
    def display_message(self, sender, message, msg_type="user", update_display=True):
        """显示消息"""
        self.chat_display.config(state=tk.NORMAL)
        
        if msg_type == "user":
            prefix, prefix_tag, content_tag = "您: ", "user_prefix", "user_content"
        elif msg_type == "assistant":
            prefix, prefix_tag, content_tag = f"{sender}: ", "assistant_prefix", "assistant_content"
        elif msg_type == "warning":
            prefix, prefix_tag, content_tag = "⚠️ 注意: ", "warning_prefix", "warning_content"
        else:
            prefix, prefix_tag, content_tag = "系统: ", "system_prefix", "system_content"
        
        self.chat_display.insert(tk.END, prefix, prefix_tag)
        self.chat_display.insert(tk.END, message + "\n\n", content_tag)
        
        self.chat_display.config(state=tk.DISABLED)
        if update_display:
            self.chat_display.see(tk.END)
            self.window.update()
    
    def process_ai_response(self, user_input):
        """处理AI响应"""
        try:
            api_key = self.config_manager.get("openai", "api_key", default="")
            
            if not api_key or api_key.startswith("your_api_key"):
                response = self.mock_ai_response(user_input)
                self.display_message(self.current_character, response, "assistant")
            else:
                response = self.real_ai_response(user_input)
            
            self.history_manager.save_message("assistant", response)
            
            if self.tts_var.get() == 1:
                self.text_to_speech(response)
                
        except Exception as e:
            error_msg = f"处理请求时出错: {str(e)}"
            self.display_message("系统", error_msg, "system")
        finally:
            self.is_processing = False
            self.send_btn.config(state=tk.NORMAL, text="发送")
            self.status_var.set("就绪")
    
    def real_ai_response(self, user_input):
        """真实AI API调用"""
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.config_manager.get("openai", "api_key"),
                base_url=self.config_manager.get("openai", "base_url", default="https://api.yuegle.com/v1")
            )
            
            self.messages.append({"role": "user", "content": user_input})
            current_model = self.config_manager.get("openai", "model", default="gemini-2.5-pro")
            
            response = client.chat.completions.create(
                model=current_model,
                messages=self.messages,
                stream=True
            )
            
            full_response = ""
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, f"{self.current_character}: ", "assistant_prefix")
            
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    self.chat_display.insert(tk.END, content, "assistant_content")
                    self.chat_display.see(tk.END)
                    self.window.update()
            
            self.chat_display.insert(tk.END, "\n\n")
            self.chat_display.config(state=tk.DISABLED)
            
            self.messages.append({"role": "assistant", "content": full_response})
            
            return full_response
            
        except Exception as e:
            error_str = str(e)
            if "503" in error_str and "无可用渠道" in error_str:
                current_model = self.config_manager.get("openai", "model", default="未知")
                warning_msg = f"""API调用失败: {error_str}

当前模型 '{current_model}' 不可用。
建议点击"切换模型"按钮尝试其他模型。

已自动切换到模拟模式。"""
                self.display_message("系统", warning_msg, "warning")
                return self.mock_ai_response(user_input)
            else:
                return f"API调用失败: {error_str}\n\n已自动切换到模拟模式。"
    
    def mock_ai_response(self, user_input):
        """模拟AI响应"""
        current_model = self.config_manager.get("openai", "model", default="未知")
        
        responses = {
            "hello": f"您好！我是{self.current_character}，很高兴为您服务。",
            "hi": f"你好！我是{self.current_character}，有什么我可以帮助您的吗？",
            "你好": f"您好！我是{self.current_character}，请告诉我您需要什么帮助。",
            "测试": "测试成功！程序运行正常。",
            "模型": f"当前使用模型: {current_model}。要切换模型，请点击右上角的模型切换按钮。",
            "切换模型": "要切换AI模型，请点击界面右上角的\"切换模型\"按钮。",
            "角色": f"当前角色: {self.current_character}。要切换角色，请点击右上角的角色按钮。",
            "切换角色": "要切换角色，请点击界面右上角的角色按钮。"
        }
        
        user_input_lower = user_input.lower()
        for key in responses:
            if key in user_input_lower:
                return responses[key]
        
        return f"""我已收到："{user_input}"

💡 当前运行在模拟模式。
要使用真实AI功能，请确保 config/config.json 中有有效的API密钥。

当前角色: {self.current_character}"""

    def text_to_speech(self, text):
        """文本转语音"""
        try:
            os.makedirs("voice", exist_ok=True)
            from TTS import BD_toapivoice as tts
            
            if hasattr(tts, 'runapi'):
                threading.Thread(target=tts.runapi, args=(text,), daemon=True).start()
                print(f"已启动TTS: {text[:50]}...")
            else:
                print("TTS模块缺少runapi函数")
                
        except ImportError as e:
            print(f"导入TTS模块失败: {e}")
            self.display_message("系统", f"语音合成模块加载失败: {e}", "system")
        except Exception as e:
            print(f"语音合成失败: {e}")
            self.display_message("系统", f"语音合成失败: {e}", "system")
    
    def create_character_tab(self):
        """创建角色管理标签页 - 卡片式设计"""
        # 使用Frame包裹整个标签页内容，确保按钮在正确位置
        self.main_frame = tk.Frame(self.character_tab, bg="#F5F5F5")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 头部信息框架
        header_frame = tk.Frame(self.main_frame, bg="#F5F5F5")
        header_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(header_frame, text="当前角色: " + self.current_character, 
                 font=("微软雅黑", 10, "bold"), bg="#F5F5F5").pack(anchor=tk.W, pady=(0, 5))
        
        tk.Label(header_frame, text="点击卡片选择角色", font=("微软雅黑", 10), bg="#F5F5F5").pack(anchor=tk.W)
        
        # 按钮框架 - 移到canvas上方，便于在窗口内完整显示
        btn_frame = tk.Frame(self.main_frame, bg="#F5F5F5")
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 添加角色按钮 - 缩小按钮大小，不再水平扩展
        add_btn = tk.Button(btn_frame, text="添加角色", command=self.show_add_character_form,
                          bg="#27AE60", fg="white", font=("微软雅黑", 8), relief=tk.RAISED, pady=4, padx=8, width=8)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # 删除角色按钮 - 缩小按钮大小，不再水平扩展
        delete_btn = tk.Button(btn_frame, text="删除角色", command=self.delete_character,
                             bg="#E74C3C", fg="white", font=("微软雅黑", 8), relief=tk.RAISED, pady=4, padx=8, width=8)
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建带有滚动条的卡片容器
        self.canvas = tk.Canvas(self.main_frame, bg="#F5F5F5", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # 先放置滚动条
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10))
        # 再放置canvas，占据剩余空间
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # 创建卡片容器框架
        self.card_frame = tk.Frame(self.canvas, bg="#F5F5F5")
        self.canvas_frame_id = self.canvas.create_window((0, 0), window=self.card_frame, anchor="nw")
        
        # 绑定滚动事件
        self.card_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # 添加防抖标志和计时器
        self._resize_timer = None
        
        # 为canvas配置事件添加防抖的卡片布局更新
        self.canvas.bind("<Configure>", self._on_canvas_configure)
    
    def _on_canvas_configure(self, event):
        """防抖处理canvas配置变化事件，避免频繁更新卡片布局"""
        # 更新canvas框架宽度
        self.canvas.itemconfig(self.canvas_frame_id, width=event.width)
        
        # 清除之前的计时器
        if self._resize_timer:
            self.window.after_cancel(self._resize_timer)
        
        # 设置新的计时器，延迟更新卡片布局
        self._resize_timer = self.window.after(100, self.update_character_cards)  # 100ms延迟
        
        # 更新角色卡片
        self.update_character_cards()
    
    def create_config_tab(self):
        """创建配置标签页"""
        # 创建滚动条框架
        config_frame = tk.Frame(self.config_tab, bg="#F5F5F5")
        config_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 配置编辑器
        self.config_text = scrolledtext.ScrolledText(
            config_frame, wrap=tk.WORD, font=("微软雅黑", 10),
            bg="#FFFFFF", fg="#2C3E50", height=20
        )
        self.config_text.pack(fill=tk.BOTH, expand=True)
        
        # 按钮框架
        btn_frame = tk.Frame(self.config_tab, bg="#F5F5F5")
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 加载配置按钮
        load_btn = tk.Button(btn_frame, text="加载配置", command=self.load_config_to_editor,
                           bg="#3498DB", fg="white", font=("微软雅黑", 9), relief=tk.FLAT)
        load_btn.pack(side=tk.LEFT, padx=5)
        
        # 保存配置按钮
        save_btn = tk.Button(btn_frame, text="保存配置", command=self.save_config_from_editor,
                           bg="#27AE60", fg="white", font=("微软雅黑", 9), relief=tk.FLAT)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # 自动加载配置
        self.load_config_to_editor()
    
    def load_config_to_editor(self):
        """加载配置到编辑器"""
        config_file = "config/config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_content = f.read()
                    self.config_text.delete(1.0, tk.END)
                    self.config_text.insert(tk.END, config_content)
            except Exception as e:
                messagebox.showerror("错误", f"加载配置失败: {str(e)}")
        else:
            messagebox.showinfo("提示", "配置文件不存在，将创建默认配置")
            self.config_manager.create_default_config()
            self.load_config_to_editor()
    
    def save_config_from_editor(self):
        """从编辑器保存配置"""
        config_file = "config/config.json"
        try:
            config_content = self.config_text.get(1.0, tk.END)
            # 验证JSON格式
            import json
            json.loads(config_content)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            messagebox.showinfo("成功", "配置保存成功")
            # 重新加载配置
            self.config_manager.load_config()
        except json.JSONDecodeError as e:
            messagebox.showerror("错误", f"JSON格式错误: {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def clear_history(self):
        """清空聊天历史"""
        if messagebox.askyesno("确认", f"确定要清空角色 '{self.current_character}' 的聊天记录吗？"):
            if self.history_manager.clear_history():
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.delete(1.0, tk.END)
                self.chat_display.config(state=tk.DISABLED)
                self.add_welcome_message()
                self.messages = []
                self.display_message("系统", f"角色 '{self.current_character}' 的历史记录已清空", "system")
            else:
                self.display_message("系统", "清空历史记录失败", "system")
    
    def update_character_cards(self):
        """更新角色卡片列表 - 响应式布局，根据窗口大小动态调整每行卡片数量，避免超出窗口范围"""
        # 清除现有卡片
        for widget in self.card_frame.winfo_children():
            widget.destroy()
        
        # 定义卡片颜色和选中状态样式
        card_bg = "#FFFFFF"
        selected_bg = "#3498DB"
        card_fg = "#333333"
        selected_fg = "#FFFFFF"
        
        # 为每个角色创建卡片
        self.character_cards = []  # 存储所有角色卡片引用
        
        # 卡片宽度和布局配置 - 使用固定值确保稳定
        card_width = 200  # 每个卡片的宽度
        card_height = 120  # 每个卡片的高度
        padding = 10      # 卡片间距
        
        # 根据窗口大小动态计算每行显示的卡片数量
        # 获取card_frame的实际可用宽度
        self.card_frame.update_idletasks()
        available_width = self.card_frame.winfo_width()
        
        # 计算每行可容纳的卡片数量
        # 每个卡片占用宽度 = 卡片宽度 + 左右padding
        card_total_width = card_width + (padding * 2)
        
        # 计算理论上可容纳的卡片数，至少1个，最多5个
        cards_per_row = max(1, min(5, available_width // card_total_width))
        
        # 如果窗口宽度过小，确保至少显示1个卡片
        if available_width < card_total_width:
            cards_per_row = 1
        
        for i, char in enumerate(self.characters):
            # 创建卡片框架
            is_selected = char['name'] == self.current_character
            bg_color = selected_bg if is_selected else card_bg
            fg_color = selected_fg if is_selected else card_fg
            
            # 创建固定大小的卡片框架 - 不设置内边距，在内部布局中控制
            card = tk.Frame(
                self.card_frame, 
                bg=bg_color, 
                relief=tk.RAISED,
                bd=2,
                cursor="hand2"
            )
            
            # 计算行和列
            row = i // cards_per_row
            col = i % cards_per_row
            
            # 使用网格布局并固定大小
            card.grid(row=row, column=col, padx=padding, pady=padding, sticky="nsew")
            
            # 关键：完全禁止卡片传播子组件的大小请求
            card.grid_propagate(False)
            card.pack_propagate(False)
            
            # 强制设置固定尺寸 - 在grid布局前先设置
            card.configure(width=card_width, height=card_height)
            
            # 存储卡片引用和角色名
            self.character_cards.append((card, char['name']))
            
            # 创建内部容器来控制内容布局，设置内边距
            content_frame = tk.Frame(card, bg=bg_color, padx=10, pady=10)
            content_frame.pack(fill=tk.BOTH, expand=True)
            content_frame.grid_propagate(False)
            content_frame.pack_propagate(False)
            
            # 角色名称标签 - 固定宽度并绑定点击事件
            name_label = tk.Label(
                content_frame, 
                text=char['name'], 
                font=("微软雅黑", 12, "bold"), 
                bg=bg_color, 
                fg=fg_color,
                wraplength=card_width - 40,  # 留出足够内边距
                height=1,
                width=15,  # 固定宽度，防止文字长度影响
                anchor=tk.W,
                justify=tk.LEFT,
                cursor="hand2"  # 鼠标指针变为手型
            )
            # 绑定点击事件到角色名标签
            name_label.bind("<Button-1>", lambda e, char_name=char['name']: self.on_card_click(char_name))
            name_label.pack(anchor=tk.W, pady=(0, 5), fill=tk.X)
            
            # 角色描述标签 - 固定宽度并绑定点击事件
            desc_label = tk.Label(
                content_frame, 
                text=char['description'] if char['description'] else "暂无描述", 
                font=("微软雅黑", 10), 
                bg=bg_color, 
                fg=fg_color,
                wraplength=card_width - 40,  # 留出足够内边距
                justify=tk.LEFT,
                height=3,
                width=15,  # 固定宽度，防止文字长度影响
                anchor=tk.NW,
                cursor="hand2"  # 鼠标指针变为手型
            )
            # 绑定点击事件到描述标签
            desc_label.bind("<Button-1>", lambda e, char_name=char['name']: self.on_card_click(char_name))
            desc_label.pack(anchor=tk.W, fill=tk.X)
            
            # 如果是当前角色，添加选中标记
            if is_selected:
                selected_mark = tk.Label(
                    content_frame, 
                    text="✓ 当前使用", 
                    font=("微软雅黑", 9, "bold"), 
                    bg=selected_bg, 
                    fg=selected_fg,
                    cursor="hand2"
                )
                # 绑定点击事件到选中标记
                selected_mark.bind("<Button-1>", lambda e, char_name=char['name']: self.on_card_click(char_name))
                selected_mark.pack(side=tk.RIGHT, anchor=tk.SE, pady=5)
            
            # 绑定卡片本身的事件
            card.bind("<Enter>", lambda e, c=card, is_sel=is_selected: self.on_card_enter(e, c, is_sel))
            card.bind("<Leave>", lambda e, c=card, is_sel=is_selected: self.on_card_leave(e, c, is_sel))
            card.bind("<Button-1>", lambda e, char_name=char['name']: self.on_card_click(char_name))
            
            # 最后再强制设置一次卡片尺寸，确保不受任何影响
            card.update_idletasks()
            card.configure(width=card_width, height=card_height)
        
        # 确保最后一行也能正确显示
        self.card_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_card_enter(self, event, card, is_selected):
        """鼠标悬停在卡片上时的效果"""
        if not is_selected:
            # 未选中的卡片在悬停时轻微改变背景色
            card.configure(bg="#F0F8FF")
            # 更新内部容器和标签的背景色
            for child in card.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg="#F0F8FF")
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Label) and not grandchild['text'].startswith('✓'):
                            grandchild.configure(bg="#F0F8FF")
    
    def on_card_leave(self, event, card, is_selected):
        """鼠标离开卡片时的效果"""
        if not is_selected:
            # 恢复未选中卡片的原始背景色
            card.configure(bg="#FFFFFF")
            # 更新内部容器和标签的背景色
            for child in card.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg="#FFFFFF")
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Label) and not grandchild['text'].startswith('✓'):
                            grandchild.configure(bg="#FFFFFF")
    
    def on_card_click(self, char_name):
        """点击卡片选择角色"""
        if char_name != self.current_character:
            self.switch_character(char_name)
            # 更新卡片显示，高亮当前选中的卡片
            self.update_character_cards()
            # 移除自动切换到聊天标签页的功能，让用户自主选择是否切换
            # 如需切换到聊天标签页，用户可以手动点击聊天标签
    
    def select_character(self):
        """选择角色 - 兼容方法"""
        # 由于我们使用卡片式设计，这个方法可能不再需要，但保留以确保兼容性
        pass
    
    def show_add_character_form(self):
        """显示添加角色表单 - 适配卡片式设计，优化布局逻辑"""
        # 清除之前可能存在的表单
        for widget in self.main_frame.winfo_children():
            if hasattr(widget, "winfo_name") and widget.winfo_name() == "add_character_form":
                widget.destroy()
        
        # 创建添加角色表单框架 - 使用卡片样式，放在main_frame内
        add_form_frame = tk.Frame(
            self.main_frame, 
            bg="#FFFFFF", 
            name="add_character_form",
            relief=tk.RAISED,
            bd=2,
            padx=15,
            pady=10
        )
        
        # 重新排序main_frame中的组件，确保布局稳定性
        # 1. 先获取所有子组件
        children = list(self.main_frame.winfo_children())
        
        # 2. 移除所有子组件
        for widget in children:
            widget.pack_forget()
        
        # 3. 重新打包组件，保持固定顺序
        header_frame = None
        btn_frame = None
        canvas_widget = None
        
        # 识别各个组件类型
        for widget in children:
            if widget.winfo_class() == 'Frame':
                # 判断是否为按钮框架（包含添加/删除按钮）
                if any(isinstance(child, tk.Button) and child['text'] in ['添加角色', '删除角色'] for child in widget.winfo_children()):
                    btn_frame = widget
                # 判断是否为头部框架（包含当前角色标签）
                elif any(isinstance(child, tk.Label) and child['text'].startswith('当前角色:') for child in widget.winfo_children()):
                    header_frame = widget
            elif widget == self.canvas:
                canvas_widget = widget
        
        # 按照固定顺序重新打包：header -> btn_frame -> form -> canvas
        if header_frame:
            header_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        if btn_frame:
            btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 插入表单
        add_form_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 重新打包canvas组件，确保卡片区域显示
        if canvas_widget:
            # 先放置滚动条
            scrollbar = None
            # 查找滚动条
            for widget in children:
                if isinstance(widget, tk.Scrollbar) and widget.cget("command") == canvas_widget.yview:
                    scrollbar = widget
                    break
            
            if scrollbar:
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10))
            
            # 再放置canvas，占据剩余空间
            canvas_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
            # 更新canvas滚动区域
            canvas_widget.update_idletasks()
            canvas_widget.configure(scrollregion=canvas_widget.bbox("all"))
        
        # 角色名称 - 缩小输入框大小
        tk.Label(add_form_frame, text="角色名称:", bg="#FFFFFF", font=("微软雅黑", 9)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=(5, 3))
        name_entry = tk.Entry(add_form_frame, font=("微软雅黑", 9), width=25)
        name_entry.grid(row=0, column=1, padx=5, pady=3, sticky=tk.W)
        name_entry.focus()
        
        # 角色描述 - 缩小输入框大小
        tk.Label(add_form_frame, text="角色描述:", bg="#FFFFFF", font=("微软雅黑", 9)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=(3, 5))
        desc_entry = tk.Entry(add_form_frame, font=("微软雅黑", 9), width=25)
        desc_entry.grid(row=1, column=1, padx=5, pady=3, sticky=tk.W)
        
        # 按钮
        btn_frame = tk.Frame(add_form_frame, bg="#F5F5F5")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        # 确认按钮
        def confirm_add():
            name = name_entry.get().strip()
            desc = desc_entry.get().strip()
            
            if not name:
                messagebox.showwarning("警告", "角色名称不能为空")
                return
            
            # 检查角色是否已存在
            for char in self.characters:
                if char['name'] == name:
                    messagebox.showwarning("警告", "该角色名称已存在")
                    return
            
            # 添加新角色
            new_char = {
                "name": name,
                "data_file": f"chat_history_{name}.json",
                "description": desc if desc else "自定义角色"
            }
            
            self.characters.append(new_char)
            self.config_manager.config["app"]["characters"] = self.characters
            self.config_manager.save_config(self.config_manager.config)
            
            # 更新角色卡片列表
            self.update_character_cards()
            # 移除表单
            add_form_frame.destroy()
        
        confirm_btn = tk.Button(btn_frame, text="确认添加", command=confirm_add,
                              bg="#27AE60", fg="white", font=("微软雅黑", 9), relief=tk.FLAT)
        confirm_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="取消", command=add_form_frame.destroy,
                             bg="#95A5A6", fg="white", font=("微软雅黑", 9), relief=tk.FLAT)
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def delete_character(self):
        """删除角色 - 支持卡片式设计，优化删除当前使用角色的逻辑，并删除对应data文件，删除后直接跳转到默认聊天"""
        # 获取当前选中的角色（通过卡片高亮状态判断）
        selected_char = None
        for card, char_name in self.character_cards:
            if card.cget("bg") == "#3498DB":  # 与selected_bg颜色匹配
                selected_char = char_name
                break
        
        if not selected_char:
            messagebox.showwarning("警告", "请先点击要删除的角色卡片")
            return
        
        char_name = selected_char
        
        if char_name == "AI":
            messagebox.showwarning("警告", "默认角色 'AI' 不能删除")
            return
        
        is_current_character = (char_name == self.current_character)
        
        # 询问是否确认删除
        if not messagebox.askyesno("确认", f"确定要删除角色 '{char_name}' 及其对应的聊天记录吗？"):
            return
        
        # 查找角色索引
        char_index = -1
        for i, char in enumerate(self.characters):
            if char['name'] == char_name:
                char_index = i
                break
        
        if char_index == -1:
            messagebox.showwarning("警告", "找不到指定角色")
            return
        
        # 删除角色
        del self.characters[char_index]
        
        # 删除对应的data文件
        try:
            data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
            data_file = os.path.join(data_folder, f"chat_history_{char_name}.json")
            if os.path.exists(data_file):
                os.remove(data_file)
                print(f"已删除角色'{char_name}'的聊天记录文件: {data_file}")
        except Exception as e:
            print(f"删除角色'{char_name}'的聊天记录文件时出错: {str(e)}")
        
        # 如果删除的是当前使用的角色，直接跳转到默认聊天（通常是AI角色）
        if is_current_character:
            # 查找可用的其他角色
            available_characters = [char['name'] for char in self.characters]
            
            if not available_characters:
                # 这种情况理论上不会发生，因为AI角色不能删除
                messagebox.showerror("错误", "没有可用角色，请重启应用")
                return
            
            # 直接选择第一个可用角色（通常是AI角色）作为默认聊天
            new_character = available_characters[0]
            self.switch_character(new_character)
        
        # 保存配置
        self.config_manager.config["app"]["characters"] = self.characters
        self.config_manager.save_config(self.config_manager.config)
        
        # 更新角色卡片列表
        self.update_character_cards()
    
    def scan_data_folder_for_characters(self):
        """扫描data文件夹中的聊天历史文件，自动添加为角色"""
        try:
            # 获取data文件夹路径
            data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
            
            # 检查文件夹是否存在
            if not os.path.exists(data_folder):
                print("data文件夹不存在，跳过扫描")
                return
            
            # 获取现有的角色名称集合，用于检查重复
            existing_char_names = {char["name"] for char in self.characters}
            
            # 扫描文件夹中的所有文件
            for filename in os.listdir(data_folder):
                # 检查文件名是否符合chat_history_*.json格式
                if filename.startswith("chat_history_") and filename.endswith(".json"):
                    # 提取角色名称（去掉前缀和扩展名）
                    char_name = filename[len("chat_history_"):-len(".json")]
                    
                    # 如果角色不存在，添加新角色
                    if char_name not in existing_char_names:
                        # 创建新角色对象
                        new_char = {
                            "name": char_name,
                            "data_file": filename,
                            "description": f"从{filename}自动加载的角色"
                        }
                        
                        # 添加到角色列表
                        self.characters.append(new_char)
                        existing_char_names.add(char_name)
                        print(f"自动添加角色: {char_name} (来自{filename})")
            
            # 如果有新角色被添加，更新配置文件
            if self.characters != self.config_manager.get("app", "characters", default=[]):
                self.config_manager.config["app"]["characters"] = self.characters
                self.config_manager.save_config(self.config_manager.config)
                print("已更新角色配置")
                
        except Exception as e:
            print(f"扫描data文件夹时出错: {e}")
    
    def switch_character(self, new_character):
        """切换角色"""
        # 更新当前角色
        self.current_character = new_character
        self.config_manager.config["app"]["current_character"] = new_character
        self.config_manager.save_config(self.config_manager.config)
        
        # 获取新角色的数据文件并重新初始化历史管理器
        data_file = self.get_current_character_data_file()
        max_history = self.config_manager.get("app", "max_history", default=100)
        self.history_manager = ChatHistoryManager(data_file, max_history)
        
        # 加载新角色的历史消息
        self.messages = self.history_manager.load_history()
        
        # 清空聊天显示区域并更新显示
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # 显示新角色的欢迎消息
        self.add_welcome_message()
        
        # 加载历史记录
        self.display_history_messages()
        
        # 显示系统消息
        self.display_message("系统", f"已切换到角色: {self.current_character}", "system")
    
    def on_closing(self):
        """关闭程序"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            self.window.destroy()
    
    def run(self):
        """运行程序"""
        self.window.mainloop()

if __name__ == "__main__":
    app = ChatApp()
    app.run()
