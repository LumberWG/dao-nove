#!/usr/bin/env python3
"""
Recover paragraph formatting for Chinese novel chapters.

Handles:
1. Entire chapter on a single line (zero newlines)
2. Severely insufficient paragraph breaks (few newlines)
3. Broken titles (body text leaked into title from previous bad recovery)

Skips chapters that are already well-formatted.
"""

import re
import os
import sys
import glob

# ── Config ─────────────────────────────────────────────────

SPEECH_VERBS = (
    '说', '道', '问', '答', '喊', '叫', '嚷', '吼', '叹', '讲', '念', '骂',
    '哭', '笑', '喝', '劝', '催', '应', '回', '吩咐', '开口', '点头', '摇头',
    '补充', '解释', '打断', '告诉', '交代', '嘱',
    '喃喃', '嘀咕', '嘟囔', '叹气', '哼', '咳',
    '说了', '问道', '答道', '喊道', '叫道', '笑道', '叹道', '骂道',
    '低声', '高声', '轻声', '冷声', '淡声', '沉声',
    '的声音', '的声', '的嗓音', '的语气', '的语调', '的口气',
    '忽然说', '突然说', '又说', '只说', '便说', '才说', '接着说',
)

CHARACTER_NAMES = [
    '许若存', '沈见微', '苏缠', '灵犀', '红姑', '纪无咎', '裴先生',
    '季真', '霍斩', '许老头', '老陈', '老孙头', '阿芷', '白无瑕',
    '方主簿', '孙大掌柜', '陈婶', '老鸹', '许衡', '王主簿',
    '院长', '厨娘', '周伯', '车夫', '守卫', '里正', '灰袍人',
]

SUBJECT_PRONOUNS = ('他', '她', '它')

# Characters that strongly suggest body text start (used in title extraction)
BODY_START_CHARS = set(
    '许沈苏灵红纪季霍裴老陈周方白阿孙王院厨车守台场风人门窗外'
    '瘸铁铜金银一二三天大地远山前身空蓝灰黑影那这有没不在是听'
    '年月日时当忽就突只便却又还也才刚名册翻到第名炭矮排感矮'
)

# Min blank-line ratio to consider a file well-formatted
MIN_BLANK_RATIO = 0.15


# ── Helpers ────────────────────────────────────────────────

def split_into_sentences(text):
    """Split text at Chinese sentence-ending punctuation."""
    if not text:
        return []
    pattern = r'(?<=[。！？])(?=(?:[^"]*"[^"]*")*[^"]*$)'
    parts = re.split(pattern, text)
    return [p for p in parts if p.strip()]


def _find_quote_end(s, start=0):
    if start >= len(s) or s[start] != '"':
        return -1
    return s.find('"', start + 1)


def _get_after_quote(sentence):
    stripped = sentence.strip()
    if not stripped.startswith('"'):
        return stripped, False
    end = _find_quote_end(stripped)
    if end < 0:
        return stripped, True
    return stripped[end+1:].strip(), True


def is_speech_attribution(sentence):
    after, has_quote = _get_after_quote(sentence)
    if not after:
        return has_quote
    for verb in SPEECH_VERBS:
        if after.startswith(verb):
            return True
    return False


def is_new_dialogue(sentence):
    stripped = sentence.strip()
    if not stripped.startswith('"'):
        return False
    return not is_speech_attribution(stripped)


def _starts_with_name(sentence):
    s = sentence.strip()
    for name in sorted(CHARACTER_NAMES, key=len, reverse=True):
        if s.startswith(name) and len(s) > len(name):
            next_c = s[len(name)]
            if next_c not in ('的', '之', '与', '和', '、', '，', '。', '；',
                              '中', '上', '下', '里', '后', '前', '边', '面',
                              '身', '手', '脸', '眼', '脚', '头', '背', '腰',
                              '腕', '指', '肩', '腿', '臂', '颈', '额', '眉'):
                return True
    return False


def _prev_is_dialogue_end(sentence):
    return sentence.rstrip().endswith('。"') or \
           sentence.rstrip().endswith('？"') or \
           sentence.rstrip().endswith('！"') or \
           sentence.rstrip().endswith('……"') or \
           sentence.rstrip().endswith('——"')


def should_split_before(curr_sentence, prev_sentence, group_so_far):
    curr = curr_sentence.strip()
    prev = prev_sentence.strip()
    if not curr or not prev:
        return False

    # New dialogue
    if is_new_dialogue(curr):
        if _prev_is_dialogue_end(prev) or prev.endswith('。'):
            return True

    # After dialogue end, new subject
    if _prev_is_dialogue_end(prev) and prev.startswith('"'):
        if _starts_with_name(curr):
            return True
        if curr[0] in SUBJECT_PRONOUNS:
            return True

    # Subject shift to named character
    if _starts_with_name(curr):
        return True

    # Scene/time transitions in longer paragraphs
    if len(group_so_far) > 200:
        for pat in ('这时候', '就在这时', '突然', '忽然', '片刻后', '过了',
                     '第二天', '天亮', '天黑', '傍晚', '清晨', '中午', '夜里',
                     '远处', '不远处', '对面', '那边', '这边'):
            if curr.startswith(pat):
                return True

    # Long paragraph + pronoun subject
    if len(group_so_far) > 400:
        if curr[0] in SUBJECT_PRONOUNS:
            return True

    return False


def extract_chapter_name_from_filename(filepath):
    """Extract chapter name from filename like '新_第22章_入城.md' -> '入城'."""
    basename = os.path.basename(filepath)
    # Remove prefix and extension
    m = re.match(r'新_第\d+章_(.+)\.md$', basename)
    if m:
        return m.group(1)
    return None


def extract_title_and_body(text):
    """Extract chapter title from text where title and body are concatenated."""
    m = re.match(r'^(#\s*第\d+章\s+)(.*)$', text)
    if not m:
        return text, ''

    prefix = m.group(1)
    rest = m.group(2)

    if '\n' in rest:
        lines = rest.split('\n')
        return (prefix + lines[0]).strip(), '\n'.join(lines[1:])

    # Score each possible title length (1-10 chars)
    best_pos = min(2, len(rest) // 2)
    best_score = -1

    for pos in range(1, min(10, len(rest))):
        title_cand = rest[:pos]
        body_char = rest[pos] if pos < len(rest) else ''
        if not body_char:
            break

        score = 0
        if body_char in '，。！？、：；""''）】》」』,；':
            score -= 10
        if body_char in BODY_START_CHARS:
            score += 5
        if body_char in '，,':
            score -= 3
        if 2 <= pos <= 4:
            score += 3
        elif 5 <= pos <= 7:
            score += 1
        if any(c in title_cand for c in '。！？…'):
            score -= 10
        if '，' in title_cand or ',' in title_cand:
            score -= 8

        if score > best_score:
            best_score = score
            best_pos = pos

    title = (prefix.rstrip() + ' ' + rest[:best_pos]).strip()
    body = rest[best_pos:]
    return title, body


def fix_broken_title(text, correct_title):
    """Fix title line and remove any residual title chars from body start.

    E.g., '# 第22章 入城名册翻到...' -> '# 第22章 入城'
           '# 第40章 三选' + body '一序塔...' -> '# 第40章 三选一' + body '序塔...'
    """
    if not correct_title:
        return text

    lines = text.split('\n')
    if not lines:
        return text

    first_line = lines[0]
    m = re.match(r'^(#\s*第\d+章\s+)(.*)$', first_line)
    if not m:
        return text

    prefix = m.group(1)
    current = m.group(2)

    # Case 1: Title has extra body text appended
    if current.startswith(correct_title) and len(current) > len(correct_title):
        fixed_first = prefix.rstrip() + ' ' + correct_title
        rest = '\n'.join(lines[1:])
        return fixed_first + '\n' + rest

    # Case 2: Title is truncated (e.g., "三选" instead of "三选一")
    if correct_title.startswith(current) and len(correct_title) > len(current):
        fixed_first = prefix.rstrip() + ' ' + correct_title
        rest = '\n'.join(lines[1:])
        missing = correct_title[len(current):]
        rest_stripped = rest.lstrip('\n')
        if rest_stripped.startswith(missing):
            rest = rest_stripped[len(missing):]
        else:
            rest = rest_stripped
        return fixed_first + '\n' + rest

    # Case 3: Title is already correct but body may have residual chars
    # from a previous bad split (e.g., title="三选一" but body starts with "一")
    if current == correct_title and len(lines) > 1:
        # Check if body starts with last char of title (common residual)
        rest = '\n'.join(lines[1:])
        rest_stripped = rest.lstrip('\n')
        last_title_char = correct_title[-1]
        # Only remove if the residual char + next char don't form a valid word start
        if rest_stripped.startswith(last_title_char):
            # Be conservative: only remove if next char is clearly body text
            if len(rest_stripped) > 1:
                next_char = rest_stripped[1]
                if next_char not in '，。！？、：；""''）】》」』':
                    rest = rest_stripped[1:]
                    return first_line + '\n' + rest

    return text


def is_well_formatted(text):
    """Check if text already has good paragraph formatting.

    Requires BOTH: minimum line count AND good blank-line ratio.
    A well-formatted chapter typically has 100+ lines with ~50% blank lines.
    """
    lines = text.split('\n')
    total_lines = len(lines)

    # A chapter with fewer than 80 lines is almost certainly under-formatted
    if total_lines < 80:
        return False

    blank_count = sum(1 for l in lines if l.strip() == '')
    ratio = blank_count / total_lines if total_lines > 0 else 0
    return ratio >= MIN_BLANK_RATIO


# ── Main Recovery ──────────────────────────────────────────

def recover_paragraphs(text, correct_chapter_name=None):
    """Main function: recover paragraph formatting."""
    if not text or not text.strip():
        return text

    # Normalize
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    # Fix broken title FIRST (before any other processing)
    if correct_chapter_name:
        text = fix_broken_title(text, correct_chapter_name)

    # Quick return if already well-formatted and title didn't change
    if is_well_formatted(text):
        return text

    # ── Pass 0: Sentence-level splitting for all under-formatted files ──
    # Extract title from body, then split body into individual sentences
    title, body = extract_title_and_body(text)

    if body:
        # Split body at scene breaks first, then into sentences
        body_parts = re.split(r'(---)', body)
        body_lines = []
        for part in body_parts:
            if part == '---':
                body_lines.append('---')
            else:
                sentences = split_into_sentences(part)
                body_lines.extend(sentences)
        text = title + '\n' + '\n'.join(body_lines)
    else:
        text = title

    # ── Pass 1: Structural markers ──
    text = re.sub(r'^(#\s*第\d+章\s+[^\n]+)\n*', r'\1\n\n', text)
    text = re.sub(r'\n*---\n*', r'\n\n---\n\n', text)

    # ── Pass 2: Sentence-level paragraph grouping ──
    paragraphs = text.split('\n\n')
    recovered = []

    for para in paragraphs:
        stripped = para.strip()
        if not stripped:
            recovered.append('')
            continue
        if stripped == '---':
            recovered.append('---')
            continue
        if re.match(r'^#\s*第\d+章', stripped):
            recovered.append(stripped)
            continue

        # Split paragraph into sentences and re-group
        sentences = split_into_sentences(stripped)
        if len(sentences) <= 1:
            recovered.append(stripped)
            continue

        groups = []
        current_group = [sentences[0]]

        for i in range(1, len(sentences)):
            s = sentences[i]
            p = sentences[i-1]
            group_text = ''.join(current_group)

            if should_split_before(s, p, group_text):
                groups.append(''.join(current_group))
                current_group = [s]
            else:
                current_group.append(s)

        if current_group:
            groups.append(''.join(current_group))

        for g in groups:
            g = g.strip()
            if g:
                recovered.append(g)

    # ── Pass 3: Assemble ──
    result = '\n\n'.join(recovered)

    # ── Pass 4: Cleanup ──
    result = re.sub(r'\n{3,}', '\n\n', result)
    result = re.sub(r'^(#\s*第\d+章\s+[^\n]+)\n([^\n])', r'\1\n\n\2', result)
    result = re.sub(r'([^\n])\n---', r'\1\n\n---', result)
    result = re.sub(r'---\n([^\n])', r'---\n\n\1', result)
    result = result.strip() + '\n'

    return result


# ── CLI ────────────────────────────────────────────────────

def process_file(filepath, dry_run=False):
    """Process a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()

    chapter_name = extract_chapter_name_from_filename(filepath)
    recovered = recover_paragraphs(original, correct_chapter_name=chapter_name)

    orig_lines = original.count('\n') + 1
    new_lines = recovered.count('\n') + 1
    orig_paras = len([p for p in original.split('\n\n') if p.strip()])
    new_paras = len([p for p in recovered.split('\n\n') if p.strip()])

    if dry_run:
        print(f"\n{'='*60}")
        print(f"File: {os.path.basename(filepath)}")
        print(f"Original: {orig_lines} lines, ~{orig_paras} paras")
        print(f"Recovered: {new_lines} lines, ~{new_paras} paras")
        print(f"{'='*60}")
        print(recovered[:1000])
        print("...")
        return

    if original == recovered:
        print(f"[SKIP] {os.path.basename(filepath)}: already well-formatted")
        return

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(recovered)

    print(f"[OK] {os.path.basename(filepath)}: {orig_lines}L/{orig_paras}P -> {new_lines}L/{new_paras}P")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Recover paragraph formatting')
    parser.add_argument('files', nargs='*', help='Files to process (supports glob)')
    parser.add_argument('--dry-run', action='store_true', help='Preview only')
    parser.add_argument('--all', action='store_true', help='Process all chapters 18-65')
    parser.add_argument('--chapter', type=int, help='Process specific chapter')
    args = parser.parse_args()

    chapters_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'chapters')

    if args.chapter:
        pattern = f'新_第{args.chapter}章_*.md'
        matches = glob.glob(os.path.join(chapters_dir, pattern))
        if not matches:
            print(f"Chapter {args.chapter} not found")
            return
        process_file(matches[0], dry_run=args.dry_run)
        return

    if args.all:
        files = []
        for i in range(18, 66):
            pattern = f'新_第{i}章_*.md'
            matches = glob.glob(os.path.join(chapters_dir, pattern))
            if matches:
                files.append(matches[0])
        print(f"Found {len(files)} chapter files")
        for f in sorted(files):
            try:
                process_file(f, dry_run=args.dry_run)
            except Exception as e:
                print(f"[ERR] {os.path.basename(f)}: {e}")
        return

    if args.files:
        for pattern in args.files:
            for f in glob.glob(pattern):
                process_file(f, dry_run=args.dry_run)
        return

    parser.print_help()


if __name__ == '__main__':
    main()
