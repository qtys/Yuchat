import requests
import json
import os
import pygame
import threading
from urllib.parse import quote_plus, urlencode
from pathlib import Path

class TTSManager:
    def __init__(self):
        self.config = self.load_config()
        self.setup_audio()
    
    def load_config(self):
        """加载配置"""
        try:
            config_path = "config/config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置失败: {e}")
            return {}
    
    def setup_audio(self):
        """初始化音频系统"""
        try:
            pygame.mixer.init()
            print("音频系统初始化成功")
        except Exception as e:
            print(f"音频初始化失败: {e}")
    
    def fetch_token(self):
        """获取百度语音token"""
        api_key = self.config.get('baidu_tts', {}).get('api_key', '')
        secret_key = self.config.get('baidu_tts', {}).get('secret_key', '')
        
        if not api_key or not secret_key:
            print("百度TTS API密钥未配置")
            return None
        
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            'grant_type': 'client_credentials',
            'client_id': api_key,
            'client_secret': secret_key
        }
        
        try:
            response = requests.post(url, params=params, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if 'access_token' in result:
                    return result['access_token']
                else:
                    print(f"获取token失败: {result}")
            else:
                print(f"获取token失败，HTTP状态码: {response.status_code}")
        except Exception as e:
            print(f"获取token失败: {e}")
        
        return None
    
    def text_to_speech(self, text):
        """文本转语音"""
        if not text or len(text.strip()) == 0:
            print("文本为空，跳过TTS")
            return False
        
        token = self.fetch_token()
        if not token:
            print("无法获取百度TTS token")
            return False
        
        # TTS参数
        params = {
            'tok': token,
            'tex': quote_plus(text),
            'per': 4194,  # 发音人
            'spd': 5,     # 语速
            'pit': 5,     # 音调
            'vol': 5,     # 音量
            'aue': 3,     # mp3格式
            'cuid': 'yuchat_tts',
            'lan': 'zh',
            'ctp': 1
        }
        
        try:
            url = 'http://tsn.baidu.com/text2audio'
            response = requests.post(url, data=params, timeout=30)
            
            # 检查是否是音频文件
            if 'audio/' in response.headers.get('content-type', ''):
                # 确保voice目录存在
                os.makedirs('voice', exist_ok=True)
                
                # 保存音频文件
                output_file = 'voice/response.mp3'
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                print(f"音频文件已保存: {output_file}")
                
                # 播放音频
                return self.play_audio(output_file)
            else:
                error_msg = response.text
                print(f"TTS API返回错误: {error_msg}")
                return False
                
        except Exception as e:
            print(f"TTS请求失败: {e}")
            return False
    
    def play_audio(self, file_path):
        """播放音频文件"""
        try:
            if not os.path.exists(file_path):
                print(f"音频文件不存在: {file_path}")
                return False
            
            # 确保音频系统已初始化
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            # 加载并播放音频
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # 等待播放完成
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            
            print("音频播放完成")
            return True
            
        except Exception as e:
            print(f"播放音频失败: {e}")
            return False

# 全局TTS管理器实例
_tts_manager = None

def get_tts_manager():
    """获取TTS管理器实例"""
    global _tts_manager
    if _tts_manager is None:
        _tts_manager = TTSManager()
    return _tts_manager

def runapi(text):
    """运行TTS的API接口"""
    def _run():
        try:
            manager = get_tts_manager()
            success = manager.text_to_speech(text)
            if not success:
                print("TTS处理失败")
        except Exception as e:
            print(f"TTS执行错误: {e}")
    
    # 在新线程中运行，避免阻塞
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

def toplay():
    """播放最新生成的音频文件"""
    try:
        manager = get_tts_manager()
        manager.play_audio('voice/response.mp3')
    except Exception as e:
        print(f"播放音频失败: {e}")
