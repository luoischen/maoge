from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QProgressBar, QTextEdit, QLabel, 
                           QMessageBox, QTreeWidget, QTreeWidgetItem, QSplitter, 
                           QLineEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from downloaders.baidu_pan import BaiduPanDownloader
from downloaders.selenium_helper import verify_share_password
from test_baidu_share_list import ShareListTester
import sys
import os
import time
import json
import re
import random
import html
from urllib.parse import unquote
import requests
from urllib.parse import parse_qs, urlparse

class PanListWorker(QThread):
    """网盘列表获取线程"""
    progress = pyqtSignal(str)  # 进度信号
    files_found = pyqtSignal(list)  # 文件列表信号
    
    def __init__(self, path='/'):  # 默认获取根目录
        super().__init__()
        self.path = path
        self.downloader = BaiduPanDownloader()
        
    def run(self):
        try:
            self.progress.emit("\n=== 获取网盘文件列表 ===")
            
            # 登录
            self.progress.emit("正在登录...")
            if not self.downloader.login():
                self.progress.emit("登录失败")
                return
            self.progress.emit("登录成功")
            
            # 获取文件列表
            self.progress.emit(f"\n获取目录: {self.path}")
            check_url = 'https://pan.baidu.com/api/list'
            params = {
                'dir': self.path,
                'order': 'time',  # 按时间排序
                'desc': '1',      # 降序
                'showempty': '1', # 显示空目录
                'web': '1',
                'page': '1',
                'num': '1000',    # 获取更多文件
                'channel': 'chunlei',
                'app_id': '250528',
                'bdstoken': self.downloader._get_bdstoken(),  # 添加bdstoken
                'clienttype': '0'
            }
            
            self.progress.emit(f"请求参数: {params}")
            resp = self.downloader.session.get(check_url, params=params)
            self.progress.emit(f"响应状态码: {resp.status_code}")
            self.progress.emit(f"响应内容: {resp.text[:500]}")  # 添加响应内容输出
            
            if resp.status_code == 200:
                result = resp.json()
                if result.get('errno') == 0:
                    files = result.get('list', [])
                    # 添加文件类型标记
                    for file in files:
                        file['is_dir'] = file.get('isdir') == 1
                    self.files_found.emit(files)
                    self.progress.emit(f"找到 {len(files)} 个文件/文件夹")
                else:
                    self.progress.emit(f"获取文件列表失败: errno={result.get('errno')}")
                    if 'show_msg' in result:
                        self.progress.emit(f"错误信息: {result['show_msg']}")
            else:
                self.progress.emit(f"请求失败: HTTP {resp.status_code}")
                
        except Exception as e:
            self.progress.emit(f"获取文件列表出错: {str(e)}")
            import traceback
            self.progress.emit(traceback.format_exc())

class ShareInfoWorker(QThread):
    """分享链接信息获取线程"""
    progress = pyqtSignal(str)  # 进度信号
    files_found = pyqtSignal(list)  # 文件列表信号
    finished = pyqtSignal()  # 添加完成信号
    
    def __init__(self, share_url, pwd, dir_path='/'):
        super().__init__()
        self.share_url = share_url
        self.pwd = pwd
        self.dir_path = dir_path
        self.downloader = BaiduPanDownloader()  # 使用 BaiduPanDownloader
        
        # 提取分享ID
        if 'surl=' in self.share_url:
            self.surl = self.share_url.split('surl=')[-1].split('&')[0]
        elif 'baidu.com/s/' in self.share_url:
            self.surl = self.share_url.split('baidu.com/s/')[-1].split('?')[0]
        else:
            self.surl = self.share_url
        
    def run(self):
        try:
            self.progress.emit("\n=== 获取分享链接信息 ===")
            
            # 使用新的 session
            session = requests.Session()
            
            # 先访问分享页面
            init_url = f'https://pan.baidu.com/s/1{self.surl}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'https://pan.baidu.com/'
            }
            
            session.get(init_url, headers=headers)
            
            # 验证提取码
            verify_url = 'https://pan.baidu.com/share/verify'
            data = {
                'surl': self.surl,
                'pwd': self.pwd,
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
            
            resp = session.post(verify_url, data=data, headers=headers)
            if resp.status_code != 200 or resp.json().get('errno') != 0:
                self.progress.emit("提取码验证失败")
                return
                
            # 获取页面内容
            resp = session.get(init_url, headers=headers)
            page_content = resp.text
            
            # 从页面提取文件列表
            match = re.search(r'yunData\.FILEINFO\s*=\s*(\[.*?\]);', page_content)
            if match:
                data_str = match.group(1)
                files = json.loads(data_str)
                
                # 添加路径信息
                for file in files:
                    if 'path' not in file:
                        file['path'] = os.path.join(self.dir_path, file['server_filename']).replace('\\', '/')
                        
                self.progress.emit(f"成功获取到 {len(files)} 个文件")
                self.files_found.emit(files)
                
        except Exception as e:
            self.progress.emit(f"获取分享信息失败: {str(e)}")
            import traceback
            self.progress.emit(traceback.format_exc())
        finally:
            self.finished.emit()

class TestWindow(QWidget):
    """测试窗口"""
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        # 创建布局
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 修改为两列布局
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧分享链接测试区域
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题
        left_title = QLabel("分享链接测试")
        left_title.setStyleSheet('''
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
                background: #f0f0f0;
                border-radius: 3px;
            }
        ''')
        left_layout.addWidget(left_title)
        
        # 添加输入框
        input_layout = QHBoxLayout()
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('输入分享链接')
        self.url_input.setText("https://pan.baidu.com/share/init?surl=OZXfJxl8wnmMzYsjw1Nzbw&pwd=uu1o")
        input_layout.addWidget(self.url_input)
        
        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText('提取码(选填)')
        self.pwd_input.setText("")  # 不需要手动输入提取码
        self.pwd_input.setFixedWidth(100)
        input_layout.addWidget(self.pwd_input)
        
        left_layout.addLayout(input_layout)
        
        # 转存按钮
        self.start_btn = QPushButton('转存到网盘', self)
        self.start_btn.setFixedHeight(35)
        self.start_btn.setStyleSheet('''
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:disabled {
                background: #cccccc;
            }
        ''')
        self.start_btn.clicked.connect(self.transfer_to_pan)
        left_layout.addWidget(self.start_btn)
        
        # 日志区域
        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet('''
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
                background: white;
            }
        ''')
        left_layout.addWidget(self.log_text)
        
        left_widget.setLayout(left_layout)
        
        # 右侧网盘文件列表区域
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题
        right_title = QLabel("网盘文件列表")
        right_title.setStyleSheet('''
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
                background: #f0f0f0;
                border-radius: 3px;
            }
        ''')
        right_layout.addWidget(right_title)
        
        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        # 返回上级目录按钮
        back_btn = QPushButton('返回上级')
        back_btn.setFixedHeight(30)
        back_btn.setStyleSheet('''
            QPushButton {
                background: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #F57C00;
            }
        ''')
        back_btn.clicked.connect(self.goToParentDir)
        toolbar.addWidget(back_btn)
        
        refresh_btn = QPushButton('刷新列表')
        refresh_btn.setFixedHeight(30)
        refresh_btn.setStyleSheet('''
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #388E3C;
            }
        ''')
        refresh_btn.clicked.connect(self.refreshPanList)
        toolbar.addWidget(refresh_btn)
        
        self.path_label = QLabel('/')
        self.path_label.setStyleSheet('''
            QLabel {
                padding: 5px;
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
        ''')
        toolbar.addWidget(self.path_label)
        
        toolbar.addStretch()
        right_layout.addLayout(toolbar)
        
        # 文件列表树
        self.pan_tree = QTreeWidget()
        self.pan_tree.setHeaderLabels(['文件', '大小', '修改时间', '类型'])
        self.pan_tree.setColumnWidth(0, 300)
        self.pan_tree.setStyleSheet('''
            QTreeWidget {
                border: 1px solid #cccccc;
                border-radius: 3px;
                background: white;
            }
            QTreeWidget::item {
                height: 25px;
            }
            QTreeWidget::item:hover {
                background: #f0f0f0;
            }
            QTreeWidget::item:selected {
                background: #e3f2fd;
                color: black;
            }
            QHeaderView::section {
                background: #f5f5f5;
                padding: 5px;
                border: none;
                border-right: 1px solid #ddd;
            }
        ''')
        # 添加双击事件处理
        self.pan_tree.itemDoubleClicked.connect(self.onItemDoubleClicked)
        right_layout.addWidget(self.pan_tree)
        
        right_widget.setLayout(right_layout)
        
        # 添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
        # 设置窗口
        self.setWindowTitle('度网盘转存工具')
        self.resize(1200, 800)
        
        # 创建网盘列表线程
        self.pan_list_thread = None
        
        # 加载网盘文件列表
        self.refreshPanList()
        
    def refreshPanList(self):
        """刷新网盘文件列表"""
        try:
            # 清空列表
            self.pan_tree.clear()
            
            # 创建并启动列表获取线程
            self.pan_list_thread = PanListWorker()
            self.pan_list_thread.progress.connect(self.update_log)
            self.pan_list_thread.files_found.connect(self.updatePanList)
            self.pan_list_thread.start()
            
        except Exception as e:
            self.update_log(f"刷新网盘列表失败: {str(e)}")
            
    def updatePanList(self, files):
        """更新网盘文件列表"""
        try:
            self.pan_tree.clear()
            
            for file in files:
                item = QTreeWidgetItem()
                item.setText(0, file.get('server_filename', ''))
                
                # 保存文件信息到item的data中
                item.setData(0, Qt.UserRole, file)
                
                # 格式化文件大小
                size = int(file.get('size', 0))
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.1f} KB"
                elif size < 1024 * 1024 * 1024:
                    size_str = f"{size/1024/1024:.1f} MB"
                else:
                    size_str = f"{size/1024/1024/1024:.2f} GB"
                item.setText(1, size_str)
                
                # 格式化修改间
                mtime = int(file.get('server_mtime', 0))
                time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
                item.setText(2, time_str)
                
                # 文件类型
                is_dir = file.get('isdir') == 1
                item.setText(3, '文件夹' if is_dir else '文件')
                
                # 设图标
                if is_dir:
                    item.setIcon(0, self.style().standardIcon(self.style().SP_DirIcon))
                else:
                    item.setIcon(0, self.style().standardIcon(self.style().SP_FileIcon))
                
                self.pan_tree.addTopLevelItem(item)
                
        except Exception as e:
            self.update_log(f"更新网盘列表失败: {str(e)}")
            import traceback
            self.update_log(traceback.format_exc())

    def transfer_to_pan(self):
        """转存分享内容到盘"""
        try:
            share_url = self.url_input.text().strip()
            if not share_url:
                self.update_log("请输入分享链接")
                return
            
            pwd = self.pwd_input.text().strip()
            self.update_log(f"开始转存分享内容...")
            self.update_log(f"分享链接: {share_url}")
            self.update_log(f"提取码: {pwd}")
            
            # 禁用按钮
            self.start_btn.setEnabled(False)
            
            # 创建并启动转存线程
            self.transfer_thread = TransferWorker(share_url, pwd)
            self.transfer_thread.progress.connect(self.update_log)
            self.transfer_thread.finished.connect(self.on_transfer_finished)
            self.transfer_thread.start()
            
        except Exception as e:
            self.update_log(f"转存失败: {str(e)}")
            import traceback
            self.update_log(traceback.format_exc())
            self.start_btn.setEnabled(True)

    def on_transfer_finished(self):
        """转存完成后的处理"""
        self.start_btn.setEnabled(True)
        self.refreshPanList()  # 刷新网盘列表

    def updateShareFileList(self, files):
        """更新分享文件列表"""
        try:
            self.share_tree.clear()
            
            for file in files:
                item = QTreeWidgetItem()
                item.setText(0, file.get('server_filename', ''))
                
                # 保存完整的文件信息
                item.setData(0, Qt.UserRole, file)
                
                # 格式化文件大小
                size = int(file.get('size', 0))
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.1f} KB"
                elif size < 1024 * 1024 * 1024:
                    size_str = f"{size/1024/1024:.1f} MB"
                else:
                    size_str = f"{size/1024/1024/1024:.2f} GB"
                item.setText(1, size_str)
                
                # 文件类型
                is_dir = file.get('isdir') == 1
                item.setText(2, '文件夹' if is_dir else '文件')
                
                # 设置图标
                if is_dir:
                    item.setIcon(0, self.style().standardIcon(self.style().SP_DirIcon))
                else:
                    item.setIcon(0, self.style().standardIcon(self.style().SP_FileIcon))
                
                self.share_tree.addTopLevelItem(item)
                
        except Exception as e:
            self.update_log(f"更新分享文件列表失败: {str(e)}")

    def onItemDoubleClicked(self, item, column):
        """双击文件夹时进入该目录"""
        try:
            # 获取文件信息
            file_info = item.data(0, Qt.UserRole)
            if not file_info:
                return
            
            # 只处理文件夹
            if not file_info.get('isdir'):
                return
            
            # 获取文件夹路径
            folder_path = file_info.get('path', '')
            if not folder_path:
                current_path = self.path_label.text().rstrip('/')
                folder_path = f"{current_path}/{file_info['server_filename']}"
            
            self.update_log(f"进入目录: {folder_path}")
            
            # 更新路径标签
            self.path_label.setText(folder_path)
            
            # 刷新当前目录的文件列表
            self.pan_list_thread = PanListWorker(folder_path)  # 传入新路径
            self.pan_list_thread.progress.connect(self.update_log)
            self.pan_list_thread.files_found.connect(self.updatePanList)
            self.pan_list_thread.start()
            
        except Exception as e:
            self.update_log(f"进入目录失败: {str(e)}")
            import traceback
            self.update_log(traceback.format_exc())

    def goToParentDir(self):
        """返回上级目录"""
        try:
            current_path = self.path_label.text()
            if current_path == '/':
                return
                
            parent_path = os.path.dirname(current_path)
            if not parent_path:
                parent_path = '/'
            parent_path = parent_path.replace('\\', '/')  # 使用正杠
            
            self.path_label.setText(parent_path)
            self.refreshPanList()
            
        except Exception as e:
            self.update_log(f"返回上级目录失败: {str(e)}")

    def update_log(self, text):
        """更新日志"""
        try:
            # 添加时间戳
            timestamp = time.strftime('%H:%M:%S', time.localtime())
            log_text = f"[{timestamp}] {text}"
            
            # 添加到日志文本框
            self.log_text.append(log_text)
            
            # 动到底部
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            print(f"更新日志失败: {str(e)}")
            
    def update_progress(self, percent):
        """更新进度条"""
        try:
            self.progress_bar.setValue(percent)
            self.progress_label.setText(f'进度: {percent}%')
        except Exception as e:
            print(f"更新进度失败: {str(e)}")

    def onShareItemDoubleClicked(self, item, column):
        """双击分享文件夹时进入目录或下载文件"""
        try:
            # 获取文件信息
            file_info = item.data(0, Qt.UserRole)
            if not file_info:
                return
            
            # 如是文件夹，进入该目录
            if file_info.get('isdir'):
                folder_path = file_info.get('path', '')
                if not folder_path:
                    folder_path = f"/{file_info['server_filename']}"
                
                self.update_log(f"进入分目: {folder_path}")
                
                # 获取分享链接和提取码
                share_url = self.url_input.text().strip()
                pwd = self.pwd_input.text().strip()
                
                # 创建并启动新的分享信息获取线程
                self.share_info_thread = ShareInfoWorker(share_url, pwd, folder_path)
                self.share_info_thread.progress.connect(self.update_log)
                self.share_info_thread.files_found.connect(self.updateShareFileList)
                self.share_info_thread.start()
                
            # 如果是文件，开始下载
            else:
                self.update_log(f"开始下载: {file_info['server_filename']}")
                
                # 创建并启动下载线程
                self.download_thread = DownloadWorker(file_info)
                self.download_thread.progress.connect(self.update_log)
                self.download_thread.download_progress.connect(self.update_progress)
                self.download_thread.start()
                
        except Exception as e:
            self.update_log(f"处理文件失败: {str(e)}")
            import traceback
            self.update_log(traceback.format_exc())

class DownloadWorker(QThread):
    """下载线程"""
    progress = pyqtSignal(str)  # 日志信号
    download_progress = pyqtSignal(int)  # 下载进度信号
    
    def __init__(self, file_info):
        super().__init__()
        self.file_info = file_info
        self.downloader = BaiduPanDownloader()
        
    def run(self):
        try:
            self.progress.emit("\n=== 开始下载文件 ===")
            
            # 登录
            self.progress.emit("正登录...")
            if not self.downloader.login():
                self.progress.emit("登录失败")
                return
            self.progress.emit("登录成功")
            
            # 获取下载链接
            self.progress.emit("\n获取下载链接...")
            dlink = self.downloader.get_download_link(self.file_info['fs_id'])
            if not dlink:
                self.progress.emit("获取下载链接失败")
                return
                
            # 开始下载
            save_path = os.path.join('downloads', self.file_info['server_filename'])
            self.progress.emit(f"\n下载到: {save_path}")
            
            def progress_callback(downloaded, total, speed):
                percent = int(downloaded / total * 100)
                self.download_progress.emit(percent)
                
            result = self.downloader.download_file(dlink, save_path, progress_callback)
            
            if result:
                self.progress.emit("\n下载完成!")
            else:
                self.progress.emit("\n下载失败!")
                
        except Exception as e:
            self.progress.emit(f"下载失���: {str(e)}")
            import traceback
            self.progress.emit(traceback.format_exc())

class TransferWorker(QThread):
    """转存线程"""
    progress = pyqtSignal(str)  # 进度信号
    finished = pyqtSignal()  # 完成信号
    
    def __init__(self, share_url, pwd):
        super().__init__()
        self.share_url = share_url
        self.pwd = pwd
        self.downloader = BaiduPanDownloader()
        
        # 提取分享ID和提取码
        if 'surl=' in self.share_url:
            # 从URL中提取surl和pwd
            try:
                query = self.share_url.split('?')[1]
                params = {}
                for param in query.split('&'):
                    if '=' in param:
                        key, value = param.split('=')
                        params[key] = value
                self.surl = params.get('surl', '')
                # 如果没有手动输入提取码，使用URL中的提取码
                if not self.pwd and 'pwd' in params:
                    self.pwd = params['pwd']
            except:
                self.surl = self.share_url.split('surl=')[-1].split('&')[0]
        elif 'baidu.com/s/' in self.share_url:
            self.surl = self.share_url.split('baidu.com/s/')[-1].split('?')[0]
        else:
            self.surl = self.share_url
    
    def run(self):
        try:
            # 登录
            self.progress.emit("正在登录...")
            if not self.downloader.login():
                self.progress.emit("登录失败")
                return
            self.progress.emit("登录成功")
            
            # 先访问分享页面
            init_url = f'https://pan.baidu.com/share/init?surl={self.surl}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'https://pan.baidu.com/'
            }
            
            self.progress.emit(f"访问分享页面: {init_url}")
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
            
            self.progress.emit("验证提取码...")
            resp = self.downloader.session.post(verify_url, data=data, headers=headers)
            self.progress.emit(f"验证响应: {resp.text}")
            
            if resp.status_code != 200 or resp.json().get('errno') != 0:
                self.progress.emit("提取码验证失败")
                return
            
            self.progress.emit("提取码验证成功")
            
            # 获取页面内容
            resp = self.downloader.session.get(init_url, headers=headers)
            page_content = resp.text
            
            # 保存页面源码用于调试
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(page_content)
            self.progress.emit("页面源码已保存到 debug_page.html")
            
            # 提取 uk 和 shareid
            uk_match = re.search(r'"uk":\s*"?(\d+)"?', page_content)
            shareid_match = re.search(r'"shareid":\s*"?(\d+)"?', page_content)
            fs_id_match = re.search(r'"fs_id":\s*"?(\d+)"?', page_content)
            
            if not uk_match or not shareid_match or not fs_id_match:
                self.progress.emit("无法获取分享文件信息")
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
                'sekey': self.downloader.session.cookies.get('BDCLND', ''),
                'to': '/我的资源',
                'ondup': 'newcopy',
                'async': '1',
                'channel': 'chunlei',
                'web': '1',
                'app_id': '250528',
                'bdstoken': self.downloader._get_bdstoken(),
                'logid': str(int(time.time() * 1000)),
                'clienttype': '0'
            }
            
            self.progress.emit(f"开始转存到 /我的资源 目录...")
            self.progress.emit(f"转存参数: {data}")
            resp = self.downloader.session.post(transfer_url, data=data, headers=headers)
            
            if resp.status_code == 200:
                result = resp.json()
                self.progress.emit(f"转存响应: {result}")
                if result.get('errno') == 0:
                    self.progress.emit("转存成功!")
                else:
                    self.progress.emit(f"转存失败: {result.get('show_msg', '未知错误')}")
            else:
                self.progress.emit(f"转存请求失败: HTTP {resp.status_code}")
                
        except Exception as e:
            self.progress.emit(f"转存过程出错: {str(e)}")
            import traceback
            self.progress.emit(traceback.format_exc())
        finally:
            self.finished.emit()

def main():
    try:
        # 确保只有一个 QApplication 实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 创建下载目录
        downloads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        print(f"下载目录: {downloads_dir}")
        
        # 创建并显示窗口
        window = TestWindow()
        window.show()
        
        # 运行应用
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 