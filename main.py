import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QThread
from main_window import MainWindow
from logger import Logger
import settings
from browser import Browser
import traceback
from errors import InitializationError
import logging
import time

class Application(QApplication):
    """应用程序类"""
    def __init__(self, argv):
        super().__init__(argv)
        self.logger = None
        self.main_window = None
        
    def init_logger(self):
        """初始化日志"""
        try:
            # 确保日志目录存在
            os.makedirs(str(settings.LOGS_DIR), exist_ok=True)
            
            # 配置根日志记录器
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(
                        str(settings.LOGS_DIR / f'spider_{time.strftime("%Y%m%d")}.log'),
                        encoding='utf-8'
                    ),
                    logging.StreamHandler()
                ]
            )
            
            self.logger = logging.getLogger('spider')
            self.logger.info("日志系统初始化成功")
            return True
        except Exception as e:
            print(f"初始化日志失败: {e}")
            return False
            
    def init_dirs(self):
        """初始化目录"""
        try:
            # 使用settings中定义的目录
            for dir_path in [
                settings.DATA_DIR,
                settings.LOGS_DIR,
                settings.RESULTS_DIR,
                settings.COOKIES_DIR,
                settings.CONFIG_DIR,
                settings.DATA_DIR / 'images'  # 添加图片目录
            ]:
                os.makedirs(str(dir_path), exist_ok=True)
                print(f"创建目录: {dir_path}")
            return True
        except Exception as e:
            print(f"初始化目录失败: {e}")
            return False
            
    def init_browser_pool(self):
        """初始化浏览器池"""
        try:
            pool_size = settings.BROWSER_CONFIG['pool_size']
            Browser.init_pool(pool_size)
            if self.logger:
                self.logger.info(f"初始化浏览器池(大小:{pool_size})")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"初始化浏览器池失败: {e}")
            else:
                print(f"初始化浏览器池失败: {e}")
            return False
            
    def cleanup(self):
        """清理资源"""
        try:
            # 关闭所有浏览器
            if Browser._pool:
                Browser._pool.close_all()
                
            # 停止所有工作线程
            for thread in self.findChildren(QThread):
                if thread.isRunning():
                    thread.stop()
                    thread.wait()
                    
            if self.logger:
                self.logger.info("清理资源完成")
        except Exception as e:
            if self.logger:
                self.logger.error(f"清理资源失败: {e}")
            else:
                print(f"清理资源失败: {e}")

def show_error(title, message):
    """显示错误对话框"""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec_()

def main():
    """主函数"""
    # 创建应用
    app = Application(sys.argv)
    
    try:
        # 初始化目录
        if not app.init_dirs():
            show_error("初始化失败", "无法创建必要的目录")
            return 1
            
        # 初始化日志
        if not app.init_logger():
            show_error("初始化失败", "无法初始化日志系统")
            return 1
            
        app.logger.info("启动程序")
        
        # 初始化浏览器池
        if not app.init_browser_pool():
            show_error("初始化失败", "无法初始化浏览器池")
            return 1
            
        # 创建主窗口
        try:
            app.main_window = MainWindow()
            app.main_window.show()
        except Exception as e:
            error_msg = f"创建主窗口失败: {str(e)}\n{traceback.format_exc()}"
            app.logger.error(error_msg)
            show_error("初始化失败", error_msg)
            return 1
        
        # 注册清理函数
        app.aboutToQuit.connect(app.cleanup)
        
        # 运行应用
        return app.exec_()
        
    except Exception as e:
        error_msg = f"程序运行错误:\n{str(e)}\n{traceback.format_exc()}"
        if app.logger:
            app.logger.error(error_msg)
        show_error("程序错误", error_msg)
        return 1
        
    finally:
        if app.logger:
            app.logger.info("程序退出")

if __name__ == '__main__':
    # 设置异常钩子
    def exception_hook(exctype, value, tb):
        print(''.join(traceback.format_tb(tb)))
        sys.__excepthook__(exctype, value, tb)
    sys.excepthook = exception_hook
    
    # 运行程序
    sys.exit(main()) 