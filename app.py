import streamlit as st
import pandas as pd
import time
import os
import shutil

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

st.set_page_config(page_title="ズメーン自動CSV取得", layout="wide")

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
# 🤖 自動化ロジック
# ==========================================
LOGIN_URL = "https://zume-n.com/login"
USER_EMAIL = "r.mori@mbs-m.co.jp"
USER_PASS = "Riki(1127)"
DOWNLOAD_DIR = "/tmp/zumen_downloads" # クラウド上の一時保存場所

def run_full_process():
    if not SELENIUM_AVAILABLE:
        st.error("Seleniumがありません。requirements.txtを確認してください。")
        return

    # ダウンロードフォルダをリセット
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)

    status = st.empty()
    status.info("🔄 ブラウザを起動中...")

    try:
        # ブラウザ設定（ダウンロード先を指定）
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # ダウンロード設定
        prefs = {"download.default_directory": DOWNLOAD_DIR}
        options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)

        # 1. サイトへアクセス
        status.info(f"🔄 {LOGIN_URL} にアクセス中...")
        driver.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        # 2. ログイン（入力欄 自動探索）
        status.info("🔄 ログイン情報を入力中...")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        text_inputs = [i for i in inputs if i.get_attribute("type") in ["text", "email", "password"]]
        
        if len(text_inputs) >= 2:
            text_inputs[0].clear()
            text_inputs[0].send_keys(USER_EMAIL)
            
            pass_inputs = [i for i in inputs if i.get_attribute("type") == "password"]
            if pass_inputs:
                pass_inputs[0].clear()
                pass_inputs[0].send_keys(USER_PASS)
            else:
                text_inputs[1].clear()
                text_inputs[1].send_keys(USER_PASS)
            
            # ログインボタン
            try:
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            except:
                # 万が一 type=submit がない場合
                for btn in driver.find_elements(By.TAG_NAME, "button"):
                    if "ログイン" in btn.text:
                        btn.click(); break
            
            time.sleep(5)
        else:
            raise Exception("ログイン入力欄が見つかりませんでした")

        # 3. 案件一覧へ移動
        status.info("🔄 「案件一覧」へ移動中...")
        try:
            link = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '案件一覧')]")))
            link.click()
            time.sleep(3)
        except:
            driver.get("https://zume-n.com/projects")
            time.sleep(3)

        # 4. メニューボタン(...)をクリック
        status.info("🔄 「新規案件」横のメニューを開きます...")
        menu_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), '新規案件')]/ancestor-or-self::button/following-sibling::button[1] | //*[contains(text(), '新規案件')]/../following-sibling::button[1]")
        ))
        menu_btn.click()
        time.sleep(2)

        # 5. 「CSVダウンロード」をクリック！
        status.info("👉 「CSVダウンロード」をクリックします！")
        
        csv_text_element = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'CSVダウンロード')]")
        ))
        csv_text_element.click()
        
        # 6. ダウンロード完了待ち
        status.info("⏳ ファイルのダウンロードを待機中...")
        time.sleep(5)
        
        # ファイルチェック
        downloaded_files = os.listdir(DOWNLOAD_DIR)
        if not downloaded_files:
            time.sleep(5) # もう少し待つ
            downloaded_files = os.listdir(DOWNLOAD_DIR)
            
        if not downloaded_files:
            raise Exception("CSVファイルが保存されませんでした")

        target_file = os.path.join(DOWNLOAD_DIR, downloaded_files[0])
        status.success(f"✅ ダウンロード成功: {downloaded_files[0]}")

        # 7. データ読み込みと表示
        try:
            df = pd.read_csv(target_file, encoding='utf-8')
        except:
            df = pd.read_csv(target_file, encoding='shift_jis') # 文字化け対策
            
        return df

    except Exception as e:
        st.error("❌ エラーが発生しました")
        st.error(str(e))
        if 'driver' in locals():
            st.image(driver.get_screenshot_as_png(), caption="エラー時の画面")
        return None
    
    finally:
        if 'driver' in locals():
            driver.quit()

# ==========================================
# 🖥️ アプリ画面
# ==========================================
st.title("🤖 ズメーン データ取得ロボット")
st.caption("サイトから最新のCSVをダウンロードして表示します。")

if st.button("🚀 最新データを取得する", type="primary"):
    df = run_full_process()
    
    if df is not None:
        st.balloons()
        st.subheader("📋 取得したデータ")
        st.dataframe(df)
        
        # CSVダウンロードボタン（手元に保存用）
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 このCSVを保存する",
            data=csv,
            file_name="zumen_data.csv",
            mime="text/csv"
        )
