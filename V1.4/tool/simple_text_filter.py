import re
import unicodedata


class SimpleTextFilter:
    """简化文本过滤器类"""
    
    # 可配置的 emoji 移除范围（按需修改）
    EMOJI_RANGES = [
        (0x1F600, 0x1F64F),  # emoticons（笑脸等）
        (0x1F300, 0x1F5FF),  # symbols & pictographs（符号图示）
        (0x1F680, 0x1F6FF),  # transport & map（交通工具、地图）
        (0x1F1E0, 0x1F1FF),  # flags（国旗）
        (0x2600, 0x26FF),    # miscellaneous symbols（杂项符号，含太阳、星星等）
        (0x2700, 0x27BF),    # dingbats（装饰符号）
        (0x1F900, 0x1F9FF),  # supplemental symbols and pictographs
        (0x1FA70, 0x1FAFF),  # newer emoji block
        (0x1F000, 0x1F02F),  # Mahjong Tiles & Dominoes（麻将、骨牌）
        (0x1F0A0, 0x1F0FF),  # Playing Cards（扑克牌）
        (0x1F100, 0x1F64F),  # Enclosed Characters（方形符号）
        (0x2300, 0x23FF),    # Miscellaneous Technical（技术符号）
        (0x2B50, 0x2B55),    # Stars（星形）
        (0x1F18E, 0x1F251),  # Additional emoticons range
    ]
    
    # 要过滤的少见字符范围（泰文、老挝文等）
    RARE_CHAR_RANGES = [
        (0x0E00, 0x0E7F),    # Thai（泰文）
        (0x0E80, 0x0EFF),    # Lao（老挝文）
        (0x0F00, 0x0FFF),    # Tibetan（藏文）
        (0x1000, 0x109F),    # Myanmar（缅甸文）
        (0x17E0, 0x17FF),    # Khmer（高棉文）
        (0x1A00, 0x1A1F),    # Buginese（布基文）
    ]
    
    # 若要完全禁用 emoji 移除，设置为 False
    ENABLE_EMOJI_REMOVAL = True
    
    # 若要禁用少见字符移除，设置为 False
    ENABLE_RARE_CHAR_REMOVAL = True
    
    # 若要保留特定 emoji 字符，添加到此列表（如 '😀', '❤' 等）
    EMOJI_WHITELIST = []
    
    @staticmethod
    def remove_think_tags(text):
        """移除 <think>...</think> 标签块（用于移除 AI 内部思考过程）"""
        if not text:
            return text
        
        # 移除 <think>...</think> 标签及其内容（支持换行和任意内容）
        text = re.sub(r'<think>[\s\S]*?</think>\s*', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = text.strip()
        return text
    
    @staticmethod
    def remove_markdown(text):
        """移除markdown格式标记"""
        if not text:
            return text
            
        text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`(.*?)`', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', text)
        text = re.sub(r'\|', '', text)
        text = re.sub(r'-{3,}', '', text)
        text = re.sub(r'^\s*[-*+]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\*{3,}$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^_{3,}$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        return text
    
    @staticmethod
    def is_emoji_char(ch):
        """检查字符是否为 emoji（按照配置的范围）"""
        if not SimpleTextFilter.ENABLE_EMOJI_REMOVAL:
            return False
        
        # 若在白名单中，保留
        if ch in SimpleTextFilter.EMOJI_WHITELIST:
            return False
        
        o = ord(ch)
        for start, end in SimpleTextFilter.EMOJI_RANGES:
            if start <= o <= end:
                return True
        return False
    
    @staticmethod
    def is_rare_char(ch):
        """检查字符是否为少见字符（泰文、老挝文等）"""
        if not SimpleTextFilter.ENABLE_RARE_CHAR_REMOVAL:
            return False
        
        o = ord(ch)
        for start, end in SimpleTextFilter.RARE_CHAR_RANGES:
            if start <= o <= end:
                return True
        return False
    
    @staticmethod
    def remove_emoji(text, strict=False):
        """
        移除 emoji，但保留标点、中文、颜文字等可见符号。
        
        Args:
            text: 原始文本
            strict: 若为 True，只保留 ASCII 字母/数字/常见标点；
                   若为 False，保留所有非 emoji 的可见 Unicode 字符（包括颜文字）
        """
        if not text:
            return text
        
        if not SimpleTextFilter.ENABLE_EMOJI_REMOVAL:
            return text

        allowed_prefix = ("L", "N", "P", "S", "Z")
        out_chars = []
        
        for ch in text:
            # 跳过 emoji 字符
            if SimpleTextFilter.is_emoji_char(ch):
                continue
            
            # 跳过少见字符（泰文等）
            if SimpleTextFilter.is_rare_char(ch):
                continue
            
            cat = unicodedata.category(ch)
            
            if strict:
                # 严格模式：只保留基础 ASCII + 中文 + 常见标点
                if cat and cat[0] in ("L", "N"):  # 字母、数字
                    out_chars.append(ch)
                elif cat == "Po":  # 其它标点
                    out_chars.append(ch)
                elif ch in ("\n", "\r", "\t", " ", "，", "。", "！", "？", "；", "：", """, """, "、"):
                    out_chars.append(ch)
            else:
                # 非严格模式（默认）：保留所有非 emoji 的可见字符
                if cat and cat[0] in allowed_prefix:
                    out_chars.append(ch)
                elif ch in ("\n", "\r", "\t", " "):
                    out_chars.append(ch)

        result = "".join(out_chars)
        # 合并多余空格（保留换行）
        result = re.sub(r'[ \t]+', ' ', result)
        result = re.sub(r'\n\s*\n', '\n\n', result)
        return result.strip()
    
    @staticmethod
    def clean_text(text, remove_think=True, remove_markdown=True, remove_emoji=True, strict_emoji=False):
        """
        综合清理文本
        
        Args:
            text: 原始文本
            remove_think: 是否移除 <think>...</think> 标签
            remove_markdown: 是否移除 markdown 标记
            remove_emoji: 是否移除 emoji
            strict_emoji: emoji 移除是否为严格模式
        """
        if not text:
            return text
        
        # 最先移除 think 标签（可能影响后续处理）
        if remove_think:
            text = SimpleTextFilter.remove_think_tags(text)
        
        if remove_markdown:
            text = SimpleTextFilter.remove_markdown(text)
        
        if remove_emoji:
            text = SimpleTextFilter.remove_emoji(text, strict=strict_emoji)
            
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def add_emoji_range(start, end):
        """动态添加 emoji 移除范围"""
        SimpleTextFilter.EMOJI_RANGES.append((start, end))
    
    @staticmethod
    def add_rare_char_range(start, end):
        """动态添加少见字符移除范围"""
        SimpleTextFilter.RARE_CHAR_RANGES.append((start, end))
    
    @staticmethod
    def add_emoji_whitelist(emoji_chars):
        """添加 emoji 白名单（这些 emoji 不会被移除）"""
        SimpleTextFilter.EMOJI_WHITELIST.extend(emoji_chars)
    
    @staticmethod
    def set_emoji_removal_enabled(enabled):
        """启用/禁用 emoji 移除功能"""
        SimpleTextFilter.ENABLE_EMOJI_REMOVAL = enabled
    
    @staticmethod
    def set_rare_char_removal_enabled(enabled):
        """启用/禁用少见字符移除功能"""
        SimpleTextFilter.ENABLE_RARE_CHAR_REMOVAL = enabled