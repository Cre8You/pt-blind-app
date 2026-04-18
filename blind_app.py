import streamlit as st
import google.generativeai as genai

# ページ設定
st.set_page_config(page_title="理学療法評価AI（Yudai式・小分け録音版）", layout="centered")

# セッション状態の初期化（録音データを溜めるための倉庫）
if "audio_list" not in st.session_state:
    st.session_state.audio_list = []

st.title("🦴 AI理学療法アシスタント")
st.write("※評価の区切りごとに録音してください。最大4つ（40分相当）まで溜めて統合できます。")

# --- サイドバー（設定用） ---
with st.sidebar:
    st.header("🔑 AI設定")
    gemini_key = st.text_input("Gemini APIキーを入力", type="password")
    selected_model = st.selectbox("使用するAIモデル", ["gemini-1.5-pro", "gemini-2.0-flash", "gemini-1.5-flash"], index=0)
    
    st.divider()
    if st.button("🗑️ 録音データをリセット"):
        st.session_state.audio_list = []
        st.rerun()

# --- メインエリア ---
st.header("📋 基本情報")
patient_id = st.text_input("患者ID", "000000")
disease_name = st.text_input("病名", "例：腰椎椎間板ヘルニア")

st.divider()

# --- 録音エリア ---
st.header("🎤 分割録音")
# 新しい録音を行う部品
new_audio = st.audio_input("マイクボタンを押して録音。終わったら「保存」を押してください。")

if new_audio:
    if st.button("📥 この録音をリストに保存"):
        st.session_state.audio_list.append(new_audio.getvalue())
        st.success(f"録音 {len(st.session_state.audio_list)} を保存しました！")
        # 録音部品をリセットするためにリロード
        st.rerun()

# 現在溜まっている録音の表示
if st.session_state.audio_list:
    st.write(f"現在【 {len(st.session_state.audio_list)} 個 】の録音データが溜まっています。")
    for i, audio in enumerate(st.session_state.audio_list):
        st.audio(audio, format="audio/wav")

st.divider()

# --- 実行ボタン ---
if st.button("🚀 すべての録音を統合して作成", use_container_width=True):
    if not gemini_key:
        st.error("左のサイドバーからAPIキーを入力してください")
    elif not st.session_state.audio_list:
        st.warning("録音データが1つも保存されていません")
    else:
        with st.spinner("複数の音声を解析し、1つのカルテに統合中です...⏳"):
            # プロンプト（Yudai式フォーマットはそのまま！）
            prompt_text = f"""
あなたは19年の経験を持つベテラン理学療法士です。
送信した「複数の音声データ」をすべて聴き取り、それらの内容を統合して、指定された【文字数制限】と【条件】を厳格に守って1つのカルテ・計画書を作成してください。

【データ】
・患者ID：{patient_id}
・病名：{disease_name}

【出力形式・条件】
（※以前のYudai式フォーマットの指示をここにすべて含める）
"""
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel(selected_model)
                
                # Geminiに「テキスト」と「複数の音声ファイル」をまとめて渡す！
                prompt_parts = [prompt_text]
                for audio_bytes in st.session_state.audio_list:
                    prompt_parts.append({
                        "mime_type": "audio/wav",
                        "data": audio_bytes
                    })
                
                response = model.generate_content(prompt_parts)
                
                st.header("✨ 統合生成結果")
                st.text_area("結果（コピーして使用してください）", response.text, height=700)
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
