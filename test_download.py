import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

def test_download(post_id, index, cookie):
    """测试下载功能"""
    driver = None
    try:
        # 初始化浏览器
        options = uc.ChromeOptions()
        options.add_argument('--window-size=1920,1080')
        driver = uc.Chrome(options=options)
        
        # 1. 打开详情页
        detail_url = f"https://www.sanmoganme.com/{post_id}.html"
        print(f"访问详情页: {detail_url}")
        driver.get(detail_url)
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
        
        # 2. 等待并点击详情页下载按钮
        print("等待详情页下载按钮...")
        download_buttons = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.download-button-box button.button"))
        )
        
        if len(download_buttons) > index:
            print("点击详情页下载按钮...")
            driver.execute_script("arguments[0].click();", download_buttons[index])
            time.sleep(3)
            
            # 3. 获取中转页的下载链接
            print("等待中转页下载按钮...")
            download_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#download-page a.empty.button"))
            )
            
            # 获取href属性
            href = download_link.get_attribute('href')
            print(f"下载链接: {href}")
            
            # 获取提取码和解压码
            try:
                extract_code = driver.find_element(By.CSS_SELECTOR, "#tq").get_attribute('data-clipboard-text')
                print(f"提取码: {extract_code}")
            except:
                print("未找到提取码")
            
            try:
                unzip_code = driver.find_element(By.CSS_SELECTOR, "#jy").get_attribute('data-clipboard-text')
                print(f"解压码: {unzip_code}")
            except:
                print("未找到解压码")
            
            # 等待用户查看
            input("按回车键继续...")
            
        else:
            print("未找到下载按钮")
            
    except Exception as e:
        print(f"测试失败: {str(e)}")
        
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    # 测试参数
    post_id = "12991"  # 游戏ID
    index = 0  # 0=百度网盘, 1=天翼网盘, 2=迅雷网盘, 3=夸克网盘, 4=阿里网盘, 5=123网盘
    
    # 从文件读取cookie
    try:
        with open('cookies/sanmo_cookie.txt', 'r', encoding='utf-8') as f:
            cookie = f.read().strip()
    except:
        cookie = None
        print("未找到cookie文件")
    
    # 运行测试
    test_download(post_id, index, cookie) 