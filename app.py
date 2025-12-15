import streamlit as st
import pandas as pd
import io
import base64
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt

# ページ設定
st.set_page_config(
    page_title="図面管理ビューアー",
    page_icon="📐",
    layout="wide"
)

# ==========================================
# 🔐 パスワード認証 (Enterキー対応)
# ==========================================
def check_password():
    """パスワード認証を行う関数"""
    SECRET_PASSWORD = "1234" # ★パスワード設定
    
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        st.markdown("## 🔒 ログイン")
        st.caption("関係者専用：図面管理システム")
        
        # フォームを使うことでEnterキーで送信可能
        with st.form("login_form"):
            password = st.text_input("パスワードを入力してください", type="password")
            submitted = st.form_submit_button("ログイン")
            
            if submitted:
                if password == SECRET_PASSWORD:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("パスワードが違います")
        st.stop()

# アプリの最初に認証を実行
check_password()


# ==========================================
# 📐 メインアプリ (ログイン後のみ表示)
# ==========================================

# サイドバー：情報とリンク
with st.sidebar:
    st.title("📐 図面管理メニュー")
    st.markdown("---")
    st.markdown("### 🔗 外部サイトリンク")
    st.markdown(
        """
        図面データのダウンロードはこちらから：<br>
        [**zume-n.com 図面検索**](https://zume-n.com/drawings)
        """,
        unsafe_allow_html=True
    )
    st.info("上記サイトからダウンロードしたファイル(PDF/DXF)をメイン画面で管理・閲覧できます。")

st.title("📂 図面ファイル管理＆ビューアー")

# セッション状態でアップロード情報を保持
if 'uploaded_files_data' not in st.session_state:
    st.session_state.uploaded_files_data = []

# --- 1. ファイルアップロード ---
st.subheader("1. 図面ファイルのアップロード")
st.caption("「zume-n.com」などから入手した PDF または DXF ファイルを登録します。")

uploaded_file = st.file_uploader("ファイルをドラッグ＆ドロップ", type=['pdf', 'dxf'])

if uploaded_file is not None:
    # リストになければ追加
    if not any(d['name'] == uploaded_file.name for d in st.session_state.uploaded_files_data):
        file_details = {
            "name": uploaded_file.name,
            "type": uploaded_file.type,
            "data": uploaded_file.getvalue(), # 実データ
            "memo": "",
            "project": ""
        }
        st.session_state.uploaded_files_data.append(file_details)
        st.success(f"「{uploaded_file.name}」をリストに追加しました。")

st.divider()

# --- 2. ファイルリストとビューアー ---
st.subheader("2. 登録済み図面リスト")

if not st.session_state.uploaded_files_data:
    st.info("まだファイルが登録されていません。")
else:
    # タブ選択
    file_names = [f["name"] for f in st.session_state.uploaded_files_data]
    selected_tab = st.radio("表示する図面を選択:", file_names, horizontal=True)
    
    # データ取得
    current_file = next(f for f in st.session_state.uploaded_files_data if f["name"] == selected_tab)
    
    # メタデータ入力
    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        current_file["project"] = st.text_input("案件名/カテゴリ", value=current_file["project"], key=f"proj_{current_file['name']}")
    with col_meta2:
        current_file["memo"] = st.text_area("メモ", value=current_file["memo"], key=f"memo_{current_file['name']}", height=68)

    st.markdown("---")
    st.subheader(f"ビューアー: {current_file['name']}")

    # === PDF表示 ===
    if current_file["name"].lower().endswith('.pdf'):
        base64_pdf = base64.b64encode(current_file["data"]).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

    # === DXF表示 (簡易レンダリング) ===
    elif current_file["name"].lower().endswith('.dxf'):
        try:
            with st.spinner("DXFファイルをレンダリング中..."):
                doc = ezdxf.read(io.StringIO(current_file["data"].decode('utf-8', errors='ignore')))
                msp = doc.modelspace()

                fig = plt.figure(figsize=(10, 6))
                ax = fig.add_axes([0, 0, 1, 1])
                ctx = RenderContext(doc)
                out = MatplotlibBackend(ax)
                Frontend(ctx, out).draw_layout(msp, finalize=True)
                
                st.pyplot(fig)
                plt.close(fig)

        except Exception as e:
            st.error(f"表示エラー: {e}")
            st.caption("※複雑なDXFは表示できない場合があります。")

    else:
        st.warning("プレビュー非対応の形式です。")
