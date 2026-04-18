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
    
    # 💡 Yudaiさんのオリジナル設定を完全復活！
    MODEL_OPTIONS = {
        "gemini-flash-latest（1日1500回・基本）": "gemini-flash-latest",
        "gemini-3.0-flash（1日20回・最新鋭！）": "gemini-3.0-flash",
        "gemini-2.5-flash（1日20回・高性能！）": "gemini-2.5-flash",
        "gemini-1.5-pro（1日50回・推論特化）": "gemini-1.5-pro"
    }
    selected_label = st.selectbox("使用するAIモデル", list(MODEL_OPTIONS.keys()), index=0)
    selected_model = MODEL_OPTIONS[selected_label]
    
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
new_audio = st.audio_input("マイクボタンを押して録音。終わったら「保存」を押してください。")

if new_audio:
    if st.button("📥 この録音をリストに保存"):
        st.session_state.audio_list.append(new_audio.getvalue())
        st.success(f"録音 {len(st.session_state.audio_list)} を保存しました！")
        st.rerun()

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
            prompt_text = f"""
あなたは19年の経験を持つベテラン理学療法士です。
送信した「複数の音声データ」をすべて聴き取り、それらの内容を統合して、指定された【文字数制限】と【条件】を厳格に守って1つのカルテ・計画書を作成してください。

【データ】
・患者ID：{patient_id}
・病名：{disease_name}

【出力形式・条件】
以下の構成と文字数制限を必ず遵守して出力してください。
※重要：出力の冒頭や末尾に挨拶や前置きは一切不要です。いきなり【電子カルテ用】の見出しから出力してください。
※重要：データ内の【PT考察】にあたる専門的な推察や、ROM測定時の【疼痛の有無】を、優先順位が高い問題点の抽出や、治療方針・対応方針に「色濃く反映」させてください。
※重要：Markdownの強調記法（アスタリスク2つ）は絶対に使用せず、強調は「【】」を使用してください。

【電子カルテ用】
・実施した評価結果を、音声メモから抽出して項目ごと（疼痛、ROM、MMTなど）に【改行】や【箇条書き（・）】を用いて、視覚的にスッキリとしたレイアウトにしてください。
・優先順位が高い問題点を３つ、改行して箇条書きで挙げます（改善が見込める、かつPT考察から導き出される視点から判断）。

【計画書用】
・疼痛について（20文字以内）
・筋力について（20文字以内）
・感覚異常について（20文字以内）
・可動域について（20文字以内。疼痛を伴う制限がある場合はその旨を記載）
・短期目標（100文字以内）
・長期目標（50文字以内）
・治療方針（120文字以内）
・治療内容（必要な治療プログラムを箇条書きで列挙、最大6行）
・参加制限に対する具体的な対応方針（200文字以内、簡潔な「です・ます調」）
・機能障害に対する具体的な対応方針（200文字以内、簡潔な「です・ます調」）

※定型文の羅列ではなく、この患者の具体的な症状と生活背景を推察した自然な専門用語で作成すること。
※【具体的な対応方針】の2項目のみ「敬体（です・ます調）」を使用してください。その際、過剰な敬語や話し言葉は厳禁です。シンプルな「〜していきます」「〜を行います」といった表現を使い、かつ文末が「ます」で連続しすぎないよう人間らしい自然なリズムで記載してください。
"""
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel(selected_model)
                
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
