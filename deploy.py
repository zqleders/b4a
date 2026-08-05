import os
import time
from playwright.sync_api import sync_playwright
import requests

# 从环境变量中获取敏感配置及访问地址
EMAIL = os.environ.get("B4A_EMAIL")
PASSWORD = os.environ.get("B4A_PASSWORD")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

LOGIN_URL = os.environ.get("B4A_LOGIN_URL")
CONTAINER_URL = os.environ.get("B4A_CONTAINER_URL")

def send_telegram_message(text):
    """发送文字消息到 Telegram"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print(f"[TG Text] {text}")
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"发送 Telegram 文字失败: {e}")

def send_telegram_photo(photo_path, caption):
    """发送截图到 Telegram"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print(f"[TG Photo] 略过发送图片: {caption}")
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as photo:
            files = {"photo": photo}
            data = {"chat_id": TG_CHAT_ID, "caption": caption}
            requests.post(url, files=files, data=data, timeout=30)
    except Exception as e:
        print(f"发送 Telegram 图片失败: {e}")

def run_automation():
    if not LOGIN_URL or not CONTAINER_URL:
        raise ValueError("环境变量 B4A_LOGIN_URL 或 B4A_CONTAINER_URL 未设置！")

    screenshot_counter = 1
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # -----------------------------------------------------------------
            # 第 1 步：访问登录页并输入邮箱
            # -----------------------------------------------------------------
            send_telegram_message("🚀 开始执行 B4A 自动部署任务...")
            print(f"正在访问登录页: {LOGIN_URL}")
            page.goto(LOGIN_URL, timeout=60000)
            page.wait_for_load_state("networkidle")
            
            print("正在输入邮箱...")
            page.locator('//*[@id="email"]').fill(EMAIL)
            
            path1 = f"step_{screenshot_counter}_email.png"
            page.screenshot(path=path1)
            send_telegram_photo(path1, "步骤 1: 成功输入邮箱")
            screenshot_counter += 1

            # -----------------------------------------------------------------
            # 第 2 步：输入密码
            # -----------------------------------------------------------------
            print("正在输入密码...")
            page.locator('//*[@id="password"]').fill(PASSWORD)
            
            path2 = f"step_{screenshot_counter}_password.png"
            page.screenshot(path=path2)
            send_telegram_photo(path2, "步骤 2: 成功输入密码")
            screenshot_counter += 1

            # -----------------------------------------------------------------
            # 第 3 步：点击登录按钮
            # -----------------------------------------------------------------
            print("正在点击登录按钮...")
            login_btn = page.locator('button.Button_primary__THcya').filter(has_text="Continue")
            login_btn.click()
            
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(5)
            
            path3 = f"step_{screenshot_counter}_login.png"
            page.screenshot(path=path3, full_page=True)
            send_telegram_photo(path3, "步骤 3: 登录动作执行完毕（请检查是否有CF验证阻拦）")
            screenshot_counter += 1

            # -----------------------------------------------------------------
            # 第 4 步：直接访问容器管理页
            # -----------------------------------------------------------------
            print(f"正在跳转至容器页: {CONTAINER_URL}")
            page.goto(CONTAINER_URL, timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            path4 = f"step_{screenshot_counter}_containers.png"
            page.screenshot(path=path4)
            send_telegram_photo(path4, "步骤 4: 成功进入容器面板页")
            screenshot_counter += 1

            # -----------------------------------------------------------------
            # 第 5 步：点击 Action 呼出菜单，再点击部署链接
            # -----------------------------------------------------------------
            print("正在查找并点击 Action 呼出按钮...")
            # 通过按钮文字 "Action" 及特征类名定位呼出按钮
            action_btn = page.locator('button').filter(has_text="Action").filter(has=page.locator('svg'))
            action_btn.wait_for(state="visible", timeout=15000)
            action_btn.click()
            
            # 等待菜单展开
            time.sleep(2)
            
            print("正在查找并点击 Deploy the latest commit...")
            deploy_item = page.locator('ul.py-1 li').filter(has_text="Deploy the latest commit")
            deploy_item.wait_for(state="visible", timeout=10000)
            deploy_item.click()
            
            time.sleep(5)
            
            path5 = f"step_{screenshot_counter}_deployed.png"
            page.screenshot(path=path5)
            send_telegram_photo(path5, "步骤 5: 已成功点开 Action 菜单并触发 Deploy the latest commit！")
            
            send_telegram_message("✅ B4A 容器项目定时自动部署流程执行完毕！")

        except Exception as e:
            error_msg = f"❌ 自动化执行过程中发生异常: {str(e)}"
            print(error_msg)
            error_path = "error_snapshot.png"
            page.screenshot(path=error_path, full_page=True)
            send_telegram_photo(error_path, error_msg)
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run_automation()
