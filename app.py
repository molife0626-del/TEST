import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# ページ設定
st.set_page_config(page_title="ズメーン自動操作", layout="wide")

st.title("🤖 ズメーン自動操作ロボット")
st.caption("ログイン → 「案件一覧」の文字をクリックします。")

# --- ログイン情報 ---
LOGIN_URL = "https://zume-n.com/login"
USER_EMAIL = "r.mori@mbs-m.co.jp"
USER_PASS = "Riki(1127)"

if st.button("🚀 実行する"):
    
    status = st.empty()
    status.info("🔄 ブラウザを起動中...")

    # --- ブラウザ設定 ---
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15)

        # ==========================================
        # 1. ログイン処理
        # ==========================================
        status.info(f"🔄 {LOGIN_URL} にアクセス中...")
        driver.get(LOGIN_URL)
        
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        status.info("🔄 ログイン情報を入力中...")
        
        email_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[type='text']")
        ))
        email_input.clear()
        email_input.send_keys(USER_EMAIL)

        pass_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        pass_input.clear()
        pass_input.send_keys(USER_PASS)

        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

        status.info("⏳ ログイン処理中...")
        time.sleep(5) 

        # ==========================================
        # 2. 「案件一覧」の文字をクリック
        # ==========================================
        status.info("🔄 「案件一覧」という文字を探しています...")

        try:
            # ★変更点: タグを限定せず(*)、テキストに「案件一覧」を含むあらゆる要素を探す
            anken_element = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), '案件一覧')]")
            ))
            
            # 見つけた要素をクリック
            anken_element.click()
            
            status.info("👉 「案件一覧」をクリックしました！画面遷移を待っています...")
            time.sleep(5)

            # ==========================================
            # 3. 結果確認
            # ==========================================
            status.success("✅ 完了しました！現在の画面を確認してください。")
            st.write(f"**現在のURL:** {driver.current_url}")
            st.image(driver.get_screenshot_as_png(), caption="クリック後の画面")

        except Exception as e:
            st.error("❌ 「案件一覧」の文字が見つからないか、クリックできませんでした。")
            st.write("▼ 現在の画面")
            st.image(driver.get_screenshot_as_png())
            st.error(f"詳細エラー: {e}")

    except Exception as e:
        st.error(f"システムエラー: {e}")
    
    finally:
        if 'driver' in locals():
            driver.quit()
