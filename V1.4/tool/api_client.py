#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API客户端模块
用于与OpenAI API进行交互，实现AI对话功能
"""

import json
import requests
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import traceback


class APIClient:
    """OpenAI API客户端"""
    
    def __init__(self, api_key: str, base_url: str, model: str = "deepseek-v3"):
        """
        初始化API客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 使用的模型
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')  # 移除末尾的斜杠
        self.model = model
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'YU-Chat/1.0'
        }
        
    def create_chat_completion(self, messages: List[Dict[str, str]], 
                             temperature: float = 0.7,
                             max_tokens: int = 2000) -> Optional[str]:
        """
        创建聊天完成请求
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "消息内容"}]
            temperature: 创造性参数 (0.0-2.0)
            max_tokens: 最大响应token数
            
        Returns:
            AI回复内容，失败时返回None
        """
        try:
            # 构建请求数据
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            # 发送请求
            print(f"发送API请求到: {self.base_url}/chat/completions")
            print(f"请求数据: {data}")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=30  # 30秒超时
            )
            
            print(f"API响应状态码: {response.status_code}")
            print(f"API响应内容: {response.text}")
            
            # 检查响应状态
            if response.status_code == 200:
                try:
                    result = response.json()
                    # API响应处理
                    print(f"API响应内容: {result}")  # 调试信息
                    
                    # 检查响应结构
                    print(f"检查choices字段: {'choices' in result}")
                    if 'choices' in result:
                        print(f"choices长度: {len(result['choices'])}")
                        if len(result['choices']) > 0:
                            print(f"第一个choice: {result['choices'][0]}")
                    
                    if 'choices' in result and len(result['choices']) > 0:
                        message_content = result['choices'][0].get('message', {}).get('content', '')
                        print(f"提取的message_content: '{message_content}'")
                        print(f"message_content长度: {len(message_content) if message_content else 0}")
                        if message_content:
                            return message_content.strip()
                        else:
                            print("AI回复内容为空")
                            return None
                    else:
                        print(f"API响应格式错误: 没有choices字段或choices为空")
                        print(f"响应内容: {result}")
                        return None
                        
                except json.JSONDecodeError as e:
                    # JSON解析错误处理
                    print(f"JSON解析错误: {e}")
                    return None
            else:
                error_msg = f"API请求失败 (状态码: {response.status_code})"
                try:
                    error_detail = response.json()
                    if 'error' in error_detail:
                        error_msg += f": {error_detail['error'].get('message', '未知错误')}"
                except:
                    error_msg += f": {response.text}"
                print(error_msg)
                return None
                
        except requests.exceptions.Timeout:
            print("API请求超时")
            return None
        except requests.exceptions.ConnectionError:
            print("网络连接错误，请检查网络连接")
            return None
        except Exception as e:
            # API请求错误处理
            traceback.print_exc()
            return None
    
    def format_messages_for_api(self, chat_history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        将本地聊天记录格式化为API所需格式
        
        Args:
            chat_history: 本地聊天记录，包含role、content、timestamp等字段
            
        Returns:
            API所需的消息格式
        """
        formatted_messages = []
        
        for message in chat_history:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            # 只添加有效的消息
            if content and role in ["user", "assistant", "system"]:
                formatted_messages.append({
                    "role": role,
                    "content": content
                })
        
        return formatted_messages
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            连接是否成功
        """
        try:
            test_messages = [{"role": "user", "content": "Hello"}]
            response = self.create_chat_completion(test_messages, max_tokens=10)
            return response is not None
        except:
            return False


# 全局API客户端实例
_api_client: Optional[APIClient] = None


def initialize_api_client(api_key: str, base_url: str, model: str = "deepseek-v3") -> APIClient:
    """
    初始化全局API客户端
    
    Args:
        api_key: API密钥
        base_url: API基础URL
        model: 模型名称
        
    Returns:
        APIClient实例
    """
    global _api_client
    _api_client = APIClient(api_key, base_url, model)
    return _api_client


def get_api_client() -> Optional[APIClient]:
    """
    获取全局API客户端实例
    
    Returns:
        APIClient实例，如果未初始化则返回None
    """
    global _api_client
    
    if _api_client is None:
        # 从配置文件加载API设置
        from .platform_utils import get_storage_path
        config_path = os.path.join(get_storage_path(), "config", "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                openai_config = config.get('openai', {})
                api_key = openai_config.get('api_key', '')
                base_url = openai_config.get('base_url', 'https://api.openai.com/v1')
                model = openai_config.get('model', 'deepseek-v3')
                
                if api_key:
                    _api_client = APIClient(api_key, base_url, model)
                else:
                    print("警告: API密钥未配置")
                    
            except Exception as e:
                print(f"加载API配置失败: {e}")
    
    return _api_client


def send_message_to_ai(message_content: str, chat_history: List[Dict[str, Any]], 
                      temperature: float = 0.7, model: Optional[str] = None) -> Optional[str]:
    """
    发送消息到AI并获取回复
    
    Args:
        message_content: 用户消息内容
        chat_history: 聊天历史记录
        temperature: 创造性参数
        model: 模型名称（可选，如果提供则临时使用指定模型）
        
    Returns:
        AI回复内容，失败时返回None
    """
    client = get_api_client()
    if not client:
        print("API客户端未初始化")
        return None
    
    try:
        # 如果需要使用特定模型，临时创建新的客户端
        if model:
            # 从配置获取API设置
            from .platform_utils import get_storage_path
            config_path = os.path.join(get_storage_path(), "config", "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    openai_config = config.get('openai', {})
                    api_key = openai_config.get('api_key', '')
                    base_url = openai_config.get('base_url', 'https://api.openai.com/v1')
                    
                    if api_key:
                        # 临时创建使用指定模型的客户端
                        temp_client = APIClient(api_key, base_url, model)
                        # 格式化消息历史
                        messages = temp_client.format_messages_for_api(chat_history)
                        
                        # 发送请求并获取回复
                        response = temp_client.create_chat_completion(messages, temperature=temperature)
                        return response
                    else:
                        print("警告: API密钥未配置，使用默认模型")
                        
                except Exception as e:
                    print(f"临时客户端创建失败: {e}")
        
        # 使用默认客户端
        # 格式化消息历史
        messages = client.format_messages_for_api(chat_history)
        
        print(f"发送给API的消息: {messages}")
        
        # 发送请求并获取回复
        response = client.create_chat_completion(messages, temperature=temperature)
        return response
        
    except Exception as e:
        print(f"发送消息到AI时发生错误: {e}")
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 测试代码
    # API客户端测试
    
    # 测试配置（使用示例密钥）
    test_key = "sk-test-key"
    test_url = "https://api.openai.com/v1"
    test_model = "gpt-3.5-turbo"
    
    # 初始化客户端
    client = initialize_api_client(test_key, test_url, test_model)
    
    # 测试连接
    if client.test_connection():
        pass  # API连接测试成功
    else:
        pass  # API连接测试失败
    
    # 测试消息格式化
    test_history = [
        {"role": "user", "content": "你好", "timestamp": "2024-01-01 10:00:00"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的吗？", "timestamp": "2024-01-01 10:00:01"}
    ]
    
    formatted = client.format_messages_for_api(test_history)
    print(f"格式化消息: {formatted}")