import os
from pathlib import Path

# 基础路径配置
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'
RESULTS_DIR = BASE_DIR / 'results'
COOKIES_DIR = BASE_DIR / 'cookies'
CONFIG_DIR = BASE_DIR / 'config'

# 创建必要的目录
for dir_path in [DATA_DIR, LOGS_DIR, RESULTS_DIR, COOKIES_DIR, CONFIG_DIR]:
    dir_path.mkdir(exist_ok=True)

# 浏览器配置
BROWSER_CONFIG = {
    'window_size': (1920, 1080),
    'headless': True,
    'disable_gpu': True,
    'no_sandbox': True,
    'disable_dev_shm': True,
    'disable_images': True,
    'pool_size': 3,  # 浏览器池大小
    'page_load_timeout': 30,
    'implicit_wait': 10
}

# 请求配置
REQUEST_CONFIG = {
    'timeout': 10,
    'retry_times': 3,
    'retry_interval': 1,
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
}

# 采集配置
SPIDER_CONFIG = {
    'delay': (2, 4),  # 随机延迟范围
    'batch_size': 10,  # 批量采集数量
    'max_failed': 3,   # 最大失败次数
    'max_workers': 10  # 最大线程数
}

# 图片配置
IMAGE_CONFIG = {
    'size': (220, 165),
    'quality': 95,
    'format': 'JPEG',
    'search_keywords': [
        '{english} steam cover',
        '{english} game cover art',
        '{chinese} steam 封面',
        '{chinese} 游戏封面'
    ]
}

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'filename': str(LOGS_DIR / 'spider_{date}.log'),
    'encoding': 'utf-8'
}

# UI配置
UI_CONFIG = {
    'window_size': (1280, 800),
    'cards_per_page': 20,
    'search_delay': 500,  # 搜索延迟(毫秒)
    'grid_columns': 5,
    'card_size': (230, 300)
}

# 从环境变量加载配置
def load_env_config():
    """从环境变量加载配置"""
    config_updates = {}
    
    # 浏览器配置
    if os.getenv('BROWSER_POOL_SIZE'):
        config_updates['BROWSER_CONFIG.pool_size'] = int(os.getenv('BROWSER_POOL_SIZE'))
        
    # 请求配置    
    if os.getenv('REQUEST_TIMEOUT'):
        config_updates['REQUEST_CONFIG.timeout'] = int(os.getenv('REQUEST_TIMEOUT'))
        
    # 采集配置
    if os.getenv('SPIDER_MAX_WORKERS'):
        config_updates['SPIDER_CONFIG.max_workers'] = int(os.getenv('SPIDER_MAX_WORKERS'))
        
    return config_updates

# 更新配置
env_config = load_env_config()
for key, value in env_config.items():
    module_name, param = key.split('.')
    if hasattr(globals()[module_name], param):
        globals()[module_name][param] = value 