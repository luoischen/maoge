import json
import os
import time
from datetime import datetime

def load_json(filepath):
    """加载JSON文件"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载JSON文件失败: {e}")
    return {}

def save_json(data, filepath):
    """保存JSON文件"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存JSON文件失败: {e}")
        return False

def load_cookie(cookie_file):
    """加载Cookie"""
    try:
        if os.path.exists(cookie_file):
            with open(cookie_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception as e:
        print(f"加载Cookie失败: {e}")
    return None

def save_cookie(cookie, cookie_file):
    """保存Cookie"""
    try:
        os.makedirs(os.path.dirname(cookie_file), exist_ok=True)
        with open(cookie_file, 'w', encoding='utf-8') as f:
            f.write(cookie)
        return True
    except Exception as e:
        print(f"保存Cookie失败: {e}")
        return False

def get_timestamp():
    """获取时间戳"""
    return datetime.now().strftime('%Y%m%d_%H%M%S') 