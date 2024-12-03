from utils import load_json
import constants

class Config:
    def __init__(self):
        self.config = self.load_config()
        
    def load_config(self):
        """加载配置"""
        config = load_json(constants.CONFIG_FILE)
        return config.get('sites', {}).get('sanmo', {})
        
    def get_selectors(self):
        """获取选择器配置"""
        return self.config.get('selectors', {})
        
    def get_download_selectors(self):
        """获取下载相关选择器"""
        return self.config.get('selectors', {}).get('download_links', {}) 