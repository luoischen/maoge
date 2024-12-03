from PyQt5.QtCore import QThread, pyqtSignal
from netdisk import NetDisk
from workers.info_worker import InfoWorker
import time
import random
import settings
from errors import *

class BatchWorker(QThread):
    """批量采集线程"""
    progress = pyqtSignal(str)  # 进度信号
    finished = pyqtSignal(list) # 完成信号,返回采集结果
    error = pyqtSignal(str)     # 错误信号
    
    def __init__(self, games, cookie=None):
        super().__init__()
        self.games = games
        self.cookie = cookie
        self.results = []
        self.is_running = True
        self.failed_count = 0
        
    def run(self):
        try:
            total = len(self.games)
            self.progress.emit(f"开始批量采集 {total} 个游戏")
            
            for i, game in enumerate(self.games, 1):
                if not self.is_running:
                    break
                    
                if self.failed_count >= settings.SPIDER_CONFIG['max_failed']:
                    raise SpiderError("失败次数过多,停止采集")
                    
                try:
                    self.progress.emit(f"\n采集第 {i}/{total} 个游戏")
                    result = self.collect_game(game)
                    if result:
                        self.results.append(result)
                except Exception as e:
                    self.failed_count += 1
                    self.error.emit(f"采集游戏失败: {str(e)}")
                    continue
                    
                # 随机延迟
                delay = settings.SPIDER_CONFIG['delay']
                time.sleep(random.uniform(*delay))
                
            self.finished.emit(self.results)
            
        except Exception as e:
            self.error.emit(f"批量采集失败: {str(e)}")
            
    def collect_game(self, game):
        """采集单个游戏"""
        # 采集基本信息
        info_worker = InfoWorker(game['url'])
        info_worker.run()
        result = info_worker.collect_info()
        
        # 采集下载信息
        netdisk = NetDisk()
        download_info = netdisk.get_download_info(game['url'], self.cookie)
        if download_info:
            result.update(download_info)
            
        return result
    
    def stop(self):
        """停止采集"""
        self.is_running = False 