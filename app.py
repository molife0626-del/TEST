import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

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
# ⚙️ データ取得ロジック (エラーに強くする)
# ==========================================
LOGIN_URL = "https://zume-n.com/login"
USER_EMAIL = "r.mori@mbs-m.co.jp"
USER_PASS = "Riki(1127)"

@st.cache_data(ttl=300, show_spinner=False)
def fetch_product_data():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    data_list = []

    try:
        # 1. ログイン
        driver.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # 入力欄を探す（複数のパターンでトライ）
        try:
            email = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        except:
            email = driver.find_element(By.CSS_SELECTOR, "input[name='email']")
            
        try:
            pwd = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        except:
            pwd = driver.find_element(By.CSS_SELECTOR, "input[name='password']")

        email.clear(); email.send_keys(USER_EMAIL)
        pwd.clear(); pwd.send_keys(USER_PASS)
        
        # ログインボタン
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)

        # 2. 案件一覧へ移動
        try:
            # "案件一覧"のリンクを探してクリック
            link = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '案件一覧')]")))
            link.click()
            time.sleep(3)
        except:
            # 失敗したらURL直打ち
            driver.get("https://zume-n.com/projects")
            time.sleep(3)

        # 3. データ抽出 (品名とロット番号を探す)
        # テーブル行を取得
        rows = driver.find_elements(By.XPATH, "//table/tbody/tr")
        
        # ヘッダーを確認して列番号を特定する
        header_cells = driver.find_elements(By.XPATH, "//table/thead/tr/th")
        headers = [h.text.strip() for h in header_cells]
        
        # デフォルトの列番号（見つからなかった場合用）
        idx_name = 0 # 品名
        idx_lot = 1  # ロット
        
        # ヘッダーから列位置を検索
        for i, h in enumerate(headers):
            if "品名" in h or "製品名" in h: idx_name = i
            if "ロット" in h or "Lot" in h: idx_lot = i

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) > max(idx_name, idx_lot):
                p_name = cols[idx_name].text.strip()
                p_lot = cols[idx_lot].text.strip()
                
                # 空データは除外
                if p_name:
                    data_list.append({"製品名": p_name, "ロット番号": p_lot})

    except Exception as e:
        # エラーが起きても空リストではなくエラー情報を返す
        return pd.DataFrame(), str(e)
    finally:
        driver.quit()

    return pd.DataFrame(data_list), None


# ==========================================
# 🏭 メイン画面レイアウト
# ==========================================
st.title("🏭 工場生産管理モニター")

# 更新ボタン
if st.button("🔄 データを最新にする"):
    fetch_product_data.clear()
    st.rerun()

# データのロード
with st.spinner("ズメーンからデータを取得中..."):
    df, error_msg = fetch_product_data()

if error_msg:
    st.error("データ取得中にエラーが発生しましたが、画面を表示します。")
    st.caption(f"エラー詳細: {error_msg}")
    # テスト用ダミーデータ（エラー時も画面イメージを確認できるように）
    if df.empty:
        df = pd.DataFrame([
            {"製品名": "(取得失敗)", "ロット番号": "---"},
            {"製品名": "テストデータA", "ロット番号": "LOT-001"},
            {"製品名": "テストデータB", "ロット番号": "LOT-002"},
        ])

# --- 2カラムレイアウト ---
col_map, col_list = st.columns([1.5, 1])

# --- 左側：機械間取り図 ---
with col_map:
    st.subheader("🗺️ 機械レイアウト")
    
    # 画像アップローダー（毎回アップロードするのは大変なので、運用時は固定画像にします）
    st.info("工場の図面画像をアップロードしてください")
    layout_img = st.file_uploader("レイアウト図 (画像)", type=['png', 'jpg', 'jpeg'])
    
    if layout_img:
        st.image(layout_img, use_column_width=True, caption="工場レイアウト")
    else:
        # 画像がない場合のプレースホルダー（四角形を描画してごまかす）
        st.markdown(
            """
            <div style="background-color:#e5e7eb; height:400px; display:flex; align-items:center; justify-content:center; border: 2px dashed #9ca3af; border-radius: 10px;">
                <p style="color:#4b5563; font-weight:bold;">ここに間取り図が表示されます<br>(画像をアップロードしてください)</p>
            </div>
            """, 
            unsafe_allow_html=True
        )

# --- 右側：製品リスト ---
with col_list:
    st.subheader("📋 進行中案件")
    
    # データを強調して表示
    if not df.empty:
        # スタイリング（文字を大きく）
        st.markdown(
            """
            <style>
            .product-card {
                background-color: #f0f9ff;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 10px;
                border-left: 5px solid #0369a1;
            }
            .p-name { font-size: 1.1em; font-weight: bold; color: #1e293b; }
            .p-lot { font-size: 0.9em; color: #64748b; }
            </style>
            """, unsafe_allow_html=True
        )
        
        for index, row in df.iterrows():
            st.markdown(
                f"""
                <div class="product-card">
                    <div class="p-name">📦 {row['製品名']}</div>
                    <div class="p-lot">🔖 ロット: {row['ロット番号']}</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
    else:
        st.info("表示するデータがありません")

