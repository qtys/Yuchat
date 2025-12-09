import json
import os
from datetime import datetime
from typing import List, Dict, Any
from .platform_utils import get_storage_path

def save_message_to_chat_data(message_content: str, role: str = "user", data_file_path: str = None) -> bool:
    """
    将消息保存到指定的聊天记录文件中
    
    Args:
        message_content: 消息内容
        role: 消息角色 ("user" 或 "assistant")
        data_file_path: 聊天记录文件路径
        
    Returns:
        bool: 保存成功返回True，失败返回False
    """
    if data_file_path is None:
        data_file_path = os.path.join(get_storage_path(), "data", "chat_data.json")
    
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(data_file_path), exist_ok=True)
        
        # 如果文件不存在，创建空列表
        if not os.path.exists(data_file_path):
            chat_data = []
        else:
            # 读取现有数据
            try:
                with open(data_file_path, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                chat_data = []
        
        # 创建新消息
        new_message = {
            "role": role,
            "content": message_content,
            "timestamp": datetime.now().isoformat()
        }
        
        # 添加到聊天记录
        chat_data.append(new_message)
        
        # 写回文件
        with open(data_file_path, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, ensure_ascii=False, indent=2)
            
        return True
        
    except Exception as e:
        print(f"保存消息失败: {e}")
        return False

def load_chat_data(data_file_path: str = None) -> List[Dict[str, Any]]:
    """
    从聊天记录文件加载数据
    
    Args:
        data_file_path: 聊天记录文件路径
        
    Returns:
        List[Dict[str, Any]]: 聊天记录列表
    """
    if data_file_path is None:
        data_file_path = os.path.join(get_storage_path(), "data", "chat_data.json")
    
    try:
        if not os.path.exists(data_file_path):
            return []
            
        with open(data_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except (json.JSONDecodeError, FileNotFoundError):
        return []
    except Exception as e:
        print(f"加载聊天记录失败: {e}")
        return []