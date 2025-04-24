import webbrowser
import threading
import time
from Web.app import app

def open_browser():
    """在新线程中打开浏览器"""
    # 延迟2秒，等待Flask服务器启动
    time.sleep(2)
    # 打开默认浏览器
    webbrowser.open('http://localhost:5000/')

if __name__ == '__main__':
    print("启动电量查询系统网站...")
    
    # 在新线程中打开浏览器
    threading.Thread(target=open_browser).start()
    
    # 启动Flask应用
    app.run(debug=False, host='localhost', port=5000) 