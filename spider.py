from base_spider import BaseSpider
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from selenium.webdriver.common.by import By
import requests
import os
import json
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class XDGameSpider(BaseSpider):
    """小刀游戏爬虫"""
    def __init__(self):
        self.driver = None
        self.data = []  # 用于存储采集的数据
        
    def get_game_list(self, start_page=1, end_page=10):
        """获取游戏列表"""
        games = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            for page in range(start_page, end_page + 1):
                url = f"{self.base_url}/list/1/list_{page}.html" if page > 1 else f"{self.base_url}/list/1/"
                print(f"正在获取第{page}页游戏列表: {url}")
                
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    game_links = soup.find_all('a', class_='tit')
                    
                    for link in game_links:
                        try:
                            title = link.text.strip()
                            url = link.get('href', '')
                            if url:
                                if not url.startswith('http'):
                                    url = self.base_url + url
                                game_id = url.split('/')[-1].replace('.html', '')
                                games.append({
                                    'id': game_id,
                                    'title': title,
                                    'url': url
                                })
                                print(f"找到游戏: {title} ({url})")
                        except Exception as e:
                            print(f"提取游戏信息失败: {e}")
                            continue
                
                time.sleep(0.5)
                
        except Exception as e:
            print(f"获取游戏列表失败: {e}")
            
        return games

    def parse_detail_page(self, url):
        """解析详情页"""
        try:
            self.driver.get(url)
            time.sleep(2)
            
            result = {
                '标题': '',
                '游戏介绍': '',
                '视频URL': '',
                '图片URL': '',
                '游戏信息': '',
                '百度网盘': '',
                '天翼网盘': '',
                '迅雷网盘': '',
                '阿里网盘': '',
                '夸克网盘': '',
                '123网盘': ''
            }
            
            # 使用配置中的选择器
            selectors = self.config.get('selectors', {})
            
            # 提取标题
            try:
                title_element = self.driver.find_element(By.CSS_SELECTOR, selectors.get('title', 'h1'))
                result['标题'] = title_element.text.strip()
            except Exception as e:
                print(f"提取标题失败: {e}")
            
            # 提取游戏介绍
            try:
                intro_element = self.driver.find_element(By.XPATH, selectors.get('intro', "//div[@class='entry-content']/p[1]"))
                result['游戏介绍'] = intro_element.text.strip()
            except Exception as e:
                print(f"提取游戏介绍失败: {e}")
            
            # 提取视频URL
            try:
                video_element = self.driver.find_element(By.TAG_NAME, selectors.get('video', 'video'))
                result['视频URL'] = video_element.get_attribute('src')
            except Exception as e:
                print(f"提取视频URL失败: {e}")
            
            # 提取游戏信息
            try:
                info_element = self.driver.find_element(By.XPATH, selectors.get('info', "//h4[contains(text(), '版本介绍')]/following-sibling::p[1]"))
                result['游戏信息'] = info_element.text.strip()
            except Exception as e:
                print(f"提取游戏信息失败: {e}")
            
            # 提取下载链接
            download_info = self.extract_download_info(url)
            result.update(download_info)
            
            return result
            
        except Exception as e:
            print(f"解析详情页失败: {e}")
            return None

    def extract_download_info(self, url):
        """提取下载信息"""
        game_id = url.split('/')[-1].replace('.html', '')
        result = {
            '百度网盘': '',
            '天翼网盘': '',
            '迅雷网盘': '',
            '阿里网盘': '',
            '夸克网盘': '',
            '123网盘': ''
        }
        
        try:
            # 获取所有下载按钮
            buttons = self.driver.find_elements(By.CSS_SELECTOR, self.config['selectors']['download_buttons'])
            
            for i, button in enumerate(buttons):
                try:
                    # 构建中转页URL
                    transfer_url = f"{self.base_url}/download?post_id={game_id}&index=0&i={i}"
                    self.driver.get(transfer_url)
                    time.sleep(1)
                    
                    # 获取实际下载链接
                    current_url = self.driver.current_url
                    
                    # 根据按钮顺序保存到对应网盘
                    pan_types = ['百度网盘', '天翼网盘', '迅雷网盘', '阿里网盘', '夸克网盘', '123网盘']
                    if i < len(pan_types):
                        result[pan_types[i]] = current_url
                        
                except Exception as e:
                    print(f"获取第{i+1}个下载链接失败: {e}")
                    continue
                    
        except Exception as e:
            print(f"提取下载信息失败: {e}")
            
        return result

    def save_to_excel(self):
        """保存数据到Excel文件"""
        try:
            # 检查是否有数据要保存
            if not self.data:
                print("没有数据需要保存")
                return False
                
            # 获取当前日期作为文件名的一部分
            current_date = time.strftime("%Y%m%d")
            filename = f"游戏数据_{current_date}.xlsx"
            
            # 将数据转换为DataFrame
            df = pd.DataFrame(self.data)
            
            # 如果文件已存在，则追加数据
            if os.path.exists(filename):
                existing_df = pd.read_excel(filename)
                df = pd.concat([existing_df, df], ignore_index=True)
                # 删除重复行
                df = df.drop_duplicates(subset=['标题'], keep='last')
            
            # 保存到Excel
            df.to_excel(filename, index=False)
            print(f"数据已保存到文件: {filename}")
            return True
            
        except Exception as e:
            print(f"保存到Excel失败: {e}")
            return False

    def process_url(self, url):
        """处理单个URL"""
        try:
            game_info = self.parse_detail_page(url)
            if game_info:
                self.data.append(game_info)  # 确保将数据添加到self.data列表
                return True
        except Exception as e:
            print(f"处理URL失败: {e}")
        return False

class SanmoSpider:
    """山猫游戏爬虫"""
    
    def __init__(self):
        self.config = self.load_config()
        self.data = []
        self.driver = None
        self.progress = None
        self.cookie = None
        
    def load_config(self):
        """加载配置"""
        try:
            with open('sites_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config['sites']['sanmo']
        except Exception as e:
            print(f"加载配置失败: {e}")
            return {
                'selectors': {
                    'title': 'h1',
                    'download_links': {
                        '百度网盘': "//a[contains(@href,'pan.baidu.com')]",
                        '天翼网盘': "//a[contains(@href,'cloud.189.cn')]",
                        '迅雷网盘': "//a[contains(@href,'pan.xunlei.com')]",
                        '阿里网盘': "//a[contains(@href,'aliyundrive.com')]",
                        '夸克网盘': "//a[contains(@href,'pan.quark.cn')]",
                        '123网盘': "//a[contains(@href,'123pan.com')]"
                    }
                }
            }
    
    def init_driver(self):
        """初始化浏览器"""
        if not self.driver:
            options = uc.ChromeOptions()
            options.add_argument('--window-size=1920,1080')
            self.driver = uc.Chrome(options=options)
    
    def close_driver(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def get_game_list(self, start_page, end_page):
        """获取游戏列表"""
        games = []
        for page in range(start_page, end_page + 1):
            try:
                url = self.config['selectors']['list_url'].format(page=page) if page > 1 else self.config['selectors']['list_first_url']
                self.driver.get(url)
                time.sleep(2)
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                game_links = soup.select(self.config['selectors']['game_link'])
                
                for link in game_links:
                    title = link.text.strip()
                    url = link.get('href', '')
                    if url:
                        game_id = url.split('/')[-1].replace('.html', '')
                        games.append({
                            'id': game_id,
                            'title': title,
                            'url': url
                        })
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"获取第{page}页失败: {e}")
                continue
                
        return games
    
    def parse_detail_page(self, url):
        """解析详情页"""
        try:
            self.driver.get(url)
            time.sleep(2)
            
            # 获取标题
            title = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, self.config['selectors']['title']))
            ).text.strip()
            
            # 获取下载链接
            result = {'标题': title}
            
            for pan_name, xpath in self.config['selectors']['download_links'].items():
                try:
                    links = self.driver.find_elements(By.XPATH, xpath)
                    if links:
                        result[pan_name] = links[0].get_attribute('href')
                except:
                    continue
            
            return result
            
        except Exception as e:
            print(f"解析页面失败: {e}")
            return None
    
    def save_to_excel(self):
        """保存数据到Excel"""
        if self.data:
            import pandas as pd
            df = pd.DataFrame(self.data)
            filename = f"游戏数据_{time.strftime('%Y%m%d')}.xlsx"
            df.to_excel(filename, index=False)
            print(f"数据已保存到: {filename}")

    def get_download_link(self, transfer_url):
        """获取下载链接"""
        driver = None
        try:
            # 初始化浏览器
            options = uc.ChromeOptions()
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-popup-blocking')  # 禁用弹窗拦截
            prefs = {
                'profile.default_content_setting_values': {
                    'popups': 1,
                    'notifications': 2
                }
            }
            options.add_experimental_option('prefs', prefs)
            
            driver = uc.Chrome(options=options)
            
            # 1. 直接访问中转页
            self.progress.emit(f"访问中转页: {transfer_url}")
            driver.get(transfer_url)
            time.sleep(3)
            
            # 添加cookie
            if self.cookie:
                for cookie_item in self.cookie.split('; '):
                    name, value = cookie_item.split('=', 1)
                    driver.add_cookie({
                        'name': name,
                        'value': value,
                        'domain': 'www.sanmoganme.com',
                        'path': '/'
                    })
                driver.refresh()
                time.sleep(3)
            
            # 2. 获取提取码和解压码
            try:
                extract_code = driver.find_element(By.CSS_SELECTOR, "div.tqma span#tq").get_attribute('data-clipboard-text')
                self.progress.emit(f"提取码: {extract_code}")
            except:
                extract_code = "无"
                self.progress.emit("未找到提取码")
            
            try:
                unzip_code = driver.find_element(By.CSS_SELECTOR, "div.tqma span#jy").get_attribute('data-clipboard-text')
                self.progress.emit(f"解压码: {unzip_code}")
            except:
                unzip_code = "XDGAME"
                self.progress.emit("未找到解压码")
            
            # 3. 获取并点击下载按钮
            self.progress.emit("\n等待下载按钮...")
            download_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#download-page a.empty.button"))
            )
            
            # 获取当前窗口句柄
            current_window = driver.current_window_handle
            
            # 点击下载按钮
            self.progress.emit("\n点击下载按钮...")
            driver.execute_script("arguments[0].click();", download_link)
            time.sleep(3)
            
            # 切换到新窗口
            for window_handle in driver.window_handles:
                if window_handle != current_window:
                    driver.switch_to.window(window_handle)
                    break
            
            # 获取最终URL
            final_url = driver.current_url
            self.progress.emit(f"跳转后URL: {final_url}")
            
            return final_url, extract_code, unzip_code
            
        except Exception as e:
            self.progress.emit(f"获取下载链接失败: {str(e)}")
            return None, None, None
            
        finally:
            if driver:
                try:
                    driver.quit()
                    time.sleep(1)
                except:
                    pass

    def set_progress_signal(self, signal):
        """设置进度信号"""
        self.progress = signal

    def set_cookie(self, cookie):
        """设置cookie"""
        self.cookie = cookie