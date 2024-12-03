import requests
import json
import os
import time
from urllib.parse import quote

class SteamImageTest:
    """Steam游戏封面获取类"""
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_search_title(self, title):
        """获取搜索用的标题"""
        # 如果包含斜杠，分别尝试中文和英文部分
        if '/' in title:
            cn_title, en_title = title.split('/', 1)
            # 优先使用中文标题
            if cn_title.strip():
                return cn_title.strip()
            # 如果中文为空，使用英文标题
            return en_title.strip()
        
        # 如果没有斜杠，直接使用完整标题
        return title.strip()
        
    def search_game(self, title):
        """搜索游戏并返回图片URL"""
        try:
            search_title = self.get_search_title(title)
            print(f"使用标题搜索: {search_title}")
            
            # 使用Steam Store API搜索
            url = f"https://store.steampowered.com/api/storesearch/?term={quote(search_title)}&l=schinese&cc=CN"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data['total'] > 0:
                game = data['items'][0]  # 获取第一个结果
                print(f"找到游戏: {game['name']}")
                
                # 获取游戏详情页
                app_id = game['id']
                
                # 构造正确的图片URL
                image_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"
                print(f"找到游戏大图URL: {image_url}")
                return image_url
            
            # 如果中文搜索失败，尝试英文搜索
            if '/' in title:
                en_title = title.split('/', 1)[1].strip()
                print(f"尝试使用英文标题搜索: {en_title}")
                url = f"https://store.steampowered.com/api/storesearch/?term={quote(en_title)}&l=english&cc=CN"
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                if data['total'] > 0:
                    game = data['items'][0]
                    print(f"找到游戏: {game['name']}")
                    
                    # 获取游戏详情页
                    app_id = game['id']
                    
                    # 构造正确的图片URL
                    image_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"
                    print(f"找到游戏大图URL: {image_url}")
                    return image_url
                
            print("未找到游戏图片")
            return None
            
        except Exception as e:
            print(f"搜索失败: {e}")
            return None

def test_search():
    """测试搜索功能"""
    # 测试游戏标题
    test_title = "纪元：变异 Anno: Mutationem"
    
    searcher = SteamImageTest()
    try:
        # 搜索游戏
        image_url = searcher.search_game(test_title)
        if image_url:
            print(f"找到图片URL: {image_url}")
        else:
            print("未找到游戏图片")
            
    except Exception as e:
        print(f"测试过程出错: {e}")

if __name__ == "__main__":
    test_search() 