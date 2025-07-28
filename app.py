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
    .output-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-top: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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

# ===============================================================================
# Gemini API 関連の関数
# ===============================================================================
def setup_gemini_api(api_key: str):
    """Gemini APIを設定"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        model.generate_content("テスト") # 接続確認
        return model
    except Exception as e:
        st.error(f"API設定エラー: {str(e)}")
        st.info("💡 ヒント: 'gemini-2.0-flash-exp' が利用できない場合、'gemini-1.5-pro-latest' や 'gemini-pro' など、利用可能なモデル名をお試しください。")
        return None

def generate_content(model, prompt_func, params, content_type):
    """コンテンツ生成の共通関数"""
    try:
        prompt = prompt_func(params)
        st.session_state.last_generation_params = {'prompt_func': prompt_func, 'params': params, 'content_type': content_type}
        with st.spinner(f"{content_type}生成中..."):
            response = model.generate_content(prompt)
            result = response.text
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
        'full-auto': '完全自動で詳細なプロットを生成してください。',
        'semi-self': 'ユーザーの入力を参考に、AIが補完・改良したプロットを生成してください。',
        'self': 'ユーザーの入力を最大限活用し、最小限の補完でプロットを整理してください。'
    }
    prompt = f"""
あなたはプロの脚本家・小説家です。以下の条件で、プロクオリティの{params.get('format', '標準')}用プロットを作成してください。

【作成モード】: {mode_instructions.get(params.get('mode', 'full-auto'))}
【基本情報】
- ジャンル: {params.get('genre', '未指定')}
- タイトル: {params.get('title', '未設定')}
- 形式: {params.get('format', '標準')}
【設定詳細】
- 主人公: {params.get('protagonist', '未設定')}
- 世界観: {params.get('worldview', '未設定')}
- テーマ: {params.get('theme', '未設定')}
{f"【既存プロット参考】: {params.get('existing_plot')}" if params.get('existing_plot') else ""}

【出力形式】
1. 作品概要（2-3行）
2. 主要登場人物（3-5人）
3. 三幕構成での詳細プロット
4. 重要シーン詳細（5-7シーン）
5. テーマ・メッセージ

プロの作家が作成したような、感情的な起伏と論理的な構成を持つ完成度の高いプロットを作成してください。
"""
    return prompt

def create_script_prompt(params: Dict) -> str:
    """台本生成用プロンプト"""
    format_instructions = {
        'standard': '標準的な台本形式（ト書き + セリフ）','screenplay': '映画脚本形式（FADE IN、INT./EXT.等の記述付き）',
        'radio': 'ラジオドラマ形式（音響効果、BGM指示付き）','youtube': 'YouTube動画台本（テロップ、カット指示付き）',
        '2ch-thread': '2ch風スレッド形式（レス番号、ID付き）','manga-name': 'マンガネーム形式（コマ割り、吹き出し指示付き）'
    }
    prompt = f"""
あなたはプロの脚本家です。以下のプロットを{format_instructions.get(params.get('format', 'standard'))}の台本に変換してください。

【プロット】
{params.get('plot')}
【台本形式】: {params.get('format', 'standard')}
【出力要件】
- セリフは自然で感情豊かに
- ト書きは具体的で映像化しやすく
- 適切な間とリズムを意識
- 各シーンの目的を明確に
- キャラクターの個性を台詞に反映

プロの脚本家が書いたような、演出意図が明確で実用性の高い台本を作成してください。
"""
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

プロの校正者として、読みやすさと正確性を両立した修正を行ってください。
"""
    return prompt

def create_2ch_video_prompt(params: Dict) -> str:
    """2ch風動画用プロンプト"""
    style_settings = {
        'love-story': '恋愛関係の悩みや体験談を扱うスレッド','work-life': '職場での人間関係やトラブルを扱うスレッド',
        'school-life': '学校生活での出来事や人間関係を扱うスレッド','family': '家族関係の問題や体験談を扱うスレッド',
        'mystery': '不思議な体験や超常現象を扱うスレッド','revenge': '復讐や因果応報の体験談を扱うスレッド','success': '成功体験や逆転エピソードを扱うスレッド'
    }
    length_settings = {'short': '5-8分','standard': '10-15分','long': '20-30分'}
    prompt = f"""
あなたは人気YouTube動画の台本作家です。2ch風の読み物動画の台本を作成してください。

【設定】
- テーマ: {params.get('theme')}
- スタイル: {style_settings.get(params.get('style', 'love-story'))}
- 動画長さ: {length_settings.get(params.get('length', 'standard'))}
【台本要件】
1. スレッドタイトル（興味を引く）
2. 主人公（1）の投稿から始まる
3. 他の住民からの反応・ツッコミ
4. 展開に合わせた適切なレス
5. 盛り上がる展開とオチ
【出力形式】
\`\`\`
スレッドタイトル: 【】
1: 名無しさん＠お腹いっぱい。 [本文]
2: 名無しさん＠お腹いっぱい。 [レス内容]
（以下続き）
\`\`\`
リアルな2chの雰囲気を再現し、視聴者が最後まで飽きない展開を作成してください。
"""
    return prompt

def create_kaigai_hanno_prompt(params: Dict) -> str:
    """海外の反応動画用のプロンプトを生成する"""
    style_details = {
        'japan_praise': "日本の文化、製品、おもてなし等の素晴らしさを称賛する内容",
        'technology': "日本の先進的な技術や製品（アニメ、ゲーム、工業製品など）に対する驚きや評価",
        'moving': "日本の心温まる話や、海外での親切な日本人のエピソードなど感動的な内容",
        'anti_china': "特定の国（特に中国や韓国）と比較し、日本の優位性や正当性を主張する内容。客観的な事実を元にしつつも、日本の視聴者が共感できるような論調で。"
    }
    length_settings = {'short': '5-8分','standard': '10-15分','long': '20-30分'}

    prompt = f"""
あなたは「海外の反応」系YouTubeチャンネルのプロの台本作家です。以下の条件で、視聴者の興味を引き、エンゲージメントを高める動画台本を作成してください。

【動画のテーマ】: {params.get('theme')}
【動画のスタイル】: {style_details.get(params.get('style'))}
【動画の長さの目安】: {length_settings.get(params.get('length', 'standard'))}

【台本の構成案】
1. **オープニング (導入)**
   - 視聴者の興味を引くキャッチーな挨拶と、今回のテーマの紹介。
   - 「今回は〇〇に関する海外の反応を見ていきましょう！」のように期待感を煽る。

2. **テーマの概要説明**
   - 今回取り上げるトピック（例: 日本の新幹線、とあるアニメ作品など）を分かりやすく簡潔に説明。

3. **海外の反応 (メインパート)**
   - 複数の海外の掲示板やSNSからの引用という形で、リアルなコメントを複数紹介する。
   - ポジティブな意見、驚きの意見、ユニークな意見などをバランス良く配置する。
   - スタイルが「{style_details.get(params.get('style'))}」であることを意識したコメントを選ぶ。
   - **（重要）** コメントの間に、ナレーター（あなた）の解説やツッコミ、補足情報を加える。「これは嬉しいコメントですね」「確かに、海外の人から見るとこう見えるんですね」など。

4. **エンディング (まとめ)**
   - 全体のまとめと、ナレーターの感想。
   - 「いかがでしたか？」と視聴者に問いかける。
   - チャンネル登録や高評価、コメントを促す定型文で締めくくる。

【出力形式】
- ナレーターのセリフ、引用コメント、テロップ指示（【テロップ】: ...）を明確に分けて記述してください。

では、以上の要件に従って、最高の台本を作成してください。
"""
    return prompt

def create_sukatto_prompt(params: Dict) -> str:
    """スカッと系動画用のプロンプトを生成する"""
    style_details = {
        'revenge': "主人公が受けた理不尽な仕打ちに対し、周到な計画で見事に復讐を遂げる物語。",
        'dqn_turn': "DQNやマナーの悪い人物に対し、主人公が機転や正論で鮮やかに論破・撃退する物語。",
        'karma': "悪事を働いていた人物が、自らの行いが原因で自滅し、悲惨な末路を迎える因果応報の物語。",
        'workplace': "職場のパワハラ、セクハラ、いじめなどに対し、主人公が証拠集めや味方の協力などを得て、加害者に制裁を下す逆転劇。"
    }
    length_settings = {'short': '5-8分', 'standard': '10-15分', 'long': '20-30分'}

    prompt = f"""
あなたは「スカッと系」YouTubeチャンネルのプロの台本作家です。視聴者が思わず「スカッとした！」とコメントしたくなるような、痛快な動画台本を作成してください。

【物語のテーマ】: {params.get('theme')}
【物語のスタイル】: {style_details.get(params.get('style'))}
【動画の長さの目安】: {length_settings.get(params.get('length', 'standard'))}

【台本の構成案】
1. **プロローグ（最悪な状況）**
   - 主人公が理不尽な状況に置かれている場面から始める。
   - 悪役（加害者）の横暴で傲慢な態度を具体的に描き、視聴者の怒りを煽る。

2. **葛藤・我慢**
   - 主人公が耐え忍ぶ日々や、反撃の機会を伺う様子を描く。
   - このパートで溜めを作ることで、後の逆転劇がより際立つ。

3. **転機（反撃の狼煙）**
   - 主人公が反撃を決意する決定的な出来事。
   - 証拠を手に入れたり、強力な協力者が現れるなど。

4. **クライマックス（スカッとタイム）**
   - 主人公が悪役に対して反撃を行う、物語で最も重要な場面。
   - 悪役が自身の過ちを突きつけられ、顔面蒼白になる様子を詳細に描写する。
   - 周囲の人物（第三者）が主人公の味方をし、悪役を非難する場面も効果的。

5. **エピローグ（悪役の末路と主人公の未来）**
   - 社会的な制裁を受けたり、全てを失ったりする悪役の悲惨な末路を語る。
   - 理不尽から解放され、平穏な日常や幸せを手に入れた主人公の様子を描いて締めくくる。

【出力形式】
- 登場人物の名前（例：主人公「ユイ」、悪役「アケミ」など）を具体的に設定してください。
- ナレーター、登場人物のセリフ、ト書き（状況説明）を明確に分けて記述してください。

では、以上の王道構成に従って、最高のスカッと系台本を作成してください。
"""
    return prompt

def create_name_prompt(params: Dict) -> str:
    """ネーム作成用プロンプト"""
    format_instructions = {
        'manga': 'マンガのネーム','4koma': '4コマ漫画のネーム','storyboard': 'アニメの絵コンテ','webtoon': 'ウェブトゥーン形式'
    }
    prompt = f"""
あなたはプロの漫画家・演出家です。以下のストーリーを{format_instructions.get(params.get('format', 'manga'))}に構成してください。

【ストーリー概要】
{params.get('story')}
【ページ数】: {params.get('pages', 20)}ページ
【形式】: {params.get('format', 'manga')}

【出力形式】
各ページ/コマごとに：
- ページ/コマ番号
- コマ割り指示
- 登場人物の配置
- セリフ・モノローグ
- 動作・表情指示
- 背景・効果音指示

読者が映像として想像しやすく、感情移入できるネームを作成してください。
"""
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
        st.info("""**設定手順:**\n1. [Google AI Studio](https://aistudio.google.com/)にアクセス\n2. APIキーを生成\n3. 左サイドバーにAPIキーを入力""")
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 プロット作成", "🎭 台本作成", "🔍 誤字脱字検出", "📺 YouTube動画台本", "🎨 ネーム作成"])

    # --- タブ1: プロット作成 ---
    with tab1:
        st.header("📝 プロット作成")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("基本設定")
            genres = ['ドラマ', 'コメディ', 'アクション', 'ロマンス', 'ホラー', 'SF', 'ファンタジー', 'ミステリー', '日常系', '2ch系']
            selected_genre = st.selectbox("ジャンル", genres, key="genre_select")
            title = st.text_input("作品タイトル", placeholder="例：青春の記憶", key="title_input")
            format_type = st.selectbox("形式・長さ", ['short', 'medium', 'long', 'series', 'youtube'], format_func=lambda x: {'short': '短編', 'medium': '中編', 'long': '長編', 'series': 'シリーズ', 'youtube': 'YouTube動画'}[x], key="format_select")
        with col2:
            st.subheader("詳細設定")
            protagonist = st.text_area("主人公設定", placeholder="年齢、性格、職業、背景など...", height=100, key="protagonist_input")
            worldview = st.text_area("世界観・設定", placeholder="時代、場所、社会情勢、特殊な設定など...", height=100, key="worldview_input")
            theme = st.text_area("テーマ・メッセージ", placeholder="作品で伝えたいテーマやメッセージ...", height=100, key="theme_input")
        st.subheader("既存プロット取り込み（オプション）")
        existing_plot = st.text_area("既存プロット", placeholder="既存のプロットを貼り付けて改良・発展させることができます...", height=150, key="existing_plot_input")
        if st.button("🎬 プロット生成", type="primary", use_container_width=True, key="plot_gen_button"):
            params = {'genre': selected_genre, 'title': title, 'format': format_type, 'protagonist': protagonist, 'worldview': worldview, 'theme': theme, 'existing_plot': existing_plot, 'mode': generation_mode}
            if generate_content(st.session_state.model, create_plot_prompt, params, "プロット"):
                st.success("✅ プロット生成完了！"); st.rerun()

    # --- タブ2: 台本作成 ---
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

    # --- タブ3: 誤字脱字検出 ---
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
    
    # --- タブ4: YouTube動画台本 ---
    with tab4:
        st.header("📺 YouTube動画台本 作成")
        
        video_type = st.selectbox("作成する動画の種類を選択してください", ["スカッと系動画", "2ch風動画", "海外の反応動画"])
        
        st.markdown("---")

        if video_type == "スカッと系動画":
            st.subheader("スカッと系動画 設定")
            col1, col2 = st.columns([1, 1])
            with col1:
                video_theme_sukatto = st.text_input("物語のテーマ", placeholder="例：私をいじめていた同僚に復讐した話", key="video_theme_sukatto")
                sukatto_style = st.selectbox(
                    "物語のスタイル", ['revenge', 'dqn_turn', 'karma', 'workplace'],
                    format_func=lambda x: {'revenge': '⚡ 復讐劇', 'dqn_turn': '👊 DQN返し', 'karma': '👼 因果応報', 'workplace': '🏢 職場の逆転劇'}[x],
                    key="sukatto_style_select"
                )
            with col2:
                video_length_sukatto = st.selectbox("動画の長さ", ['short', 'standard', 'long'], format_func=lambda x: {'short': 'ショート', 'standard': '標準', 'long': '長編'}[x], key="video_length_sukatto")
            
            if st.button("🚀 スカッと系台本 生成", type="primary", use_container_width=True, key="sukatto_gen_button"):
                if not video_theme_sukatto.strip(): st.error("物語のテーマを入力してください")
                else:
                    params = {'theme': video_theme_sukatto, 'style': sukatto_style, 'length': video_length_sukatto, 'mode': generation_mode}
                    if generate_content(st.session_state.model, create_sukatto_prompt, params, "スカッと系動画台本"):
                        st.success("✅ スカッと系動画台本 生成完了！"); st.rerun()

        elif video_type == "2ch風動画":
            st.subheader("2ch風動画 設定")
            col1, col2 = st.columns([1, 1])
            with col1:
                video_theme_2ch = st.text_input("動画テーマ", placeholder="例：同僚とのトラブルと予想外の結末", key="video_theme_2ch")
                ch2_style = st.selectbox(
                    "2ch風スタイル", ['love-story', 'work-life', 'school-life', 'family', 'mystery', 'revenge', 'success'],
                    format_func=lambda x: {'love-story': '💕 恋愛系', 'work-life': '💼 社会人系', 'school-life': '🎓 学生系', 'family': '👨‍👩‍👧‍👦 家族系', 'mystery': '👻 不思議体験系', 'revenge': '⚡ 復讐・因果応報系', 'success': '🌟 成功体験系'}[x],
                    key="ch2_style_select"
                )
            with col2:
                video_length_2ch = st.selectbox("動画の長さ", ['short', 'standard', 'long'], format_func=lambda x: {'short': 'ショート', 'standard': '標準', 'long': '長編'}[x], key="video_length_2ch")
            
            if st.button("🚀 2ch風動画 台本生成", type="primary", use_container_width=True, key="2ch_gen_button"):
                if not video_theme_2ch.strip(): st.error("動画テーマを入力してください")
                else:
                    params = {'theme': video_theme_2ch, 'style': ch2_style, 'length': video_length_2ch, 'mode': generation_mode}
                    if generate_content(st.session_state.model, create_2ch_video_prompt, params, "2ch風動画台本"):
                        st.success("✅ 2ch風動画台本 生成完了！"); st.rerun()

        elif video_type == "海外の反応動画":
            st.subheader("海外の反応動画 設定")
            col1, col2 = st.columns([1, 1])
            with col1:
                video_theme_kaigai = st.text_input("動画テーマ", placeholder="例：日本の新幹線に対する海外の評価", key="video_theme_kaigai")
                kaigai_style = st.selectbox(
                    "動画のスタイル", ['japan_praise', 'technology', 'moving', 'anti_china'],
                    format_func=lambda x: {'japan_praise': '🇯🇵 日本称賛系', 'technology': '🤖 技術系', 'moving': '💖 感動系', 'anti_china': '⚔️ 嫌中・比較系'}[x],
                    key="kaigai_style_select"
                )
            with col2:
                video_length_kaigai = st.selectbox("動画の長さ", ['short', 'standard', 'long'], format_func=lambda x: {'short': 'ショート', 'standard': '標準', 'long': '長編'}[x], key="video_length_kaigai")

            if st.button("🚀 海外の反応動画 台本生成", type="primary", use_container_width=True, key="kaigai_gen_button"):
                if not video_theme_kaigai.strip(): st.error("動画テーマを入力してください")
                else:
                    params = {'theme': video_theme_kaigai, 'style': kaigai_style, 'length': video_length_kaigai, 'mode': generation_mode}
                    if generate_content(st.session_state.model, create_kaigai_hanno_prompt, params, "海外の反応動画台本"):
                        st.success("✅ 海外の反応動画台本 生成完了！"); st.rerun()

    # --- タブ5: ネーム作成 ---
    with tab5:
        st.header("🎨 マンガ・アニメネーム作成")
        story_summary = st.text_area("ストーリー概要", placeholder="ネーム化したいストーリーの概要（プロットやあらすじ）を入力...", height=200, key="story_summary_input")
        col1, col2 = st.columns([1, 1])
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
        stats_cols = st.columns(3)
        stats_cols[0].metric("文字数", len(content))
        stats_cols[1].metric("行数", content.count('\n') + 1)
        stats_cols[2].metric("段落数", len([p for p in content.split('\n\n') if p.strip()]))
        
        st.download_button(
            label="💾 テキストファイルダウンロード", data=content.encode('utf-8'),
            file_name=f"generated_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain", use_container_width=True
        )
        
        with st.expander("⭐ 生成結果の評価"):
            with st.form(key="feedback_form"):
                st.selectbox("評価", [5, 4, 3, 2, 1], format_func=lambda x: "⭐" * x)
                st.text_area("フィードバック（任意）", placeholder="改善点や良かった点など")
                if st.form_submit_button("📝 評価を送信"): st.success("✅ 評価を保存しました！ご協力ありがとうございます。")

    st.markdown("---")
    st.markdown("""<div style="text-align: center; padding: 2rem; color: #666;"><p><strong>Powered by:</strong> Google Gemini API | <strong>Version:</strong> 2.2.0</p></div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    initialize_session_state()
    main()
