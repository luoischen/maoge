from abc import ABC, abstractmethod
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import json

class BaseSpider(ABC):
    """基础爬虫类"""
    def __init__(self, site_config):
        self.name = site_config.get('name', '未命名站点')
        self.base_url = site_config.get('base_url', '')
        self.config = site_config.get('config', {})
        self.driver = None
        self.data = []
        self.cookie = self.load_cookie()
    
    def load_cookie(self):
        """从文件加载Cookie"""
        try:
            with open(f'cookies/{self.name}_cookie.txt', 'r', encoding='utf-8') as f:
                return f.read().strip()
        except:
            return None
    
    def init_driver(self):
        """初始化浏览器"""
        options = uc.ChromeOptions()
        options.add_argument('--window-size=1920,1080')
        self.driver = uc.Chrome(options=options)
        return self.set_cookies()
    
    def set_cookies(self):
        """设置Cookie"""
        if not self.cookie:
            return True
            
        try:
            self.driver.get(self.base_url)
            time.sleep(2)
            
            # 设置Cookie
            for cookie in self.parse_cookies(self.cookie):
                self.driver.add_cookie(cookie)
            
            self.driver.refresh()
            return True
        except Exception as e:
            print(f"设置Cookie失败: {e}")
            return False
    
    def parse_cookies(self, cookie_string):
        """解析Cookie字符串"""
        cookies = []
        for item in cookie_string.split(';'):
            if '=' in item:
                name, value = item.strip().split('=', 1)
                cookies.append({
                    'name': name,
                    'value': value,
                    'domain': f".{self.base_url.split('//')[1].split('/')[0]}",
                    'path': '/'
                })
        return cookies
    
    @abstractmethod
    def get_game_list(self, start_page=1, end_page=10):
        """获取游戏列表"""
        pass
    
    @abstractmethod
    def parse_detail_page(self, url):
        """解析详情页"""
        pass
    
    @abstractmethod
    def extract_download_info(self, url):
        """提取下载信息"""
        pass
    
    def close_driver(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            self.driver = None 