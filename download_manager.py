from PyQt5.QtCore import QThread, pyqtSignal
from downloaders.baidu_pan import BaiduPanDownloader
from downloaders.aliyun_pan import AliyunPanDownloader
from downloaders.download_task import DownloadTask, TaskStatus
import os
import time

class DownloadManager(QThread):
    """下载管理器"""
    progress = pyqtSignal(str)  # 进度信号
    task_progress = pyqtSignal(str, float)  # 任务进度信号(任务ID, 进度)
    task_status = pyqtSignal(str, str)  # 任务状态信号(任务ID, 状态)
    task_error = pyqtSignal(str, str)  # 任务错误信号(任务ID, 错误信息)
    
    def __init__(self):
        super().__init__()
        self.tasks = {}  # 任务字典
        self.downloaders = {
            'baidu': BaiduPanDownloader(),
            'aliyun': AliyunPanDownloader(),
            # TODO: 添加其他网盘下载器
        }
        self.is_running = True
        
    def add_task(self, game_info):
        """添加下载任务"""
        try:
            # 检查网盘链接
            pan_types = ['baidu', 'aliyun', 'quark', 'xunlei', 'tianyi', '123pan']
            available_pan = None
            for pan_type in pan_types:
                if pan_type in game_info:
                    available_pan = pan_type
                    break
                    
            if available_pan:
                # 处理游戏标题
                title = game_info['title']
                if '/' in title:
                    cn_title, en_title = title.split('/', 1)
                    title = cn_title.strip()
                
                # 创建保存路径
                save_dir = os.path.join('downloads', title)
                os.makedirs(save_dir, exist_ok=True)
                
                # 创建任务
                task = DownloadTask(
                    url=game_info[available_pan],
                    save_path=save_dir,
                    pwd=game_info.get('提取码')
                )
                
                # 添加到任务列表
                task_id = str(int(time.time()))
                self.tasks[task_id] = task
                self.progress.emit(f"添加下载任务: {title}")
                
                return task_id
            else:
                self.progress.emit("未找到可用的网盘链接")
                return None
                
        except Exception as e:
            self.progress.emit(f"添加任务失败: {str(e)}")
            return None
            
    def start_task(self, task_id):
        """开始下载任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.start()
            self.task_status.emit(task_id, TaskStatus.DOWNLOADING.value)
            
    def pause_task(self, task_id):
        """暂停任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.pause()
            self.task_status.emit(task_id, TaskStatus.PAUSED.value)
            
    def resume_task(self, task_id):
        """恢复任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.resume()
            self.task_status.emit(task_id, TaskStatus.DOWNLOADING.value)
            
    def remove_task(self, task_id):
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.progress.emit(f"删除任务: {task_id}")
            
    def run(self):
        """运行下载管理器"""
        while self.is_running:
            try:
                # 处理所有等待中的任务
                for task_id, task in self.tasks.items():
                    if task.status == TaskStatus.WAITING:
                        self.process_task(task_id, task)
                        
                time.sleep(1)  # 避免CPU占用过高
                
            except Exception as e:
                self.progress.emit(f"下载管理器运行错误: {str(e)}")
                
    def process_task(self, task_id, task):
        """处理单个下载任务"""
        try:
            # 获取下载器
            downloader = self.downloaders['baidu']
            
            # 登录
            if not downloader.login():
                raise Exception("登录失败")
                
            # 解析分享链接
            share_info = downloader.parse_share_url(task.url, task.pwd)
            if not share_info:
                raise Exception("解析分享链接失败")
                
            # 获取下载链接
            dlink = downloader.get_download_link(share_info['fs_id'])
            if not dlink:
                raise Exception("获取下载链接失败")
                
            # 开始下载
            def progress_callback(current, total):
                task.update_progress(current, total)
                self.task_progress.emit(task_id, task.progress)
                
            success = downloader.download_file(
                dlink,
                task.save_path,
                progress_callback
            )
            
            if success:
                task.complete()
                self.task_status.emit(task_id, TaskStatus.COMPLETED.value)
            else:
                raise Exception("下载失败")
                
        except Exception as e:
            task.fail(str(e))
            self.task_error.emit(task_id, str(e))
            self.task_status.emit(task_id, TaskStatus.FAILED.value)
            
    def stop(self):
        """停止下载管理器"""
        self.is_running = False 