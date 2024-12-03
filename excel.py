import pandas as pd
import os
from datetime import datetime
import settings

class ExcelExporter:
    """Excel导出工具类"""
    
    @staticmethod
    def export_data(data, prefix='游戏数据'):
        """导出数据到Excel"""
        try:
            if not data:
                return False
                
            # 创建结果目录
            os.makedirs(settings.FILE_CONFIG['result_dir'], exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{prefix}_{timestamp}.xlsx"
            filepath = os.path.join(settings.FILE_CONFIG['result_dir'], filename)
            
            # 转换为DataFrame
            df = pd.DataFrame(data)
            
            # 如果文件存在,则追加数据
            if os.path.exists(filepath):
                existing_df = pd.read_excel(filepath)
                df = pd.concat([existing_df, df], ignore_index=True)
                # 删除重复行
                if '标题' in df.columns:
                    df = df.drop_duplicates(subset=['标题'], keep='last')
            
            # 保存Excel
            df.to_excel(filepath, index=False)
            return True
            
        except Exception as e:
            print(f"导出Excel失败: {e}")
            return False
    
    @staticmethod        
    def export_links(data, prefix='下载链接'):
        """导出下载链接"""
        try:
            if not data:
                return False
                
            # 创建结果目录
            os.makedirs(settings.FILE_CONFIG['result_dir'], exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{prefix}_{timestamp}.xlsx"
            filepath = os.path.join(settings.FILE_CONFIG['result_dir'], filename)
            
            # 转换为DataFrame
            df = pd.DataFrame([data])
            
            # 保存Excel
            df.to_excel(filepath, index=False)
            return True
            
        except Exception as e:
            print(f"导出链接失败: {e}")
            return False 