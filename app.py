import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# ページ設定
st.set_page_config(page_title="サイト接続テスト", layout="wide")

st.title("🌐 サイト接続テスト")
st.caption("指定したURLを開き、中身が正しく表示されるか確認します。")

# URL入力欄（デフォルトは解析したHTMLにあった drawings ページ）
target_url = st.text_input("アクセスするURL", "https://zume-n.com/drawings")

if st.button("🚀 ページを開く"):
    
    status = st.empty()
    status.info("🔄 ブラウザを起動しています...")

    # --- ブラウザ設定 (Headlessモード) ---
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20) # 最大20秒待つ

        # --- アクセス開始 ---
        status.info(f"🔄 {target_url} にアクセス中...")
        driver.get(target_url)

        # --- 読み込み待ち (重要) ---
        status.info("⏳ 画面の描画を待っています...")
        
        # Next.jsのサイトは <div id="__next"> の中にコンテンツが作られます。
        # まずこれが存在するか確認します。
        wait.until(EC.presence_of_element_located((By.ID, "__next")))
        
        # さらに、人間が見るためのコンテンツ（例えば「図面」や「一覧」という文字）が出るまで少し待ちます
        time.sleep(5) 

        # --- 結果確認 ---
        status.success("✅ ページが開けました！")
        
        # 現在のURLとタイトルを表示
        st.write(f"**現在のURL:** {driver.current_url}")
        st.write(f"**ページタイトル:** {driver.title}")

        # スクリーンショットを表示（証拠写真）
        st.image(driver.get_screenshot_as_png(), caption="ロボットが見ている画面")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        # エラー時も念のためスクショを撮る
        try:
            st.image(driver.get_screenshot_as_png(), caption="エラー時の画面")
        except:
            pass
    
    finally:
        if 'driver' in locals():
            driver.quit()
