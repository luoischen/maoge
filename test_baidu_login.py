from downloaders.baidu_pan import BaiduPanDownloader
import os

def test_baidu_login():
    print("\n=== 测试百度网盘登录 ===")
    
    # 检查cookie文件
    cookie_file = os.path.join('cookies', 'baidu_cookie.txt')
    if not os.path.exists(cookie_file):
        print("错误：未找到cookie文件")
        print(f"请创建文件: {cookie_file}")
        return
        
    # 创建下载器实例
    downloader = BaiduPanDownloader()
    
    # 测试登录
    print("正在登录...")
    if downloader.login():
        print("登录成功！")
    else:
        print("登录失败！")

if __name__ == '__main__':
    test_baidu_login() 