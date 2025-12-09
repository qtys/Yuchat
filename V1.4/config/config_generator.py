#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件生成器
快速生成默认配置文件
"""

import json
import os
from datetime import datetime
from pathlib import Path


def generate_config(config_path: str = None, force: bool = False) -> bool:
    """
    生成配置文件
    
    Args:
        config_path: 配置文件路径
        force: 是否强制覆盖现有文件
    
    Returns:
        bool: 是否成功生成
    """
    if config_path is None:
        from tool.platform_utils import get_storage_path
        config_path = str(Path(get_storage_path()) / "config" / "config.json")
    
    config_dir = Path(config_path).parent
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # 如果文件存在且不强制覆盖
    if os.path.exists(config_path) and not force:
        print(f"配置文件已存在: {config_path}")
        response = input("是否覆盖? (y/N): ").strip().lower()
        if response != 'y':
            print("操作已取消")
            return False
    
    # 默认配置模板（使用相对路径）
    default_config = {
        "openai": {
            "api_key": "",  # 请填入您的API密钥
            "base_url": "https://api.yuegle.com/v1",
            "model": "deepseek-v3"
        },
        "baidu_tts": {
            "api_key": "",  # 请填入您的百度API Key
            "secret_key": ""  # 请填入您的百度Secret Key
        },
        "app": {
            "data_file": "data/chat_data.json",  # 使用相对路径
            "context_length": 50,
            "available_models": [
                "gemini-2.5-pro",
                "gemini-2.5-flash",
                "gpt-4.1",
                "deepseek-v3",
                "deepseek-r1"
            ],
            "background_image": "image/image1.png",  # 使用相对路径
            "characters": [
                {
                    "name": "AI",
                    "data_file": "data/chat_history_AI.json",  # 使用相对路径
                    "description": "默认AI助手"
                }
            ],
            "current_character": "AI"
        },
        "metadata": {
            "version": "1.0",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": "YU-Chat配置文件",
            "author": "YU-Chat System"
        }
    }
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        print(f"✅ 配置文件已生成: {config_path}")
        return True
    except Exception as e:
        print(f"❌ 生成配置文件失败: {e}")
        return False


def show_config_template():
    """显示配置模板说明"""
    print("配置文件说明:")
    print("=" * 50)
    print("""
openai.api_key: OpenAI API密钥 (必需)
openai.base_url: API基础URL
openai.model: 使用的AI模型

baidu_tts.api_key: 百度TTS API Key (语音功能需要)
baidu_tts.secret_key: 百度TTS Secret Key (语音功能需要)

app.data_file: 聊天数据保存路径
app.context_length: 上下文对话长度
app.available_models: 可用AI模型列表
app.background_image: 背景图片路径
app.current_character: 当前角色
""")


def main():
    """主函数"""
    print("配置文件生成器")
    print("=" * 30)
    
    show_config_template()
    print("\n" + "=" * 30)
    
    # 生成配置文件
    success = generate_config(force=True)
    
    if success:
        print("\n💡 提示:")
        print("1. 请在生成的config.json中填入您的API密钥")
        print("2. OpenAI API密钥是必需的")
        print("3. 百度TTS密钥用于语音功能，可选")
        print("4. 可使用 config_init.py 进行交互式配置")


if __name__ == "__main__":
    main()