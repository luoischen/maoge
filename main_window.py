from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QLineEdit, QGridLayout,
                           QScrollArea, QFrame, QMessageBox, QApplication,
                           QProgressBar, QCheckBox, QMenu, QAction, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QIcon
import constants
import settings
from utils import load_cookie, save_cookie
from workers.list_worker import ListWorker
from workers.link_worker import LinkWorker
from workers.info_worker import InfoWorker
from workers.image_worker import ImageWorker
from workers.batch_image_worker import BatchImageWorker
from workers.fast_list_worker import FastListWorker
from workers.data_worker import DataWorker
from ui.log_window import LogWindow
from game_list import GameList
import os
from ui.game_detail_dialog import GameDetailDialog
import time
from ui.admin_panel import AdminPanel
import requests
from ui.image_cache import ImageCache, ImageLoadWorker

class GameCard(QFrame):
    """游戏卡片组件"""
    def __init__(self, game_info, parent=None):
        super().__init__(parent)
        self.game_info = game_info
        self.image_size = (220, 165)
        self.selected = False
        self.initUI()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.setFocusPolicy(Qt.NoFocus)
        
    def initUI(self):
        """初始化UI"""
        self.setStyleSheet('''
            QFrame {
                background-color: white;
                border: none;
                outline: none;
            }
            QFrame:hover {
                background-color: #f0f0f0;
            }
            QFrame:focus {
                outline: none;
            }
        ''')
        self.setFixedSize(230, 300)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 游戏图片
        self.image_label = QLabel()
        self.image_label.setFixedSize(*self.image_size)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.loadImage()
        layout.addWidget(self.image_label)
        
        # 游戏标题
        title = QLabel(self.game_info['title'])
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet('font-size: 12px;')
        title.setFixedHeight(40)
        layout.addWidget(title)
        
        # 网盘按钮组
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)
        buttons_layout.setAlignment(Qt.AlignCenter)
        for pan_type, name in constants.PAN_TYPES:
            if pan_type in self.game_info:
                btn = QPushButton(QIcon(f'icons/{pan_type}.png'), '')
                btn.setFixedSize(35, 35)
                btn.setToolTip(name)
                btn.setStyleSheet('QPushButton { border: none; }')
                btn.clicked.connect(lambda x, url=self.game_info[pan_type]: self.copyLink(url))
                buttons_layout.addWidget(btn)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        # 设置鼠标追踪
        self.setMouseTracking(True)
        
    def loadImage(self):
        """加载游戏图片"""
        try:
            if 'image_url' in self.game_info and self.game_info['image_url']:
                # 使用图片缓存
                cache_key = self.game_info['image_url']
                if cache_key in ImageCache.cache:
                    self.image_label.setPixmap(ImageCache.cache[cache_key])
                    return
                
                # 异步加载图片
                self.image_worker = ImageLoadWorker(self.game_info['image_url'])
                self.image_worker.finished.connect(self.onImageLoaded)
                self.image_worker.start()
                
                # 显示加载占位图
                self.image_label.setPixmap(ImageCache.placeholder)
                
        except Exception as e:
            print(f"加载图片失败: {str(e)}")
            self.image_label.setPixmap(ImageCache.default)
        
    def onImageLoaded(self, image_path):
        """图片加载完成"""
        try:
            if image_path:
                # 重新加载图片
                self.loadImage()
                self.updateLog(f"图片更新成功: {image_path}")
            else:
                self.updateLog("图片更新失败")
                
            # 隐藏进度条
            self.progress_bar.hide()
            
        except Exception as e:
            print(f"处理图片更新结果失败: {str(e)}")
            if self.progress_bar:
                self.progress_bar.hide()

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 获取主窗口
            main_window = self.get_main_window()
            if main_window:
                # 如果按住了Ctrl键，则进入多选模式
                if event.modifiers() & Qt.ControlModifier:
                    self.toggleSelection()
                # 如果按住了Shift键，则进入范围选择模式
                elif event.modifiers() & Qt.ShiftModifier:
                    main_window.selection_start = True
                    main_window.last_selected = self
                    self.toggleSelection()
                # 否则就是单选模式
                else:
                    # 清除其他选中状态
                    for i in range(main_window.grid_layout.count()):
                        widget = main_window.grid_layout.itemAt(i).widget()
                        if isinstance(widget, GameCard) and widget != self and widget.selected:
                            widget.selected = False
                            widget.updateStyle()
                    # 切换当前卡片的选择状态
                    self.toggleSelection()
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            # 获取主窗口
            main_window = self.get_main_window()
            if main_window:
                # 结束选择操作
                main_window.selection_start = False
        super().mouseReleaseEvent(event)
        
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        # 获取主窗口
        main_window = self.get_main_window()
        if main_window and main_window.selection_start:
            # 如果正在进行选择操作，则选中当前卡片
            if not self.selected:
                self.toggleSelection()
        super().mouseMoveEvent(event)
        
    def toggleSelection(self):
        """切换选中状态"""
        self.selected = not self.selected
        self.updateStyle()
        # 通知主窗口选择状态改变
        self.parent().parent().parent().updateSelection()
        
    def updateStyle(self):
        """更新样式"""
        if self.selected:
            self.setStyleSheet('''
                QFrame {
                    background-color: #e0e0e0;
                    outline: none;
                }
            ''')
        else:
            self.setStyleSheet('''
                QFrame {
                    background-color: white;
                    border: none;
                    outline: none;
                }
                QFrame:hover {
                    background-color: #f0f0f0;
                }
                QFrame:focus {
                    outline: none;
                }
            ''')
        
    def showContextMenu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        main_window = self.get_main_window()
        
        if main_window:
            # 获取选中的游戏数量
            selected_count = len(main_window.selected_games)
            
            if selected_count > 1 and self.selected:
                # 如果有多个选中且当前卡片被选中，显示批量操作选项
                update_action = QAction(f'更新选中的 {selected_count} 个游戏图片', self)
                update_action.triggered.connect(main_window.updateSelectedImages)
                menu.addAction(update_action)
                
                download_action = QAction(f'下载选中的 {selected_count} 个游戏详情', self)
                download_action.triggered.connect(main_window.downloadSelectedGamesData)
                menu.addAction(download_action)
                
                delete_action = QAction(f'删除选中的 {selected_count} 个游戏', self)
                delete_action.triggered.connect(main_window.deleteSelectedGames)
                menu.addAction(delete_action)
            else:
                # 单个游戏操作
                update_action = QAction('更新图片', self)
                update_action.triggered.connect(self.updateImage)
                menu.addAction(update_action)
                
                download_action = QAction('下载游戏详情', self)
                download_action.triggered.connect(self.downloadGameData)
                menu.addAction(download_action)
                
                delete_action = QAction('删除游戏', self)
                delete_action.triggered.connect(self.deleteGame)
                menu.addAction(delete_action)
            
            menu.exec_(self.mapToGlobal(pos))
        
    def get_main_window(self):
        """获取主窗口实例"""
        widget = self
        while widget:
            if isinstance(widget, MainWindow):
                return widget
            widget = widget.parent()
        return None
        
    def updateImage(self):
        """更新单个游戏图片"""
        try:
            main_window = self.get_main_window()
            if main_window:
                # 显示进度条
                main_window.progress_bar.setMaximum(0)
                main_window.progress_bar.show()
                
                # 创建Steam图片搜索线程
                from test_steam_search import SteamImageTest
                searcher = SteamImageTest()
                
                # 搜索游戏图片URL
                image_url = searcher.search_game(self.game_info['title'])
                if image_url:
                    # 更新游戏信息中的图片URL
                    self.game_info['image_url'] = image_url
                    # 保存更新
                    main_window.game_list.save_games()
                    # 重新加载图片
                    self.loadImage()
                    main_window.updateLog(f"图片URL更新成功: {image_url}")
                else:
                    main_window.updateLog("未找到游戏图片")
                
                # 隐藏进度条
                main_window.progress_bar.hide()
                
        except Exception as e:
            print(f"更新图片失败: {str(e)}")
            
    def deleteGame(self):
        """删除游戏"""
        main_window = self.get_main_window()
        if main_window:
            main_window.deleteGame(self.game_info)

    def mouseDoubleClickEvent(self, event):
        """双击事件处理"""
        if event.button() == Qt.LeftButton:
            dialog = GameDetailDialog(self.game_info, self)
            dialog.exec_()

    def downloadGameData(self):
        """下载单个游戏详情"""
        try:
            main_window = self.get_main_window()
            if main_window:
                # 显示进度条
                main_window.progress_bar.setMaximum(0)
                main_window.progress_bar.show()
                
                # 创建数据下载线程，传入当前游戏信息
                self.data_worker = DataWorker(game_info=self.game_info)
                self.data_worker.progress.connect(main_window.updateLog)
                self.data_worker.game_found.connect(lambda game_info: self.onGameDataDownloaded(game_info, main_window))
                self.data_worker.finished.connect(lambda: main_window.progress_bar.hide())
                
                # 开始下载
                self.data_worker.start()
                
        except Exception as e:
            main_window.updateLog(f"下载游戏详情失败: {str(e)}")
            main_window.progress_bar.hide()

    def onGameDataDownloaded(self, game_info, main_window):
        """游戏详情下载完成"""
        try:
            # 更新游戏信息
            if game_info:
                self.game_info.update(game_info)
                main_window.game_list.save_games()
                main_window.updateLog(f"游戏详情下载完成: {self.game_info['title']}")
                
                # 刷新显示
                main_window.loadGames()
            else:
                main_window.updateLog("游戏详情下载失败")
                
        except Exception as e:
            main_window.updateLog(f"处理游戏详情失败: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.game_list = GameList(constants.SITE_ID)
        self.log_window = LogWindow()
        self.batch_image_worker = None
        self.list_worker = None  # 添加列表获取线程
        self.current_page = 1
        self.cards_per_page = settings.UI_CONFIG['cards_per_page']  # 从配置文件获取每页显示数量
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.performSearch)
        self.selected_games = set()  # 添加选中游戏集合
        self.selection_start = False  # 是否正在进行选择操作
        self.last_selected = None  # 最后选中的卡片
        self.admin_panel = None  # 添加管理面板引用
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        self.setFixedSize(1280, 800)
        self.setWindowTitle(constants.WINDOW_TITLE)
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部布局
        top_layout = self.createTopLayout()
        main_layout.addLayout(top_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)
        
        # 创建内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建网格布局容器
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.grid_widget)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        content_layout.addWidget(self.scroll)
        main_layout.addWidget(content_widget)
        
        # 底部分页控制
        bottom_widget = QWidget()
        bottom_widget.setFixedHeight(50)  # 固定高度
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 5, 0, 5)
        
        # 分页控制
        self.prev_button = QPushButton('上一页')
        self.prev_button.clicked.connect(self.prevPage)
        
        # 页码按钮布局
        self.page_buttons_layout = QHBoxLayout()
        self.page_buttons = []  # 存储页码按钮
        
        # 下一页按钮
        self.next_button = QPushButton('下一页')
        self.next_button.clicked.connect(self.nextPage)
        
        # 总页数信息
        self.total_info_label = QLabel()
        self.total_info_label.setAlignment(Qt.AlignCenter)
        
        # 添加管理按钮到右下角
        admin_button = QPushButton('管理')
        admin_button.setFixedSize(80, 30)
        admin_button.clicked.connect(self.showAdminPanel)
        
        # 将管理按钮添加到底部布局的右侧
        bottom_layout.addStretch()  # 在页码和管理钮之间添加弹性空间
        bottom_layout.addWidget(admin_button)
        
        bottom_layout.addWidget(self.prev_button)
        bottom_layout.addLayout(self.page_buttons_layout)
        bottom_layout.addWidget(self.next_button)
        bottom_layout.addWidget(self.total_info_label)
        bottom_layout.addStretch()
        
        main_layout.addWidget(bottom_widget)
        
        # 加载第一页游戏
        self.loadGames()
        
    def createTopLayout(self):
        """创建顶部布局"""
        top_layout = QHBoxLayout()
        
        # Logo
        logo_label = QLabel()
        logo_label.setPixmap(QPixmap('icons/logo.png').scaled(40, 40))
        top_layout.addWidget(logo_label)
        
        # 标题
        title_label = QLabel(constants.WINDOW_TITLE)
        title_label.setStyleSheet('font-size: 20px; font-weight: bold;')
        top_layout.addWidget(title_label)
        
        # 搜索和控制按钮布局
        control_layout = QHBoxLayout()
        
        # 搜索框和搜索按钮
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('搜索游戏...')
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self.onSearchInput)
        search_layout.addWidget(self.search_input)
        
        # 搜索按钮
        search_button = QPushButton('搜索')
        search_button.clicked.connect(self.performSearch)
        search_layout.addWidget(search_button)
        
        control_layout.addLayout(search_layout)
        
        # 更新图片按钮
        self.update_images_button = QPushButton('更新图片')
        self.update_images_button.clicked.connect(self.startUpdateSelectedImages)
        control_layout.addWidget(self.update_images_button)
        
        # 显示日志按钮
        log_button = QPushButton('显示志')
        log_button.clicked.connect(self.showLogWindow)
        control_layout.addWidget(log_button)
        
        top_layout.addLayout(control_layout)
        return top_layout
        
    def loadGames(self, games=None, reset=True):
        """加载游戏列表"""
        try:
            # 清空网格布局中的所有内容
            self.clearGrid()
            
            if games is None:
                games = self.game_list.get_sorted_games()
                
            # 计算总页数和当前页范围
            total_games = len(games)
            total_pages = (total_games + self.cards_per_page - 1) // self.cards_per_page
            
            # 确保当前页不超过总页数
            self.current_page = min(self.current_page, max(1, total_pages))
            
            # 计算当前页的游戏范围
            start_idx = (self.current_page - 1) * self.cards_per_page
            end_idx = min(start_idx + self.cards_per_page, total_games)
            page_games = games[start_idx:end_idx]
            
            # 计算网格布局
            cols = settings.UI_CONFIG['grid_columns']
            row = col = 0
            
            # 添加游戏卡片
            for game in page_games:
                card = GameCard(game)
                self.grid_layout.addWidget(card, row, col)
                col += 1
                if col >= cols:
                    col = 0
                    row += 1
            
            # 更新页码按钮
            self.updatePageButtons(total_pages)
            
            # 更新总数信息
            self.total_info_label.setText(f'共 {total_pages} 页 ({total_games} 个游戏)')
            
            # 更新按钮状态
            self.prev_button.setEnabled(self.current_page > 1)
            self.next_button.setEnabled(self.current_page < total_pages)
            
            # 滚动到顶部
            self.scroll.verticalScrollBar().setValue(0)
            
        except Exception as e:
            self.updateLog(f"加载游戏列表失败: {str(e)}")

    def clearGrid(self):
        """清空网格布局"""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def prevPage(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.loadGames()  # 移reset=False参数

    def nextPage(self):
        """下一页"""
        total_games = len(self.game_list.get_sorted_games())
        total_pages = (total_games + self.cards_per_page - 1) // self.cards_per_page
        
        if self.current_page < total_pages:
            self.current_page += 1
            self.loadGames()  # 移除reset=False参数

    def onScroll(self, value):
        """除滚动加载"""
        pass

    def onSearchInput(self, text):
        """索输入处理"""
        # 延迟500ms执行搜索,避免频繁搜索
        self.search_timer.start(500)
        
    def performSearch(self):
        """执行搜索"""
        text = self.search_input.text().lower()
        games = self.game_list.get_sorted_games()
        
        if text:
            games = [
                game for game in games
                if text in game['title'].lower()
            ]
            
        self.loadGames(games)
        
    def startUpdateSelectedImages(self, games=None):
        """更新选中或指定游戏的图片"""
        try:
            if games is None:
                # 获取选中的游戏
                games = []
                for i in range(self.grid_layout.count()):
                    widget = self.grid_layout.itemAt(i).widget()
                    if isinstance(widget, GameCard) and widget.selected:
                        games.append(widget.game_info)
        
            if not games:
                QMessageBox.information(
                    self,
                    '提示',
                    '没有需要更新的游戏',
                    QMessageBox.Ok
                )
                return
            
            # 显示进度条
            self.progress_bar.setMaximum(len(games))
            self.progress_bar.setValue(0)
            self.progress_bar.show()
            
            # 创建批量图片更新线程
            self.batch_image_worker = BatchImageWorker(games)
            self.batch_image_worker.progress.connect(self.updateLog)
            self.batch_image_worker.image_updated.connect(self.onImageUpdated)
            self.batch_image_worker.finished.connect(self.onImagesUpdateFinished)
            self.batch_image_worker.start()
            
            self.updateLog(f"开始更新 {len(games)} 个游戏的图片...")
            
        except Exception as e:
            self.updateLog(f"启动更新失败: {str(e)}")
            self.progress_bar.hide()

    def onImageUpdated(self, game_id):
        """单游戏图片更新完成"""
        try:
            # 更新进度条
            value = self.progress_bar.value() + 1
            self.progress_bar.setValue(value)
            
            # 刷新显示
            self.loadGames()
        except Exception as e:
            self.updateLog(f"更新显示失败: {str(e)}")

    def onImagesUpdateFinished(self):
        """图片更新完成"""
        self.progress_bar.hide()
        self.updateLog("所有游戏图片更新完成")
        # 更新完图片后自动备份
        self.autoBackupData()
        self.loadGames()

    def showLogWindow(self):
        """显日志窗口"""
        self.log_window.show()
        self.log_window.raise_()  # 将窗口提升到最前
        
    def updateLog(self, msg):
        """更新日志显示"""
        try:
            # 添加时间戳
            from datetime import datetime
            timestamp = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
            log_msg = f"{timestamp} {msg}"
            
            # 添加到日志文本框
            if hasattr(self, 'log_text'):
                self.log_text.append(log_msg)
                # 滚动到底部
                self.log_text.verticalScrollBar().setValue(
                    self.log_text.verticalScrollBar().maximum()
                )
            
            # 同时输出到控制台
            print(log_msg)
            
        except Exception as e:
            print(f"更新日志显示失败: {e}")
        
    def copyLink(self, url):
        """复制链到剪贴板"""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(url)
            self.updateLog("已复制链接到剪贴板")
        except Exception as e:
            self.updateLog(f"复制链接失败: {str(e)}")

    def startGetGameList(self):
        """开始获取游戏列表"""
        try:
            # 创建并启动列表获取线程
            self.list_worker = ListWorker(existing_games=self.game_list.games)  # 传入现有游戏
            self.list_worker.progress.connect(self.updateLog)
            self.list_worker.game_found.connect(self.onGameFound)
            self.list_worker.finished.connect(self.onGetListFinished)
            self.list_worker.start()
            
            # 启用停止按钮
            if hasattr(self, 'admin_panel') and self.admin_panel:
                self.admin_panel.stop_btn.setEnabled(True)
            
            self.updateLog("开始获取游戏列表...")
            
        except Exception as e:
            self.updateLog(f"启动获取游戏列表失败: {str(e)}")

    def onGameFound(self, game_info):
        """发现新游戏"""
        try:
            # 添加到游戏列表并立即保存
            if self.game_list.add_game(
                game_info['id'],
                game_info['title'],
                game_info['url']
            ):
                self.updateLog(f"添加新游戏: {game_info['title']}")
                # 立即保存到数据库
                self.game_list.save_games()
                
        except Exception as e:
            self.updateLog(f"添加游戏失败: {str(e)}")

    def onGetListFinished(self):
        """获取列表完成"""
        try:
            if self.list_worker:
                self.list_worker.deleteLater()
                self.list_worker = None
                
                # 禁用停止按钮
                if hasattr(self, 'admin_panel') and self.admin_panel:
                    self.admin_panel.stop_btn.setEnabled(False)
                
            # 重新加载游戏列表
            self.loadGames()
            # 自动备份
            self.autoBackupData()
            self.updateLog("游戏列表更新完成")
            
        except Exception as e:
            self.updateLog(f"完成列表获取失败: {str(e)}")

    def updateSelection(self):
        """更新选中状态"""
        self.selected_games.clear()
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, GameCard) and widget.selected:
                self.selected_games.add(widget.game_info['id'])
                self.updateLog(f"选中游戏: {widget.game_info['title']}")
                
    def updateSingleImage(self, game_info):
        """更新单个游戏图片"""
        try:
            # 显示进度条
            self.progress_bar.setMaximum(0)  # 不确定进度
            self.progress_bar.show()
            
            # 创建图片下载线程
            image_worker = ImageWorker(game_info['title'], game_info['id'])
            image_worker.progress.connect(self.updateLog)
            image_worker.finished.connect(lambda path: self.onSingleImageUpdated(game_info['id'], path))
            image_worker.start()
            
        except Exception as e:
            self.updateLog(f"更新图片失败: {str(e)}")
            self.progress_bar.hide()
            
    def onSingleImageUpdated(self, game_id, image_path):
        """单个图片更新完成"""
        try:
            if image_path:
                self.updateLog(f"游戏 {game_id} 图片更新成功")
            else:
                self.updateLog(f"游戏 {game_id} 图片更新失败")
                
            # 隐藏进度条
            self.progress_bar.hide()
            
            # 刷新显示
            self.loadGames()
            
        except Exception as e:
            self.updateLog(f"更新显示失败: {str(e)}")
            self.progress_bar.hide()

    def deleteGame(self, game_info):
        """删除游戏"""
        reply = QMessageBox.question(
            self,
            '确认删除',
            f'确定要删除游戏 "{game_info["title"]}" 吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 从游戏列表删除
                self.game_list.delete_game(game_info['id'])
                # 删除图片文件
                image_path = f'data/images/{game_info["id"]}.jpg'
                if os.path.exists(image_path):
                    os.remove(image_path)
                self.updateLog(f"已删除游戏: {game_info['title']}")
                self.loadGames()
            except Exception as e:
                self.updateLog(f"删除游戏失败: {str(e)}")
                
    def updateSelectedImages(self):
        """更新选中的游戏图片"""
        try:
            # 获取选中的戏
            selected_games = []
            for game in self.game_list.get_sorted_games():
                if game['id'] in self.selected_games:
                    selected_games.append(game)
            
            if selected_games:
                # 显示进度条
                self.progress_bar.setMaximum(len(selected_games))
                self.progress_bar.setValue(0)
                self.progress_bar.show()
                
                # 创建批量图片更新线程
                self.batch_image_worker = BatchImageWorker(selected_games)
                self.batch_image_worker.progress.connect(self.updateLog)
                self.batch_image_worker.image_updated.connect(self.onImageUpdated)
                self.batch_image_worker.finished.connect(self.onImagesUpdateFinished)
                self.batch_image_worker.start()
                
                self.updateLog(f"开始更新 {len(selected_games)} 个选中游戏的图片")
                
        except Exception as e:
            self.updateLog(f"更新选中图片失败: {str(e)}")
            self.progress_bar.hide()

    def deleteSelectedGames(self):
        """删除选中的游戏"""
        count = len(self.selected_games)
        reply = QMessageBox.question(
            self,
            '确认删除',
            f'确定要删除选中的 {count} 个游戏吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                for game_id in self.selected_games:
                    self.game_list.delete_game(game_id)
                    image_path = f'data/images/{game_id}.jpg'
                    if os.path.exists(image_path):
                        os.remove(image_path)
                self.updateLog(f"已删除 {count} 个游戏")
                self.selected_games.clear()
                self.loadGames()
            except Exception as e:
                self.updateLog(f"删除游戏失败: {str(e)}")

    def updatePageButtons(self, total_pages):
        """更新页码按钮"""
        # 清除现有的页码按钮
        for btn in self.page_buttons:
            self.page_buttons_layout.removeWidget(btn)
            btn.deleteLater()
        self.page_buttons.clear()
        
        # 计算显示的页码范围
        start_page = max(1, self.current_page - 4)
        end_page = min(total_pages, start_page + 9)
        if end_page - start_page < 9:
            start_page = max(1, end_page - 9)
        
        # 添加页码按钮
        for page in range(start_page, end_page + 1):
            btn = QPushButton(str(page))
            btn.setFixedSize(30, 30)
            if page == self.current_page:
                btn.setStyleSheet('''
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        border: none;
                        border-radius: 15px;
                    }
                ''')
            else:
                btn.setStyleSheet('''
                    QPushButton {
                        background-color: white;
                        border: 1px solid #ccc;
                        border-radius: 15px;
                    }
                    QPushButton:hover {
                        border-color: #2196F3;
                    }
                ''')
            btn.clicked.connect(lambda x, p=page: self.gotoPage(p))
            self.page_buttons.append(btn)
            self.page_buttons_layout.addWidget(btn)

    def gotoPage(self, page):
        """跳转到指定页"""
        if page != self.current_page:
            self.current_page = page
            self.loadGames()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.selection_start:
            # 获取鼠标下的部件
            widget = self.childAt(event.pos())
            if isinstance(widget, GameCard) and not widget.selected:
                widget.toggleSelection()
        super().mouseMoveEvent(event)

    def showAdminPanel(self):
        """显示管理面板"""
        if not self.admin_panel:
            self.admin_panel = AdminPanel(self)
        self.admin_panel.show()

    def startDownloadGameData(self):
        """开始下载游戏数据"""
        try:
            # 获取所有未采集的游戏
            uncollected_games = [game for game in self.game_list.get_sorted_games() 
                               if game.get('status') == '未采集']
            
            if not uncollected_games:
                self.updateLog("没有需要采集的游戏")
                return
            
            reply = QMessageBox.question(
                self,
                '确认下载',
                f'否下载 {len(uncollected_games)} 个游戏的详细数据？\n这可能需要一些时间。',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 显示进度条
                self.progress_bar.setMaximum(len(uncollected_games))
                self.progress_bar.setValue(0)
                self.progress_bar.show()
                
                # 创建并启动数据采集线程
                self.data_worker = DataWorker(games=uncollected_games)
                self.data_worker.progress.connect(self.updateLog)
                self.data_worker.game_found.connect(self.onGameDataCollected)
                self.data_worker.finished.connect(self.onDataDownloadFinished)
                self.data_worker.start()
                
                self.updateLog(f"开始下载 {len(uncollected_games)} 个游戏的数据...")
                
        except Exception as e:
            self.updateLog(f"启动数据下载失败: {str(e)}")
            self.progress_bar.hide()

    def exportGameList(self):
        """导出游戏列表"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "导出游戏列表",
                str(settings.RESULTS_DIR / f"game_list_{time.strftime('%Y%m%d')}.json"),
                "JSON Files (*.json)"
            )
            
            if filename:
                self.game_list.save_to_json(filename)
                self.updateLog(f"游戏列表已导出到: {filename}")
                
        except Exception as e:
            self.updateLog(f"导出游戏列表失败: {str(e)}")

    def importGameList(self):
        """导入游戏列表"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "导入游戏列表",
                str(settings.RESULTS_DIR),
                "JSON Files (*.json)"
            )
            
            if filename:
                reply = QMessageBox.question(
                    self,
                    '确认导入',
                    '导入将覆盖现有游戏列表，是否继续？',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.game_list.load_from_json(filename)
                    self.loadGames()  # 刷新显示
                    self.updateLog(f"已导入游戏列表: {filename}")
                    
        except Exception as e:
            self.updateLog(f"导入游戏列表失败: {str(e)}")

    def onDataDownloadFinished(self):
        """数据下载完成"""
        self.updateLog("游戏数据下载完成")
        self.loadGames()  # 刷新显示

    def downloadSelectedGamesData(self):
        """下载选中游戏的详情"""
        try:
            # 获取选中的游戏
            selected_games = []
            for game in self.game_list.get_sorted_games():
                if game['id'] in self.selected_games:
                    selected_games.append(game)
            
            if selected_games:
                reply = QMessageBox.question(
                    self,
                    '确认下载',
                    f'是否下载选中的 {len(selected_games)} 个游戏详情？',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 显示进度条
                    self.progress_bar.setMaximum(len(selected_games))
                    self.progress_bar.setValue(0)
                    self.progress_bar.show()
                    
                    # 创建数据下载线程
                    self.data_worker = DataWorker()
                    self.data_worker.progress.connect(self.updateLog)
                    self.data_worker.game_found.connect(self.onGameDataCollected)
                    self.data_worker.finished.connect(self.onDataDownloadFinished)
                    self.data_worker.start()
                    
                    self.updateLog(f"开始下载 {len(selected_games)} 个游戏的详情")
                    
        except Exception as e:
            self.updateLog(f"下载游戏详情失败: {str(e)}")
            self.progress_bar.hide()

    def onGameDataCollected(self, game_info):
        """游戏数据采集完成"""
        try:
            # 更新游戏列表中的游戏信息
            if game_info['id'] in self.game_list.games:
                self.game_list.games[game_info['id']].update(game_info)
                self.game_list.save_games()  # 保存更新
                self.updateLog(f"更新游戏数据: {game_info['title']}")
                
                # 更新进度条
                value = self.progress_bar.value() + 1
                self.progress_bar.setValue(value)
                
        except Exception as e:
            self.updateLog(f"新游戏数据失败: {str(e)}")

    def autoBackupData(self):
        """自动备份数据"""
        try:
            backup_file = self.game_list.backup_data()
            if backup_file:
                self.updateLog(f"自动备份完成: {backup_file}")
        except Exception as e:
            self.updateLog(f"自动备份失败: {str(e)}")

    def log(self, msg):
        """添加日志"""
        try:
            # 如果有日志窗口就使用日志窗口
            if hasattr(self, 'log_window') and self.log_window:
                self.log_window.log_text.append(msg)
            else:
                # 否则打印到控制台
                print(msg)
                
            # 确保日志立即显示
            QApplication.processEvents()
            
        except Exception as e:
            print(f"记录日志失败: {e}")
            print(msg)

    def refresh_game(self, game_id):
        """刷新单个游戏的显示"""
        try:
            # 如果有游戏列表视图，刷新对应项
            if hasattr(self, 'game_list_view'):
                # 找到对应的游戏项并更新
                for i in range(self.game_list_view.count()):
                    item = self.game_list_view.item(i)
                    if item and item.data(Qt.UserRole).get('id') == game_id:
                        # 从game_list获取最新数据
                        game_info = self.game_list.games.get(game_id)
                        if game_info:
                            # 更新item的数据
                            item.setData(Qt.UserRole, game_info)
                            # 如果需要，更新显示
                            self.updateGameItem(item)
                        break
                    
            # 如果当前显示的是这个游戏的详情，也要刷新
            if hasattr(self, 'current_game_id') and self.current_game_id == game_id:
                self.showGameDetail(game_id)
            
            self.updateLog(f"刷新游戏显示: {game_id}")
            
        except Exception as e:
            self.updateLog(f"刷新游戏显示失败: {str(e)}")

    def updateGameItem(self, item):
        """更新游戏列表项显示"""
        try:
            game_info = item.data(Qt.UserRole)
            if game_info:
                # 更新显示文本
                item.setText(game_info['title'])
                
                # 如果有图片URL，加载图片
                if 'image_url' in game_info and game_info['image_url']:
                    # 这里可以添加图片加载逻辑
                    pass
                    
        except Exception as e:
            self.updateLog(f"更新游戏项显示失败: {str(e)}")