# 内置库
import json
import time
import re
import http.client
import uuid
import asyncio
import os
import tkinter as tk
from tqdm import tqdm

# 第三方库
import cv2
from pyzbar.pyzbar import decode
import pyzbar.pyzbar as pyzbar
import numpy as np
import win32gui
import win32ui
import win32con
from pyppeteer import launch
import zipfile
import requests

# 动态获取当前用户的 home 目录并组合成 Chromium 的路径
CHROMIUM_RELATIVE_PATH = '\\AppData\\Local\\pyppeteer\\pyppeteer\\local-chromium\\588429\\chrome-win32\\chrome.exe'
CHROMIUM_PATH = os.path.join(os.environ['USERPROFILE'], CHROMIUM_RELATIVE_PATH.lstrip('\\'))

def download_file(destination):
    """从给定的 URL 下载文件到指定的目的地"""
    # 确保目录存在
    directory = os.path.dirname(destination)
    if not os.path.exists(directory):
        os.makedirs(directory)
    res= requests.get(url="https://easylink.cc/kodo/object/1ryhaw_chrome-win32.zip").json()
    download_url = res.get('download_url', None)
    print(download_url)
    response = requests.get(
        url=download_url, 
        stream=True
    )
    response.raise_for_status()  # 如果请求不成功则抛出异常
    # 从响应头中获取文件总大小（以字节为单位）
    total_size = int(response.headers.get('content-length', 0))
    # 创建一个 tqdm 对象以显示进度条
    progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True)

    with open(destination, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
            # 更新进度条
            progress_bar.update(len(chunk))
    # 确保进度条完成
    progress_bar.close()
    # 如果文件大小不匹配，抛出异常
    if total_size != 0 and progress_bar.n != total_size:
        raise ValueError("下载的文件大小与预期的文件大小不匹配")
    
def ensure_chromium_exists():
    """确保 Chromium 存在，如果不存在则下载"""
    if not os.path.exists(CHROMIUM_PATH):
        print(CHROMIUM_PATH)
        print("未找到 Chromium。使用 Chromium ZIP 文件的备用下载链接：")
        zip_path = os.path.join(os.path.dirname(CHROMIUM_PATH), 'chromium_backup.zip')
        print("正在从备用源下载 Chromium...")
        download_file(zip_path)
        print("下载完成。正在解压...")
        # 解压 ZIP 文件
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(CHROMIUM_PATH))
        os.remove(zip_path)
        print("Chromium 设置成功。")
    else:
        print("Chromium 已存在。")

async def main(username, devtools_value):
    # 启动浏览器
    browser = await launch(devtools=devtools_value)
    # 打开一个新页面
    page = await browser.newPage()
    # 导航到带有验证码的登录页面
    await page.goto("https://user.mihoyo.com/#/login/captcha")
    # 获取用户输入的用户名
    await page.type('.input-container input[type="text"]', username)
    print("验证码正在赶来的路上，请客官耐心稍等...(如果长时间没有收到验证码，可能存在人机验证，请重新运行程序，在是否开启浏览器？中选择y)")
    # 点击获取验证码按钮
    await page.click(".input-inner-btn")
    # 输入验证码
    captcha = input("请输入验证码: ")
    await page.type('.input-container input[type="tel"]', captcha)
    print("正在登陆中，请稍等...")
    # 点击用户协议复选框
    await asyncio.sleep(2)
    await page.click(".box-container")
    await asyncio.sleep(2)
    # 找到登录按钮并点击
    await page.click('button[type="submit"]')
    await asyncio.sleep(5)
    # 输出登录后的页面标题
    page_title = await page.title()
    if page_title == "账号管理":
        print("账号登录成功")
    else:
        print("账号登录失败")

    stoken_script = """
    (async function() {
        function getCookieMap(cookie) {
            let cookiePattern = /^(\S+)=(\S+)$/;
            let cookieArray = cookie.replace(/\s*/g, "").split(";");
            let cookieMap = new Map();
            for (let item of cookieArray) {
                let entry = item.split("=");
                if (!entry[0]) continue;
                cookieMap.set(entry[0], entry[1]);
            }
            return cookieMap;
                
        }   

        const map = getCookieMap(document.cookie);
        let loginTicket = map.get("login_ticket");
        const loginUid = map.get("login_uid") ? map.get("login_uid") : map.get("ltuid");
        const url = "https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket?login_ticket=" +
            loginTicket + "&token_types=3&uid=" + loginUid;

        let stoken;

        try {
            const response = await fetch(url, {
                "headers": {
                    "x-rpc-device_id": "zxcvbnmasadfghjk123456",
                    "Content-Type": "application/json;charset=UTF-8",
                    "x-rpc-client_type": "",
                    "x-rpc-app_version": "",
                    "DS": "",
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/%s",
                    "Referer": "cors",
                    "Accept-Encoding": "gzip, deflate, br",
                    "x-rpc-channel": "appstore",
                },
                "method": "GET"
            });

            if (response.status !== 200) {
                return false;
            }

            const data = await response.json();

            if (!data.data) {
                console.log(`stoken获取失败请刷新页面重试,错误信息：${data.message}`);
                return false;
            }

            stoken = `stuid=${map.get("login_uid")};stoken=${data.data.list[0].token};ltoken=${data.data.list[1].token};`;
            return stoken;  // 返回stoken值

        } catch (err) {
            console.error("获取stoken时出错:", err);
            return false;
        }
    })();
    """

    stokens = await page.evaluate(stoken_script)
    await asyncio.sleep(5)
    await browser.close()
    return stokens;    



#初始化屏幕和窗口
def setup_screen_and_window():
    # 随机获取一个UUID来作为device
    device = str(uuid.uuid1())

    # 获取屏幕尺寸
    win_width = tk.Tk().winfo_screenwidth()
    win_height = tk.Tk().winfo_screenheight()

    # 获取屏幕DC
    hwnd = win32gui.GetDesktopWindow()   
    hdc = win32gui.GetWindowDC(hwnd)
    dc = win32ui.CreateDCFromHandle(hdc)

    # 设置全屏扫描区域左上角的坐标和宽高
    left, top, width, height = 0, 0, win_width, win_height
    right = left + width
    bottom = top + height

    # 创建窗口并设置窗口名称
    cv2.namedWindow("QR Code Scanner", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("QR Code Scanner", win_width, win_height)
    
    # 隐藏窗口
    cv2.destroyWindow("QR Code Scanner")

    return device, left, top, right, bottom, dc

# 截取指定区域的屏幕截图
def capture_screen(left, top, right, bottom, dc):
 
    saveDC = dc.CreateCompatibleDC()
 
    # 创建位图对象
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(dc, right-left, bottom-top)
 
    # 将位图选入到DC中
    saveDC.SelectObject(saveBitMap)
 
    # 截屏并保存到位图中
    saveDC.BitBlt((0, 0), (right-left, bottom-top),
                  dc, (left, top), win32con.SRCCOPY)
 
    # 将位图对象转换为numpy数组并进行颜色空间转换
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    screenshot = np.frombuffer(bmpstr, dtype='uint8').reshape(
        (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4))[:, :, :3]
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
 
    # 释放资源
    saveDC.DeleteDC()
    win32gui.DeleteObject(saveBitMap.GetHandle())
 
    return screenshot
# 抢码开始
def Request(ticket,device,GameType):
    conn = http.client.HTTPSConnection("api-sdk.mihoyo.com")
    payload = json.dumps({
        "app_id": GameType,
        "device": device,
        "ticket": ticket
    })
    headers = {}
    if GameType == 4 :# 原神
        conn.request("POST", "/hk4e_cn/combo/panda/qrcode/scan", payload, headers)
    elif GameType == 8 :# 星穹铁道
        conn.request("POST", "/hkrpg_cn/combo/panda/qrcode/scan", payload, headers)
         
    res = conn.getresponse()
    data = res.read()
    data = json.loads(data.decode("utf-8"))
    retcode = data["retcode"]
    return retcode
# 确认登陆
def ConfirmRequest(ticket,device,cookie,uid):
 
    conn = http.client.HTTPSConnection("api-takumi.miyoushe.com")
    payload = ''
    headers = {
        'cookie': cookie,
    }
    conn.request("GET", "/auth/api/getGameToken",
                 '', headers)
    res = conn.getresponse()
    data = res.read()
 
    print(data.decode("utf-8"))
 
    data = json.loads(data.decode("utf-8"))
    token = data["data"]["game_token"]
 
    conn = http.client.HTTPSConnection("api-sdk.mihoyo.com")
    payload = json.dumps({
        "app_id": GameType,
        "device": device,
        "payload": {
            "proto": "Account",
            "raw": f"{{\"uid\":\"{uid}\",\"token\":\"{token}\"}}"
        },
        "ticket": ticket
    })
    headers = {
        'cookie': cookie,
    }
    conn.request("POST", "/hk4e_cn/combo/panda/qrcode/confirm",
                 payload, headers)
    res = conn.getresponse()
    # data = res.read()
    # print(data.decode("utf-8"))

def qr_code_scanner(
    capture_function=capture_screen,
    request_function=Request,
    confirm_request_function=ConfirmRequest
):
    frame_count = 0
    frame_start_time = time.time()
    print_login_message = True  # 新增的标志，用于控制是否打印消息
    
    while True:
        screenshot = capture_function()
        codes = decode(screenshot, symbols=[pyzbar.ZBarSymbol.QRCODE])
        
        if codes:
            print("扫码成功！")
            pattern = r"ticket=([a-f0-9]+)"
            match = re.search(pattern, codes[0].data.decode())
            
            if match:
                print(match.group(1))
                start_time = time.time()
                retcode = request_function(match.group(1))
                end_time = time.time()

                if retcode == 0:
                    elapsed_time = end_time - start_time
                    print("抢码成功耗时 %.3f 秒" % elapsed_time)
                    random_delay = 1.3
                    time.sleep(random_delay)
                    print("防止过快被察觉插入随机延迟")
                    
                    start_time = time.time()
                    confirm_request_function(match.group(1))
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print("确认登陆成功耗时 %.3f 秒" % elapsed_time)
                    time.sleep(1)
                    break   # 当登录成功时退出循环
                else:
                    print("登录失败，继续尝试...")
            else:
                print("未知二维码抢码失败")
                time.sleep(1)

        frame_count += 1
        if time.time() - frame_start_time >= 1:
            fps = frame_count
            print(f"FPS:{fps}" + "\r", end='', flush=True)
            if print_login_message:  # 使用标志来决定是否打印消息
                print("扫码功能已打开，请开始抢码登陆")
                print_login_message = False  # 更新标志，确保消息只打印一次
            frame_count = 0
            frame_start_time = time.time()
        
              
# 保存 stokens 到文件
def save_stokens(stokens):
    try:
        with open("stoken.txt", "w") as file:
            file.write(stokens)
            print("stoken写入成功")
    except Exception as e:
        print(f"保存stoken时出错: {e}")
# 从文件中读取 stokens
def load_stokens():
    # 尝试从文件中读取stokens
    try:
        with open('stoken.txt', 'r') as file:
            return file.read().strip()  # 去除可能的空格或换行
    except FileNotFoundError:
        return None

if __name__ == '__main__':
    print("欢迎使用原神抢码器！本程序由吾爱作者tseed和lanlanyang共同开发，仅供学习交流使用！不得用于商业用途，否则后果自负！")
    print("欢迎参观我的个人博客：https://luomengguo.top")
    # 运行函数以确保 Chromium 存在
    ensure_chromium_exists()
    # 检查stokens文件是否存在
    if not os.path.exists("stoken.txt"):
        # 获取用户输入
        choice = input("是否开启浏览器？(Y代表开启，N代表关闭，默认为N,不区分大小写): ")
        username = input("请输入电话号码: ")
        # 如果用户没有输入任何内容，则使用默认值2
        if not choice:
            choice = "N"
        # 将choice转换为小写并进行比较
        devtools_value = True if choice.lower() == "y" else False
        # 启动异步事件
        stokens = (asyncio.get_event_loop().run_until_complete(main(username, devtools_value)))
        #等待3秒
        time.sleep(3)
        print(stokens)
        # 当获得 stokens 后
        save_option = input("是否要保存stoken? (Y/N，默认为N，不区分大小写): ")
        if save_option.lower() == 'y':
            save_stokens(stokens)
    else:
        stokens = load_stokens()
        if stokens:
            print("已从文件中加载 stoken!")
        else:    
            print("未从文件中加载到 stoken!")
    # 当前抢码游戏 原神=4，星穹铁道=8
    GameType = int(input('当前抢码游戏 原神=4，星穹铁道=8:'))
    #等待2秒
    time.sleep(2)
    print("正在打开扫码功能，请稍等...")
    # 使用分号分割字符串
    split_str = stokens.split(";")
    # 遍历分割后的字符串列表
    for item in split_str:
        # 判断是否包含stuid
        if "stuid" in item:
            # 使用等号分割字符串
            uid = item.split("=")[1]
            break
    # 填写米游社cookie
    cookie = stokens+'mid=0mmmmato08_mhy;'
    # 初始化屏幕和窗口
    device, left, top, right, bottom, dc = setup_screen_and_window()
    # 抢码开始
    qr_code_scanner(
        capture_function=lambda: capture_screen(left, top, right, bottom, dc),
        request_function=lambda ticket: Request(ticket,device,GameType),
        confirm_request_function=lambda ticket: ConfirmRequest(ticket,device,cookie,uid)
    )
    # 释放资源
    dc.DeleteDC()
    # 关闭窗口
    cv2.destroyAllWindows()
    # 退出程序
    exit(0)
