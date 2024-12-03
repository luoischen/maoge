from base_spider import BaseSpider
from bs4 import BeautifulSoup
import requests
import time
import random
from selenium.webdriver.common.by import By

class SanmoSpider(BaseSpider):
    """三摩游戏爬虫"""
    
    def get_game_list(self, start_page=1, end_page=10):
        """获取游戏列表"""
        games = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cookie': self.cookie if self.cookie else ''  # 添加Cookie
        }
        
        try:
            for page in range(start_page, end_page + 1):
                url = f"{self.base_url}/category/pcdanji/page/{page}" if page > 1 else f"{self.base_url}/category/pcdanji"
                print(f"正在获取第{page}页游戏列表: {url}")
                
                try:
                    response = requests.get(url, headers=headers, timeout=5)
                    print(f"页面响应状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        # 查找包含游戏列表的div
                        game_divs = soup.find_all('div', class_='item-in')
                        print(f"找到 {len(game_divs)} 个游戏div")
                        
                        page_games = []
                        for div in game_divs:
                            try:
                                # 在div中查找h2标签
                                h2 = div.find('h2')
                                if h2:
                                    link = h2.find('a')
                                    if link:
                                        title = link.text.strip()
                                        url = link.get('href', '')
                                        if url:
                                            game_id = url.split('/')[-1].replace('.html', '')
                                            game_info = {
                                                'id': game_id,
                                                'title': title,
                                                'url': url
                                            }
                                            page_games.append(game_info)
                                            print(f"找到游戏: {title} (ID: {game_id})")
                            except Exception as e:
                                print(f"处理游戏div失败: {e}")
                                continue
                        
                        print(f"第{page}页找到 {len(page_games)} 个游戏")
                        if page_games:
                            games.extend(page_games)
                        else:
                            print("当前页没有找到游戏，可能是最后一页")
                            break
                            
                    else:
                        print(f"获取页面失败，状态码: {response.status_code}")
                        break
                        
                except requests.RequestException as e:
                    print(f"请求异常: {e}")
                    break
                    
                time.sleep(0.5)
                
        except Exception as e:
            print(f"获取游戏列表失败: {e}")
        
        print(f"总共获取到 {len(games)} 个游戏")
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
            
            # 提取标题
            try:
                title_element = self.driver.find_element(By.TAG_NAME, 'h1')
                result['标题'] = title_element.text.strip()
            except Exception as e:
                print(f"提取标题失败: {e}")
            
            # 提取游戏介绍
            try:
                intro_element = self.driver.find_element(By.XPATH, "//div[@class='entry-content']/p[1]")
                result['游戏介绍'] = intro_element.text.strip()
            except Exception as e:
                print(f"提取游戏介绍失败: {e}")
            
            # 提取视频URL
            try:
                video_element = self.driver.find_element(By.TAG_NAME, 'video')
                result['视频URL'] = video_element.get_attribute('src')
            except Exception as e:
                print(f"提取视频URL失败: {e}")
            
            # 提取游戏信息
            try:
                info_element = self.driver.find_element(By.XPATH, "//h4[contains(text(), '版本介绍')]/following-sibling::p[1]")
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
            buttons = self.driver.find_elements(By.CSS_SELECTOR, '.download-button-box button')
            
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