import base64
import json
import os
import random
import time
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# 1. ページ初期設定
# ---------------------------------------------------------
st.set_page_config(page_title="助詞かるた", page_icon="🎴", layout="centered")


# ---------------------------------------------------------
# 2. 背景画像（.jpg）をCSSに適用する関数
# ---------------------------------------------------------
def set_background(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpeg;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------
# 3. デザインCSS（レイアウト位置調整＆カードサイズ）
# ---------------------------------------------------------
st.markdown(
    """
<style>
    /* 全体フォント */
    html, body, [class*="css"] {
        font-family: 'Hiragino Mincho ProN', 'Yu Mincho', serif;
    }

    /* Streamlit上部ヘッダーの透過化と余白（上部が見切れないように適切なマージンを確保） */
    header {
        background-color: transparent !important;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
        max-width: 750px !important;
    }
    
    /* スタート画面のスペース */
    .title-spacer {
        height: 120px;
    }

    /* 上部ステータス表示パネル */
    .status-container {
        display: flex;
        justify-content: space-around;
        align-items: center;
        background-color: rgba(255, 255, 255, 0.95);
        border: 2px solid #8b261d;
        border-radius: 10px;
        padding: 10px 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .status-box {
        text-align: center;
    }
    .status-label {
        font-size: 0.85rem;
        color: #555;
        font-weight: bold;
    }
    .status-value {
        font-size: 1.4rem;
        color: #8b261d;
        font-weight: bold;
    }

    /* ルール説明カード */
    .rule-card {
        background-color: rgba(255, 253, 245, 0.94);
        border: 3px solid #8b261d;
        border-radius: 12px;
        padding: 16px 20px;
        margin-top: 15px;
        margin-bottom: 15px;
        width: 100%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        text-align: center;
        color: #1a1a1a;
        box-sizing: border-box;
    }
    .rule-card h3 {
        font-size: 1.4rem;
        color: #8b261d;
        margin-bottom: 10px;
        font-weight: bold;
    }
    .rule-card p {
        font-size: 1.0rem;
        line-height: 1.7;
        margin-bottom: 6px;
    }

    /* ゲームプレイ中の読み札カード */
    .yomifuda-play {
        background-color: rgba(255, 253, 250, 0.96);
        border: 4px solid #8b261d;
        border-radius: 10px;
        padding: 14px 18px;
        margin-top: 5px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        text-align: center;
        color: #2b2b2b;
    }
    .yomifuda-title {
        font-size: 1.0rem;
        color: #8b261d;
        font-weight: bold;
        letter-spacing: 2px;
        margin-bottom: 6px;
    }
    .yomifuda-text {
        font-size: 1.8rem;
        font-weight: bold;
        line-height: 1.5;
    }
    .target-highlight {
        color: #d9381e;
        border-bottom: 3px solid #d9381e;
        padding-bottom: 2px;
    }

    /* 🎴 かるた取り札風ボタン */
    div.stButton {
        display: flex !important;
        justify-content: center !important;
    }
    div.stButton > button {
        background-color: #faf6ed !important;
        color: #111111 !important;
        border: 5px double #2c4c3b !important;
        border-radius: 10px !important;
        
        width: 160px !important;
        height: 200px !important;
        
        writing-mode: vertical-rl !important;
        text-orientation: upright !important;
        
        font-size: 2.6rem !important;
        font-weight: 900 !important;
        letter-spacing: 4px !important;
        
        box-shadow: 0px 6px 14px rgba(0, 0, 0, 0.35) !important;
        transition: all 0.15s ease-in-out !important;
        margin: 8px auto !important;
        padding: 10px 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }

    div.stButton > button:hover {
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 0px 10px 18px rgba(0, 0, 0, 0.45) !important;
        background-color: #fffdf5 !important;
        border-color: #8b261d !important;
        color: #8b261d !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 4. 進行状況（JSON）の読み書き処理
# ---------------------------------------------------------
PROGRESS_FILE = "user_progress.json"


def load_all_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_user_progress(
    user_id, current_index, score, mistakes, question_order=None
):
    data = load_all_progress()

    if question_order is None and user_id in data:
        question_order = data[user_id].get("question_order", [])

    data[user_id] = {
        "current_index": current_index,
        "score": score,
        "mistakes": mistakes,
        "question_order": question_order,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------
# 5. CSVデータ読み込み
# ---------------------------------------------------------
def load_questions(csv_file="questions.csv"):
    df = pd.read_csv(csv_file)
    questions = []
    options = ["格助詞", "接続助詞", "終助詞", "副助詞"]
    for _, row in df.iterrows():
        questions.append(
            {
                "sentence": row["sentence"],
                "target": row["target"],
                "options": options,
                "answer": row["answer"],
            }
        )
    return questions


RANK_LIST = [
    "十級",
    "九級",
    "八級",
    "七級",
    "六級",
    "五級",
    "四級",
    "三級",
    "二級",
    "一級",
    "初段",
    "二段",
    "三段",
    "四段",
    "五段",
]


def calculate_rank(score, total_questions):
    if score >= total_questions and total_questions > 0:
        return "🏆 助詞名人 🏆"
    rank_index = min(score // 20, len(RANK_LIST) - 1)
    return RANK_LIST[rank_index]


# ---------------------------------------------------------
# 6. アプリデータの初期化
# ---------------------------------------------------------
try:
    QUESTIONS = load_questions("questions.csv")
except Exception as e:
    st.error(
        f"`questions.csv` の読み込みに失敗しました。`bunpou_app` フォルダ内にファイルがあるか確認してください。\nエラー: {e}"
    )
    st.stop()

if "game_state" not in st.session_state:
    st.session_state.game_state = "start"
    st.session_state.user_id = ""
    st.session_state.score = 0
    st.session_state.mistakes = 0
    st.session_state.current_index = 0
    st.session_state.question_order = []
    st.session_state.start_time = 0


def start_new_game():
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.mistakes = 0

    order = list(range(len(QUESTIONS)))
    random.shuffle(order)

    st.session_state.question_order = order
    st.session_state.game_state = "playing"
    st.session_state.start_time = time.time()


# ---------------------------------------------------------
# 7. 画面制御
# ---------------------------------------------------------

# 【スタート画面 / 途中再開選択】
if st.session_state.game_state == "start":
    set_background("title_bg.jpg")

    st.markdown('<div class="title-spacer"></div>', unsafe_allow_html=True)

    st.markdown(
        f"""
    <div class="rule-card">
        <h3>【ルール】</h3>
        <p>問題文の<b>「強調された助詞」</b>の種類を見極め、かるたの取り札を選んでください！</p>
        <p>📚 <b>総問題数</b>: 全 {len(QUESTIONS)} 問 ｜ ⏱️ <b>制限時間</b>: 1問につき <b>10秒</b> ｜ ❌ <b>お手つき</b>: <b>2回</b>でゲームオーバー ｜ 🏅 <b>段位認定</b>: <b>20問正解ごとに昇段</b></p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    user_input = st.text_input(
        "👤 ユーザー名 または 出席番号を入力してください",
        value=st.session_state.user_id,
        placeholder="例: 2J01_tanaka",
    )

    if user_input:
        st.session_state.user_id = user_input.strip()
        all_progress = load_all_progress()

        if st.session_state.user_id in all_progress:
            saved = all_progress[st.session_state.user_id]
            st.info(
                f"🔖 **保存された進捗が見つかりました！**\n\n"
                f"- 前回通過: **第 {saved['current_index'] + 1} 問**\n"
                f"- 正解数: **{saved['score']} 枚** | お手つき: **{saved['mistakes']} / 2**\n"
                f"- 最終更新: {saved.get('updated_at', '不明')}"
            )

            col_resume, col_restart = st.columns(2)
            if col_resume.button("▶ 続きから再開する"):
                st.session_state.current_index = saved["current_index"]
                st.session_state.score = saved["score"]
                st.session_state.mistakes = saved["mistakes"]

                saved_order = saved.get("question_order")
                if saved_order and len(saved_order) == len(QUESTIONS):
                    st.session_state.question_order = saved_order
                else:
                    order = list(range(len(QUESTIONS)))
                    random.shuffle(order)
                    st.session_state.question_order = order

                st.session_state.game_state = "playing"
                st.session_state.start_time = time.time()
                st.rerun()

            if col_restart.button("🔄 最初からやり直す"):
                start_new_game()
                if st.session_state.user_id:
                    save_user_progress(
                        st.session_state.user_id,
                        0,
                        0,
                        0,
                        st.session_state.question_order,
                    )
                st.rerun()
        else:
            if st.button("🎴 はじめから開始する"):
                start_new_game()
                if st.session_state.user_id:
                    save_user_progress(
                        st.session_state.user_id,
                        0,
                        0,
                        0,
                        st.session_state.question_order,
                    )
                st.rerun()
    else:
        st.warning("⚠️ プレイを始めるにはユーザー名・IDを入力してください。")

# 【ゲームプレイ画面】
elif st.session_state.game_state == "playing":
    set_background("game_bg.jpg")

    # 全問終了または2回お手つきでゲームオーバー
    if (
        st.session_state.current_index >= len(QUESTIONS)
        or st.session_state.mistakes >= 2
    ):
        st.session_state.game_state = "game_over"
        st.rerun()

    if not st.session_state.question_order or len(
        st.session_state.question_order
    ) != len(QUESTIONS):
        order = list(range(len(QUESTIONS)))
        random.shuffle(order)
        st.session_state.question_order = order

    q_idx = st.session_state.question_order[st.session_state.current_index]
    q = QUESTIONS[q_idx]

    # タイマー計算 (1問あたり10秒)
    elapsed = time.time() - st.session_state.start_time
    time_left = max(0, int(10 - elapsed))

    # タイムオーバー判定
    if time_left <= 0:
        st.error("⏰ タイムオーバー！お手つき！")
        st.session_state.mistakes += 1
        st.session_state.current_index += 1

        if st.session_state.user_id:
            save_user_progress(
                st.session_state.user_id,
                st.session_state.current_index,
                st.session_state.score,
                st.session_state.mistakes,
                st.session_state.question_order,
            )

        st.session_state.start_time = time.time()
        time.sleep(1)
        st.rerun()

    # 上部ステータスバー表示（残り時間・獲得札数・お手つき）
    st.markdown(
        f"""
    <div class="status-container">
        <div class="status-box">
            <div class="status-label">獲得札数</div>
            <div class="status-value">{st.session_state.score} 枚</div>
        </div>
        <div class="status-box">
            <div class="status-label">お手つき</div>
            <div class="status-value">{st.session_state.mistakes} / 2</div>
        </div>
        <div class="status-box">
            <div class="status-label">残り時間</div>
            <div class="status-value">{time_left} 秒</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    sentence_html = q["sentence"].replace(
        f"**{q['target']}**",
        f"<span class='target-highlight'>{q['target']}</span>",
    )
    st.markdown(
        f"""
    <div class="yomifuda-play">
        <div class="yomifuda-title">【 第 {st.session_state.current_index + 1} 首 / 全 {len(QUESTIONS)} 首 】 (対局者: {st.session_state.user_id})</div>
        <div class="yomifuda-text">「 {sentence_html} 」</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 4枚のかるた札を2×2で配置
    col_a, col_b = st.columns(2)
    cards = [
        (col_a, "格助詞"),
        (col_b, "接続助詞"),
        (col_a, "終助詞"),
        (col_b, "副助詞"),
    ]

    for col, opt_name in cards:
        with col:
            if st.button(opt_name, key=f"karuta_{opt_name}"):
                if opt_name == q["answer"]:
                    st.success(f"🎉 お見事！ 「{opt_name}」を取った！")
                    st.session_state.score += 1
                else:
                    st.error(
                        f"💥 お手つき！ 正解は 「{q['answer']}」 でした..."
                    )
                    st.session_state.mistakes += 1

                st.session_state.current_index += 1

                if st.session_state.user_id:
                    save_user_progress(
                        st.session_state.user_id,
                        st.session_state.current_index,
                        st.session_state.score,
                        st.session_state.mistakes,
                        st.session_state.question_order,
                    )

                st.session_state.start_time = time.time()
                time.sleep(0.8)
                st.rerun()

    # 下部に「保存して中断」ボタンを配置
    st.write("")
    if st.button("💾 保存して中断", key="btn_save_exit"):
        if st.session_state.user_id:
            save_user_progress(
                st.session_state.user_id,
                st.session_state.current_index,
                st.session_state.score,
                st.session_state.mistakes,
                st.session_state.question_order,
            )
            st.success("進捗を保存しました！")
            time.sleep(1)
            st.session_state.game_state = "start"
            st.rerun()

    # タイマーをリアルタイム更新するための1秒ごとの画面再描画
    time.sleep(1)
    st.rerun()

# 【結果発表画面】
elif st.session_state.game_state == "game_over":
    set_background("title_bg.jpg")

    st.markdown('<div class="title-spacer"></div>', unsafe_allow_html=True)

    total_q = len(QUESTIONS)
    score = st.session_state.score
    rank = calculate_rank(score, total_q)

    st.markdown(
        f"""
    <div class="rule-card">
        <h2 style="color: #8b261d;">📜 大会結果 📜</h2>
        <p style="font-size: 1.1rem; color: #555;">対局者: <b>{st.session_state.user_id}</b></p>
        <p style="font-size: 1.3rem;">獲得札数: <b>{score} / {total_q} 枚</b></p>
        <p style="font-size: 1.3rem;">到達問題: <b>第 {st.session_state.current_index} 問</b></p>
        <p style="font-size: 1.3rem;">お手つき回数: <b>{st.session_state.mistakes} 回</b></p>
        <hr>
        <p style="font-size: 1.2rem; color: #555;">認定された段位</p>
        <h1 style="color: #8b261d; font-size: 3rem;">{rank}</h1>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if st.button("🎴 スタート画面に戻る"):
        st.session_state.game_state = "start"
        st.rerun()