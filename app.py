import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# ページ設定
st.set_page_config(page_title="ズメーン自動操作", layout="wide")

st.title("🤖 ズメーン CSVゲッター")
st.caption("ログイン → 「新規案件」の右隣のボタン(...) → CSVダウンロード")

# --- ログイン情報 ---
LOGIN_URL = "https://zume-n.com/login"
USER_EMAIL = "r.mori@mbs-m.co.jp"
USER_PASS = "Riki(1127)"

if st.button("🚀 CSVを取得する"):
    
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

        email_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[type='text']")
        ))
        email_input.clear()
        email_input.send_keys(USER_EMAIL)

        pass_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        pass_input.clear()
        pass_input.send_keys(USER_PASS)

        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(5) 

        # ==========================================
        # 2. 「案件一覧」へ移動
        # ==========================================
        status.info("🔄 「案件一覧」へ移動中...")
        
        try:
            anken_link = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), '案件一覧')]")
            ))
            anken_link.click()
            time.sleep(5)

        except:
            st.warning("URLで直接移動を試みます")
            driver.get("https://zume-n.com/projects")
            time.sleep(5)

        # ==========================================
        # 3. 「新規案件」の右隣のボタン(...)をクリック
        # ==========================================
        status.info("🔄 「新規案件」の右隣にあるボタン(...)を探しています...")

        try:
            # ★変更点: 「新規案件」という文字を含む要素の、親(ボタン自体)の、すぐ次の兄弟要素(Sibling)を探す
            # 構造: [新規案件ボタン] [・・・ボタン] と並んでいると想定
            
            menu_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), '新規案件')]/ancestor-or-self::button/following-sibling::button[1] | //*[contains(text(), '新規案件')]/../following-sibling::button[1]")
            ))
            
            # 見つかったボタンをクリック
            menu_btn.click()
            
            status.info("👉 メニューボタン(...)をクリックしました！")
            time.sleep(2) 

            # ==========================================
            # 4. 「CSV」を含む文字をクリック
            # ==========================================
            status.info("🔄 「CSV」ボタンを探して押します...")
            
            # ドロップダウンメニューの中からCSVを探す
            csv_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'CSV') or contains(text(), 'csv')]")
            ))
            csv_btn.click()
            
            time.sleep(5)

            # ==========================================
            # 5. 結果確認
            # ==========================================
            status.success("✅ CSVボタンを押しました！")
            st.image(driver.get_screenshot_as_png(), caption="操作後の画面")
            st.info("※クラウド環境のため、ファイルはサーバーに保存されました。")

        except Exception as e:
            st.error("❌ ボタンが見つからないか、押せませんでした。")
            st.write("▼ 現在の画面")
            st.image(driver.get_screenshot_as_png())
            st.error(f"詳細エラー: {e}")

    except Exception as e:
        st.error(f"システムエラー: {e}")
    
    finally:
        if 'driver' in locals():
            driver.quit()
