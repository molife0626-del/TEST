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
DOWNLOAD_DIR = "/tmp/zumen_downloads"

def fetch_data_via_csv():
    """CSVダウンロードボタンを押してデータを取得する"""
    if not SELENIUM_AVAILABLE:
        return pd.DataFrame(), "Seleniumライブラリがありません"

    status_log = []
    
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)

    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        prefs = {"download.default_directory": DOWNLOAD_DIR}
        options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15)

        # 1. ログイン
        status_log.append("ログイン中...")
        driver.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
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
        status_log.append("メニュー操作...")
        menu_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), '新規案件')]/ancestor-or-self::button/following-sibling::button[1] | //*[contains(text(), '新規案件')]/../following-sibling::button[1]")
        ))
        menu_btn.click()
        time.sleep(1)

        # 4. CSVダウンロード
        status_log.append("ダウンロード開始...")
        csv_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'CSVダウンロード')]")
        ))
        csv_btn.click()
        
        time.sleep(5)
        
        downloaded_files = os.listdir(DOWNLOAD_DIR)
        if not downloaded_files:
            time.sleep(5)
            downloaded_files = os.listdir(DOWNLOAD_DIR)
            
        if not downloaded_files:
            raise Exception("CSVファイルが見つかりませんでした")

        target_file = os.path.join(DOWNLOAD_DIR, downloaded_files[0])
        
        try:
            df = pd.read_csv(target_file, encoding='utf-8')
        except:
            df = pd.read_csv(target_file, encoding='shift_jis')

        driver.quit()
        return df, None

    except Exception as e:
        if 'driver' in locals(): driver.quit()
        return pd.DataFrame(), f"{str(e)}"

# ==========================================
# 🏭 メイン画面レイアウト
# ==========================================

# --- サイドバー：工場選択 ---
with st.sidebar:
    st.title("🏭 工場切替")
    # ここで工場を切り替える
    selected_factory = st.radio(
        "表示する工場を選択:",
        ("本社工場", "八尾工場")
    )
    st.divider()
    st.caption("工場ごとにレイアウト図を保存・表示できます。")

st.title(f"📊 {selected_factory} 稼働モニター")

# --- データ管理 ---
if 'product_df' not in st.session_state:
    st.session_state.product_df = pd.DataFrame()
if 'fetch_error' not in st.session_state:
    st.session_state.fetch_error = None

# 更新ボタン
if st.button("🔄 最新データを取得 (ズメーン連携)"):
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

if st.session_state.fetch_error:
    st.warning("⚠️ データの取得に失敗しました。")
    with st.expander("エラー詳細"):
        st.text(st.session_state.fetch_error)

# ==========================================
# 2カラムレイアウト
# ==========================================
col_map, col_list = st.columns([1.5, 1])

# --- 左側：機械間取り図 (工場ごとに切り替え) ---
with col_map:
    st.subheader(f"🗺️ {selected_factory} レイアウト図")
    
    # 工場ごとに異なるキー(key)を設定することで、画像を別々に保存します
    if selected_factory == "本社工場":
        uploaded_map = st.file_uploader("本社工場の図面をアップロード", type=['png', 'jpg', 'jpeg'], key="map_honsha")
    else:
        uploaded_map = st.file_uploader("八尾工場の図面をアップロード", type=['png', 'jpg', 'jpeg'], key="map_yao")
    
    # 画像表示エリア
    if uploaded_map:
        st.image(uploaded_map, use_column_width=True, caption=f"{selected_factory} レイアウト")
    else:
        # 画像がない時のプレースホルダー
        st.markdown(
            f"""
            <div style="
                background-color:#f3f4f6; 
                height:400px; 
                display:flex; 
                align-items:center; 
                justify-content:center; 
                border: 2px dashed #9ca3af; 
                border-radius: 10px;
                color:#4b5563; font-weight:bold; text-align:center;">
                {selected_factory}の図面が未登録です<br>
                画像をアップロードしてください
            </div>
            """, 
            unsafe_allow_html=True
        )

# --- 右側：製品リスト ---
with col_list:
    st.subheader("📋 進行中案件")
    
    if not display_df.empty:
        # 列名調整
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
        
        # リスト表示 (スクロールできるようにコンテナ化も可能)
        with st.container(height=600):
            for index, row in display_df.iterrows():
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
