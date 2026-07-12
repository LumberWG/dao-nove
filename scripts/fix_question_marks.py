import re, sys, glob, os

qwords = ['什么','谁','哪儿','哪里','怎么','为什么','如何','多少','几','哪']
end_qwords = ['吗', '呢']

def should_be_question(text):
    """判断引号内文本最后一个分句是否为问句"""
    # 用常见句内标点切分
    parts = re.split(r'[，。；：！？\s]+', text.strip())
    parts = [p for p in parts if p]
    if not parts:
        return False
    last = parts[-1]
    # 最后以吗/呢结尾，极大概率为问句
    if last.endswith(('吗', '呢')):
        return True
    # 最后分句较短且以疑问词结尾，是问句
    for w in qwords:
        if last.endswith(w):
            # 但形如“知道什么”“清楚为什么”“没说在哪”等多为陈述
            if len(last) <= 6:
                return True
            # 若最后分句包含明显陈述动词+疑问词结构，视为陈述
            # 如：知道/清楚/明白/告诉/说/写/改/看/听/想/猜/懂/记得 + 什么/谁/哪
            if re.search(r'(知道|清楚|明白|告诉|说|写|改|看|听|想|猜|懂|记得|没见|没说|不知|也不知道)[^，。；：！？]*?' + w + r'$', last):
                return False
            # 否则末尾有疑问词且前面无陈述动词，判为问句
            return True
        if last.startswith(w):
            return True
    return False

def fix_line(line):
    def repl(m):
        inner = m.group(1)
        if should_be_question(inner):
            return '"' + inner.rstrip('。') + '？"'
        return m.group(0)
    # 匹配双引号包裹内容，结尾是句号
    return re.sub(r'"([^"]*。)"', repl, line)

def fix_file(path, dry_run=False):
    with open(path, 'r', encoding='utf8') as f:
        lines = f.readlines()
    new_lines = [fix_line(l) for l in lines]
    changes = sum(1 for a,b in zip(lines, new_lines) if a != b)
    if not dry_run and changes:
        with open(path, 'w', encoding='utf8') as f:
            f.writelines(new_lines)
    return changes

if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    total = 0
    for path in sorted(glob.glob('chapters/新_第*.md')):
        c = fix_file(path, dry_run=dry)
        if c:
            print(f"{'[预览]' if dry else ''}{path}: {c}处")
            total += c
    print(f"总计: {total}处")
