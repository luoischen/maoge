import json
import os
import time
from datetime import datetime
from pathlib import Path
import sqlite3
import settings
from errors import FileError, DatabaseError
import logging

class GameList:
    """游戏列表管理类"""
    def __init__(self, site_id):
        self.site_id = site_id
        self.games = {}
        self.db_path = settings.DATA_DIR / f'{site_id}.db'
        self.json_path = settings.DATA_DIR / f'{site_id}_games.json'
        self.logger = logging.getLogger('spider')
        self.init_storage()
        self.load_games()
        
    def init_storage(self):
        """初始化存储"""
        try:
            # 创建SQLite数据库
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 先删除旧表
            cursor.execute('DROP TABLE IF EXISTS games')
            
            # 创建新的游戏表 - 包含image_url字段
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    status TEXT DEFAULT '未采集',
                    update_time TEXT,
                    data TEXT,
                    image_url TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info(f"初始化数据库成功: {self.db_path}")
        except Exception as e:
            self.logger.error(f"初始化数据库失败: {e}")
            raise DatabaseError(f"初始化数据库失败: {e}")
        
    def load_games(self):
        """加载游戏列表"""
        try:
            # 优先从JSON文件加载
            if self.json_path.exists():
                self.logger.info(f"从JSON文件加载游戏列表: {self.json_path}")
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self.games = json.load(f)
                self.logger.info(f"成功加载 {len(self.games)} 个游戏")
                return
                
            # 如果JSON不存在，尝试从数据库加载
            self.logger.info(f"从数据库加载游戏列表: {self.db_path}")
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM games')
            rows = cursor.fetchall()
            
            for row in rows:
                game_id, title, url, status, update_time, data, image_url = row
                self.games[game_id] = {
                    'id': game_id,
                    'title': title,
                    'url': url,
                    'status': status,
                    'time': update_time,
                    'image_url': image_url
                }
                if data:
                    self.games[game_id].update(json.loads(data))
                    
            conn.close()
            self.logger.info(f"成功加载 {len(self.games)} 个游戏")
            
            # 保存到JSON作为备份
            self.save_to_json()
                
        except Exception as e:
            self.logger.error(f"加载游戏列表失败: {e}")
            raise DatabaseError(f"加载游戏列表失败: {e}")
            
    def save_to_json(self):
        """保存到JSON文件"""
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.games, f, ensure_ascii=False, indent=2)
            self.logger.info(f"保存到JSON文件成功: {self.json_path}")
        except Exception as e:
            self.logger.error(f"保存到JSON文件失败: {e}")
            
    def save_games(self):
        """保存游戏列表"""
        try:
            # 保存到数据库
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            for game_id, game_info in self.games.items():
                basic_info = {
                    'id': game_id,
                    'title': game_info['title'],
                    'url': game_info['url'],
                    'status': game_info.get('status', '未采集'),
                    'time': game_info.get('time', ''),
                    'image_url': game_info.get('image_url', '')
                }
                
                # 其他数据存储为JSON
                other_data = {k: v for k, v in game_info.items() 
                            if k not in basic_info}
                
                cursor.execute('''
                    INSERT OR REPLACE INTO games 
                    (id, title, url, status, update_time, data, image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    game_id,
                    basic_info['title'],
                    basic_info['url'],
                    basic_info['status'],
                    basic_info['time'],
                    json.dumps(other_data) if other_data else None,
                    basic_info['image_url']
                ))
            
            conn.commit()
            conn.close()
            self.logger.info(f"保存到数据库成功: {len(self.games)} 个游戏")
            
            # 同时保存到JSON
            self.save_to_json()
            
            # 创建备份
            backup_path = settings.DATA_DIR / f'{self.site_id}_games_{datetime.now():%Y%m%d}.json'
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.games, f, ensure_ascii=False, indent=2)
            self.logger.info(f"创建备份成功: {backup_path}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"保存游戏列表失败: {e}")
            raise DatabaseError(f"保存游戏列表失败: {e}")
            
    def add_game(self, game_id, title, url, **kwargs):
        """添加游戏"""
        try:
            game_id = str(game_id)
            if game_id not in self.games:
                self.games[game_id] = {
                    'id': game_id,
                    'title': title,
                    'url': url,
                    'status': kwargs.get('status', '未采集'),
                    'time': kwargs.get('time', ''),
                    'add_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.games[game_id].update(kwargs)
                self.logger.info(f"添加游戏: {title} (ID: {game_id})")
                return True
            return False
        except Exception as e:
            self.logger.error(f"添加游戏失败: {e}")
            return False
            
    def get_sorted_games(self):
        """获取排序后的游戏列表"""
        try:
            sorted_games = sorted(
                self.games.values(),
                key=lambda x: int(x['id']),
                reverse=True
            )
            self.logger.info(f"获取排序游戏列表: {len(sorted_games)} 个游戏")
            return sorted_games
        except Exception as e:
            self.logger.error(f"获取排序游戏列表失败: {e}")
            return []
            
    def delete_game(self, game_id):
        """删除游戏"""
        try:
            game_id = str(game_id)
            if game_id in self.games:
                del self.games[game_id]
                self.save_games()
                self.logger.info(f"删除游戏: {game_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"删除游戏失败: {e}")
            return False
            
    def backup_data(self):
        """备份数据"""
        try:
            # 创建备份目录
            backup_dir = settings.DATA_DIR / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f'games_backup_{timestamp}.json'
            
            # 保存游戏数据
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.games, f, ensure_ascii=False, indent=2)
            
            # 备份数据库文件
            import shutil
            db_backup = backup_dir / f'games_backup_{timestamp}.db'
            shutil.copy2(self.db_path, db_backup)
            
            # 清理旧备份
            self._clean_old_backups(backup_dir)
            
            self.logger.info(f"数据备份完成: {backup_file}")
            return backup_file
            
        except Exception as e:
            self.logger.error(f"数据备份失败: {e}")
            raise DatabaseError(f"数据备份失败: {e}")
            
    def restore_backup(self, backup_file):
        """恢复备份"""
        try:
            if not backup_file.exists():
                raise FileNotFoundError(f"备份文件不存在: {backup_file}")
            
            # 恢复JSON数据
            with open(backup_file, 'r', encoding='utf-8') as f:
                self.games = json.load(f)
            
            # 恢复数据库
            db_file = backup_file.parent / backup_file.name.replace('.json', '.db')
            if db_file.exists():
                import shutil
                shutil.copy2(db_file, self.db_path)
            
            self.logger.info(f"数据恢复完成: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"数据恢复失败: {e}")
            raise DatabaseError(f"数据恢复失败: {e}")
            
    def _clean_old_backups(self, backup_dir, keep_count=5):
        """清理旧备份文件"""
        try:
            # 获取所有备份文件
            backup_files = []
            for ext in ['.json', '.db']:
                backup_files.extend(backup_dir.glob(f'*{ext}'))
            
            # 按修改时间排序
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 删除多余的备份
            if len(backup_files) > keep_count * 2:  # *2是因为每次备份有json和db两个文件
                for old_file in backup_files[keep_count * 2:]:
                    old_file.unlink()
                    self.logger.info(f"删除旧备份: {old_file}")
                
        except Exception as e:
            self.logger.error(f"清理旧备份失败: {e}")