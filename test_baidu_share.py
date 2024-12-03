import unittest
from downloaders.baidu_pan import BaiduPanDownloader
import time

class TestBaiduShare(unittest.TestCase):
    def setUp(self):
        self.downloader = BaiduPanDownloader()
        # 确保先登录
        self.assertTrue(self.downloader.login(), "登录失败")
        
    def test_transfer_file(self):
        """测试文件转存功能"""
        # 1. 先检查网盘根目录
        print("\n=== 检查网盘目录 ===")
        check_url = 'https://pan.baidu.com/api/list'
        params = {
            'dir': '/',
            'order': 'name',
            'desc': '0',
            'showempty': '0',
            'web': '1',
            'page': '1',
            'num': '100',
            'channel': 'chunlei',
            'app_id': '250528',
            'clienttype': '0'
        }
        resp = self.downloader.session.get(check_url, params=params)
        print(f"目录列表响应: {resp.text}")
        
        # 2. 尝试转存文件
        print("\n=== 测试转存文件 ===")
        # 使用一个测试分享链接
        share_url = "https://pan.baidu.com/s/11zNvK-93NUpOMfr2vc7hIQ"  # 替换为实际的分享链接
        pwd = "test"  # 替换为实际的提取码
        
        result = self.downloader.parse_share_url(share_url, pwd)
        self.assertIsNotNone(result, "转存失败")
        print(f"转存结果: {result}")
        
        # 3. 等待一下让转存完成
        time.sleep(5)
        
        # 4. 检查转存后的文件
        print("\n=== 检查转存后的文件 ===")
        check_url = 'https://pan.baidu.com/api/list'
        params = {
            'dir': '/Downloads',  # 检查 Downloads 目录
            'order': 'name',
            'desc': '0',
            'showempty': '0',
            'web': '1',
            'page': '1',
            'num': '100',
            'channel': 'chunlei',
            'app_id': '250528',
            'clienttype': '0'
        }
        resp = self.downloader.session.get(check_url, params=params)
        print(f"转存后目录列表响应: {resp.text}")
        
        # 5. 验证文件是否存在
        files = resp.json().get('list', [])
        found = False
        for file in files:
            if file.get('server_filename') == result['filename']:
                found = True
                print(f"找到转存的文件: {file}")
                break
                
        self.assertTrue(found, "未找到转存的文件")

if __name__ == '__main__':
    unittest.main() 