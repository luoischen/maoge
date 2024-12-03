from test_baidu_download_ui import TestWindow
from PyQt5.QtWidgets import QApplication
import sys

def main():
    try:
        # 确保只有一个 QApplication 实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
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