from test_baidu_download_ui import ShareInfoWorker
from PyQt5.QtCore import QCoreApplication
import sys

def test_button_click():
    """测试获取分享内容按钮的功能"""
    # 测试参数
    share_url = "https://pan.baidu.com/share/init?surl=1zNvK-93NUpOMfr2vc7hIQ"
    pwd = "79c8"
    
    # 创建应用实例
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv)
    
    # 创建工作线程
    worker = ShareInfoWorker(share_url, pwd)
    
    # 添加日志输出
    def print_log(msg):
        print(f"[LOG] {msg}")
    worker.progress.connect(print_log)
    
    # 添加文件列表处理
    def handle_files(files):
        print("\n=== 获取到文件列表 ===")
        for file in files:
            print(f"文件: {file.get('server_filename')}")
    worker.files_found.connect(handle_files)
    
    # 启动线程
    worker.start()
    
    # 运行事件循环
    app.exec_()

if __name__ == '__main__':
    test_button_click() 