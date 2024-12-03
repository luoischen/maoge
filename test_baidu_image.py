import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os
import time
import re

def clean_title(title):
    """清理游戏标题"""
    # 分离中英文标题
    if '/' in title:
        chinese, english = title.split('/', 1)
    else:
        chinese = english = title
        
    # 清理标题
    chinese = re.sub(r'[【\[\(（].*?[】\]\)）]', '', chinese)
    chinese = re.sub(r'\d{4}.*$', '', chinese)
    chinese = chinese.strip()
    
    english = re.sub(r'[【\[\(（].*?[】\]\)）]', '', english)
    english = re.sub(r'\d{4}.*$', '', english)
    english = english.strip()
    
    return chinese, english

def test_baidu_image_search(keyword):
    """测试百度图片搜索"""
    print(f"\n原始关键词: {keyword}")
    
    # 初始化浏览器
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    driver = uc.Chrome(options=options)
    
    try:
        # 访问百度图片
        url = f"https://image.baidu.com/search/index?tn=baiduimage&word={keyword}"
        print(f"访问URL: {url}")
        driver.get(url)
        
        # 等待页面加载
        time.sleep(3)
        
        # 等待图片元素出现
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "imgitem"))
        )
        
        # 获取所有图片元素
        img_elements = driver.find_elements(By.CLASS_NAME, "imgitem")
        print(f"找到 {len(img_elements)} 个图片元素")
        
        if img_elements:
            # 创建测试目录
            os.makedirs('test_images', exist_ok=True)
            
            # 下载前5张图片
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://image.baidu.com'
            }
            
            for i, img in enumerate(img_elements[:5], 1):
                try:
                    # 获取大图URL
                    img_url = img.get_attribute('data-objurl')
                    if not img_url:
                        # 尝试获取缩略图URL
                        img_url = img.get_attribute('data-thumburl')
                    
                    if img_url:
                        print(f"\n图片 {i}:")
                        print(f"URL: {img_url}")
                        
                        # 下载图片
                        response = requests.get(img_url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            img_path = f'test_images/test_{i}.jpg'
                            with open(img_path, 'wb') as f:
                                f.write(response.content)
                            print(f"已保存到: {img_path}")
                        else:
                            print(f"下载失败: {response.status_code}")
                except Exception as e:
                    print(f"处理图片失败: {e}")
                    continue
        else:
            print("未找到图片元素")
            
    except Exception as e:
        print(f"搜索失败: {e}")
        
    finally:
        driver.quit()

if __name__ == '__main__':
    # 测试几个游戏标题
    test_cases = [
        "Cyberpunk 2077/赛博朋克2077",
        "God of War/战神4",
        "Starfield/星空",
        "The Last of Us/最后生还者",
        "Elden Ring/艾尔登法环"
    ]
    
    for title in test_cases:
        print("\n" + "="*50)
        chinese, english = clean_title(title)
        print(f"处理后的标题: 中文[{chinese}] 英文[{english}]")
        
        # 优先使用英文标题搜索
        keywords = [
            f"{english} game cover",
            f"{english} box art",
            f"{english} poster",
            f"{chinese} 游戏封面"
        ]
        
        for keyword in keywords:
            print("\n" + "-"*30)
            test_baidu_image_search(keyword)
            input("\n按回车继续下一个测试...") 