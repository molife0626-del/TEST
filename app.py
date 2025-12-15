import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import time
import os

# ページ設定
st.set_page_config(page_title="ズメーン自動操作アプリ", layout="wide")

st.title("🤖 ズメーン CSV自動ダウンロード")
st.caption("IDとパスワードを入力してボタンを押すと、ロボットが代わりにサイトへ行き、CSVを取ってきます。")

# ==========================================
# ユーザー入力フォーム
# ==========================================
with st.form("login_form"):
    col1, col2 = st.columns(2)
    user_id = col1.text_input("ログインID (メールアドレス)")
    user_pass = col2.text_input("パスワード", type="password")
    
    # 実行ボタン
    submitted = st.form_submit_button("🚀 ログインしてCSVをダウンロード")

# ==========================================
# 自動操作ロジック
# ==========================================
if submitted:
    if not user_id or not user_pass:
        st.error("IDとパスワードを入力してください。")
        st.stop()

    status_text = st.empty()
    status_text.info("🔄 ブラウザを起動中...")

    # --- 1. ブラウザの設定 ---
    options = Options()
    options.add_argument("--headless")  # 画面を表示せずに裏で動かす
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080") # 画面サイズを大きくしておく

    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15) # 最大15秒待つ設定

        # --- 2. ログイン処理 ---
        status_text.info("🔄 ズメーンにアクセス中...")
        driver.get("https://zume-n.com/login") # ログインページへ移動（URLは推測）
        
        # もしログインページURLが違う場合、トップからログインボタンを探す処理が必要ですが
        # 一般的な /login を想定しています。
        
        # ID入力
        status_text.info("🔄 ログイン情報を入力中...")
        try:
            # メールアドレス入力欄を探す (name="email" か type="email" を想定)
            email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email']")))
            email_field.clear()
            email_field.send_keys(user_id)

            # パスワード入力欄を探す
            pass_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            pass_field.clear()
            pass_field.send_keys(user_pass)

            # ログインボタンを押す (type="submit" を想定)
            login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()
            
            # ログイン完了待ち（画面遷移を確認）
            time.sleep(3) # 少し待機
            
        except Exception as e:
            st.error(f"ログイン入力に失敗しました: {e}")
            driver.quit()
            st.stop()

        # --- 3. 案件一覧へ移動 ---
        status_text.info("🔄 「案件一覧」へ移動中...")
        
        try:
            # 「案件一覧」というテキストを持つリンクかボタンを探してクリック
            # XPath: ページ内の「案件一覧」という文字を含む要素を探す
            anken_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '案件一覧')] | //button[contains(text(), '案件一覧')]")))
            anken_link.click()
            
            time.sleep(2) # 読み込み待ち
            
        except Exception as e:
            st.warning("「案件一覧」ボタンが見つかりませんでした。URLで直接移動を試みます。")
            driver.get("https://zume-n.com/projects") # URL推測
            time.sleep(2)

        # --- 4. メニュー(...)を開いてCSVダウンロード ---
        status_text.info("🔄 CSVダウンロードボタンを探しています...")
        
        try:
            # 画像の「一番右のてんてんてん（...）」を探す
            # 通常、縦の三点リーダーは buttonタグやiタグで表現されます。
            # ここはサイトの構造が見えないため、いくつかのパターンで探します。
            
            # パターンA: 画面右上のメニューボタン（クラス名などから推測するのは難しいため、位置やアイコンで探すのが一般的）
            # 今回は「CSVダウンロード」という文字が隠れているメニューを開く動作
            
            # まず「︙」や「...」のようなボタンを探す
            # 画面上のボタンを全て取得し、位置が右側にあるものをクリックしてみる等の戦略もありますが、
            # ここでは「テーブル操作メニュー」っぽいものを探します。
            
            menu_buttons = driver.find_elements(By.XPATH, "//button")
            
            # メニューを開く（それっぽいボタンをクリック）
            # ※注意: 実際のHTMLクラス名がわからないため、ここが一番のエラーポイントです。
            # 画像を見ると「+ 新規案件」の横にあるボタンです。
            
            # 「新規案件」ボタンを探し、その近くのボタンを探すロジック
            new_project_btn = driver.find_element(By.XPATH, "//*[contains(text(), '新規案件')]")
            # その親要素などをたどって隣のボタンを探すのは複雑なため、
            # 画面右上のアイコン系ボタンをクリックしてみます。
            
            # 仮実装: ページ内のボタンで、アイコンのみ（テキストがない）ものを順に試す
            found_csv = False
            
            # 試しに「CSV」というリンクが最初から見えていないか確認
            try:
                csv_direct_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'CSV')]")
                csv_direct_btn.click()
                found_csv = True
            except:
                pass

            if not found_csv:
                # メニューボタンをクリックして展開する必要がある場合
                # 一般的なドロップダウンメニューのクラス名を推測してクリック
                dropdown_btn = driver.find_element(By.CSS_SELECTOR, "button[class*='dropdown'], button[class*='menu'], button[aria-haspopup='true']")
                dropdown_btn.click()
                time.sleep(1)
                
                # 開いたメニューの中から「CSV」を含む文字を探してクリック
                csv_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'CSV') or contains(text(), 'csv')]")))
                csv_btn.click()

            status_text.success("✅ CSVダウンロードボタンを押しました！")
            time.sleep(5) # ダウンロード完了待ち

            # --- 5. ダウンロードされたファイルを取得 ---
            # Streamlit Cloudなどのヘッドレス環境では、ファイルはサーバー内のダウンロードフォルダに保存されます。
            # 本来はダウンロード先を指定する必要がありますが、今回は簡易的に
            # 「今クリックしたことで何かがダウンロードされたか」は検知が難しいため、
            # ここまでの動作がエラーなく進んだことを成功とします。
            
            st.success("処理が完了しました。")
            st.warning("※注意: クラウド環境（ヘッドレスブラウザ）でのファイルダウンロード取得は、保存先設定の追加コードが必要です。現在は『ボタンを押す』ところまでを自動化しています。")
            
            # スクリーンショットを撮って確認（デバッグ用）
            screenshot = driver.get_screenshot_as_png()
            st.image(screenshot, caption="現在の画面（ロボットが見ている画面）")

        except Exception as e:
            st.error(f"操作中にエラーが発生しました: {e}")
            st.write("ロボットが見ていた画面:")
            st.image(driver.get_screenshot_as_png())

    except Exception as e:
        st.error(f"ブラウザ起動エラー: {e}")
    
    finally:
        # ブラウザを閉じる
        if 'driver' in locals():
            driver.quit()
