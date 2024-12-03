from downloaders.baidu_pan import BaiduPanDownloader
from downloaders.selenium_helper import verify_share_password
import time
import json
import re
import logging
import os
import html
from urllib.parse import unquote

# 配置日志
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ShareListTester:
    def __init__(self, share_url, pwd, progress_callback=None):
        self.share_url = share_url
        self.pwd = pwd
        self.dir_path = '/'
        self.downloader = BaiduPanDownloader()
        self.progress_callback = progress_callback
        
        # 提取分享ID
        if 'surl=' in self.share_url:
            self.surl = self.share_url.split('surl=')[-1].split('&')[0]
        elif 'baidu.com/s/' in self.share_url:
            self.surl = self.share_url.split('baidu.com/s/')[-1].split('?')[0]
        else:
            self.surl = self.share_url
            
        if self.progress_callback:
            self.progress_callback(f"初始化完成: surl={self.surl}")
        
    def log(self, msg):
        """输出日志"""
        logger.info(msg)
        if self.progress_callback:
            self.progress_callback(msg)
        
    def prepare(self):
        """准备工作:登录并验证提取码"""
        self.log("=== 开始准备 ===")
        
        # 登录
        self.log("正在登录...")
        if not self.downloader.login():
            self.log("登录失败")
            return False
        self.log("登录成功")
        
        # 先访问分享页面
        init_url = f'https://pan.baidu.com/s/1{self.surl}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://pan.baidu.com/'
        }
        
        self.log(f"访问分享页面: {init_url}")
        self.downloader.session.get(init_url, headers=headers)
        
        # 验证提取码
        verify_url = 'https://pan.baidu.com/share/verify'
        data = {
            'surl': self.surl,
            'pwd': self.pwd,
            't': str(int(time.time() * 1000)),
            'channel': 'chunlei',
            'web': '1',
            'app_id': '250528',
            'bdstoken': self.downloader._get_bdstoken(),
            'logid': str(int(time.time() * 1000)),
            'clienttype': '0'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://pan.baidu.com',
            'Referer': init_url,
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        self.log("验证提取码...")
        self.log(f"验证请求参数: {data}")
        resp = self.downloader.session.post(verify_url, data=data, headers=headers)
        self.log(f"验证响应: {resp.text}")
        
        if resp.status_code != 200 or resp.json().get('errno') != 0:
            self.log("提取码验证失败")
            return False
            
        self.log("提取码验证成功")
        return True
        
    def get_file_list(self):
        """获取文件列表"""
        if not self.prepare():
            return None
            
        # 访问分享页面
        init_url = f'https://pan.baidu.com/s/1{self.surl}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://pan.baidu.com/',
            'Cookie': '; '.join([f'{k}={v}' for k, v in self.downloader.session.cookies.items()])
        }
        
        self.log("获取页面内容...")
        resp = self.downloader.session.get(init_url, headers=headers)
        page_content = resp.text
        
        # 保存页面源码
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(page_content)
        self.log("页面源码已保存到 debug_page.html")
        
        # 尝试从页面中提取文件列表
        self.log("从页面提取文件列表...")
        
        patterns = [
            # 基础模式
            (r'yunData\.FILEINFO\s*=\s*(\[.*?\]);', 'yunData.FILEINFO'),
            (r'yunData\.SHARE_FILE_LIST\s*=\s*(\[.*?\]);', 'yunData.SHARE_FILE_LIST'),
            (r'locals\.mset\s*=\s*({.*?});', 'locals.mset'),
            (r'filedata\s*=\s*({.*?});', 'filedata'),
            
            # HTML 属性模式
            (r'data-context="([^"]+)"', 'data-context'),
            (r'data-fileinfo="([^"]+)"', 'data-fileinfo'),
            
            # JavaScript 对象模式
            (r'var\s+context\s*=\s*({[^;]+?});', 'var context'),
            (r'var\s+yunData\s*=\s*({[^;]+?});', 'var yunData'),
            (r'locals\.mset\s*=\s*({[^;]+?});', 'locals.mset (non-greedy)'),
            
            # JSON 数据模式
            (r'"currentProduct"\s*:\s*"share"[^}]*"list"\s*:\s*(\[.*?\])', 'share product list'),
            (r'{"list":\s*(\[.*?\])}', 'list object'),
            (r'"file_list"\s*:\s*(\[.*?\])', 'file_list array'),
            
            # Script 标签模式
            (r'<script\s+id="shareInfo"\s+type="text/javascript">\s*(.*?)\s*</script>', 'shareInfo script'),
            (r'require\.async\([^)]+,\s*({[^}]+})\);', 'require.async data')
        ]
        
        for pattern, name in patterns:
            try:
                self.log(f"\n尝试模式: {name}")
                matches = re.finditer(pattern, page_content, re.DOTALL)
                for match in matches:
                    try:
                        data_str = match.group(1)
                        self.log(f"找到匹配: {data_str[:200]}")
                        
                        # 处理 HTML 编码的数据
                        if 'data-' in name:
                            data_str = html.unescape(data_str)
                            data_str = unquote(data_str)
                        
                        # 处理 JavaScript 对象
                        data_str = data_str.replace("'", '"')
                        data_str = re.sub(r'(\w+):', r'"\1":', data_str)
                        data_str = re.sub(r',(\s*[}\]])', r'\1', data_str)
                        data_str = re.sub(r':\s*undefined\b', ':null', data_str)
                        data_str = re.sub(r':\s*function\s*\([^)]*\)\s*{[^}]*}', ':null', data_str)
                        
                        try:
                            data = json.loads(data_str)
                            if isinstance(data, list):
                                files = data
                            elif isinstance(data, dict):
                                for key in ['list', 'file_list', 'files', 'FILEINFO', 'SHARE_FILE_LIST']:
                                    if key in data:
                                        files = data[key]
                                        if isinstance(files, list):
                                            break
                                else:
                                    continue
                            else:
                                continue
                                
                            # 添加路径信息
                            for file in files:
                                if 'path' not in file:
                                    file['path'] = os.path.join(self.dir_path, file['server_filename']).replace('\\', '/')
                                    
                            self.log(f"成功获取到 {len(files)} 个文件")
                            return files
                            
                        except json.JSONDecodeError as e:
                            self.log(f"JSON 解析失败: {str(e)}, 数据: {data_str[:200]}")
                            continue
                            
                    except Exception as e:
                        self.log(f"处理匹配项失败: {str(e)}")
                        continue
                        
            except Exception as e:
                self.log(f"模式 {name} 失败: {str(e)}")
                continue
                
        self.log("无法从页面提取文件列表")
        return None

def main():
    # 测试参数
    share_url = "https://pan.baidu.com/share/init?surl=1zNvK-93NUpOMfr2vc7hIQ"
    pwd = "79c8"
    
    # 创建测试器
    tester = ShareListTester(share_url, pwd)
    
    # 获取文件列表
    files = tester.get_file_list()
    
    # 输出结果
    if files:
        print("\n=== 获取成功 ===")
        print("文件列表:", json.dumps(files, indent=2, ensure_ascii=False))
    else:
        print("\n=== 获取失败 ===")

if __name__ == '__main__':
    main() 