import streamlit as st
import time
import os

# Selenium関連のインポート
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# ページ設定
st.set_page_config(page_title="ズメーン自動操作", layout="wide")

# ==========================================
# 🔐 パスワード認証
# ==========================================
def check_password():
    SECRET_PASSWORD = "1234"
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        st.markdown("## 🔒 ログイン")
        with st.form("login_form"):
            password = st.text_input("パスワード", type="password")
            if st.form_submit_button("ログイン"):
                if password == SECRET_PASSWORD:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("パスワードが違います")
        st.stop()

check_password()

# ==========================================
# 🤖 自動操作ロジック
# ==========================================
LOGIN_URL = "https://zume-n.com/login"
USER_EMAIL = "r.mori@mbs-m.co.jp"
USER_PASS = "Riki(1127)"

def run_automation():
    """ログインしてメニューを開き、CSVダウンロードの文字を表示するまで"""
    if not SELENIUM_AVAILABLE:
        st.error("Seleniumライブラリがありません。requirements.txtを確認してください。")
        return

    status = st.empty()
    status.info("🔄 ブラウザを起動中...")

    try:
        # ブラウザ設定
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15)

        # 1. ログイン
        status.info(f"🔄 {LOGIN_URL} にアクセス中...")
        driver.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        try: email = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        except: email = driver.find_element(By.CSS_SELECTOR, "input[name='email']")
        try: pwd = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        except: pwd = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        
        email.clear(); email.send_keys(USER_EMAIL)
        pwd.clear(); pwd.send_keys(USER_PASS)
        
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3) # ログイン待ち

        # 2. 案件一覧へ移動
        status.info("🔄 「案件一覧」へ移動中...")
        try:
            link = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '案件一覧')]")))
            link.click()
            time.sleep(3)
        except:
            driver.get("https://zume-n.com/projects")
            time.sleep(3)

        # 3. メニューボタン(...)をクリック
        status.info("🔄 「新規案件」の右隣にあるメニュー(...)を開きます...")
        
        # 「新規案件」ボタンのすぐ後ろにあるボタンを探してクリック
        menu_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), '新規案件')]/ancestor-or-self::button/following-sibling::button[1] | //*[contains(text(), '新規案件')]/../following-sibling::button[1]")
        ))
        menu_btn.click()
        time.sleep(1) # メニューが開くのを待つ

        # 4. 「CSVダウンロード」の文字を確認
        status.info("👀 「CSVダウンロード」の文字が表示されているか確認中...")
        
        # 画面上に「CSV」を含む要素が見えているかチェック
        csv_element = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), 'CSV') or contains(text(), 'csv')]")
        ))
        
        # ここでストップ！
        status.success("✅ 成功！メニューが開き、「CSVダウンロード」が表示されました。")
        
        # 証拠写真を撮る
        st.image(driver.get_screenshot_as_png(), caption="現在の画面（メニューが開いている状態）")
        
    except Exception as e:
        st.error("❌ エラーが発生しました")
        st.error(f"詳細: {e}")
        # エラー時の画面も表示
        if 'driver' in locals():
            st.image(driver.get_screenshot_as_png(), caption="エラー時の画面")
    
    finally:
        if 'driver' in locals():
            driver.quit()

# ==========================================
# 🖥️ アプリ画面
# ==========================================
st.title("🤖 ズメーン自動操作 (メニュー表示まで)")
st.caption("ボタンを押すと、ロボットがログインしてメニューを開き、CSVダウンロードの文字を表示します。")

if st.button("🚀 ロボットを起動する", type="primary"):
    run_automation()
