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
    # ★★★ トークン数管理用のセッション状態を追加 ★★★
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
            
            # ★★★ 生成後にトークン数を取得してセッションに保存 ★★★
            if response.usage_metadata:
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
# プロンプト生成関数群 (スタイルと長さのバリエーションを強化)
# ===============================================================================
def create_plot_prompt(params: Dict) -> str:
    """プロット生成用プロンプト"""
    mode_instructions = {
        'full-auto': '完全自動で詳細なプロットを生成。', 'semi-self': 'ユーザー入力を参考にAIが補完・改良。', 'self': 'ユーザー入力を最大限活用し最小限の補完で整理。'
    }
    prompt = f"あなたはプロの脚本家です。以下の条件でプロクオリティの{params.get('format', '標準')}用プロットを作成してください...\n（プロンプト内容は変更なし）"
    return prompt

def create_script_prompt(params: Dict) -> str:
    """台本生成用プロンプト"""
    # (この関数は変更なし)
    return "（台本作成のプロンプト内容は変更なし）"

def create_error_check_prompt(params: Dict) -> str:
    """誤字脱字チェック用プロンプト"""
    # (この関数は変更なし)
    return "（誤字脱字チェックのプロンプト内容は変更なし）"

def create_2ch_video_prompt(params: Dict) -> str:
    """2ch風動画用プロンプト（スタイルと長さを拡張）"""
    style_settings = {
        'love-story': '恋愛関係の悩みや体験談を扱うスレッド', 'work-life': '職場での人間関係やトラブルを扱うスレッド',
        'school-life': '学校生活での出来事や人間関係を扱うスレッド', 'family': '家族関係の問題や体験談を扱うスレッド',
        'mystery': '不思議な体験や超常現象を扱うスレッド', 'revenge': '復讐や因果応報の体験談を扱うスレッド',
        'success': '成功体験や逆転エピソードを扱うスレッド',
        'heartwarming': '心が温まるような、ほのぼのとした話や良い話系のスレッド',
        'shuraba': '壮絶な修羅場や、人間関係のいざこざを扱うスレッド',
        'occult': 'SFやオカルト、都市伝説などを扱う少し怖いスレッド'
    }
    length_settings = {
        'super_short': '~5分程度', 'short': '5-8分程度', 'standard': '10-15分程度', 'long': '15-20分程度', 'super_long': '20分以上'
    }
    prompt = f"""
あなたは人気YouTube動画の台本作家です。2ch風の読み物動画の台本を作成してください。
【設定】- テーマ:{params.get('theme')}- スタイル:{style_settings.get(params.get('style'))}- 動画長さ:{length_settings.get(params.get('length'))}
【台本要件】...（以下、プロンプト内容は変更なし）"""
    return prompt

def create_kaigai_hanno_prompt(params: Dict) -> str:
    """海外の反応動画用のプロンプト（スタイルと長さを拡張）"""
    style_details = {
        'japan_praise': "日本の文化、製品、おもてなし等の素晴らしさを称賛する内容", 'technology': "日本の先進的な技術や製品（アニメ、ゲーム、工業製品など）に対する驚きや評価",
        'moving': "日本の心温まる話や、海外での親切な日本人のエピソードなど感動的な内容", 'anti_china': "特定の国（特に中国や韓国）と比較し、日本の優位性や正当性を主張する内容。",
        'food': "日本の食文化（ラーメン、寿司、菓子など）や料理に対する海外の反応", 'history': "日本の歴史や伝統文化（武士、城、祭りなど）に対する反応",
        'anime_manga': "特定のアニメや漫画作品の展開やキャラクターに対する海外の熱狂的な反応"
    }
    length_settings = {
        'super_short': '~5分程度', 'short': '5-8分程度', 'standard': '10-15分程度', 'long': '15-20分程度', 'super_long': '20分以上'
    }
    prompt = f"""
あなたは「海外の反応」系YouTubeチャンネルのプロの台本作家です。以下の条件で動画台本を作成してください。
【動画のテーマ】:{params.get('theme')}
【動画のスタイル】:{style_details.get(params.get('style'))}
【動画の長さの目安】:{length_settings.get(params.get('length'))}
【台本の構成案】...（以下、プロンプト内容は変更なし）"""
    return prompt

def create_sukatto_prompt(params: Dict) -> str:
    """スカッと系動画用のプロンプト（スタイルと長さを拡張）"""
    style_details = {
        'revenge': "主人公が受けた理不尽な仕打ちに対し、周到な計画で見事に復讐を遂げる物語。", 'dqn_turn': "DQNやマナーの悪い人物に対し、主人公が機転や正論で鮮やかに論破・撃退する物語。",
        'karma': "悪事を働いていた人物が、自らの行いが原因で自滅し、悲惨な末路を迎える因果応報の物語。", 'workplace': "職場のパワハラ、セクハラ、いじめなどに対し、主人公が逆転する物語。",
        'neighbor': "騒音、ゴミ問題、噂話など、ご近所トラブルを解決する物語。", 'in_laws': "理不尽な要求をしてくる義理の家族（嫁姑など）に制裁を下す物語。",
        'cheating': "浮気や不倫をしたパートナーとその相手に、法的な手段なども使って制裁する物語。"
    }
    length_settings = {
        'super_short': '~5分程度', 'short': '5-8分程度', 'standard': '10-15分程度', 'long': '15-20分程度', 'super_long': '20分以上'
    }
    prompt = f"""
あなたは「スカッと系」YouTubeチャンネルのプロの台本作家です。以下の条件で動画台本を作成してください。
【物語のテーマ】:{params.get('theme')}
【物語のスタイル】:{style_details.get(params.get('style'))}
【動画の長さの目安】:{length_settings.get(params.get('length'))}
【台本の構成案】...（以下、プロンプト内容は変更なし）"""
    return prompt

def create_name_prompt(params: Dict) -> str:
    """ネーム作成用プロンプト"""
    # (この関数は変更なし)
    return "（ネーム作成のプロンプト内容は変更なし）"

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
        # (サイドバーのUIは変更なし)
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

    # (タブ1, 2, 3, 5 のUIは変更なし)
    
    # --- ★★★ タブ4: YouTube動画台本 (スタイルと長さを拡張) ★★★ ---
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
                    "物語のスタイル", ['revenge', 'dqn_turn', 'karma', 'workplace', 'neighbor', 'in_laws', 'cheating'],
                    format_func=lambda x: {'revenge': '⚡ 復讐劇', 'dqn_turn': '👊 DQN返し', 'karma': '👼 因果応報', 'workplace': '🏢 職場の逆転劇', 'neighbor': '🏘️ ご近所トラブル', 'in_laws': '👩‍👧‍👦 嫁姑問題', 'cheating': '💔 浮気・不倫の制裁'}[x],
                    key="sukatto_style_select"
                )
            with col2:
                video_length_sukatto = st.selectbox("動画の長さ", ['super_short', 'short', 'standard', 'long', 'super_long'], format_func=lambda x: {'super_short': '超ショート(~5分)', 'short': 'ショート(5-8分)', 'standard': '標準(10-15分)', 'long': '長編(15-20分)', 'super_long': '超長編(20分以上)'}[x], key="video_length_sukatto")
            if st.button("🚀 スカッと系台本 生成", type="primary", use_container_width=True, key="sukatto_gen_button"):
                params = {'theme': video_theme_sukatto, 'style': sukatto_style, 'length': video_length_sukatto, 'mode': generation_mode}
                if generate_content(st.session_state.model, create_sukatto_prompt, params, "スカッと系動画台本"):
                    st.success("✅ スカッと系動画台本 生成完了！"); st.rerun()

        elif video_type == "2ch風動画":
            st.subheader("2ch風動画 設定")
            col1, col2 = st.columns([1, 1])
            with col1:
                video_theme_2ch = st.text_input("動画テーマ", placeholder="例：同僚とのトラブルと予想外の結末", key="video_theme_2ch")
                ch2_style = st.selectbox(
                    "2ch風スタイル", ['love-story', 'work-life', 'school-life', 'family', 'mystery', 'revenge', 'success', 'heartwarming', 'shuraba', 'occult'],
                    format_func=lambda x: {'love-story': '💕 恋愛系', 'work-life': '💼 社会人系', 'school-life': '🎓 学生系', 'family': '👨‍👩‍👧‍👦 家族系', 'mystery': '👻 不思議体験系', 'revenge': '⚡ 復讐系', 'success': '🌟 成功体験系', 'heartwarming': '😊 ほのぼの系', 'shuraba': '🔥 修羅場系', 'occult': '👽 SF・オカルト系'}[x],
                    key="ch2_style_select"
                )
            with col2:
                video_length_2ch = st.selectbox("動画の長さ", ['super_short', 'short', 'standard', 'long', 'super_long'], format_func=lambda x: {'super_short': '超ショート(~5分)', 'short': 'ショート(5-8分)', 'standard': '標準(10-15分)', 'long': '長編(15-20分)', 'super_long': '超長編(20分以上)'}[x], key="video_length_2ch")
            if st.button("🚀 2ch風動画 台本生成", type="primary", use_container_width=True, key="2ch_gen_button"):
                params = {'theme': video_theme_2ch, 'style': ch2_style, 'length': video_length_2ch, 'mode': generation_mode}
                if generate_content(st.session_state.model, create_2ch_video_prompt, params, "2ch風動画台本"):
                    st.success("✅ 2ch風動画台本 生成完了！"); st.rerun()

        elif video_type == "海外の反応動画":
            st.subheader("海外の反応動画 設定")
            col1, col2 = st.columns([1, 1])
            with col1:
                video_theme_kaigai = st.text_input("動画テーマ", placeholder="例：日本の新幹線に対する海外の評価", key="video_theme_kaigai")
                kaigai_style = st.selectbox(
                    "動画のスタイル", ['japan_praise', 'technology', 'moving', 'anti_china', 'food', 'history', 'anime_manga'],
                    format_func=lambda x: {'japan_praise': '🇯🇵 日本称賛系', 'technology': '🤖 技術系', 'moving': '💖 感動系', 'anti_china': '⚔️ 嫌中・比較系', 'food': '🍣 食文化・料理系', 'history': '🏯 歴史・伝統系', 'anime_manga': 'ანი메 アニメ・漫画系'}[x],
                    key="kaigai_style_select"
                )
            with col2:
                video_length_kaigai = st.selectbox("動画の長さ", ['super_short', 'short', 'standard', 'long', 'super_long'], format_func=lambda x: {'super_short': '超ショート(~5分)', 'short': 'ショート(5-8分)', 'standard': '標準(10-15分)', 'long': '長編(15-20分)', 'super_long': '超長編(20分以上)'}[x], key="video_length_kaigai")
            if st.button("🚀 海外の反応動画 台本生成", type="primary", use_container_width=True, key="kaigai_gen_button"):
                params = {'theme': video_theme_kaigai, 'style': kaigai_style, 'length': video_length_kaigai, 'mode': generation_mode}
                if generate_content(st.session_state.model, create_kaigai_hanno_prompt, params, "海外の反応動画台本"):
                    st.success("✅ 海外の反応動画台本 生成完了！"); st.rerun()

    # --- 生成結果の表示エリア ---
    if st.session_state.generated_content:
        st.markdown("---")
        st.header("📄 生成結果")
        
        # (ボタンのUIは変更なし)
        
        st.info("💡 以下のボックス内をクリックし、Ctrl+A (全選択) -> Ctrl+C (コピー) で内容をコピーできます。")
        st.text_area(label="生成された内容", value=st.session_state.generated_content, height=500, key="generated_content_display")
        
        content = st.session_state.generated_content
        
        # --- ★★★ 統計情報 & トークン使用量表示 ★★★ ---
        st.subheader("📊 統計情報 & トークン使用量")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("文字数", len(content))
        col2.metric("行数", content.count('\n') + 1)
        col3.metric("段落数", len([p for p in content.split('\n\n') if p.strip()]))

        t_col1, t_col2 = st.columns(2)
        t_col1.metric("今回の使用トークン", f"{st.session_state.last_token_count:,}")
        t_col2.metric("このセッションの累計トークン", f"{st.session_state.session_token_count:,}")

        # 注意：この料金はモデルやリージョンによって異なり、将来変更される可能性があります。
        # ここではgemini-1.5-flashの料金($0.525/1Mトークン)を参考にしています。
        # gemini-2.0-flash-expの正確な料金は公式ドキュメントでご確認ください。
        price_per_million_tokens_input = 0.525 # 仮の料金（USD）
        session_cost = (st.session_state.session_token_count / 1_000_000) * price_per_million_tokens_input
        st.info(f"💰 このセッションの概算料金: 約 ${session_cost:.6f} (USD)\n\n※この料金は概算です。正確な料金はGoogle Cloudの請求をご確認ください。")
        
        st.download_button(label="💾 テキストファイルダウンロード", data=content.encode('utf-8'), file_name=f"generated_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain", use_container_width=True)
        
        with st.expander("⭐ 生成結果の評価"):
            # (評価フォームは変更なし)
            pass

    st.markdown("---")
    st.markdown("""<div style="text-align: center; padding: 2rem; color: #666;"><p><strong>Powered by:</strong> Google Gemini API | <strong>Version:</strong> 2.3.0</p></div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    initialize_session_state()
    main()
