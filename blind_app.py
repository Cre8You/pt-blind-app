import streamlit as st
import google.generativeai as genai

# ページ設定
st.set_page_config(page_title="理学療法評価AI（Yudai式・ブラウザ録音版）", layout="centered")

st.title("🦴 AI理学療法アシスタント")
st.write("※下の「マイク」ボタンを押し、評価内容を自由に喋って録音してください。")

# --- サイドバー（設定用） ---
with st.sidebar:
    st.header("🔑 AI設定")
    gemini_key = st.text_input("Gemini APIキーを入力", type="password")
    
    MODEL_OPTIONS = {
        "gemini-flash-latest": "gemini-flash-latest",
        "gemini-3.0-flash": "gemini-3.0-flash",
        "gemini-2.5-flash": "gemini-2.5-flash",
        "gemini-1.5-pro": "gemini-1.5-pro"
    }
    selected_label = st.selectbox("使用するAIモデル", list(MODEL_OPTIONS.keys()), index=0)
    selected_model = MODEL_OPTIONS[selected_label]

# --- メインエリア ---
st.header("📋 基本情報")
patient_id = st.text_input("患者ID", "000000")
disease_name = st.text_input("病名", "例：腰椎椎間板ヘルニア")

st.divider()

st.header("🎤 評価の直接録音")
# ブラウザ上で直接録音できるマイク部品
audio_data = st.audio_input("マイクのボタンを押して録音開始／停止")

st.divider()

# --- 実行ボタン ---
if st.button("🚀 Yudai式：カルテと計画書を作成", use_container_width=True):
    if not gemini_key:
        st.error("左のサイドバーからAPIキーを入力してください")
    elif audio_data is None:
        st.warning("音声が録音されていません")
    else:
        with st.spinner("AIが音声を聴き取り、指定された書式で作成中です...⏳"):
            # プロンプトの文章部分
            prompt_text = f"""
あなたは19年の経験を持つベテラン理学療法士です。一緒に送信した「音声データ（評価メモ）」を聴き取り、以下の指定された【文字数制限】と【条件】を厳格に守って文章を作成してください。

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
                
                # Geminiに「テキスト」と「録音した音声ファイル」を同時に渡す！
                prompt_parts = [
                    prompt_text,
                    {
                        "mime_type": "audio/wav",
                        "data": audio_data.getvalue()
                    }
                ]
                
                response = model.generate_content(prompt_parts)
                
                st.header("✨ 生成結果")
                st.text_area("結果（コピーして使用してください）", response.text, height=700)
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
