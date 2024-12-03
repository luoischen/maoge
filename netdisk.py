from browser import Browser
from selenium.webdriver.common.by import By
import time

class NetDisk(Browser):
    def __init__(self):
        super().__init__()
        
    def get_download_info(self, url, cookie=None):
        """获取下载信息"""
        try:
            self.init_driver()
            self.driver.get(url)
            time.sleep(3)
            
            if cookie:
                self.add_cookie(cookie, 'www.sanmoganme.com')
                self.driver.refresh()
                time.sleep(3)
            
            # 获取提取码和解压码
            result = {
                '提取码': self.get_extract_code(),
                '解压码': self.get_unzip_code()
            }
            
            # 获取下载链接
            download_url = self.get_download_url()
            if download_url:
                result['下载链接'] = download_url
                
            return result
            
        except Exception as e:
            print(f"获取下载信息失败: {e}")
            return None
        finally:
            self.close_driver()
            
    def get_extract_code(self):
        """获取提取码"""
        try:
            element = self.wait_for_element(By.CSS_SELECTOR, "div.tqma span#tq")
            return element.get_attribute('data-clipboard-text')
        except:
            return "无"
            
    def get_unzip_code(self):
        """获取解压码"""
        try:
            element = self.wait_for_element(By.CSS_SELECTOR, "div.tqma span#jy")
            return element.get_attribute('data-clipboard-text')
        except:
            return "XDGAME"
            
    def get_download_url(self):
        """获取下载链接"""
        try:
            download_link = self.wait_for_element(By.CSS_SELECTOR, "#download-page a.empty.button")
            current_window = self.driver.current_window_handle
            
            self.driver.execute_script("arguments[0].click();", download_link)
            time.sleep(3)
            
            for window_handle in self.driver.window_handles:
                if window_handle != current_window:
                    self.driver.switch_to.window(window_handle)
                    break
                    
            return self.driver.current_url
            
        except Exception as e:
            print(f"获取下载链接失败: {e}")
            return None 