#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理已爬取的《龙族》Markdown文件中残留的广告和导航文字
"""

import re
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "龙族"

# 需要清理的广告/导航行（精确匹配或包含匹配）
AD_PATTERNS = [
    r'这章没有结束，请点击下一页继续阅读！',
    r'小主，这个章节后面还有哦，请点击下一页继续阅读，后面更精彩！',
    r'投推荐票',
    r'上一章',
    r'下一章',
    r'章节目录',
    r'加入书签',
    r'返回书架',
    r'请点击下一页继续阅读',
]


def clean_file(filepath):
    """清理单个文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_len = len(content)
    
    # 逐行清理
    lines = content.split('\n')
    cleaned_lines = []
    changed = False
    
    for line in lines:
        stripped = line.strip()
        
        # 跳过空行（在正文区域）
        if not stripped:
            continue
        
        # 检查是否是广告/导航行
        is_ad = False
        for pattern in AD_PATTERNS:
            if re.search(pattern, stripped):
                is_ad = True
                changed = True
                break
        
        if not is_ad:
            cleaned_lines.append(line)
    
    # 重建内容
    # 合并相邻空行
    result = '\n'.join(cleaned_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    result = result.strip() + '\n'
    
    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f'  ✅ 清理: {filepath.name} ({original_len} -> {len(result)} 字符)')
        return True
    return False


def main():
    print('🔍 扫描并清理广告/导航文字...\n')
    
    md_files = list(OUTPUT_DIR.rglob('*.md'))
    md_files = [f for f in md_files if f.name != 'index.md']
    
    print(f'共发现 {len(md_files)} 个章节文件')
    
    cleaned_count = 0
    for filepath in sorted(md_files):
        if clean_file(filepath):
            cleaned_count += 1
    
    print(f'\n✅ 清理完成！共清理 {cleaned_count} 个文件')


if __name__ == '__main__':
    main()
