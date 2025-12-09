# 配置管理指南

本目录包含聊天应用的配置管理和初始化工具。

## 文件说明

### 📁 主要文件

| 文件名 | 功能描述 | 使用场景 |
|--------|----------|----------|
| `config.json` | 应用配置文件 | 存储所有配置参数 |
| `config_init.py` | 交互式配置向导 | 第一次配置或重新配置 |
| `config_generator.py` | 快速配置文件生成器 | 快速生成默认配置 |

## 🚀 快速开始

### 方法1: 使用交互式配置向导（推荐）

```bash
# 运行交互式配置向导
python config/config_init.py
```

**特点：**
- ✅ 自动检查现有配置
- ✅ 交互式配置设置
- ✅ 实时配置验证
- ✅ 详细配置说明

### 方法2: 使用快速生成器

```bash
# 生成默认配置文件
python config/config_generator.py
```

**特点：**
- ⚡ 一键生成默认配置
- 📋 显示配置字段说明
- 🔄 可强制覆盖现有配置

## 📝 配置说明

### OpenAI 配置（必需）
```json
{
    "openai": {
        "api_key": "sk-...",        // 您的API密钥
        "base_url": "https://api.yuegle.com/v1",  // API地址
        "model": "deepseek-v3"      // 使用的模型
    }
}
```

### 百度TTS 配置（可选，语音功能）
```json
{
    "baidu_tts": {
        "api_key": "...",           // 百度API Key
        "secret_key": "..."         // 百度Secret Key
    }
}
```

### 应用配置
```json
{
    "app": {
        "data_file": "chat_data.json",              // 聊天数据文件
        "context_length": 50,                       // 上下文长度
        "available_models": [...],                  // 可用模型列表
        "background_image": "image1.png",           // 背景图片
        "current_character": "AI"                   // 当前角色
    }
}
```

## 🛠️ 配置字段详解

| 字段 | 说明 | 示例值 |
|------|------|--------|
| `api_key` | OpenAI API密钥 | `sk-xxxxxxxxxxxx` |
| `base_url` | API基础地址 | `https://api.yuegle.com/v1` |
| `model` | 使用的AI模型 | `deepseek-v3` |
| `data_file` | 聊天记录存储文件 | `chat_data.json` |
| `context_length` | 对话上下文长度 | `50` |
| `available_models` | 可选择的模型列表 | `["gpt-4", "deepseek-v3"]` |

## 🔧 使用流程

### 首次配置
1. **复制环境变量**：
   ```bash
   cp .env.example .env
   # 或者直接生成配置
   python config/config_generator.py
   ```

2. **编辑配置**：
   - 手动编辑 `config.json`
   - 或者使用交互式向导：`python config/config_init.py`

3. **填入API密钥**：
   - OpenAI API密钥（必需）
   - 百度TTS密钥（语音功能需要）

### 重新配置
```bash
# 使用交互式向导重新配置
python config/config_init.py
```

### 验证配置
```bash
# 运行配置验证（检查必需字段）
python config/config_init.py --validate
```

## ⚠️ 注意事项

1. **安全提示**：
   - API密钥是敏感信息，请妥善保管
   - 不要将包含密钥的配置文件提交到版本控制
   - 建议使用环境变量存储密钥

2. **文件路径**：
   - 所有路径都是相对路径（相对于应用根目录）
   - 确保相关目录和文件存在

3. **模型兼容性**：
   - `available_models` 中的模型名称需要与您的API兼容
   - 不同API提供商可能有不同的模型名称

## 📋 故障排除

### 配置文件不存在
```bash
# 自动生成配置文件
python config/config_generator.py
```

### 配置格式错误
1. 运行交互式向导重新配置
2. 检查JSON格式是否正确
3. 参考本README中的示例配置

### API连接失败
1. 检查 `api_key` 是否正确
2. 确认 `base_url` 是否可访问
3. 检查网络连接

## 🔄 更新历史

- **v1.0** - 初始版本
  - 交互式配置向导
  - 快速配置文件生成器
  - 配置验证功能