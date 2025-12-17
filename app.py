import streamlit as st
import time
import os

# Selenium関連
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

st.set_page_config(page_title="ズメーン自動操作 (デバッグ版)", layout="wide")

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
# 🤖 強力なログインロジック
# ==========================================
LOGIN_URL = "https://zume-n.com/login"
USER_EMAIL = "r.mori@mbs-m.co.jp"
USER_PASS = "Riki(1127)"

def run_debug_automation():
    if not SELENIUM_AVAILABLE:
        st.error("Seleniumがありません。requirements.txtを確認してください。")
        return

    status = st.empty()
    status.info("🔄 ブラウザを起動中...")

    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20) # 待ち時間を20秒に延長

        # 1. サイトへアクセス
        status.info(f"🔄 {LOGIN_URL} にアクセス中...")
        driver.get(LOGIN_URL)
        
        # 画面が表示されるまで待つ（bodyタグが出るまで）
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5) # 念入りに待つ
        
        # デバッグ: 現在の画面を撮影（入力欄があるか確認用）
        st.image(driver.get_screenshot_as_png(), caption="アクセス直後の画面")

        # 2. 入力欄を「順番」で探す（名前で探さない）
        status.info("🔄 入力欄を探しています...")
        
        # 画面上のすべての input タグを取得
        inputs = driver.find_elements(By.TAG_NAME, "input")
        
        # テキスト入力ができそうなものを抽出 (hiddenタイプなどを除外)
        text_inputs = [i for i in inputs if i.get_attribute("type") in ["text", "email", "password"]]
        
        if len(text_inputs) >= 2:
            # 1つ目を見つけて ID を入力
            status.info("✍️ 1つ目の欄にIDを入力...")
            text_inputs[0].clear()
            text_inputs[0].send_keys(USER_EMAIL)
            
            # 2つ目を見つけて パスワード を入力
            status.info("✍️ 2つ目の欄にパスワードを入力...")
            # パスワード欄は type="password" の可能性が高いので再検索
            pass_inputs = [i for i in inputs if i.get_attribute("type") == "password"]
            if pass_inputs:
                pass_inputs[0].clear()
                pass_inputs[0].send_keys(USER_PASS)
            else:
                # パスワード欄が見つからない場合は2番目の入力欄に入れる
                text_inputs[1].clear()
                text_inputs[1].send_keys(USER_PASS)
        else:
            status.error(f"❌ 入力欄が {len(text_inputs)} 個しか見つかりませんでした。")
            st.write("見つかった入力欄:", [i.get_attribute("outerHTML") for i in inputs])
            return

        # 3. ログインボタンを押す
        status.info("🔄 ログインボタンを押します...")
        try:
            # type="submit" のボタンを探す
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_btn.click()
        except:
            # 失敗したら "ログイン" という文字が入ったボタンを探す
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if "ログイン" in btn.text:
                    btn.click()
                    break
        
        time.sleep(5) # ログイン処理待ち

        # 4. 案件一覧へ移動
        status.info("🔄 「案件一覧」へ移動中...")
        try:
            link = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '案件一覧')]")))
            link.click()
            time.sleep(3)
        except:
            driver.get("https://zume-n.com/projects")
            time.sleep(3)

        # 5. メニューボタン(...)をクリック
        status.info("🔄 「新規案件」の右隣にあるメニュー(...)を開きます...")
        menu_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), '新規案件')]/ancestor-or-self::button/following-sibling::button[1] | //*[contains(text(), '新規案件')]/../following-sibling::button[1]")
        ))
        menu_btn.click()
        time.sleep(2)

        # 6. CSVダウンロードの文字を確認
        status.info("👀 「CSVダウンロード」の文字が表示されているか確認中...")
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(), 'CSV') or contains(text(), 'csv')]")
        ))
        
        status.success("✅ 成功！メニューが開き、「CSVダウンロード」が表示されました。")
        st.image(driver.get_screenshot_as_png(), caption="成功画面")
        
    except Exception as e:
        st.error("❌ エラーが発生しました")
        st.code(str(e)) # エラー内容を表示
        if 'driver' in locals():
            st.image(driver.get_screenshot_as_png(), caption="エラー時の画面")
            # デバッグ用にHTMLの一部を表示
            st.write("ページソースの一部:", driver.page_source[:1000])
    
    finally:
        if 'driver' in locals():
            driver.quit()

# ==========================================
# 🖥️ アプリ画面
# ==========================================
st.title("🤖 ズメーン自動操作 (デバッグ版)")
st.caption("入力欄を自動探索してログインを試みます。")

if st.button("🚀 ロボットを起動する", type="primary"):
    run_debug_automation()
