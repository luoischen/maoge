import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import pandas as pd
import os

def test_transfer_button(transfer_url, cookie=None):
    """测试中转页按钮点击"""
    driver = None
    try:
        # 初始化浏览器
        options = uc.ChromeOptions()
        options.add_argument('--window-size=1920,1080')
        # 禁用弹窗拦截
        options.add_argument('--disable-popup-blocking')
        # 允许所有弹窗
        prefs = {
            'profile.default_content_setting_values': {
                'popups': 1,
                'notifications': 2
            }
        }
        options.add_experimental_option('prefs', prefs)
        
        driver = uc.Chrome(options=options)
        
        # 1. 直接访问中转页
        print(f"访问中转页: {transfer_url}")
        driver.get(transfer_url)
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
        
        # 2. 获取提取码和解压码
        try:
            extract_code = driver.find_element(By.CSS_SELECTOR, "div.tqma span#tq").get_attribute('data-clipboard-text')
            print(f"提取码: {extract_code}")
        except:
            extract_code = "无"
            print("未找到提取码")
        
        try:
            unzip_code = driver.find_element(By.CSS_SELECTOR, "div.tqma span#jy").get_attribute('data-clipboard-text')
            print(f"解压码: {unzip_code}")
        except:
            unzip_code = "XDGAME"
            print("未找到解压码")
        
        # 3. 获取并点击下载按钮
        print("\n等待下载按钮...")
        download_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#download-page a.empty.button"))
        )
        
        # 显示下载按钮的href属性
        href = download_link.get_attribute('href')
        print(f"下载按钮href: {href}")
        
        # 获取当前窗口句柄
        current_window = driver.current_window_handle
        
        # 点击下载按钮
        print("\n点击下载按钮...")
        driver.execute_script("arguments[0].click();", download_link)
        time.sleep(3)
        
        # 切换到新窗口
        for window_handle in driver.window_handles:
            if window_handle != current_window:
                driver.switch_to.window(window_handle)
                break
        
        # 获取最终URL
        final_url = driver.current_url
        print(f"跳转后URL: {final_url}")
        
        # 保存结果到Excel
        # 创建results目录
        os.makedirs('results', exist_ok=True)
        
        # 生成带时间戳的文件名
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f'download_test_{timestamp}.xlsx'
        filepath = os.path.join('results', filename)
        
        # 准备数据
        data = {
            '中转页URL': [transfer_url],
            '提取码': [extract_code],
            '解压码': [unzip_code],
            '下载按钮href': [href],
            '最终URL': [final_url]
        }
        
        # 保存到Excel
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False)
        print(f"\n结果已保存到: {filepath}")
        
        # 等待用户确认
        input("\n按回车键继续...")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    # 测试中转页URL
    transfer_url = "https://www.sanmoganme.com/download?post_id=12953&index=0&i=0"
    
    # 从文件读取cookie
    try:
        with open('cookies/sanmo_cookie.txt', 'r', encoding='utf-8') as f:
            cookie = f.read().strip()
    except:
        cookie = None
        print("未找到cookie文件")
    
    # 运行测试
    test_transfer_button(transfer_url, cookie) 