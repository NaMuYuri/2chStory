
リアルな2chの雰囲気を再現し、視聴者が最後まで飽きない展開を作成してください。
"""
    return prompt

def create_name_prompt(params: Dict) -> str:
    """ネーム作成用プロンプト"""
    format_instructions = {
        'manga': 'マンガのネーム（コマ割り、セリフ、動作指示）',
        '4koma': '4コマ漫画のネーム（起承転結の4コマ構成）',
        'storyboard': 'アニメの絵コンテ（カット番号、カメラワーク指示）',
        'webtoon': 'ウェブトゥーン形式（縦読み、スクロール対応）'
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

# 生成関数
def generate_content(model, prompt_func, params, content_type):
    """コンテンツ生成の共通関数"""
    try:
        prompt = prompt_func(params)
        
        # パラメータを保存（再生成用）
        st.session_state.last_generation_params = {
            'prompt_func': prompt_func,
            'params': params,
            'content_type': content_type
        }
        
        with st.spinner(f"{content_type}生成中..."):
            response = model.generate_content(prompt)
            result = response.text
            
            # セッション状態更新
            st.session_state.generated_content = result
            st.session_state.generation_history.append({
                'timestamp': datetime.now().strftime("%Y/%m/%d %H:%M"),
                'type': content_type,
                'content': result
            })
            
            return result
            
    except Exception as e:
        st.error(f"生成エラー: {str(e)}")
        return None

# メイン関数
def main():
    # ヘッダー
    st.markdown("""
    <div class="main-header">
        <h1>🎬 プロ仕様 台本・プロット作成システム</h1>
        <p>Gemini 1.5 Powered | AI誤字脱字検出 | YouTube 2ch系動画対応</p>
        <div class="quality-badge">プロクオリティ生成</div>
    </div>
    """, unsafe_allow_html=True)

    # サイドバー - API設定
    with st.sidebar:
        st.header("🔧 システム設定")
        
        # API Key入力
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            value=st.session_state.api_key,
            help="Google AI StudioでAPIキーを取得してください"
        )
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            st.session_state.model = None  # モデルをリセット
        
        if api_key and not st.session_state.model:
            with st.spinner("API接続中..."):
                st.session_state.model = setup_gemini_api(api_key)
        
        if st.session_state.model:
            st.success("✅ API接続成功")
        elif api_key:
            st.error("❌ API接続失敗")
        else:
            st.warning("APIキーを入力してください")

        st.markdown("---")
        
        # 生成モード選択
        st.subheader("🎯 生成モード")
        generation_mode = st.selectbox(
            "モード選択",
            ['full-auto', 'semi-self', 'self'],
            format_func=lambda x: {
                'full-auto': '🤖 フルオート',
                'semi-self': '🤝 セミセルフ（AI）',
                'self': '✋ セルフ'
            }[x]
        )
        
        # 生成履歴
        if st.session_state.generation_history:
            st.subheader("📜 生成履歴")
            # 直近5件の履歴を表示
            for item in reversed(st.session_state.generation_history[-5:]):
                with st.expander(f"{item['timestamp']} - {item['type']}"):
                    st.text(item['content'][:200] + "..." if len(item['content']) > 200 else item['content'])

    # メインコンテンツ
    if not st.session_state.model:
        st.error("🚫 サイドバーでAPIキーを設定してください")
        st.info("""
        **設定手順:**
        1. [Google AI Studio](https://aistudio.google.com/)にアクセス
        2. APIキーを生成
        3. 左サイドバーにAPIキーを入力
        """)
        return

    # 機能選択タブ
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 プロット作成", 
        "🎭 台本作成", 
        "🔍 誤字脱字検出", 
        "📺 YouTube 2ch系", 
        "🎨 ネーム作成"
    ])

    # --- プロット作成タブ ---
    with tab1:
        st.header("📝 プロット作成")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("基本設定")
            genres = [
                'ドラマ', 'コメディ', 'アクション', 'ロマンス', 'ホラー',
                'SF', 'ファンタジー', 'ミステリー', '日常系', '2ch系'
            ]
            selected_genre = st.selectbox("ジャンル", genres)
            title = st.text_input("作品タイトル", placeholder="例：青春の記憶")
            format_type = st.selectbox(
                "形式・長さ",
                ['short', 'medium', 'long', 'series', 'youtube'],
                format_func=lambda x: {
                    'short': '短編（5-10分）',
                    'medium': '中編（15-30分）',
                    'long': '長編（45-90分）',
                    'series': 'シリーズ（複数話）',
                    'youtube': 'YouTube動画（10-20分）'
                }[x]
            )
        
        with col2:
            st.subheader("詳細設定")
            protagonist = st.text_area("主人公設定", placeholder="年齢、性格、職業、背景など...", height=100)
            worldview = st.text_area("世界観・設定", placeholder="時代、場所、社会情勢、特殊な設定など...", height=100)
            theme = st.text_area("テーマ・メッセージ", placeholder="作品で伝えたいテーマやメッセージ...", height=100)
        
        st.subheader("既存プロット取り込み（オプション）")
        existing_plot = st.text_area(
            "既存プロット",
            placeholder="既存のプロットを貼り付けて改良・発展させることができます...",
            height=150
        )
        
        if st.button("🎬 プロット生成", type="primary", use_container_width=True, key="plot_gen_button"):
            if not any([selected_genre, title, protagonist, worldview, theme, existing_plot]):
                st.warning("何らかの情報を入力すると、より精度の高いプロットが生成されます。")
            
            params = {
                'genre': selected_genre, 'title': title, 'format': format_type,
                'protagonist': protagonist, 'worldview': worldview, 'theme': theme,
                'existing_plot': existing_plot, 'mode': generation_mode
            }
            if generate_content(st.session_state.model, create_plot_prompt, params, "プロット"):
                st.success("✅ プロット生成完了！")
                st.rerun()

    # --- 台本作成タブ ---
    with tab2:
        st.header("🎭 台本作成")
        plot_from_history = ""
        if st.session_state.generation_history:
            plot_items = [item for item in st.session_state.generation_history if item['type'] == 'プロット']
            if plot_items:
                plot_from_history = plot_items[-1]['content']
        
        plot_input = st.text_area(
            "プロット入力", value=plot_from_history,
            placeholder="台本化したいプロットを入力してください...", height=250
        )
        script_format = st.selectbox(
            "台本形式",
            ['standard', 'screenplay', 'radio', 'youtube', '2ch-thread', 'manga-name'],
            format_func=lambda x: {
                'standard': '標準台本', 'screenplay': '映画脚本', 'radio': 'ラジオドラマ',
                'youtube': 'YouTube動画', '2ch-thread': '2ch風スレッド', 'manga-name': 'マンガネーム'
            }[x]
        )
        
        if st.button("🎭 台本生成", type="primary", use_container_width=True, key="script_gen_button"):
            if not plot_input.strip():
                st.error("プロットを入力してください")
            else:
                params = {'plot': plot_input, 'format': script_format, 'mode': generation_mode}
                if generate_content(st.session_state.model, create_script_prompt, params, "台本"):
                    st.success("✅ 台本生成完了！")
                    st.rerun()

    # --- 誤字脱字検出タブ ---
    with tab3:
        st.header("🔍 AI誤字脱字検出")
        text_to_check = st.text_area(
            "チェック対象テキスト",
            placeholder="誤字脱字をチェックしたいテキストを入力してください...", height=250
        )
        check_level = st.selectbox(
            "チェックレベル",
            ['basic', 'advanced', 'professional'],
            format_func=lambda x: {
                'basic': '基本チェック', 'advanced': '高度チェック', 'professional': 'プロフェッショナル'
            }[x]
        )
        
        if st.button("🔍 誤字脱字チェック実行", type="primary", use_container_width=True, key="proofread_button"):
            if not text_to_check.strip():
                st.error("チェックするテキストを入力してください")
            else:
                params = {'text': text_to_check, 'level': check_level}
                if generate_content(st.session_state.model, create_error_check_prompt, params, "校正"):
                    st.success("✅ チェック完了！")
                    st.rerun()

    # --- YouTube 2ch系タブ ---
    with tab4:
        st.header("📺 YouTube 2ch系動画作成")
        col1, col2 = st.columns([1, 1])
        with col1:
            video_theme = st.text_input("動画テーマ", placeholder="例：同僚とのトラブルと予想外の結末")
            ch2_style = st.selectbox(
                "2ch風スタイル",
                ['love-story', 'work-life', 'school-life', 'family', 'mystery', 'revenge', 'success'],
                format_func=lambda x: {
                    'love-story': '💕 恋愛系スレ', 'work-life': '💼 社会人系スレ', 'school-life': '🎓 学生系スレ',
                    'family': '👨‍👩‍👧‍👦 家族系スレ', 'mystery': '👻 不思議体験系', 'revenge': '⚡ 復讐・因果応報系',
                    'success': '🌟 成功体験系'
                }[x]
            )
        with col2:
            video_length = st.selectbox(
                "動画の長さ",
                ['short', 'standard', 'long'],
                format_func=lambda x: {
                    'short': 'ショート（5-8分）', 'standard': '標準（10-15分）', 'long': '長編（20-30分）'
                }[x]
            )
        
        if st.button("📺 2ch風動画プロット生成", type="primary", use_container_width=True, key="2ch_gen_button"):
            if not video_theme.strip():
                st.error("動画テーマを入力してください")
            else:
                params = {
                    'theme': video_theme, 'style': ch2_style,
                    'length': video_length, 'mode': generation_mode
                }
                if generate_content(st.session_state.model, create_2ch_video_prompt, params, "2ch動画"):
                    st.success("✅ 2ch風動画生成完了！")
                    st.rerun()

    # --- ネーム作成タブ ---
    with tab5:
        st.header("🎨 マンガ・アニメネーム作成")
        story_summary = st.text_area(
            "ストーリー概要",
            placeholder="ネーム化したいストーリーの概要（プロットやあらすじ）を入力...", height=200
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            page_count = st.number_input("ページ数", min_value=1, max_value=200, value=20)
        with col2:
            name_format = st.selectbox(
                "ネーム形式",
                ['manga', '4koma', 'storyboard', 'webtoon'],
                format_func=lambda x: {
                    'manga': '📚 マンガネーム', '4koma': '📄 4コマネーム',
                    'storyboard': '🎬 アニメ絵コンテ', 'webtoon': '📱 ウェブトゥーン'
                }[x]
            )
        
        if st.button("🎨 ネーム生成", type="primary", use_container_width=True, key="name_gen_button"):
            if not story_summary.strip():
                st.error("ストーリー概要を入力してください")
            else:
                params = {
                    'story': story_summary, 'pages': page_count,
                    'format': name_format, 'mode': generation_mode
                }
                if generate_content(st.session_state.model, create_name_prompt, params, "ネーム"):
                    st.success("✅ ネーム生成完了！")
                    st.rerun()

    # --- 生成結果表示 ---
    if st.session_state.generated_content:
        st.markdown("---")
        st.header("📄 生成結果")
        
        # 操作ボタン
        b_col1, b_col2, b_col3, _ = st.columns([1, 1, 1, 5])
        
        if b_col1.button("📋 コピー", help="生成結果をクリップボードにコピー"):
            pyperclip.copy(st.session_state.generated_content)
            st.success("📋 コピーしました！")

        if b_col2.button("🔄 再生成", help="同じ条件で再生成"):
            if st.session_state.last_generation_params:
                params = st.session_state.last_generation_params
                if generate_content(st.session_state.model, params['prompt_func'], params['params'], params['content_type']):
                    st.success("✅ 再生成完了！")
                    st.rerun()
            else:
                st.warning("再生成するパラメータが見つかりません")
        
        if b_col3.button("🗑️ クリア", help="生成結果をクリア"):
            st.session_state.generated_content = ""
            st.rerun()
        
        # 結果表示エリア
        st.markdown(f"""
        <div class="output-section">
            <pre style="white-space: pre-wrap; font-family: 'Courier New', monospace; line-height: 1.6; max-height: 600px; overflow-y: auto; background: white; padding: 1rem; border-radius: 5px; border: 1px solid #dee2e6;">{st.session_state.generated_content}</pre>
        </div>
        """, unsafe_allow_html=True)
        
        # 統計情報
        content = st.session_state.generated_content
        stats_cols = st.columns(3)
        stats_cols[0].metric("文字数", len(content))
        stats_cols[1].metric("行数", content.count('\n') + 1)
        stats_cols[2].metric("段落数", len([p for p in content.split('\n\n') if p.strip()]))
        
        # ダウンロード
        st.download_button(
            label="💾 テキストファイルダウンロード",
            data=content.encode('utf-8'),
            file_name=f"generated_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        # 評価機能
        with st.expander("⭐ 生成結果の評価"):
            feedback_form = st.form(key="feedback_form")
            rating = feedback_form.selectbox("評価", [5, 4, 3, 2, 1], format_func=lambda x: "⭐" * x)
            feedback_text = feedback_form.text_area("フィードバック（任意）", placeholder="改善点や良かった点など")
            
            if feedback_form.form_submit_button("📝 評価を送信"):
                # ここで評価データをDBなどに保存する処理を実装
                st.success("✅ 評価を保存しました！ご協力ありがとうございます。")

    # --- フッター ---
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #666;">
        <p><strong>Powered by:</strong> Google Gemini API | <strong>Version:</strong> 1.1.0</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    initialize_session_state()
    main()