import streamlit as st
import pandas as pd
import json
import os
import random
from streamlit_local_storage import LocalStorage

# -----------------------------------------------------------------------------
# ページ基本設定
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="クイズ＆論述 チャレンジ",
    page_icon="⚔️",
    layout="wide"
)

# Local Storage の初期化
local_s = LocalStorage()

# -----------------------------------------------------------------------------
# 安全な画像表示ユーティリティ関数
# -----------------------------------------------------------------------------
def safe_image_display(image_path, width=120, caption=None):
    """
    画像ファイルが存在しない場合や破損している場合、
    あるいは拡張子 (.png / .jpg / .jpeg / .JPG) が異なる場合でも
    エラーで落ちずに柔軟に表示する関数
    """
    if not image_path:
        return

    # 指定されたパスそのままで存在確認
    target_path = image_path
    if not os.path.exists(target_path):
        # 拡張子の違いを検索（.png, .jpg, .jpeg, .JPG など）
        base, _ = os.path.splitext(image_path)
        possible_exts = [".jpg", ".png", ".jpeg", ".JPG", ".PNG", ".JPEG"]
        found = False
        for ext in possible_exts:
            alt_path = base + ext
            if os.path.exists(alt_path):
                target_path = alt_path
                found = True
                break
        if not found:
            # 画像が見つからない場合はスキップ（メッセージ表示）
            st.info(f"画像が見つかりません: {os.path.basename(image_path)}")
            return

    # 画像表示の試行
    try:
        st.image(target_path, width=width, caption=caption)
    except Exception:
        st.warning(f"画像の読み込みに失敗しました: {os.path.basename(target_path)}")

# -----------------------------------------------------------------------------
# データ・マスタ定義（キャラクター・パーツなど）
# -----------------------------------------------------------------------------
CHARACTERS = {
    "勇者": {"base_image": "assets/images/hero.png", "price": 0},
    "魔法使い": {"base_image": "assets/images/wizard.png", "price": 100},
    "てんぐ": {"base_image": "assets/images/tengu.jpg", "price": 150},
}

PARTS = {
    "伝説の剣": {"image": "assets/images/sword.png", "price": 50, "slot": "weapon"},
    "魔法の杖": {"image": "assets/images/wand.png", "price": 50, "slot": "weapon"},
    "てんぐのうちわ": {"image": "assets/images/fan.jpg", "price": 80, "slot": "weapon"},
    "王冠": {"image": "assets/images/crown.png", "price": 40, "slot": "head"},
}

# -----------------------------------------------------------------------------
# セーブデータ構造と初期化
# -----------------------------------------------------------------------------
INITIAL_SAVE_DATA = {
    "coins": 0,
    "unlocked_characters": ["勇者"],
    "current_character": "勇者",
    "unlocked_parts": [],
    "equipped_parts": {}
}

def load_user_data():
    """Local Storage からユーザーデータを読み込み"""
    raw_data = local_s.getItem("study_quiz_game_save")
    if raw_data:
        try:
            data = json.loads(raw_data)
            # 不足しているキーの補完
            for k, v in INITIAL_SAVE_DATA.items():
                if k not in data:
                    data[k] = v
            return data
        except Exception:
            pass
    return INITIAL_SAVE_DATA.copy()

def save_user_data(data):
    """Local Storage へユーザーデータを保存"""
    local_s.setItem("study_quiz_game_save", json.dumps(data))

# セッション状態への保存
if "save_data" not in st.session_state:
    st.session_state.save_data = load_user_data()

# -----------------------------------------------------------------------------
# 問題データの読み込み (quiz_questions.csv)
# -----------------------------------------------------------------------------
@st.cache_data
def load_questions():
    csv_path = "quiz_questions.csv"
    if not os.path.exists(csv_path):
        return None, "quiz_questions.csv が見つかりません。ルートフォルダに配置してください。"
    
    try:
        df = pd.read_csv(csv_path)
        required_cols = {"id", "type", "question", "answer", "keywords"}
        if not required_cols.issubset(set(df.columns)):
            return None, f"CSVのヘッダーが正しくありません。必須: {required_cols}"
        return df, None
    except Exception as e:
        return None, f"CSV読み込みエラー: {e}"

df_questions, err_msg = load_questions()

# -----------------------------------------------------------------------------
# サイドバー（ステータス表示・ショップ）
# -----------------------------------------------------------------------------
save_data = st.session_state.save_data

with st.sidebar:
    st.title("🎒 マイステータス")
    st.metric("所持コイン", f"{save_data['coins']} 🪙")
    
    st.markdown("---")
    st.subheader("👤 現在のキャラクター")
    curr_char = save_data.get("current_character", "勇者")
    st.write(f"**{curr_char}**")
    
    # 現在のキャラクター画像の表示
    if curr_char in CHARACTERS:
        safe_image_display(CHARACTERS[curr_char]["base_image"], width=150)
    
    # 装備中パーツの表示
    if save_data.get("equipped_parts"):
        st.markdown("**装備パーツ:**")
        for slot, part_name in save_data["equipped_parts"].items():
            if part_name in PARTS:
                st.caption(f"- {slot}: {part_name}")
                safe_image_display(PARTS[part_name]["image"], width=60)

    st.markdown("---")
    # ガチャ / ショップの統合アコーディオン
    with st.expander("🛒 キャラクター＆装備ショップ"):
        st.markdown("### キャラクター解放")
        for char_name, char_info in CHARACTERS.items():
            if char_name in save_data["unlocked_characters"]:
                if st.button(f"{char_name} に変更", key=f"select_{char_name}"):
                    save_data["current_character"] = char_name
                    save_user_data(save_data)
                    st.rerun()
            else:
                if st.button(f"{char_name} を購入 ({char_info['price']}🪙)", key=f"buy_{char_name}"):
                    if save_data["coins"] >= char_info["price"]:
                        save_data["coins"] -= char_info["price"]
                        save_data["unlocked_characters"].append(char_name)
                        save_data["current_character"] = char_name
                        save_user_data(save_data)
                        st.success(f"{char_name} を解放しました！")
                        st.rerun()
                    else:
                        st.error("コインが足りません！")

        st.markdown("---")
        st.markdown("### 装備パーツ解放")
        for part_name, part_info in PARTS.items():
            if part_name in save_data["unlocked_parts"]:
                is_equipped = save_data["equipped_parts"].get(part_info["slot"]) == part_name
                btn_label = f"{part_name} を外す" if is_equipped else f"{part_name} を装備"
                if st.button(btn_label, key=f"equip_{part_name}"):
                    if is_equipped:
                        del save_data["equipped_parts"][part_info["slot"]]
                    else:
                        save_data["equipped_parts"][part_info["slot"]] = part_name
                    save_user_data(save_data)
                    st.rerun()
            else:
                if st.button(f"{part_name} を購入 ({part_info['price']}🪙)", key=f"buy_part_{part_name}"):
                    if save_data["coins"] >= part_info["price"]:
                        save_data["coins"] -= part_info["price"]
                        save_data["unlocked_parts"].append(part_name)
                        save_user_data(save_data)
                        st.success(f"{part_name} を獲得しました！")
                        st.rerun()
                    else:
                        st.error("コインが足りません！")

# -----------------------------------------------------------------------------
# メインコンテンツ（クイズ・論述機能）
# -----------------------------------------------------------------------------
st.title("⚔️ クイズ＆論述 チャレンジ")

if err_msg:
    st.error(err_msg)
    st.stop()

if df_questions is None or df_questions.empty:
    st.warning("問題データが空です。`quiz_questions.csv` に問題を登録してください。")
    st.stop()

# セッション状態のクイズ管理初期化
if "current_q_idx" not in st.session_state:
    st.session_state.current_q_idx = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "answered" not in st.session_state:
    st.session_state.answered = False

# 出題順序の管理
q_indices = list(range(len(df_questions)))
current_idx = st.session_state.current_q_idx % len(df_questions)
row = df_questions.iloc[current_idx]

st.subheader(f"問題 {current_idx + 1} / {len(df_questions)}")
st.markdown(f"### {row['question']}")

# 解答入力
q_type = str(row['type']).strip().lower()

if q_type == "quiz":
    user_ans = st.text_input("回答を入力してください:", key=f"q_{current_idx}")
    
    if st.button("回答する", key="btn_submit") and not st.session_state.answered:
        correct_ans = str(row['answer']).strip()
        if user_ans.strip().lower() == correct_ans.lower():
            st.success("✨ 正解！ (+10 コイン獲得)")
            save_data["coins"] += 10
            save_user_data(save_data)
        else:
            st.error(f"❌ 残念... 正解は: **{correct_ans}** です。")
        st.session_state.answered = True

elif q_type == "essay":
    user_essay = st.text_area("論述を入力してください:", key=f"essay_{current_idx}")
    
    if st.button("送信して自己採点", key="btn_essay_submit"):
        keywords = [k.strip() for k in str(row['keywords']).split(",") if k.strip()]
        st.markdown("---")
        st.markdown("#### 模範解答")
        st.info(row['answer'])
        
        st.markdown("#### 含まれるべきキーワードのチェック")
        hit_count = 0
        for kw in keywords:
            if kw in user_essay:
                st.write(f"- ✅ **{kw}** (含まれています)")
                hit_count += 1
            else:
                st.write(f"- ❌ **{kw}** (含まれていません)")
        
        earned_coins = hit_count * 5
        if earned_coins > 0:
            st.success(f"キーワード一致により **{earned_coins} コイン** 獲得！")
            save_data["coins"] += earned_coins
            save_user_data(save_data)
        st.session_state.answered = True

# 次の問題へ進むボタン
if st.session_state.answered:
    if st.button("次の問題へ ➔", key="btn_next"):
        st.session_state.current_q_idx += 1
        st.session_state.answered = False
        st.rerun()