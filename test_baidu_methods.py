from downloaders.baidu_pan import BaiduPanDownloader
from downloaders.selenium_helper import verify_share_password
import time
import json
import requests

class BaiduMethodTester:
    def __init__(self, share_url, pwd):
        self.share_url = share_url
        self.pwd = pwd
        self.downloader = BaiduPanDownloader()
        self.dir_path = '/'
        
        # 提取分享ID
        if 'surl=' in self.share_url:
            self.surl = self.share_url.split('surl=')[-1].split('&')[0]
        elif 'baidu.com/s/' in self.share_url:
            self.surl = self.share_url.split('baidu.com/s/')[-1].split('?')[0]
        else:
            self.surl = self.share_url
            
        # 定义所有可能的方法
        self.methods = [
            {
                'name': 'share/filelist',
                'url': 'https://pan.baidu.com/share/filelist',
                'method': 'GET',
                'params': {
                    'surl': self.surl,
                    'pwd': self.pwd,
                    'page': '1',
                    'size': '100',
                    'path': self.dir_path,
                    'root': '0' if self.dir_path != '/' else '1',
                    'web': '1',
                    'appid': '250528',
                    'clienttype': '0',
                    'dp-logid': str(int(time.time() * 1000)),
                    'order': 'time',
                    'desc': '1',
                    'sign': self.downloader._get_sign(),
                    'timestamp': str(int(time.time())),
                    'devuid': None  # 将在登录后设置
                }
            },
            {
                'name': 'share/list',
                'url': 'https://pan.baidu.com/share/list',
                'method': 'GET',
                'params': {
                    'uk': None,  # 将在登录后设置
                    'shareid': self.surl,
                    'order': 'time',
                    'desc': '1',
                    'showempty': '0',
                    'web': '1',
                    'page': '1',
                    'num': '100',
                    'dir': self.dir_path,
                    'channel': 'chunlei',
                    'clienttype': '0',
                    'app_id': '250528',
                    'bdstoken': None  # 将在登录后设置
                }
            },
            {
                'name': 'share/browse',
                'url': 'https://pan.baidu.com/share/browse',
                'method': 'GET',
                'params': {
                    'shareid': self.surl,
                    'uk': None,  # 将在登录后设置
                    'dir': self.dir_path,
                    'web': '1',
                    'channel': 'chunlei',
                    'clienttype': '0',
                    'app_id': '250528',
                    'dp-logid': str(int(time.time() * 1000)),
                    'bdstoken': None,  # 将在登录后设置
                    'type': 'folder',
                    'start': '0',
                    'limit': '100',
                    'order': 'time',
                    'desc': '1'
                }
            },
            {
                'name': 'share/wxlist',
                'url': 'https://pan.baidu.com/share/wxlist',
                'method': 'GET',
                'params': {
                    'channel': 'chunlei',
                    'version': '2.2.2',
                    'clienttype': '0',
                    'web': '1',
                    'shorturl': self.surl,
                    'dir': self.dir_path,
                    'root': '0' if self.dir_path != '/' else '1',
                    't': str(int(time.time() * 1000))
                }
            }
        ]
        
    def prepare(self):
        """准备工作:登录并验证提取码"""
        print("=== 开始准备 ===")
        
        # 登录
        print("正在登录...")
        if not self.downloader.login():
            print("登录失败")
            return False
        print("登录成功")
        
        # 验证提取码
        init_url = f'https://pan.baidu.com/s/1{self.surl}'
        print(f"验证提取码: {init_url}")
        
        if self.pwd:
            cookies = verify_share_password(init_url, self.pwd)
            if not cookies:
                print("提取码验证失败")
                return False
                
            print("设置cookie...")
            for cookie in cookies:
                self.downloader.session.cookies.set(
                    cookie['name'],
                    cookie['value'],
                    domain=cookie.get('domain', '.baidu.com'),
                    path=cookie.get('path', '/')
                )
            print("设置cookie成功")
            
        # 更新方法参数
        baiduid = self.downloader.session.cookies.get('BAIDUID')
        bdstoken = self.downloader._get_bdstoken()
        
        for method in self.methods:
            if 'uk' in method['params']:
                method['params']['uk'] = baiduid
            if 'devuid' in method['params']:
                method['params']['devuid'] = baiduid
            if 'bdstoken' in method['params']:
                method['params']['bdstoken'] = bdstoken
                
        return True
        
    def test_all(self):
        """测试所有方法"""
        if not self.prepare():
            return
            
        print("\n=== 开始测试所有方法 ===")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': f'https://pan.baidu.com/s/1{self.surl}',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        for method in self.methods:
            print(f"\n--- 测试方法: {method['name']} ---")
            print(f"请求参数: {method['params']}")
            
            try:
                if method['method'] == 'GET':
                    resp = self.downloader.session.get(method['url'], params=method['params'], headers=headers)
                else:
                    resp = self.downloader.session.post(method['url'], data=method['params'], headers=headers)
                    
                print(f"响应状态码: {resp.status_code}")
                print(f"响应内容: {resp.text[:500]}")
                
                if resp.status_code == 200:
                    result = resp.json()
                    if result.get('errno') == 0:
                        print(f"方法 {method['name']} 成功!")
                        return result
                        
                print(f"方法 {method['name']} 失败")
                
            except Exception as e:
                print(f"方法 {method['name']} 出错: {str(e)}")
                continue
                
        print("\n所有方法都失败了")
        return None

def main():
    # 测试参数
    share_url = "https://pan.baidu.com/share/init?surl=1zNvK-93NUpOMfr2vc7hIQ"
    pwd = "79c8"
    
    # 创建测试器
    tester = BaiduMethodTester(share_url, pwd)
    
    # 运行测试
    result = tester.test_all()
    
    # 输出结果
    if result:
        print("\n=== 测试成功 ===")
        print("文件列表:", json.dumps(result.get('list', []), indent=2, ensure_ascii=False))
    else:
        print("\n=== 测试失败 ===")

if __name__ == '__main__':
    main() 