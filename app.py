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
    """コンテンツ生成の共通関数"""
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
def create_theme_generation_prompt(params: Dict) -> str:
    """テーマ生成用のプロンプト"""
    if params['generation_type'] == 'genre':
        source_text = f"【ジャンル】: {params['genre']}"
        instruction = "このジャンルに沿った、独創的で魅力的な物語や動画のテーマを考えてください。"
    else:
        source_text = f"【キーワード】: {params['keyword']}"
        instruction = "このキーワードから発想を広げ、面白そうな物語や動画のテーマを考えてください。"

    prompt = f"""
あなたは一流のクリエイティブプロデューサーです。あなたの仕事は、まだ誰も見たことがないような、視聴者の心を掴む物語のアイデアを生み出すことです。
{instruction}

{source_text}

以下の要件に従って、{params['num_ideas']}個のテーマ案を提案してください。

【出力要件】
- 各テーマは、キャッチーな「タイトル」と、2～3行の「概要」で構成してください。
- 視聴者が「面白そう！」「続きが見たい！」と思うような、好奇心を刺激する内容にしてください。
- ありきたりなアイデアではなく、少しひねりのある、独創的な切り口を重視してください。

【出力形式】
1. **タイトル**: （ここにタイトル）
   **概要**: （ここに2～3行の概要）

2. **タイトル**: （ここにタイトル）
   **概要**: （ここに2～3行の概要）

(以下、指定された数まで繰り返す)
"""
    return prompt

def create_plot_prompt(params: Dict) -> str:
    """プロット生成用プロンプト"""
    mode_instructions = {
        'full-auto': '完全自動で詳細なプロットを生成してください。','semi-self': 'ユーザーの入力を参考に、AIが補完・改良したプロットを生成してください。','self': 'ユーザーの入力を最大限活用し、最小限の補完でプロットを整理してください。'
    }
    prompt = f"""
あなたはプロの脚本家・小説家です。以下の条件でプロットを作成してください。
【作成モード】: {mode_instructions.get(params.get('mode', 'full-auto'))}
【基本情報】- ジャンル: {params.get('genre', '未指定')} - タイトル: {params.get('title', '未設定')}
【設定詳細】- 主人公: {params.get('protagonist', '未設定')} - 世界観: {params.get('worldview', '未設定')}
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

def create_youtube_prompt_base(params: Dict) -> str:
    """YouTube台本プロンプトの共通ベースを作成する関数"""
    pov_instruction = ""
    if params.get('pov_character') == '主人公':
        pov_instruction = "物語は主人公の一人称（私、俺など）で進行し、モノローグ（心の声）を多めに含めてください。"
    elif params.get('pov_character') == '悪役・敵役':
        pov_instruction = "物語は悪役の一人称（私、俺様など）で進行し、その傲慢な思考や誤算を描写してください。"
    elif params.get('pov_character') == '第三者ナレーター':
        pov_instruction = "物語を客観的な第三者の視点から、登場人物の行動や状況を冷静に説明してください。"
    else: # その他の登場人物
        pov_instruction = f"物語を「{params.get('pov_character')}」の視点から語り、その人物がどう事件に関わったかを描写してください。"

    narrative_framework = ""
    if params.get('use_advanced_settings'):
        narrative_framework = f"""
【物語の詳細な骨子】
この骨子はユーザーが設定した物語の土台です。必ずこの内容を物語に反映させてください。
- 主人公の設定: {params.get('protagonist_setting')}
- 物語の導入（起）: {params.get('story_start')}
- 物語の展開（承）: {params.get('story_development')}
- 物語の転機（転）: {params.get('story_turn')}
- 物語の結末（結）: {params.get('story_ending')}
"""

    long_story_instruction = ""
    if params.get('length') in ['long', 'super_long']:
        long_story_instruction = """
【超長文生成のための特別指示】
あなたのモデルには一度に出力できる文章量に上限があることを理解しています。その上限を最大限に活用し、可能な限り長い物語を生成するために、物語を5つの章（第一章: 発端、第二章: 展開、第三章: 転機、第四章: クライマックス、第五章: 結末）に明確に分割して構成してください。
各章ごとに、最低でも1500文字以上、可能であれば2000文字以上を執筆してください。各章では、情景描写、人物の心理描写、会話のやり取りを詳細かつ豊富に盛り込んでください。
この指示に従うことで、あなたは自身の能力を最大限に発揮し、ユーザーが求める長大で満足度の高い物語を完成させることができます。"""

    return f"""
【最重要指示】
{pov_instruction}
{narrative_framework}
{long_story_instruction}
"""

def create_2ch_video_prompt(params: Dict) -> str:
    base_prompt = create_youtube_prompt_base(params)
    style_settings = {'love-story': '恋愛','work-life': '職場','school-life': '学校','family': '家族','mystery': '不思議体験','revenge': '復讐','success': '成功体験','heartwarming': 'ほっこり・感動','shuraba': '修羅場','occult': '洒落怖・ホラー','history': '歴史・偉人語り'}
    prompt = f"""
あなたは人気YouTube動画の台本作家です。
{base_prompt}
【設定】
- 動画のテーマ: {params.get('theme')}
- スレッドの雰囲気: {style_settings.get(params.get('style'))}
【台本要件】
- 興味を引くスレッドタイトルを考える。
- 主人公「スレ主」、反応する「住民A」「住民B」などを登場させる。
- 物語に山場とオチを作る。
【出力形式】
語り手（{params.get('pov_character')}）: 「（オープニングや状況説明、心の声など）」
【テロップ】: （スレッドタイトル）
スレ主: 「（投稿内容）」
住民A: 「（レス）」
（以下、この形式を繰り返して物語を完成させる）
以上の要件を厳守し、最高の2ch風動画台本を作成してください。"""
    return prompt

def create_kaigai_hanno_prompt(params: Dict) -> str:
    base_prompt = create_youtube_prompt_base(params)
    style_details = {'praise': '日本称賛','technology': '技術・経済','moving': '感動・ほっこり','vs': '嫌中・比較','food': '食文化・料理','history': '歴史・伝統','anime': 'アニメ・漫画感想','culture_shock': '日常・カルチャーショック','social': '社会・ニュース'}
    prompt = f"""
あなたは「海外の反応」系YouTubeチャンネルのプロの台本作家です。
{base_prompt}
【設定】
- 動画のテーマ: {params.get('theme')}
- 動画のスタイル: {style_details.get(params.get('style'))}
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
    base_prompt = create_youtube_prompt_base(params)
    style_details = {'revenge': '復讐劇','dqn': 'DQN返し','karma': '因果応報','workplace': '職場の逆転劇','neighbor': 'ご近所トラブル','in_laws': '嫁姑問題','cheating': '浮気・不倫の制裁','manners': 'マナー違反への天罰','monster_parent': 'モンスターペアレント撃退','history': 'スカッと偉人伝'}
    prompt = f"""
あなたは「スカッと系」YouTubeチャンネルのプロの台本作家です。
{base_prompt}
【設定】
- 物語のテーマ: {params.get('theme')}
- 物語のスタイル: {style_details.get(params.get('style'))}
【台本の構成案】
1. プロローグ（最悪な状況）
2. 葛藤・我慢
3. 転機（反撃の狼煙）
4. クライマックス（スカッとタイム）
5. エピローグ（悪役の末路と主人公の未来）
【出力形式】
- 登場人物の名前を具体的に設定してください。
- 語り手({params.get('pov_character')})、他の登場人物のセリフ、ト書きを明確に分けて記述してください。
最高のスカッと系台本を作成してください。"""
    return prompt

def create_name_prompt(params: Dict) -> str:
    format_instructions = {'manga': 'マンガのネーム','4koma': '4コマ漫画のネーム','storyboard': 'アニメの絵コンテ','webtoon': 'ウェブトゥーン形式'}
    prompt = f"""
あなたはプロの漫画家・演出家です。以下のストーリーを{format_instructions.get(params.get('format', 'manga'))}に構成してください。
【ストーリー概要】: {params.get('story')}
【ページ数】: {params.get('pages', 20)}ページ
【形式】: {params.get('format', 'manga')}
【出力形式】
各ページ/コマごとに：- ページ/コマ番号 - コマ割り指示 - 登場人物の配置 - セリフ・モノローグ - 動作・表情指示 - 背景・効果音指示
読者が映像として想像しやすく、感情移入できるネームを作成してください。"""
    return prompt

def create_secondary_check_prompt(params: Dict) -> str:
    """推敲・二次チェック用のプロンプト"""
    check_points = {
        'plot_holes': '物語のプロット（構成）に矛盾や破綻、ご都合主義な点がないか探し、具体的な改善案を提示してください。',
        'character_consistency': '登場人物の言動や性格に一貫性があるか確認してください。矛盾している点があれば指摘し、キャラクターの魅力を高めるための提案をしてください。',
        'dialogue_polish': 'セリフが陳腐であったり、説明的すぎたりしないかチェックしてください。よりキャラクターの個性が際立ち、生き生きとした会話になるようにリライト案を提示してください。',
        'pacing_improvement': '物語のテンポは適切か確認してください。中だるみしている部分や、展開が早すぎる部分を指摘し、緩急のある魅力的な展開にするための改善案を提案してください。'
    }
    prompt = f"""
あなたは超一流の脚本家、または編集者です。
以下の【元のテキスト】を、指定された【チェック項目】に従って、プロの視点から厳しくチェックし、具体的な改善提案を出してください。

【チェック項目】
{check_points.get(params.get('check_type'))}

【元のテキスト】
---
{params.get('text_to_check')}
---

【出力形式】
1. **総評**: 全体を読んだ上での良い点と、最も改善が必要な点を簡潔に述べてください。
2. **具体的な問題点の指摘と改善案**:
   - (問題箇所1の引用) → (問題点の指摘) → (具体的な改善案やリライト例)
   - (問題箇所2の引用) → (問題点の指摘) → (具体的な改善案やリライト例)
   - (以下、問題点を複数挙げる)
3. **総合的な改善後のプロット/文章の提案**: 可能であれば、指摘事項を反映した改善後の全体の流れや、新しいシーンのアイデアなどを提案してください。

あなたの厳しい視点と的確なアドバイスで、この作品を一段上のレベルに引き上げてください。"""
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

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["💡 テーマ生成", "📝 プロット作成", "🎭 台本作成", "🔍 誤字脱字検出", "📺 YouTube動画台本", "🎨 ネーム作成", "✍️ 推敲・二次チェック"])

    with tab1:
        st.header("💡 テーマ生成＆アイデア出し")
        st.info("物語のテーマが思いつかない時に、AIがアイデア出しをお手伝いします。")

        col1, col2 = st.columns(2)
        with col1:
            generation_type = st.selectbox("生成方法を選択してください", ["ジャンルからアイデアを得る", "キーワードから発想を広げる"], key="theme_gen_type")
        with col2:
            num_ideas = st.slider("生成するアイデアの数", min_value=3, max_value=10, value=5, key="num_ideas_slider")
        
        if generation_type == "ジャンルからアイデアを得る":
            genre_options = ["スカッと系", "2ch風", "海外の反応", "恋愛", "SF", "ファンタジー", "ホラー", "ミステリー", "コメディ", "日常系"]
            selected_genre = st.selectbox("アイデアが欲しいジャンルを選択してください", genre_options, key="theme_genre_select")
            keyword_input = ""
        else: # キーワードから発想を広げる
            keyword_input = st.text_input("アイデアを広げたいキーワードを入力してください", placeholder="例：タイムマシン、最後の夏休み、AIとの共存", key="theme_keyword_input")
            selected_genre = ""
            
        if st.button("💡 アイデアを生成する", type="primary", use_container_width=True, key="theme_gen_button"):
            if generation_type == "キーワードから発想を広げる" and not keyword_input.strip():
                st.error("キーワードを入力してください。")
            else:
                params = {
                    'generation_type': 'genre' if generation_type == "ジャンルからアイデアを得る" else 'keyword',
                    'genre': selected_genre,
                    'keyword': keyword_input,
                    'num_ideas': num_ideas
                }
                if generate_content(st.session_state.model, create_theme_generation_prompt, params, "テーマ案"):
                    st.success(f"✅ テーマ案を{num_ideas}個生成しました！"); st.rerun()

    with tab2:
        st.header("📝 プロット作成")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("基本設定")
            genres = ['ドラマ', 'コメディ', 'アクション', 'ロマンス', 'ホラー', 'SF', 'ファンタジー', 'ミステリー', '日常系', '2ch系', '異世界転生', 'サイバーパンク', '歴史・時代劇']
            selected_genre = st.selectbox("ジャンル", genres, key="genre_select_plot")
            title = st.text_input("作品タイトル", placeholder="例：青春の記憶", key="title_input_plot")
        with col2:
            st.subheader("詳細設定")
            protagonist = st.text_area("主人公設定", placeholder="年齢、性格、職業、背景など...", height=100, key="protagonist_input_plot")
            worldview = st.text_area("世界観・設定", placeholder="時代、場所、社会情勢、特殊な設定など...", height=100, key="worldview_input_plot")
        st.subheader("既存プロット取り込み（オプション）")
        existing_plot = st.text_area("既存プロット", placeholder="既存のプロットを貼り付けて改良・発展させることができます...", height=150, key="existing_plot_plot")
        if st.button("🎬 プロット生成", type="primary", use_container_width=True, key="plot_gen_button"):
            params = {'genre': selected_genre, 'title': title, 'protagonist': protagonist, 'worldview': worldview, 'existing_plot': existing_plot, 'mode': generation_mode}
            if generate_content(st.session_state.model, create_plot_prompt, params, "プロット"):
                st.success("✅ プロット生成完了！"); st.rerun()

    with tab3:
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

    with tab4:
        st.header("🔍 AI誤字脱字検出")
        text_to_check = st.text_area("チェック対象テキスト", placeholder="誤字脱字をチェックしたいテキストを入力してください...", height=250, key="text_to_check_input")
        check_level = st.selectbox("チェックレベル", ['basic', 'advanced', 'professional'], format_func=lambda x: {'basic': '基本チェック', 'advanced': '高度チェック', 'professional': 'プロフェッショナル'}[x], key="check_level_select")
        if st.button("🔍 誤字脱字チェック実行", type="primary", use_container_width=True, key="proofread_button"):
            if not text_to_check.strip(): st.error("チェックするテキストを入力してください")
            else:
                params = {'text': text_to_check, 'level': check_level}
                if generate_content(st.session_state.model, create_error_check_prompt, params, "校正"):
                    st.success("✅ チェック完了！"); st.rerun()
    
    with tab5:
        st.header("📺 YouTube動画台本 作成")
        video_type = st.selectbox("作成する動画の種類を選択してください", ["スカッと系動画", "2ch風動画", "海外の反応動画"], key="video_type_select")
        
        col1, col2 = st.columns(2)
        with col1:
            if video_type == "スカッと系動画":
                style_options = {'revenge': '⚡ 復讐劇', 'dqn': '👊 DQN返し', 'karma': '👼 因果応報', 'workplace': '🏢 職場の逆転劇', 'neighbor': '🏘️ ご近所トラブル', 'in_laws': '👩‍👧‍👦 嫁姑問題', 'cheating': '💔 浮気・不倫の制裁', 'manners': '😠 マナー違反への天罰', 'monster_parent': '🦖 モンスターペアレント撃退', 'history': '⚔️ スカッと偉人伝'}
                base_prompt_func = create_sukatto_prompt
            elif video_type == "2ch風動画":
                style_options = {'love-story': '💕 恋愛系', 'work-life': '💼 社会人系', 'school-life': '🎓 学生系', 'family': '👨‍👩‍👧‍👦 家族系', 'mystery': '👻 不思議体験系', 'revenge': '⚡ 復讐系', 'success': '🌟 成功体験系', 'heartwarming': '😊 ほっこり・感動系', 'shuraba': '🔥 修羅場系', 'occult': '👽 洒落怖・ホラー系', 'history': '📜 歴史・偉人語り系'}
                base_prompt_func = create_2ch_video_prompt
            else: # 海外の反応動画
                style_options = {'praise': '🇯🇵 日本称賛系', 'technology': '🤖 技術・経済系', 'moving': '💖 感動・ほっこり系', 'vs': '⚔️ 嫌中・比較系', 'food': '🍣 食文化・料理系', 'history': '🏯 歴史・伝統系', 'anime': 'ანიメ アニメ・漫画感想系', 'culture_shock': '😮 日常・カルチャーショック系', 'social': '📰 社会・ニュース系'}
                base_prompt_func = create_kaigai_hanno_prompt
            selected_style = st.selectbox("スタイル", options=list(style_options.keys()), format_func=lambda x: style_options[x], key=f"{video_type}_style")
        with col2:
            length_options = {'super_short': '超ショート(~5分)', 'short': 'ショート(5-8分)', 'standard': '標準(10-15分)', 'long': '長編(15-20分)', 'super_long': '超長編(20分以上)'}
            selected_length = st.selectbox("動画の長さ", options=list(length_options.keys()), format_func=lambda x: length_options[x], key=f"{video_type}_length")

        video_theme = st.text_input("動画テーマ", placeholder=f"{video_type}のテーマを入力", key=f"{video_type}_theme")
        pov_character = st.selectbox("視点・語り手を選択してください",["第三者ナレーター", "主人公", "悪役・敵役", "その他の登場人物"],key="pov_select",help="物語を誰の視点で語るかを選択します。")
        
        with st.expander("📝 高度な物語設定（オプション）"):
            use_advanced = st.checkbox("高度な設定を有効にする", key="use_advanced_settings")
            protagonist_setting = st.text_input("主人公の設定", placeholder="例：気弱だが芯の強いOL、正義感あふれるフリーターなど", key="protagonist_setting_adv")
            
            start_options = {'peaceful': '平穏な日常が、ある出来事をきっかけに崩れ始める。', 'difficult': '主人公が最初から困難な状況に置かれている。', 'mysterious': '謎の出来事や人物が登場し、物語が始まる。', 'unexpected_encounter': '運命的な（あるいは最悪な）出会いから始まる。', 'prophecy': '運命的な予言やお告げを受ける。', 'letter': '謎の手紙やアイテムを受け取る。'}
            selected_start = st.selectbox("物語の導入（起）", options=list(start_options.keys()), format_func=lambda x: start_options[x], key="start_select")
            custom_start = st.text_area("（または、導入を自由記述）", key="start_custom", height=100)
            
            dev_options = {'escalation': '悪役の嫌がらせがエスカレートしていく。', 'evidence': '主人公が秘密裏に反撃の証拠を集める。', 'misunderstanding': '事態が誤解を招き、より複雑化していく。', 'ally_struggle': '味方と共に困難に立ち向かうが、苦戦する。', 'rival': '強力なライバルが出現し、主人公の前に立ちはだかる。', 'betrayal': '信頼していた人物からの予期せぬ裏切り。'}
            selected_dev = st.selectbox("物語の展開（承）", options=list(dev_options.keys()), format_func=lambda x: dev_options[x], key="dev_select")
            custom_dev = st.text_area("（または、展開を自由記述）", key="dev_custom", height=100)

            turn_options = {'ally': '強力な助っ人や味方が現れる。', 'limit': '主人公の我慢が限界に達し、覚醒する。', 'mistake': '悪役が決定的なミスを犯す。', 'truth_revealed': '隠されていた真実が明らかになる。', 'great_loss': '大切な何か（人や物）を失い、主人公が覚悟を決める。', 'forgotten_memory': '忘れていた過去の記憶が蘇る。'}
            selected_turn = st.selectbox("物語の転機（転）", options=list(turn_options.keys()), format_func=lambda x: turn_options[x], key="turn_select")
            custom_turn = st.text_area("（または、転機を自由記述）", key="turn_custom", height=100)

            end_options = {'revenge': '悪役は社会的制裁を受け、主人公は幸せになる。', 'forgiveness': '主人公は悪役を許し、新たな一歩を踏み出す。', 'unexpected': '誰も予想しなかった意外な結末を迎える。', 'bittersweet': '何かを得るが、何かを失うほろ苦い結末。', 'loop': '物語が振り出しに戻るループエンド。', 'new_journey': '事件は解決し、主人公の新たな旅が始まる（続編を示唆）。'}
            selected_end = st.selectbox("物語の結末（結）", options=list(end_options.keys()), format_func=lambda x: end_options[x], key="end_select")
            custom_end = st.text_area("（または、結末を自由記述）", key="end_custom", height=100)
        
        if st.button(f"🚀 {video_type} 台本生成", type="primary", use_container_width=True, key=f"{video_type}_gen"):
            if not video_theme.strip(): st.error("動画テーマを入力してください")
            else:
                params = {
                    'theme': video_theme, 'style': selected_style, 'length': selected_length, 
                    'pov_character': pov_character, 'mode': generation_mode,
                    'use_advanced_settings': use_advanced,
                    'protagonist_setting': protagonist_setting,
                    'story_start': custom_start if custom_start.strip() else start_options[selected_start],
                    'story_development': custom_dev if custom_dev.strip() else dev_options[selected_dev],
                    'story_turn': custom_turn if custom_turn.strip() else turn_options[selected_turn],
                    'story_ending': custom_end if custom_end.strip() else end_options[selected_end],
                }
                if generate_content(st.session_state.model, base_prompt_func, params, f"{video_type}台本"):
                    st.success(f"✅ {video_type}台本 生成完了！"); st.rerun()

    with tab6:
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

    with tab7:
        st.header("✍️ 推敲・二次チェック")
        st.info("完成した台本やプロットを貼り付けて、プロの視点から改善案を得ましょう。")
        text_to_check_secondary = st.text_area("チェックしたい文章をここに貼り付けてください", height=300, key="secondary_check_input")
        check_type = st.selectbox(
            "どの視点でチェックしますか？",
            options=['plot_holes', 'character_consistency', 'dialogue_polish', 'pacing_improvement'],
            format_func=lambda x: {'plot_holes': 'プロットの穴・矛盾チェック','character_consistency': 'キャラクターの一貫性チェック','dialogue_polish': 'セリフの洗練','pacing_improvement': '物語のテンポ改善'}[x],
            key="secondary_check_type"
        )
        if st.button("📝 二次チェックを実行", type="primary", use_container_width=True, key="secondary_check_button"):
            if not text_to_check_secondary.strip(): st.error("チェックする文章を入力してください。")
            else:
                params = {'text_to_check': text_to_check_secondary, 'check_type': check_type}
                if generate_content(st.session_state.model, create_secondary_check_prompt, params, "二次チェック結果"):
                    st.success("✅ 二次チェック完了！"); st.rerun()

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
    st.markdown("""<div style="text-align: center; padding: 2rem; color: #666;"><p><strong>Powered by:</strong> Google Gemini API | <strong>Version:</strong> 3.1.0</p></div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    initialize_session_state()
    main()
