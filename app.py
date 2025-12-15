import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# ページ設定
st.set_page_config(page_title="ズメーン自動ログイン", layout="wide")

st.title("🤖 ズメーン自動ログイン")
st.caption("指定されたアカウントで自動ログインを試みます。")

# --- ログイン情報 (コードに埋め込み) ---
LOGIN_URL = "https://zume-n.com/login"  # ログインページのURL（推測）
USER_EMAIL = "r.mori@mbs-m.co.jp"
USER_PASS = "Riki(1127)"

if st.button("🚀 ログインを実行"):
    
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

        # 1. ログインページへアクセス
        status.info(f"🔄 {LOGIN_URL} にアクセスしています...")
        driver.get(LOGIN_URL)
        
        # 読み込み待ち
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2) # 念のための待機

        # 2. メールアドレス入力
        status.info("🔄 メールアドレスを入力中...")
        # inputタグの中から emailタイプ または name="email" を探す
        email_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[type='text']")
        ))
        email_input.clear()
        email_input.send_keys(USER_EMAIL)

        # 3. パスワード入力
        status.info("🔄 パスワードを入力中...")
        pass_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        pass_input.clear()
        pass_input.send_keys(USER_PASS)

        # 4. ログインボタン押下
        status.info("🔄 ログインボタンを押しています...")
        # ボタンを探す (type="submit" または "ログイン" という文字を含むボタン)
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

        # 5. 結果確認
        status.info("⏳ ログイン後の画面を読み込んでいます...")
        time.sleep(5) # 画面遷移待ち

        # 成功メッセージと証拠写真
        status.success("✅ 処理が完了しました！現在の画面を確認してください。")
        
        st.write(f"**現在のURL:** {driver.current_url}")
        
        # スクリーンショットを表示
        st.image(driver.get_screenshot_as_png(), caption="現在の画面")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        # エラー時の画面も保存
        if 'driver' in locals():
            st.image(driver.get_screenshot_as_png(), caption="エラー時の画面")
    
    finally:
        if 'driver' in locals():
            driver.quit()
