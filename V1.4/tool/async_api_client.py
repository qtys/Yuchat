#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步API客户端模块
使用后台线程进行API调用，避免阻塞主线程和UI
"""

import threading
import queue
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime
import traceback

from tool.api_client import get_api_client, send_message_to_ai


class AsyncAPIClient:
    """异步API客户端，使用后台线程处理API调用"""
    
    def __init__(self):
        """初始化异步API客户端"""
        self._thread = None
        self._queue = queue.Queue()
        self._running = False
        self._callbacks = {}
        self._request_id = 0
        
    def start(self):
        """启动异步处理线程"""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()
            # 异步API客户端已启动
            
    def stop(self):
        """停止异步处理线程"""
        if self._running:
            self._running = False
            # 发送停止信号
            self._queue.put(None)
            if self._thread:
                self._thread.join(timeout=5)
            # 异步API客户端已停止
            
    def send_message_async(self, message_content: str, 
                          chat_history: List[Dict[str, Any]],
                          callback: Callable[[Optional[str], Optional[str]], None],
                          temperature: float = 0.7,
                          model: Optional[str] = None) -> int:
        """
        异步发送消息到AI
        
        Args:
            message_content: 用户消息内容
            chat_history: 聊天历史记录
            callback: 回调函数，参数为(response, error)
            temperature: 创造性参数
            
        Returns:
            请求ID，可用于跟踪请求
        """
        request_id = self._request_id
        self._request_id += 1
        
        # 创建请求任务
        task = {
            'id': request_id,
            'type': 'send_message',
            'message_content': message_content,
            'chat_history': chat_history,
            'temperature': temperature,
            'model': model,
            'callback': callback,
            'timestamp': datetime.now()
        }
        
        # 添加到队列
        self._queue.put(task)
        return request_id
        
    def test_connection_async(self, callback: Callable[[bool, Optional[str]], None]) -> int:
        """
        异步测试API连接
        
        Args:
            callback: 回调函数，参数为(success, error)
            
        Returns:
            请求ID
        """
        request_id = self._request_id
        self._request_id += 1
        
        task = {
            'id': request_id,
            'type': 'test_connection',
            'callback': callback,
            'timestamp': datetime.now()
        }
        
        self._queue.put(task)
        return request_id
        
    def _worker(self):
        """后台工作线程"""
        # 异步API工作线程已启动
        
        while self._running:
            try:
                # 获取任务（最多等待1秒）
                task = self._queue.get(timeout=1)
                
                # 检查是否为停止信号
                if task is None:
                    break
                    
                # 处理任务
                self._process_task(task)
                
            except queue.Empty:
                # 队列为空，继续循环
                continue
            except Exception as e:
                print(f"工作线程错误: {e}")
                traceback.print_exc()
                
        # 异步API工作线程已停止
        
    def _process_task(self, task: Dict[str, Any]):
        """处理单个任务"""
        try:
            task_type = task['type']
            callback = task.get('callback')
            
            if task_type == 'send_message':
                self._handle_send_message(task, callback)
            elif task_type == 'test_connection':
                self._handle_test_connection(callback)
            else:
                print(f"未知任务类型: {task_type}")
                
        except Exception as e:
            print(f"处理任务时发生错误: {e}")
            if callback:
                try:
                    callback(None, str(e))
                except:
                    pass
                    
    def _handle_send_message(self, task: Dict[str, Any], 
                           callback: Callable[[Optional[str], Optional[str]], None]):
        """处理发送消息任务"""
        try:
            message_content = task['message_content']
            chat_history = task['chat_history']
            temperature = task['temperature']
            model = task.get('model')
            
            print(f"异步消息处理开始: {message_content}")
            
            print(f"异步处理消息: '{message_content}'")
            print(f"消息历史: {chat_history}")
            
            # 调用同步API，传入模型参数
            response = send_message_to_ai(message_content, chat_history, temperature, model)
            
            print(f"同步API返回结果: {response is not None}")
            if response:
                print(f"返回内容长度: {len(response)}")
            
            if callback:
                if response:
                    print("调用成功回调")
                    callback(True, response, None)
                else:
                    print("调用失败回调 - AI回复为空")
                    callback(False, None, "AI回复为空")
                    
        except Exception as e:
            # 发送消息错误处理
            print(f"异步消息处理异常: {e}")
            if callback:
                print("调用异常回调")
                callback(False, None, str(e))
                
    def _handle_test_connection(self, callback: Callable[[bool, Optional[str]], None]):
        """处理测试连接任务"""
        try:
            # 异步测试API连接
            
            client = get_api_client()
            if not client:
                if callback:
                    callback(False, "API客户端未初始化")
                return
                
            success = client.test_connection()
            
            if callback:
                if success:
                    callback(True, None)
                else:
                    callback(False, "连接测试失败")
                    
        except Exception as e:
            # 测试连接失败
            if callback:
                callback(False, str(e))


# 全局异步API客户端实例
_async_api_client = None


def get_async_api_client() -> AsyncAPIClient:
    """获取全局异步API客户端实例"""
    global _async_api_client
    
    if _async_api_client is None:
        _async_api_client = AsyncAPIClient()
        _async_api_client.start()
        
    return _async_api_client


def stop_async_api_client():
    """停止全局异步API客户端"""
    global _async_api_client
    
    if _async_api_client:
        _async_api_client.stop()
        _async_api_client = None


if __name__ == "__main__":
    # 测试异步客户端
    # 测试异步API客户端
    
    async_client = get_async_api_client()
    
    # 测试连接
    def test_callback(success, error):
        if success:
            pass  # 异步连接测试成功
        else:
            pass  # 异步连接测试失败
    
    async_client.test_connection_async(test_callback)
    
    # 测试发送消息
    def message_callback(response, error):
        if response:
            print(f"[成功] 异步消息发送成功: {response[:50]}...")
        else:
            print(f"[错误] 异步消息发送失败: {error}")
    
    test_history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
    ]
    
    async_client.send_message_async("请介绍一下自己", test_history, message_callback)
    
    # 等待异步处理完成
    import time
    time.sleep(10)
    
    # 停止客户端
    stop_async_api_client()
    # 测试完成