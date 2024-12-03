class SpiderError(Exception):
    """爬虫基础异常类"""
    pass

class NetworkError(SpiderError):
    """网络错误"""
    pass

class ParseError(SpiderError):
    """解析错误"""
    pass

class BrowserError(SpiderError):
    """浏览器错误"""
    pass

class ConfigError(SpiderError):
    """配置错误"""
    pass

class FileError(SpiderError):
    """文件操作错误"""
    pass

class LoginError(SpiderError):
    """登录错误"""
    pass

class CookieError(SpiderError):
    """Cookie错误"""
    pass

class DatabaseError(SpiderError):
    """数据库错误"""
    pass

class StorageError(SpiderError):
    """存储错误"""
    pass

class ValidationError(SpiderError):
    """数据验证错误"""
    pass

class ResourceError(SpiderError):
    """资源错误"""
    pass

class InitializationError(SpiderError):
    """初始化错误"""
    pass

class CleanupError(SpiderError):
    """清理错误"""
    pass 