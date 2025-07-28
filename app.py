import streamlit as st
import google.generativeai as genai
from typing import Dict
from datetime import datetime

# ===============================================================================
# ページ設定
# ===============================================================================
st.set_page_config(
    page_title="プロ仕様 台本・プロット作成システム",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================================================================
# カスタムCSS
# ===============================================================================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .quality-badge {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ===============================================================================
# セッション管理
# ===============================================================================
def initialize_session_state():
    """セッション状態を初期化"""
    if 'generated_content' not in st.session_state:
        st.session_state.generated_content = ""
    if 'generation_history' not in st.session_state:
        st.session_state.generation_history = []
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""
    if 'model' not in st.session_state:
        st.session_state.model = None
    if 'last_generation_params' not in st.session_state:
        st.session_state.last_generation_params = {}
    if 'session_token_count' not in st.session_state:
        st.session_state.session_token_count = 0
    if 'last_token_count' not in st.session_state:
        st.session_state.last_token_count = 0

# ===============================================================================
# Gemini API 関連の関数
# ===============================================================================
def setup_gemini_api(api_key: str):
    """Gemini APIを設定"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        model.generate_content("テスト")
        return model
    except Exception as e:
        st.error(f"API設定エラー: {str(e)}")
        st.info("💡 ヒント: 'gemini-2.0-flash-exp' が利用できない場合、他のモデル名をお試しください。")
        return None

def generate_content(model, prompt_func, params, content_type):
    """コンテンツ生成の共通関数（トークン数取得機能を追加）"""
    try:
        prompt = prompt_func(params)
        st.session_state.last_generation_params = {'prompt_func': prompt_func, 'params': params, 'content_type': content_type}
        
        with st.spinner(f"{content_type}生成中..."):
            response = model.generate_content(prompt)
            result = response.text
            
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                last_tokens = response.usage_metadata.total_token_count
                st.session_state.last_token_count = last_tokens
                st.session_state.session_token_count += last_tokens
            else:
                st.session_state.last_token_count = 0

            st.session_state.generated_content = result
            st.session_state.generation_history.append({'timestamp': datetime.now().strftime("%Y/%m/%d %H:%M"), 'type': content_type, 'content': result})
            return result
            
    except Exception as e:
        st.error(f"生成エラー: {str(e)}")
        return None

# ===============================================================================
# プロンプト生成関数群
# ===============================================================================
def create_plot_prompt(params: Dict) -> str:
    """プロット生成用プロンプト"""
    mode_instructions = {
        'full-auto': '完全自動で詳細なプロットを生成してください。','semi-self': 'ユーザーの入力を参考に、AIが補完・改良したプロットを生成してください。','self': 'ユーザーの入力を最大限活用し、最小限の補完でプロットを整理してください。'
    }
    prompt = f"""
あなたはプロの脚本家・小説家です。以下の条件でプロットを作成してください。
【作成モード】: {mode_instructions.get(params.get('mode', 'full-auto'))}
【基本情報】- ジャンル: {params.get('genre', '未指定')} - タイトル: {params.get('title', '未設定')} - 形式: {params.get('format', '標準')}
【設定詳細】- 主人公: {params.get('protagonist', '未設定')} - 世界観: {params.get('worldview', '未設定')} - テーマ: {params.get('theme', '未設定')}
{f"【既存プロット参考】: {params.get('existing_plot')}" if params.get('existing_plot') else ""}
【出力形式】
1. 作品概要
2. 主要登場人物
3. 三幕構成での詳細プロット
4. 重要シーン詳細
5. テーマ・メッセージ
プロの作家が作成したような、感情的な起伏と論理的な構成を持つ完成度の高いプロットを作成してください。"""
    return prompt

def create_script_prompt(params: Dict) -> str:
    """台本生成用プロンプト"""
    format_instructions = {
        'standard': '標準的な台本形式','screenplay': '映画脚本形式','radio': 'ラジオドラマ形式','youtube': 'YouTube動画台本','2ch-thread': '2ch風スレッド形式','manga-name': 'マンガネーム形式'
    }
    prompt = f"""
あなたはプロの脚本家です。以下のプロットを{format_instructions.get(params.get('format', 'standard'))}の台本に変換してください。
【プロット】
{params.get('plot')}
【台本形式】: {params.get('format', 'standard')}
【出力要件】
- セリフは自然で感情豊かに
- ト書きは具体的で映像化しやすく
- キャラクターの個性を台詞に反映
プロの脚本家が書いたような、演出意図が明確で実用性の高い台本を作成してください。"""
    return prompt

def create_error_check_prompt(params: Dict) -> str:
    """誤字脱字チェック用プロンプト"""
    level_instructions = {
        'basic': '基本的な誤字脱字、変換ミスをチェック','advanced': '文法、表現の不自然さもチェック','professional': '敬語、専門用語、文体統一まで総合チェック'
    }
    prompt = f"""
あなたはプロの校正者です。以下のテキストを{level_instructions.get(params.get('level', 'basic'))}してください。
【チェック対象テキスト】
{params.get('text')}
【チェックレベル】: {params.get('level', 'basic')}
【出力形式】
1. 修正済みテキスト
2. 修正箇所一覧（原文、修正、理由）
3. 全体的な改善提案
プロの校正者として、読みやすさと正確性を両立した修正を行ってください。"""
    return prompt

def create_2ch_video_prompt(params: Dict) -> str:
    """2ch風動画用プロンプト"""
    style_settings = {
        'love-story': '恋愛関係の悩みや体験談','work-life': '職場での人間関係やトラブル','school-life': '学校生活での出来事や人間関係','family': '家族関係の問題や体験談','mystery': '不思議な体験や超常現象','revenge': '復讐や因果応報の体験談','success': '成功体験や逆転エピソード','heartwarming': '心が温まるような良い話','shuraba': '壮絶な修羅場や人間関係のいざこざ','occult': 'SFやオカルト、都市伝説'
    }
    length_settings = {
        'super_short': '3000文字程度','short': '4000文字程度','standard': '5000文字程度','long': '6000～8000文字程度','super_long': '8000～10000文字以上'
    }
    prompt = f"""
あなたは人気YouTube動画の台本作家です。
【最重要指示】
これはナレーターが読み上げる「台本」です。2chのスレッドそのものではなく、必ず以下の【出力形式】に従って台本を作成してください。
物語は指定された「視点・語り手」から語られるように構成してください。

【設定】
- 動画のテーマ: {params.get('theme')}
- スレッドの雰囲気: {style_settings.get(params.get('style'))}
- 目標文字数: {length_settings.get(params.get('length'))}
- 視点・語り手: {params.get('pov_character')}

【台本要件】
- 興味を引くスレッドタイトルを考える。
- 主人公「スレ主」、反応する「住民A」「住民B」などを登場させる。
- 指定された「視点・語り手」からのナレーションやモノローグを効果的に入れる。
- 物語に山場とオチを作る。

【出力形式】
語り手（{params.get('pov_character')}）: 「（オープニングや状況説明、心の声など）」
【テロップ】: （スレッドタイトル）
スレ主: 「（投稿内容）」
住民A: 「（レス）」
語り手（{params.get('pov_character')}）: 「（住民の反応に対する解説や、スレ主の心の動きなど）」
スレ主: 「（返信や状況の進展）」
（以下、この形式を繰り返して物語を完成させる）

以上の要件を厳守し、最高の2ch風動画台本を作成してください。"""
    return prompt

def create_kaigai_hanno_prompt(params: Dict) -> str:
    """海外の反応動画用のプロンプト"""
    style_details = {
        'japan_praise': "日本の文化、製品、おもてなし等の素晴らしさを称賛する内容",'technology': "日本の先進的な技術や製品への驚きや評価",'moving': "日本の心温まる話や、海外での親切な日本人のエピソードなど感動的な内容",'anti_china': "特定の国と比較し、日本の優位性や正当性を主張する内容",'food': "日本の食文化（ラーメン、寿司、菓子など）や料理に対する海外の反応",'history': "日本の歴史や伝統文化（武士、城、祭りなど）に対する反応",'anime_manga': "特定のアニメや漫画作品の展開やキャラクターに対する海外の熱狂的な反応"
    }
    length_settings = {
        'super_short': '3000文字程度','short': '4000文字程度','standard': '5000文字程度','long': '6000～8000文字程度','super_long': '8000～10000文字以上'
    }
    prompt = f"""
あなたは「海外の反応」系YouTubeチャンネルのプロの台本作家です。
【設定】
- 動画のテーマ: {params.get('theme')}
- 動画のスタイル: {style_details.get(params.get('style'))}
- 目標文字数: {length_settings.get(params.get('length'))}
- 視点・語り手: {params.get('pov_character')}  (この動画では主に「第三者ナレーター」として客観的な解説をしてください)

【台本の構成案】
1. オープニング
2. テーマの概要説明
3. 海外の反応（メインパート）
4. エンディング

【出力形式】
- ナレーターのセリフ、引用コメント、テロップ指示を明確に分けて記述してください。
最高の台本を作成してください。"""
    return prompt

def create_sukatto_prompt(params: Dict) -> str:
    """スカッと系動画用のプロンプト"""
    style_details = {
        'revenge': "主人公が受けた理不尽な仕打ちに対し、見事に復讐を遂げる物語。",'dqn_turn': "DQNやマナーの悪い人物に対し、主人公が鮮やかに論破・撃退する物語。",'karma': "悪事を働いていた人物が、自らの行いが原因で自滅する因果応報の物語。",'workplace': "職場のパワハラなどに対し、主人公が逆転する物語。",'neighbor': "ご近所トラブルを解決する物語。",'in_laws': "理不尽な義理の家族に制裁を下す物語。",'cheating': "浮気や不倫をしたパートナーに制裁する物語。"
    }
    length_settings = {
        'super_short': '3000文字程度','short': '4000文字程度','standard': '5000文字程度','long': '6000～8000文字程度','super_long': '8000～10000文字以上'
    }
    prompt = f"""
あなたは「スカッと系」YouTubeチャンネルのプロの台本作家です。
【最重要指示】
物語は指定された「視点・語り手」から語られるように構成してください。
- 「主人公」視点の場合: 主人公の一人称（私、俺）で物語が進行し、モノローグ（心の声）を多めに含めてください。
- 「第三者ナレーター」視点の場合: 客観的な視点から登場人物の行動や状況を説明してください。
- 「悪役・敵役」視点の場合: 悪役の一人称（私、俺様）で物語が進行し、その傲慢な思考を描写してください。

【設定】
- 物語のテーマ: {params.get('theme')}
- 物語のスタイル: {style_details.get(params.get('style'))}
- 目標文字数: {length_settings.get(params.get('length'))}
- 視点・語り手: {params.get('pov_character')}

【台本の構成案】
1. プロローグ（最悪な状況）
2. 葛藤・我慢
3. 転機（反撃の狼煙）
4. クライマックス（スカッとタイム）
5. エピローグ（悪役の末路と主人公の未来）

【出力形式】
- 登場人物の名前（例：主人公「ユイ」、悪役「アケミ」）を具体的に設定してください。
- 語り手({params.get('pov_character')})、他の登場人物のセリフ、ト書きを明確に分けて記述してください。
最高のスカッと系台本を作成してください。"""
    return prompt

def create_name_prompt(params: Dict) -> str:
    """ネーム作成用プロンプト"""
    format_instructions = {
        'manga': 'マンガのネーム','4koma': '4コマ漫画のネーム','storyboard': 'アニメの絵コンテ','webtoon': 'ウェブトゥーン形式'
    }
    prompt = f"""
あなたはプロの漫画家・演出家です。以下のストーリーを{format_instructions.get(params.get('format', 'manga'))}に構成してください。
【ストーリー概要】: {params.get('story')}
【ページ数】: {params.get('pages', 20)}ページ
【形式】: {params.get('format', 'manga')}
【出力形式】
各ページ/コマごとに：- ページ/コマ番号 - コマ割り指示 - 登場人物の配置 - セリフ・モノローグ - 動作・表情指示 - 背景・効果音指示
読者が映像として想像しやすく、感情移入できるネームを作成してください。"""
    return prompt

# ===============================================================================
# メインアプリケーション
# ===============================================================================
def main():
    st.markdown("""
    <div class="main-header">
        <h1>🎬 プロ仕様 台本・プロット作成システム</h1>
        <p>Gemini 2.0 Powered | AI誤字脱字検出 | YouTube動画台本対応</p>
        <div class="quality-badge">プロクオリティ生成</div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("🔧 システム設定")
        api_key = st.text_input("Gemini API Key", type="password", value=st.session_state.api_key, help="Google AI StudioでAPIキーを取得してください")
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key; st.session_state.model = None
        if api_key and not st.session_state.model:
            with st.spinner("API接続中..."): st.session_state.model = setup_gemini_api(api_key)
        if st.session_state.model: st.success("✅ API接続成功")
        elif api_key: st.error("❌ API接続失敗")
        else: st.warning("APIキーを入力してください")
        st.markdown("---")
        st.subheader("🎯 生成モード")
        generation_mode = st.selectbox("モード選択", ['full-auto', 'semi-self', 'self'], format_func=lambda x: {'full-auto': '🤖 フルオート', 'semi-self': '🤝 セミセルフ（AI）', 'self': '✋ セルフ'}[x])
        if st.session_state.generation_history:
            st.subheader("📜 生成履歴")
            for item in reversed(st.session_state.generation_history[-5:]):
                with st.expander(f"{item['timestamp']} - {item['type']}"): st.text(item['content'][:200] + "...")

    if not st.session_state.model:
        st.error("🚫 サイドバーでAPIキーを設定してください")
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 プロット作成", "🎭 台本作成", "🔍 誤字脱字検出", "📺 YouTube動画台本", "🎨 ネーム作成"])

    # --- 各タブのUI ---
    with tab1:
        st.header("📝 プロット作成")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("基本設定")
            genres = ['ドラマ', 'コメディ', 'アクション', 'ロマンス', 'ホラー', 'SF', 'ファンタジー', 'ミステリー', '日常系', '2ch系']
            selected_genre = st.selectbox("ジャンル", genres, key="genre_select")
            title = st.text_input("作品タイトル", placeholder="例：青春の記憶", key="title_input")
        with col2:
            st.subheader("詳細設定")
            protagonist = st.text_area("主人公設定", placeholder="年齢、性格、職業、背景など...", height=100, key="protagonist_input")
            worldview = st.text_area("世界観・設定", placeholder="時代、場所、社会情勢、特殊な設定など...", height=100, key="worldview_input")
        st.subheader("既存プロット取り込み（オプション）")
        existing_plot = st.text_area("既存プロット", placeholder="既存のプロットを貼り付けて改良・発展させることができます...", height=150, key="existing_plot_input")
        if st.button("🎬 プロット生成", type="primary", use_container_width=True, key="plot_gen_button"):
            params = {'genre': selected_genre, 'title': title, 'format': 'standard', 'protagonist': protagonist, 'worldview': worldview, 'theme': '', 'existing_plot': existing_plot, 'mode': generation_mode}
            if generate_content(st.session_state.model, create_plot_prompt, params, "プロット"):
                st.success("✅ プロット生成完了！"); st.rerun()

    with tab2:
        st.header("🎭 台本作成")
        plot_from_history = ""
        plot_items = [item for item in st.session_state.generation_history if item['type'] == 'プロット']
        if plot_items: plot_from_history = plot_items[-1]['content']
        plot_input = st.text_area("プロット入力", value=plot_from_history, placeholder="台本化したいプロットを入力してください...", height=250, key="plot_input_for_script")
        script_format = st.selectbox("台本形式", ['standard', 'screenplay', 'radio', 'youtube', '2ch-thread', 'manga-name'], format_func=lambda x: {'standard': '標準台本', 'screenplay': '映画脚本', 'radio': 'ラジオドラマ', 'youtube': 'YouTube動画', '2ch-thread': '2ch風スレッド', 'manga-name': 'マンガネーム'}[x], key="script_format_select")
        if st.button("🎭 台本生成", type="primary", use_container_width=True, key="script_gen_button"):
            if not plot_input.strip(): st.error("プロットを入力してください")
            else:
                params = {'plot': plot_input, 'format': script_format, 'mode': generation_mode}
                if generate_content(st.session_state.model, create_script_prompt, params, "台本"):
                    st.success("✅ 台本生成完了！"); st.rerun()

    with tab3:
        st.header("🔍 AI誤字脱字検出")
        text_to_check = st.text_area("チェック対象テキスト", placeholder="誤字脱字をチェックしたいテキストを入力してください...", height=250, key="text_to_check_input")
        check_level = st.selectbox("チェックレベル", ['basic', 'advanced', 'professional'], format_func=lambda x: {'basic': '基本チェック', 'advanced': '高度チェック', 'professional': 'プロフェッショナル'}[x], key="check_level_select")
        if st.button("🔍 誤字脱字チェック実行", type="primary", use_container_width=True, key="proofread_button"):
            if not text_to_check.strip(): st.error("チェックするテキストを入力してください")
            else:
                params = {'text': text_to_check, 'level': check_level}
                if generate_content(st.session_state.model, create_error_check_prompt, params, "校正"):
                    st.success("✅ チェック完了！"); st.rerun()
    
    with tab4:
        st.header("📺 YouTube動画台本 作成")
        video_type = st.selectbox("作成する動画の種類を選択してください", ["スカッと系動画", "2ch風動画", "海外の反応動画"], key="video_type_select")
        pov_character = st.selectbox(
            "視点・語り手を選択してください",
            ["第三者ナレーター", "主人公", "悪役・敵役", "その他の登場人物"],
            key="pov_select",
            help="物語を誰の視点で語るかを選択します。"
        )
        st.markdown("---")
        
        if video_type == "スカッと系動画":
            st.subheader("スカッと系動画 設定")
            prompt_func = create_sukatto_prompt
            content_type = "スカッと系動画台本"
            style_options = {'revenge': '⚡ 復讐劇', 'dqn_turn': '👊 DQN返し', 'karma': '👼 因果応報', 'workplace': '🏢 職場の逆転劇', 'neighbor': '🏘️ ご近所トラブル', 'in_laws': '👩‍👧‍👦 嫁姑問題', 'cheating': '💔 浮気・不倫の制裁'}
        elif video_type == "2ch風動画":
            st.subheader("2ch風動画 設定")
            prompt_func = create_2ch_video_prompt
            content_type = "2ch風動画台本"
            style_options = {'love-story': '💕 恋愛系', 'work-life': '💼 社会人系', 'school-life': '🎓 学生系', 'family': '👨‍👩‍👧‍👦 家族系', 'mystery': '👻 不思議体験系', 'revenge': '⚡ 復讐系', 'success': '🌟 成功体験系', 'heartwarming': '😊 ほのぼの系', 'shuraba': '🔥 修羅場系', 'occult': '👽 SF・オカルト系'}
        else: # 海外の反応動画
            st.subheader("海外の反応動画 設定")
            prompt_func = create_kaigai_hanno_prompt
            content_type = "海外の反応動画台本"
            style_options = {'japan_praise': '🇯🇵 日本称賛系', 'technology': '🤖 技術系', 'moving': '💖 感動系', 'anti_china': '⚔️ 嫌中・比較系', 'food': '🍣 食文化・料理系', 'history': '🏯 歴史・伝統系', 'anime_manga': 'ანიメ アニメ・漫画系'}

        col1, col2 = st.columns(2)
        with col1:
            video_theme = st.text_input("動画テーマ", placeholder=f"{video_type}のテーマを入力", key=f"{video_type}_theme")
            selected_style = st.selectbox("スタイル", options=list(style_options.keys()), format_func=lambda x: style_options[x], key=f"{video_type}_style")
        with col2:
            length_options = {'super_short': '超ショート(~5分)', 'short': 'ショート(5-8分)', 'standard': '標準(10-15分)', 'long': '長編(15-20分)', 'super_long': '超長編(20分以上)'}
            selected_length = st.selectbox("動画の長さ", options=list(length_options.keys()), format_func=lambda x: length_options[x], key=f"{video_type}_length")

        if st.button(f"🚀 {video_type} 台本生成", type="primary", use_container_width=True, key=f"{video_type}_gen"):
            if not video_theme.strip(): st.error("動画テーマを入力してください")
            else:
                params = {'theme': video_theme, 'style': selected_style, 'length': selected_length, 'pov_character': pov_character, 'mode': generation_mode}
                if generate_content(st.session_state.model, prompt_func, params, content_type):
                    st.success(f"✅ {content_type} 生成完了！"); st.rerun()

    with tab5:
        st.header("🎨 マンガ・アニメネーム作成")
        story_summary = st.text_area("ストーリー概要", placeholder="ネーム化したいストーリーの概要（プロットやあらすじ）を入力...", height=200, key="story_summary_input")
        col1, col2 = st.columns(2)
        with col1: page_count = st.number_input("ページ数", min_value=1, max_value=200, value=20, key="page_count_input")
        with col2: name_format = st.selectbox("ネーム形式", ['manga', '4koma', 'storyboard', 'webtoon'], format_func=lambda x: {'manga': '📚 マンガネーム', '4koma': '📄 4コマネーム', 'storyboard': '🎬 アニメ絵コンテ', 'webtoon': '📱 ウェブトゥーン'}[x], key="name_format_select")
        if st.button("🎨 ネーム生成", type="primary", use_container_width=True, key="name_gen_button"):
            if not story_summary.strip(): st.error("ストーリー概要を入力してください")
            else:
                params = {'story': story_summary, 'pages': page_count, 'format': name_format, 'mode': generation_mode}
                if generate_content(st.session_state.model, create_name_prompt, params, "ネーム"):
                    st.success("✅ ネーム生成完了！"); st.rerun()

    # --- 生成結果の表示エリア ---
    if st.session_state.generated_content:
        st.markdown("---")
        st.header("📄 生成結果")
        
        b_col1, b_col2, _ = st.columns([1, 1, 5])
        if b_col1.button("🔄 再生成", help="同じ条件で再生成"):
            if st.session_state.last_generation_params:
                params = st.session_state.last_generation_params
                if generate_content(st.session_state.model, params['prompt_func'], params['params'], params['content_type']):
                    st.success("✅ 再生成完了！"); st.rerun()
            else:
                st.warning("再生成するパラメータが見つかりません")
        if b_col2.button("🗑️ クリア", help="生成結果をクリア"):
            st.session_state.generated_content = ""; st.rerun()
        
        st.info("💡 以下のボックス内をクリックし、Ctrl+A (全選択) -> Ctrl+C (コピー) で内容をコピーできます。")
        st.text_area(label="生成された内容", value=st.session_state.generated_content, height=500, key="generated_content_display")
        
        content = st.session_state.generated_content
        st.subheader("📊 統計情報 & トークン使用量")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("文字数", f"{len(content):,}")
        col2.metric("行数", f"{content.count('n') + 1:,}")
        col3.metric("段落数", f"{len([p for p in content.split('nn') if p.strip()]):,}")

        t_col1, t_col2 = st.columns(2)
        t_col1.metric("今回の使用トークン", f"{st.session_state.last_token_count:,}")
        t_col2.metric("このセッションの累計トークン", f"{st.session_state.session_token_count:,}")
        
        price_per_million_tokens_input = 0.525
        session_cost = (st.session_state.session_token_count / 1_000_000) * price_per_million_tokens_input
        st.info(f"💰 このセッションの概算料金: 約 ${session_cost:.6f} (USD)\n\n※この料金は概算です。正確な料金はGoogle Cloudの請求をご確認ください。")
        
        st.download_button(label="💾 テキストファイルダウンロード", data=content.encode('utf-8'), file_name=f"generated_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain", use_container_width=True)
        
        with st.expander("⭐ 生成結果の評価"):
            with st.form(key="feedback_form"):
                st.selectbox("評価", [5, 4, 3, 2, 1], format_func=lambda x: "⭐" * x)
                st.text_area("フィードバック（任意）", placeholder="改善点や良かった点など")
                if st.form_submit_button("📝 評価を送信"): st.success("✅ 評価を保存しました！ご協力ありがとうございます。")

    st.markdown("---")
    st.markdown("""<div style="text-align: center; padding: 2rem; color: #666;"><p><strong>Powered by:</strong> Google Gemini API | <strong>Version:</strong> 2.5.0</p></div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    initialize_session_state()
    main()
