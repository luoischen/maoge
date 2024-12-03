import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
import time
import re
import json
import traceback
from utils.logger import logger

class BaiduPanGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("百度网盘转存工具")
        self.root.geometry("800x600")
        
        # Cookie输入框
        cookie_frame = ttk.LabelFrame(root, text="Cookie设置 (从浏览器复制)", padding="5")
        cookie_frame.pack(fill="x", padx=5, pady=5)
        
        self.cookie_text = scrolledtext.ScrolledText(cookie_frame, height=4)
        self.cookie_text.pack(fill="x")
        
        # 分享链接输入框
        share_frame = ttk.LabelFrame(root, text="分享链接", padding="5")
        share_frame.pack(fill="x", padx=5, pady=5)
        
        self.url_entry = ttk.Entry(share_frame)
        self.url_entry.pack(fill="x")
        self.url_entry.insert(0, "https://pan.baidu.com/share/init?surl=OZXfJxl8wnmMzYsjw1Nzbw&pwd=uu1o")
        
        # 提取码输入框
        pwd_frame = ttk.LabelFrame(root, text="提取码", padding="5")
        pwd_frame.pack(fill="x", padx=5, pady=5)
        
        self.pwd_entry = ttk.Entry(pwd_frame)
        self.pwd_entry.pack(fill="x")
        self.pwd_entry.insert(0, "uu1o")
        
        # 转存按钮
        self.transfer_btn = ttk.Button(root, text="转存到网盘", command=self.transfer_to_pan)
        self.transfer_btn.pack(pady=5)
        
        # 日志输出
        log_frame = ttk.LabelFrame(root, text="日志", padding="5")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame)
        self.log_text.pack(fill="both", expand=True)
        
    def log(self, msg):
        """添加日志"""
        timestamp = time.strftime('%H:%M:%S', time.localtime())
        self.log_text.insert("end", f"[{timestamp}] {msg}\n")
        self.log_text.see("end")
        logger.info(msg)
        
    def transfer_to_pan(self):
        """转存到网盘"""
        try:
            # 禁用按钮
            self.transfer_btn.configure(state='disabled')
            
            # 获取输入
            cookie_str = self.cookie_text.get("1.0", "end").strip()
            share_url = self.url_entry.get().strip()
            pwd = self.pwd_entry.get().strip()
            
            if not cookie_str:
                self.log("请输入Cookie")
                return
                
            if not share_url:
                self.log("请输入分享链接")
                return
                
            # 提取surl
            if 'surl=' in share_url:
                surl = share_url.split('surl=')[-1].split('&')[0]
            elif 'baidu.com/s/' in share_url:
                surl = share_url.split('baidu.com/s/')[-1].split('?')[0]
            else:
                surl = share_url
                
            # 创建session并设置cookie
            session = requests.Session()
            for item in cookie_str.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    session.cookies.set(key, value)
                    
            # 先访问分享页面
            init_url = f'https://pan.baidu.com/share/init?surl={surl}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'https://pan.baidu.com/'
            }
            
            self.log(f"访问分享页面: {init_url}")
            session.get(init_url, headers=headers)
                    
            # 验证提取码
            verify_url = 'https://pan.baidu.com/share/verify'
            data = {
                'surl': surl,
                'pwd': pwd,
                't': str(int(time.time() * 1000)),
                'channel': 'chunlei',
                'web': '1',
                'app_id': '250528',
                'bdstoken': '',
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
            resp = session.post(verify_url, data=data, headers=headers)
            self.log(f"验证响应: {resp.text}")
            
            if resp.status_code != 200 or resp.json().get('errno') != 0:
                self.log("提取码验证失败")
                return
                
            self.log("提取码验证成功")
            
            # 获取文件信息
            resp = session.get(init_url, headers=headers)
            page_content = resp.text
            
            # 保存页面源码用于调试
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(page_content)
            self.log("页面源码已保存到 debug_page.html")
            
            # 提取必要信息
            uk_match = re.search(r'"uk":(\d+)', page_content)
            shareid_match = re.search(r'"shareid":(\d+)', page_content)
            fs_id_match = re.search(r'"fs_id":(\d+)', page_content)
            
            if not uk_match or not shareid_match or not fs_id_match:
                self.log("无法获取分享文件信息")
                return
                
            uk = uk_match.group(1)
            shareid = shareid_match.group(1)
            fs_id = fs_id_match.group(1)
            
            # 转存文件
            transfer_url = 'https://pan.baidu.com/share/transfer'
            data = {
                'from_uk': uk,
                'from_shareid': shareid,
                'from_fsids': f"[{fs_id}]",
                'sekey': session.cookies.get('BDCLND', ''),
                'to': '/我的资源',
                'ondup': 'newcopy',
                'async': '1',
                'channel': 'chunlei',
                'web': '1',
                'app_id': '250528',
                'bdstoken': '',
                'logid': str(int(time.time() * 1000)),
                'clienttype': '0'
            }
            
            self.log(f"开始转存到 /我的资源 目录...")
            self.log(f"转存参数: {data}")
            resp = session.post(transfer_url, data=data, headers=headers)
            
            if resp.status_code == 200:
                result = resp.json()
                self.log(f"转存响应: {result}")
                if result.get('errno') == 0:
                    self.log("转存成功!")
                else:
                    self.log(f"转存失败: {result.get('show_msg', '未知错误')}")
            else:
                self.log(f"转存请求失败: HTTP {resp.status_code}")
                
        except Exception as e:
            self.log(f"转存过程出错: {str(e)}")
            self.log(traceback.format_exc())
        finally:
            # 恢复按钮
            self.transfer_btn.configure(state='normal')

def main():
    root = tk.Tk()
    app = BaiduPanGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main() 