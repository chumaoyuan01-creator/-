import os
import re
from openai import OpenAI
from genre_rules import build_genre_rules_text

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = 'https://api.deepseek.com'
MODEL_NAME = 'deepseek-flash'

client = None

# ============================================================
# 写作风格选项
# ============================================================

WRITING_STYLES = {
    '抒情': '情感饱满真挚，善用意象和细节打动人心，以情动人',
    '冷静': '克制客观，多呈现少评判，把判断留给读者，语气平稳',
    '幽默': '诙谐风趣，善用比喻、反讽和夸张，在轻松中传递深意',
    '犀利': '观点尖锐，直指要害，一针见血，不绕弯子',
    '温润': '平和从容，娓娓道来，有温度但不煽情',
    '苍凉': '沧桑厚重，带时代的悲悯与反思，有历史的纵深感和宿命感',
    '明快': '轻快明亮，节奏干净利落，读起来轻松顺畅',
}

NARRATIVE_PERSPECTIVES = {
    '第一人称': '使用「我」作为叙述者，增强代入感和真实感',
    '第三人称': '使用「他/她」作为叙述者，视角灵活，适合全景叙事',
    '全知视角': '叙述者知晓一切，可自由切换视角，适合宏大叙事',
}

LANGUAGE_STYLES = {
    '现代白话': '使用当代通行的书面语，干净流畅，符合现代阅读习惯',
    '古典文言': '遣词造句偏向文言，多用四字短语，凝练古雅，有古典韵味',
    '市井口语': '使用生活化口语，像街坊闲谈，接地气，有烟火味',
    '书面雅正': '使用规范的书面语，用词考究，庄重得体，适合正式表达',
    '网络语感': '使用当代网络语感，轻松活泼，贴近年轻人的表达习惯',
}

# ============================================================
# 约束规则定义
# ============================================================

SENSITIVE_WORDS = [
    '自杀', '自残', '毒品', '赌博', '色情', '暴力', '血腥',
    '恐怖', '极端', '仇恨', '歧视', '辱骂', '枪支', '弹药',
]

MAX_PARAGRAPH_LENGTH = 300  # 每段最大字数

# ============================================================
# 提示词构建
# ============================================================

def _get_client():
    """获取 DeepSeek 客户端"""
    global client
    if client is None:
        api_key = os.environ.get('DEEPSEEK_API_KEY', DEEPSEEK_API_KEY)
        if not api_key:
            raise ValueError('DEEPSEEK_API_KEY 未配置')
        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    return client


def _build_system_prompt(genre, style, perspective, language_style, constraints, format_type='article'):
    """构建系统提示词 - 定义 AI 的角色和规则"""
    style_desc = WRITING_STYLES.get(style, '')
    persp_desc = NARRATIVE_PERSPECTIVES.get(perspective, '')
    lang_desc = LANGUAGE_STYLES.get(language_style, '')

    genre_rules = build_genre_rules_text(genre, format_type)
    role = '小说家' if format_type == 'novel' else '写作者'
    prompt = f"""你是一位专业的中文写作大师，精通各种文体创作。请严格按照以下要求创作。

【角色设定】
你是一位经验丰富的{genre}{role}，擅长{style_desc}的写作风格。

【文体要求】
- 文体类型：{genre}
- 叙事视角：{perspective}，{persp_desc}
- 语言风格：{lang_desc}

【写作风格】
{style_desc}

【文体专属规则】
{genre_rules}

【通用约束规则】
1. 内容必须健康积极，禁止出现以下内容：{('、'.join(SENSITIVE_WORDS))}
2. 文章结构完整，有清晰的开头、发展和结尾
3. 语言流畅自然，避免生硬的过渡
4. 内容原创，不得抄袭或套用常见模板
5. 紧扣主题，自然融入关键词，不生硬堆砌
6. 段落分明，每段不超过{MAX_PARAGRAPH_LENGTH}字
7. 不要在文章中出现「以下是文章内容」等元描述
8. 直接输出文章正文，不要加标题和额外说明"""

    # 添加用户自定义约束
    if constraints:
        prompt += f"\n\n【自定义约束】\n{constraints}"

    return prompt


def _build_short_prompt(genre, topic, keyword, length):
    """构建短文生成的用户提示词"""
    length_map = {
        'short': '300-500字',
        'medium': '600-1000字',
        'long': '1200-2000字',
    }
    target = length_map.get(length, '600-1000字')

    return f"""请创作一篇{genre}。

主题：{topic}
关键词：{keyword}
目标篇幅：{target}

请开始创作："""


def _build_long_chapter_prompt(genre, topic, keyword, chapter_index, total_chapters, chapter_title, prev_ending, style, perspective, language_style, constraints, format_type='article'):
    """构建长文分章节生成的用户提示词（带入完整文体规则）"""
    style_desc = WRITING_STYLES.get(style, '')
    persp_desc = NARRATIVE_PERSPECTIVES.get(perspective, '')
    lang_desc = LANGUAGE_STYLES.get(language_style, '')
    genre_rules = build_genre_rules_text(genre, format_type)
    unit = '章' if format_type == 'novel' else '节'

    base_prompt = f"""请创作本{'小说' if format_type == 'novel' else '文章'}的第{chapter_index}{unit}（共{total_chapters}{unit}）。

【本章定位】
- 文体：{genre}
- 主题：{topic}
- 关键词：{keyword}
- 本{unit}标题：{chapter_title}
- 写作风格：{style}（{style_desc}）
- 叙事视角：{perspective}（{persp_desc}）
- 语言风格：{language_style}（{lang_desc}）

【必须严格遵守的文体专属规则】
{genre_rules}

【本章硬性要求】
1. 本章约800-1200字，紧扣主题，自然融入关键词
2. 必须严格遵守上面的文体专属规则，尤其是标题风格、开头要求、语言风格、禁用内容
3. 本章必须至少包含1处可截图传播的金句，并用加粗标记（**金句内容**）
4. 必须避免规则中列出的所有禁用词汇和写法
5. 直接输出本章正文，不加章节标题、不加任何说明"""

    if chapter_index == 1:
        base_prompt += "\n6. 作为第一章，开头必须严格遵循规则中的【开头要求】，做到抓人眼球"
    elif chapter_index == total_chapters:
        base_prompt += "\n6. 作为最后一章，需要有完整有力的结尾，留有余韵"
    else:
        base_prompt += f"\n6. 上一章结尾内容（用于自然衔接，不要重复）：{prev_ending}"

    if constraints:
        base_prompt += f"\n7. 用户自定义约束（优先级最高）：{constraints}"

    return base_prompt


def _filter_content(content):
    """内容过滤，移除敏感词"""
    filtered = content
    for word in SENSITIVE_WORDS:
        filtered = filtered.replace(word, '*' * len(word))
    return filtered


def _split_long_paragraphs(content):
    """将过长的段落拆分为较短的段落"""
    paragraphs = content.split('\n')
    result = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # 如果段落过长，按句号拆分
        if len(p) > MAX_PARAGRAPH_LENGTH:
            sentences = re.split(r'(?<=。)', p)
            current = ''
            for s in sentences:
                if len(current + s) > MAX_PARAGRAPH_LENGTH and current:
                    result.append(current)
                    current = s
                else:
                    current += s
            if current:
                result.append(current)
        else:
            result.append(p)
    return '\n\n'.join(result)


def generate_article_ai(genre, topic, keyword, length='medium',
                         style='抒情', perspective='第三人称', language_style='现代',
                         constraints='', format_type='article'):
    """使用 DeepSeek AI 生成短文章"""
    c = _get_client()

    system_prompt = _build_system_prompt(genre, style, perspective, language_style, constraints, format_type)
    user_prompt = _build_short_prompt(genre, topic, keyword, length)

    response = c.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        max_tokens=3000,
        temperature=0.8,
        stream=False,
        timeout=60,
        extra_body={"thinking": {"type": "disabled"}},
    )

    content = response.choices[0].message.content.strip()
    content = _filter_content(content)
    content = _split_long_paragraphs(content)

    return content


def generate_long_article_ai(genre, topic, keyword, target_words=10000,
                              style='抒情', perspective='第三人称', language_style='现代',
                              constraints='', format_type='article'):
    """使用 DeepSeek AI 生成长文（分章节）"""
    c = _get_client()

    total_chapters = max(3, target_words // 1000)
    print(f'[AI] Generating outline: {total_chapters} chapters for {genre}/{topic}', flush=True)

    # 生成大纲
    outline_prompt = f"""你是一位专业的中文写作大师。请为一篇关于「{topic}」的{genre}长文设计章节大纲。

要求：
- 共 {total_chapters} 章
- 每章一个标题，简洁有力，体现章节核心内容
- 章节之间有逻辑递进关系，构成完整故事线
- 只输出标题列表，每行一个

请输出大纲："""

    outline_response = c.chat.completions.create(
        model=MODEL_NAME,
        messages=[{'role': 'user', 'content': outline_prompt}],
        max_tokens=1000,
        temperature=0.7,
        stream=False,
        timeout=60,
        extra_body={"thinking": {"type": "disabled"}},
    )

    outline_text = outline_response.choices[0].message.content.strip()
    chapter_titles_raw = [line.strip() for line in outline_text.split('\n') if line.strip()]
    print(f'[AI] Outline done: {len(chapter_titles_raw)} titles', flush=True)

    while len(chapter_titles_raw) < total_chapters:
        chapter_titles_raw.append(f'{topic}第{len(chapter_titles_raw)+1}章')
    chapter_titles_raw = chapter_titles_raw[:total_chapters]

    chapters = []
    prev_ending = ''

    for idx in range(1, total_chapters + 1):
        title = chapter_titles_raw[idx - 1]
        title = re.sub(r'^[\d.第章节\s]+', '', title).strip()
        if not title:
            title = f'{topic}第{idx}章'

        chapter_title = f'第{idx}章 {title}'

        chapter_prompt = _build_long_chapter_prompt(
            genre, topic, keyword, idx, total_chapters, title, prev_ending,
            style, perspective, language_style, constraints, format_type
        )

        response = c.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {'role': 'system', 'content': _build_system_prompt(genre, style, perspective, language_style, constraints, format_type)},
                {'role': 'user', 'content': chapter_prompt},
            ],
            max_tokens=2000,
            temperature=0.8,
            stream=False,
            timeout=60,
            extra_body={"thinking": {"type": "disabled"}},
        )

        content = response.choices[0].message.content.strip()
        content = _filter_content(content)
        content = _split_long_paragraphs(content)

        word_count = len(content.replace('\n', '').replace(' ', ''))
        prev_ending = content[-100:] if len(content) > 100 else content

        chapters.append({
            'chapter_index': idx,
            'chapter_title': chapter_title,
            'content': content,
            'word_count': word_count,
        })

    return chapters


def generate_outline_ai(genre, topic, keyword, target_words=10000,
                              style='抒情', perspective='第三人称', language_style='现代',
                              constraints='', format_type='article'):
    """生成大纲（章节标题列表）"""
    c = _get_client()
    total_chapters = max(3, target_words // 1000)

    system_prompt = _build_system_prompt(genre, style, perspective, language_style, constraints, format_type)
    outline_prompt = f"""请为一篇关于「{topic}」的{genre}长文设计章节大纲。

要求：
- 共 {total_chapters} 章
- 每章一个标题，简洁有力，体现章节核心内容
- 章节之间有逻辑递进关系，构成完整故事线
- 只输出标题列表，每行一个，格式：章节标题

请输出大纲："""

    response = c.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': outline_prompt},
        ],
        max_tokens=2000,
        temperature=0.7,
        stream=False,
        timeout=60,
        extra_body={"thinking": {"type": "disabled"}},
    )

    outline_text = response.choices[0].message.content.strip()
    chapter_titles = [line.strip() for line in outline_text.split('\n') if line.strip()]

    while len(chapter_titles) < total_chapters:
        chapter_titles.append(f'{topic}第{len(chapter_titles)+1}章')
    chapter_titles = chapter_titles[:total_chapters]

    return [{'chapter_index': i + 1, 'chapter_title': re.sub(r'^[\d.第章节\s]+', '', t).strip() or f'{topic}第{i+1}章'} for i, t in enumerate(chapter_titles)]


def generate_single_chapter_ai(genre, topic, keyword, chapter_index, total_chapters,
                               chapter_title, prev_ending='',
                               style='抒情', perspective='第三人称', language_style='现代',
                               constraints='', format_type='article'):
    """生成单个章节"""
    c = _get_client()

    system_prompt = _build_system_prompt(genre, style, perspective, language_style, constraints, format_type)
    chapter_prompt = _build_long_chapter_prompt(
        genre, topic, keyword, chapter_index, total_chapters, chapter_title, prev_ending,
        style, perspective, language_style, constraints, format_type
    )

    response = c.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': chapter_prompt},
        ],
        max_tokens=2000,
        temperature=0.8,
        stream=False,
        timeout=60,
        extra_body={"thinking": {"type": "disabled"}},
    )

    content = response.choices[0].message.content.strip()
    content = _filter_content(content)
    content = _split_long_paragraphs(content)

    return content


def test_connection():
    """测试 DeepSeek API 连接"""
    try:
        c = _get_client()
        response = c.chat.completions.create(
            model=MODEL_NAME,
            messages=[{'role': 'user', 'content': '请回复：连接成功'}],
            max_tokens=20,
            temperature=0,
            stream=False,
            timeout=60,
            extra_body={"thinking": {"type": "disabled"}},
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f'连接失败: {str(e)}'
