from downloaders.baidu_pan import BaiduPanDownloader

def test_download():
    print("\n=== 测试百度网盘下载 ===")
    
    # 创建下载器实例
    downloader = BaiduPanDownloader()
    
    # 先登录
    print("\n1. 登录测试")
    if not downloader.login():
        print("登录失败，无法继续测试")
        return
    print("登录成功")
    
    # 测试分享链接
    print("\n2. 解析分享链接")
    test_url = "https://pan.baidu.com/share/init?surl=1zNvK-93NUpOMfr2vc7hIQ"
    test_pwd = "79c8"
    
    share_info = downloader.parse_share_url(test_url, test_pwd)
    if not share_info:
        print("解析分享链接失败")
        return
    
    print("解析成功:")
    print(f"文件ID: {share_info['fs_id']}")
    print(f"文件名: {share_info['filename']}")
    
    # 获取下载链接
    print("\n3. 获取下载链接")
    dlink = downloader.get_download_link(share_info['fs_id'])
    if not dlink:
        print("获取下载链接失败")
        return
    
    print(f"下载链接: {dlink}")
    
    # 开始下载
    print("\n4. 开始下载")
    save_path = "downloads/test.zip"
    result = downloader.download_file(dlink, save_path)
    
    if result:
        print("\n下载成功!")
    else:
        print("\n下载失败!")

if __name__ == '__main__':
    test_download() 