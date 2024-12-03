import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import pandas as pd
import os

def test_single_page(url, cookie=None):
    """测试单个页面的采集"""
    driver = None
    try:
        # 初始化浏览器
        options = uc.ChromeOptions()
        options.add_argument('--window-size=1920,1080')
        driver = uc.Chrome(options=options)
        
        # 1. 打开详情页
        print(f"访问详情页: {url}")
        driver.get(url)
        time.sleep(3)
        
        # 添加cookie
        if cookie:
            for cookie_item in cookie.split('; '):
                name, value = cookie_item.split('=', 1)
                driver.add_cookie({
                    'name': name,
                    'value': value,
                    'domain': 'www.sanmoganme.com',
                    'path': '/'
                })
            driver.refresh()
            time.sleep(3)
        
        # 2. 获取标题
        title = driver.find_element(By.TAG_NAME, 'h1').text.strip()
        print(f"标题: {title}")
        
        # 3. 点击百度网盘按钮
        print("点击百度网盘按钮...")
        download_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.download-button-box button.button"))
        )
        download_buttons[0].click()  # 点击第一个按钮(百度网盘)
        time.sleep(3)
        
        # 4. 获取中转页信息
        print("获取中转页信息...")
        
        # 等待提取码和解压码元素出现
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.tqma"))
        )
        
        # 获取提取码
        extract_code = driver.find_element(By.CSS_SELECTOR, "div.tqma span#tq").get_attribute('data-clipboard-text')
        print(f"提取码: {extract_code}")
        
        # 获取解压码
        unzip_code = driver.find_element(By.CSS_SELECTOR, "div.tqma span#jy").get_attribute('data-clipboard-text')
        print(f"解压码: {unzip_code}")
        
        # 获取下载链接
        download_link = driver.find_element(By.CSS_SELECTOR, "#download-page a.empty.button").get_attribute('href')
        print(f"下载链接: {download_link}")
        
        # 保存到Excel
        data = {
            '标题': [title],
            '百度网盘': [download_link],
            '提取码': [extract_code],
            '解压码': [unzip_code]
        }
        df = pd.DataFrame(data)
        
        # 生成带时间戳的文件名
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f'test_result_{timestamp}.xlsx'
        
        # 创建tests目录（如果不存在）
        os.makedirs('tests', exist_ok=True)
        filepath = os.path.join('tests', filename)
        
        # 保存Excel
        df.to_excel(filepath, index=False)
        print(f"\n结果已保存到: {filepath}")
        
        # 等待用户确认
        input("\n按回车键继续...")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        
    finally:
        if driver:
            try:
                driver.quit()
                time.sleep(1)  # 等待浏览器完全关闭
            except:
                pass
            driver = None

if __name__ == '__main__':
    # 测试URL
    url = "https://www.sanmoganme.com/12953.html"
    
    # 从文件读取cookie
    try:
        with open('cookies/sanmo_cookie.txt', 'r', encoding='utf-8') as f:
            cookie = f.read().strip()
    except:
        cookie = None
        print("未找到cookie文件")
    
    # 运行测试
    test_single_page(url, cookie) 