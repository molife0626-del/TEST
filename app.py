import streamlit as st
import pandas as pd
import time
import os
import shutil

# Selenium関連のインポート（エラー時はスキップ）
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
st.set_page_config(page_title="工場稼働モニタリング", layout="wide")

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
# ⚙️ データ取得ロジック (CSVダウンロード方式)
# ==========================================
LOGIN_URL = "https://zume-n.com/login"
USER_EMAIL = "r.mori@mbs-m.co.jp"
USER_PASS = "Riki(1127)"
DOWNLOAD_DIR = "/tmp/zumen_downloads" # クラウド上の一時保存場所

def fetch_data_via_csv():
    """CSVダウンロードボタンを押してデータを取得する"""
    if not SELENIUM_AVAILABLE:
        return pd.DataFrame(), "Seleniumライブラリがありません"

    status_log = []
    
    # ダウンロードフォルダの初期化
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)

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
        
        status_log.append("ブラウザ起動...")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15)

        # 1. ログイン
        status_log.append("ログイン中...")
        driver.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # 入力欄特定
        try: email = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        except: email = driver.find_element(By.CSS_SELECTOR, "input[name='email']")
        
        try: pwd = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        except: pwd = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        
        email.clear(); email.send_keys(USER_EMAIL)
        pwd.clear(); pwd.send_keys(USER_PASS)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)

        # 2. 案件一覧へ
        status_log.append("案件一覧へ移動...")
        try:
            link = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '案件一覧')]")))
            link.click()
            time.sleep(3)
        except:
            driver.get("https://zume-n.com/projects")
            time.sleep(3)

        # 3. メニュー(...)を開く
        status_log.append("メニュー(...)をクリック...")
        menu_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), '新規案件')]/ancestor-or-self::button/following-sibling::button[1] | //*[contains(text(), '新規案件')]/../following-sibling::button[1]")
        ))
        menu_btn.click()
        time.sleep(1)

        # 4. CSVダウンロードを押す
        status_log.append("CSVダウンロードをクリック...")
        csv_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'CSVダウンロード')]")
        ))
        csv_btn.click()
        
        # 5. ダウンロード完了待ち
        status_log.append("ファイル保存待ち...")
        time.sleep(5) # ダウンロード時間を確保
        
        # ファイルを探す
        downloaded_files = os.listdir(DOWNLOAD_DIR)
        if not downloaded_files:
            # もう少し待つ
            time.sleep(5)
            downloaded_files = os.listdir(DOWNLOAD_DIR)
            
        if not downloaded_files:
            raise Exception("CSVファイルがダウンロードされませんでした")

        # 最新のファイルを取得
        target_file = os.path.join(DOWNLOAD_DIR, downloaded_files[0])
        status_log.append(f"ファイル取得成功: {downloaded_files[0]}")
        
        # CSV読み込み (Shift-JISかUTF-8か判別しながら)
        try:
            df = pd.read_csv(target_file, encoding='utf-8')
        except:
            df = pd.read_csv(target_file, encoding='shift_jis')

        driver.quit()
        return df, None

    except Exception as e:
        if 'driver' in locals(): driver.quit()
        return pd.DataFrame(), f"{str(e)} (ログ: {' -> '.join(status_log)})"

# ==========================================
# 🏭 メイン画面レイアウト
# ==========================================
st.title("🏭 工場生産管理モニター")

# --- データ管理 ---
if 'product_df' not in st.session_state:
    st.session_state.product_df = pd.DataFrame()
if 'fetch_error' not in st.session_state:
    st.session_state.fetch_error = None

# 更新ボタン
if st.button("🔄 最新データを取得 (CSVダウンロード)"):
    with st.spinner("ロボットがCSVをダウンロード中..."):
        df, err = fetch_data_via_csv()
        st.session_state.product_df = df
        st.session_state.fetch_error = err

# --- データ表示用 (空ならデモデータ) ---
display_df = st.session_state.product_df
if display_df.empty:
    display_df = pd.DataFrame([
        {"品名": "【デモ】製品A", "ロット番号": "LOT-001"},
        {"品名": "【デモ】製品B", "ロット番号": "LOT-002"},
    ])

# エラー表示
if st.session_state.fetch_error:
    st.warning("⚠️ データの取得に失敗しました。")
    with st.expander("エラー詳細"):
        st.text(st.session_state.fetch_error)

# ==========================================
# 画面レイアウト
# ==========================================
col_map, col_list = st.columns([1.5, 1])

# --- 左側：機械間取り図 ---
with col_map:
    st.subheader("🗺️ 機械レイアウト")
    uploaded_map = st.file_uploader("レイアウト図をアップロード", type=['png', 'jpg', 'jpeg'])
    if uploaded_map:
        st.image(uploaded_map, use_column_width=True, caption="工場レイアウト")
    else:
        st.info("画像をアップロードしてください")

# --- 右側：製品リスト ---
with col_list:
    st.subheader("📋 進行中案件")
    
    if not display_df.empty:
        # 列名調整 (CSVの列名が微妙に違う場合に対応)
        # 品名っぽい列とロットっぽい列を探す
        cols = display_df.columns.tolist()
        col_name = next((c for c in cols if "品名" in c or "製品" in c), cols[0])
        col_lot = next((c for c in cols if "ロット" in c or "Lot" in c), cols[1] if len(cols)>1 else cols[0])

        st.markdown(
            """
            <style>
            .p-card {
                background-color: white;
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 8px;
                border-left: 5px solid #3b82f6;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .p-title { font-weight: bold; font-size: 1.1em; color: #1f2937; }
            .p-info { color: #6b7280; font-size: 0.9em; margin-top: 4px; }
            </style>
            """, unsafe_allow_html=True
        )
        
        for index, row in display_df.iterrows():
            # データが存在する場合のみ表示
            if pd.notna(row[col_name]):
                p_name = row[col_name]
                p_lot = row[col_lot] if pd.notna(row[col_lot]) else "---"
                
                st.markdown(
                    f"""
                    <div class="p-card">
                        <div class="p-title">📦 {p_name}</div>
                        <div class="p-info">🔖 ロット: {p_lot}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
