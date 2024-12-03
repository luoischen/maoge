from browser import Browser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium import webdriver
import json

class DownloadLinkTest:
    """下载链接测试类"""
    def __init__(self):
        self.browser = None
        # cookie配置 - 长期有效的cookie
        self.cookies = [
            {
                "name": "wordpress_logged_in_db1523c142c7044168e72b97cd921937",
                "value": "sanmogame%7C1733061191%7CWK4GndFAq85QMalgvS4ib2LOEmSDc8OTVhNTMy3Danm%7C867d5124e5e5b63b070a7791a23fd593028037fab914cdfb6d746db91178f610",
                "domain": "www.sanmoganme.com",
                "path": "/"
            },
            {
                "name": "b2_token",
                "value": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczpcL1wvd3d3LnNhbm1vZ2FubWUuY29tIiwiaWF0IjoxNzMzMDIwNTYwLCJuYmYiOjE3MzMwMjA1NjAsImV4cCI6MTczNDIzMDE2MCwiZGF0YSI6eyJ1c2VyIjp7ImlkIjoiMSJ9fX0.xJO8cMkSxVosAIqL30hreBJiQ1Xx6Da1vVhYWCr3lQI",
                "domain": "www.sanmoganme.com",
                "path": "/"
            }
        ]
        
    def init_browser(self):
        """初始化浏览器"""
        try:
            # 创建Chrome选项
            options = webdriver.ChromeOptions()
            # 使用无头模式
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # 创建浏览器实例
            self.browser = webdriver.Chrome(options=options)
            print("浏览器创建成功")
            return True
        except Exception as e:
            print(f"创建浏览器失败: {e}")
            return False
        
    def get_download_info(self, url):
        """获取下载信息"""
        try:
            print(f"开始获取下载信息: {url}")
            
            # 初始化浏览器
            if not self.init_browser():
                raise Exception("初始化浏览器失败")
                
            # 获取游戏ID
            game_id = url.split('/')[-1].replace('.html', '')
            print(f"游戏ID: {game_id}")
            
            result = {}
            
            # 定义所有网盘类型
            pan_types = [
                ('baidu', 0),    # 百度网盘
                ('tianyi', 1),   # 天翼网盘
                ('xunlei', 2),   # 迅雷网盘
                ('quark', 3),    # 夸克网盘
                ('aliyun', 4),   # 阿里云盘
                ('123pan', 5)    # 123网盘
            ]
            
            # 先访问一次主页以设置cookie
            self.browser.get("https://www.sanmoganme.com")
            time.sleep(1)
            
            # 添加cookie
            for cookie in self.cookies:
                self.browser.add_cookie(cookie)
            print("已添加cookie")
            
            # 获取每个网盘的下载链接
            for pan_type, index in pan_types:
                try:
                    # 访问对应的中转页
                    transfer_url = f"https://www.sanmoganme.com/download?post_id={game_id}&index=0&i={index}"
                    print(f"\n访问{pan_type}中转页: {transfer_url}")
                    
                    # 访问中转页
                    self.browser.get(transfer_url)
                    time.sleep(2)
                    
                    # 等待下载按钮出现并点击
                    try:
                        download_btn = WebDriverWait(self.browser, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.empty.button"))
                        )
                        
                        # 点击按钮
                        download_btn.click()
                        time.sleep(2)  # 等待新页面打开
                        
                        # 获取所有窗口句柄
                        handles = self.browser.window_handles
                        if len(handles) > 1:
                            # 切换到新窗口
                            self.browser.switch_to.window(handles[-1])
                            # 获取网盘链接
                            pan_url = self.browser.current_url
                            print(f"获取到{pan_type}链接: {pan_url}")
                            result[pan_type] = pan_url
                            
                            # 关闭新窗口
                            self.browser.close()
                            # 切回主窗口
                            self.browser.switch_to.window(handles[0])
                            
                    except Exception as e:
                        print(f"获取{pan_type}链接失败: {str(e)}")
                        continue
                        
                except Exception as e:
                    print(f"处理{pan_type}网盘失败: {str(e)}")
                    continue
            
            # 获取提取码和解压码
            try:
                extract_code = self.browser.find_element(By.CSS_SELECTOR, "div.tqma span#tq").get_attribute('data-clipboard-text')
                result['提取码'] = extract_code
                print(f"获取到提取码: {extract_code}")
            except:
                result['提取码'] = "无"
                print("未找到提取码")
                
            try:
                unzip_code = self.browser.find_element(By.CSS_SELECTOR, "div.tqma span#jy").get_attribute('data-clipboard-text')
                result['解压码'] = unzip_code
                print(f"获取到解压码: {unzip_code}")
            except:
                result['解压码'] = "XDGAME"
                print("使用默认解压码: XDGAME")
                
            return result
            
        except Exception as e:
            print(f"获取下载信息失败: {str(e)}")
            return {}
            
        finally:
            if self.browser:
                input("按Enter关闭浏览器...")
                self.browser.quit()

def test():
    """测试函数"""
    url = "https://www.sanmoganme.com/12950.html"
    
    tester = DownloadLinkTest()
    try:
        # 获取下载信息
        download_info = tester.get_download_info(url)
        
        # 打印结果
        print("\n获取结果:")
        for key, value in download_info.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == "__main__":
    test() 