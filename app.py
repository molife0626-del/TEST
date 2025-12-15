import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
# スタイリッシュな表表示ライブラリ
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

# ページ設定 (ワイド表示で見やすく)
st.set_page_config(page_title="工場内案件一覧", layout="wide", page_icon="🏭")

# カスタムCSSで少しおしゃれに
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: 700; color: #1E3A8A;}
    .sub-header {font-size: 1.2rem; color: #6B7280;}
    /* AgGridのヘッダー色を調整 */
    .ag-header-cell-label {color: #374151 !important; font-weight: 600 !important;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 パスワード認証
# ==========================================
def check_password():
    SECRET_PASSWORD = "1234" # ★パスワード
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        st.markdown("## 🔒 ログイン")
        with st.form("login_form"):
            password = st.text_input("パスワードを入力", type="password")
            submitted = st.form_submit_button("ログイン")
            if submitted and password == SECRET_PASSWORD:
                st.session_state.password_correct = True
                st.rerun()
            elif submitted:
                st.error("パスワードが違います")
        st.stop()

check_password()

# ==========================================
# 🏭 メインアプリ
# ==========================================
st.markdown('<div class="main-header">🏭 工場内 案件・図面一覧システム</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ズメーンから最新データを取得し、スタイリッシュに可視化します。</div>', unsafe_allow_html=True)
st.divider()

# --- ズメーンのログイン情報 ---
LOGIN_URL = "https://zume-n.com/login"
USER_EMAIL = "r.mori@mbs-m.co.jp"
USER_PASS = "Riki(1127)"

# データ取得関数（キャッシュ化して無駄なアクセスを防ぐ）
@st.cache_data(ttl=300, show_spinner=False) # 5分間データを保持
def fetch_data_from_zumen():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        # 1. ログイン
        driver.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)

        email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email']")))
        email_input.clear(); email_input.send_keys(USER_EMAIL)
        pass_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        pass_input.clear(); pass_input.send_keys(USER_PASS)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)

        # 2. 案件一覧へ移動
        try:
            anken_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '案件一覧')]")))
            anken_link.click()
        except:
            driver.get("https://zume-n.com/projects")
        
        # 3. データスクレイピング（表データを読み取る）
        time.sleep(5) # 表の描画待ち
        
        # テーブルの行を取得 (tbody内のtrタグを探す)
        rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table/tbody/tr")))
        
        data = []
        for row in rows:
            # 各行のセル(td)のテキストを取得
            cols = row.find_elements(By.TAG_NAME, "td")
            cols_text = [ele.text.strip() for ele in cols if ele.text.strip() != ""]
            if cols_text:
                data.append(cols_text)

        # ヘッダー取得試行（失敗したら仮のヘッダー）
        try:
            header_elements = driver.find_elements(By.XPATH, "//table/thead/tr/th")
            headers = [h.text.strip().replace("\n", "") for h in header_elements if h.text.strip() != ""]
            # 画像を見る限り、最初の数列はチェックボックスやアイコン用なので調整が必要かも
            # いったんデータ数に合わせてカット
            if len(headers) > len(data[0]):
                headers = headers[:len(data[0])]
        except:
            headers = [f"項目{i+1}" for i in range(len(data[0]))]

        # DataFrame作成
        df = pd.DataFrame(data, columns=headers)
        return df

    except Exception as e:
        raise e
    finally:
        driver.quit()


# ==========================================
# UI表示部分
# ==========================================

col1, col2 = st.columns([1, 3])
with col1:
    # データ取得ボタン
    if st.button("🔄 最新データを取得・更新", type="primary", use_container_width=True):
        try:
            with st.spinner("ロボットがサイトにアクセス中...少し時間がかかります"):
                # キャッシュをクリアして再取得
                fetch_data_from_zumen.clear()
                df = fetch_data_from_zumen()
                st.session_state['data_df'] = df
            st.success("取得完了！")
        except Exception as e:
            st.error(f"データ取得エラー: {e}")
            st.info("サイトの構造が変わった可能性があります。")

# データが存在する場合、スタイリッシュな表を表示
if 'data_df' in st.session_state and not st.session_state['data_df'].empty:
    df = st.session_state['data_df']

    # --- AgGridの設定 (スタイリッシュ化) ---
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # 全列に適用する設定
    gb.configure_default_column(
        resizable=True, 
        filterable=True, 
        sortable=True,
        editable=False, # 編集不可
        minWidth=100,
    )
    
    # 特定の列の設定（例：もし「ステータス」列があれば色を変えるなど）
    # ※列名が正確に分からないため、汎用的な設定にします。
    # もし列名が分かれば、以下のように特定列を装飾できます。
    # gb.configure_column("ステータス", cellStyle=JsCode("""
    #     function(params) {
    #         if (params.value === '加工中') { return {'color': 'orange', 'fontWeight': 'bold'}; }
    #         if (params.value === '完了') { return {'color': 'green', 'fontWeight': 'bold'}; }
    #         return null;
    #     }
    # """))

    # ページネーション（行が多い場合に見やすく）
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    
    # 選択機能
    gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren=True)
    
    # グリッドオプションの構築
    gridOptions = gb.build()

    st.markdown("#### 📋 案件・図面リスト")
    st.caption("ヘッダーをクリックで並べ替え、フィルタアイコンで検索ができます。")

    # AgGridの表示
    grid_response = AgGrid(
        df, 
        gridOptions=gridOptions,
        # テーマ選択: 'streamlit', 'alpine', 'balham', 'material'
        theme='balham',  # プロフェッショナルで見やすいテーマ
        height=600, 
        width='100%',
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED, 
        update_mode=GridUpdateMode.NO_UPDATE,
        fit_columns_on_grid_load=False, # 列幅を自動調整しない（横スクロール許可）
        allow_unsafe_jscode=True # JSCodeを使う場合に必要
    )

    st.markdown(f"*合計 {len(df)} 件のデータを表示中*")

else:
    st.info("👈 左上のボタンを押して、最新データを取得してください。")
