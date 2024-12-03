from queue import Queue
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class BrowserPool:
    """浏览器实例池"""
    def __init__(self, pool_size=3):
        self.pool_size = pool_size
        self.available = Queue()
        self.in_use = set()
        self.lock = threading.Lock()
        
        # 初始化浏览器池
        for _ in range(pool_size):
            browser = self.create_browser()
            if browser:
                self.available.put(browser)
    
    def create_browser(self):
        """创建新的浏览器实例"""
        try:
            # 使用 webdriver_manager 自动下载和管理 chromedriver
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # 禁用图片加载
            prefs = {
                'profile.managed_default_content_settings.images': 2,
                'profile.default_content_setting_values': {
                    'notifications': 2
                }
            }
            options.add_experimental_option('prefs', prefs)
            
            # 使用 webdriver_manager 自动管理 chromedriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            print("浏览器创建成功")
            return driver
                
        except Exception as e:
            print(f"创建浏览器实例失败: {e}")
            return None
    
    def get_browser(self, timeout=30):
        """获取浏览器实例"""
        try:
            browser = self.available.get(timeout=timeout)
            with self.lock:
                self.in_use.add(browser)
            return browser
        except:
            return self.create_browser()
    
    def return_browser(self, browser):
        """归还浏览器实例"""
        if browser:
            with self.lock:
                if browser in self.in_use:
                    self.in_use.remove(browser)
                    # 检查浏览器是否仍然可用
                    if self.check_browser(browser):
                        self.available.put(browser)
                    else:
                        self.replace_browser()
    
    def check_browser(self, browser):
        """检查浏览器是否可用"""
        try:
            browser.current_url
            return True
        except:
            try:
                browser.quit()
            except:
                pass
            return False
    
    def replace_browser(self):
        """替换失效的浏览器"""
        browser = self.create_browser()
        if browser:
            self.available.put(browser)
    
    def close_all(self):
        """关闭所有浏览器"""
        # 关闭可用的浏览器
        while not self.available.empty():
            browser = self.available.get()
            try:
                browser.quit()
            except:
                pass
        
        # 关闭使用中的浏览器
        with self.lock:
            for browser in self.in_use:
                try:
                    browser.quit()
                except:
                    pass
            self.in_use.clear()

class Browser:
    """浏览器管理类"""
    _pool = None
    
    @classmethod
    def init_pool(cls, pool_size=3):
        """初始化浏览器池"""
        if not cls._pool:
            cls._pool = BrowserPool(pool_size)
    
    def __init__(self):
        self.driver = None
        if not self._pool:
            self.init_pool()
    
    def init_driver(self):
        """初始化浏览器"""
        if not self.driver:
            self.driver = self._pool.get_browser()
        return self.driver is not None
    
    def close_driver(self):
        """关闭浏览器"""
        if self.driver:
            self._pool.return_browser(self.driver)
            self.driver = None
    
    def wait_for_element(self, by, value, timeout=10):
        """等待元素出现"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    
    def add_cookie(self, cookie_str, domain):
        """添加Cookie"""
        if cookie_str and self.driver:
            for cookie_item in cookie_str.split('; '):
                name, value = cookie_item.split('=', 1)
                self.driver.add_cookie({
                    'name': name,
                    'value': value,
                    'domain': domain,
                    'path': '/'
                }) 