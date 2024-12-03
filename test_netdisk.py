import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import pandas as pd
import os

def test_get_netdisk_link(url, cookie=None):
    """测试获取网盘链接"""
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
        
        # 3. 获取所有下载按钮
        print("\n获取所有下载按钮...")
        download_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.download-button-box button.button"))
        )
        
        # 4. 遍历所有网盘按钮
        pan_types = ['百度网盘', '天翼网盘', '迅雷网盘', '夸克网盘', '阿里网盘', '123网盘']
        results = {'标题': title}
        
        for i, button in enumerate(download_buttons):
            if i >= len(pan_types):
                break
                
            pan_name = pan_types[i]
            print(f"\n测试{pan_name}...")
            
            # 点击网盘按钮
            print(f"点击{pan_name}按钮")
            driver.execute_script("arguments[0].click();", button)
            time.sleep(3)
            
            # 获取中转页URL
            transfer_url = driver.current_url
            print(f"中转页URL: {transfer_url}")
            
            # 获取提取码和解压码
            try:
                extract_code = driver.find_element(By.CSS_SELECTOR, "div.tqma span#tq").get_attribute('data-clipboard-text')
                print(f"提取码: {extract_code}")
                results['提取码'] = extract_code
            except:
                print("未找到提取码")
            
            try:
                unzip_code = driver.find_element(By.CSS_SELECTOR, "div.tqma span#jy").get_attribute('data-clipboard-text')
                print(f"解压码: {unzip_code}")
                results['解压码'] = unzip_code
            except:
                print("未找到解压码")
            
            # 获取下载链接
            try:
                # 获取当前窗口句柄
                current_window = driver.current_window_handle
                
                # 点击下载按钮
                download_link = driver.find_element(By.CSS_SELECTOR, "#download-page a.empty.button")
                driver.execute_script("arguments[0].click();", download_link)
                time.sleep(3)
                
                # 切换到新窗口
                for window_handle in driver.window_handles:
                    if window_handle != current_window:
                        driver.switch_to.window(window_handle)
                        break
                
                # 获取网盘链接
                final_url = driver.current_url
                print(f"{pan_name}链接: {final_url}")
                results[pan_name] = final_url
                
                # 关闭当前窗口，切回主窗口
                driver.close()
                driver.switch_to.window(current_window)
                
                # 返回详情页继续测试下一个网盘
                driver.get(url)
                time.sleep(3)
                
                # 重新获取下载按钮
                download_buttons = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.download-button-box button.button"))
                )
                
            except Exception as e:
                print(f"获取{pan_name}链接失败: {e}")
        
        # 保存结果到Excel
        df = pd.DataFrame([results])
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f'netdisk_test_{timestamp}.xlsx'
        os.makedirs('tests', exist_ok=True)
        filepath = os.path.join('tests', filename)
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
                time.sleep(1)
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
    test_get_netdisk_link(url, cookie) 