#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《龙族》小说爬虫 - 从 x33yq.org 爬取并保存为 Markdown
按部（卷）和章节分目录存放。
"""

import requests
import re
import os
import sys
import time
import random
import json
from pathlib import Path

import urllib3
urllib3.disable_warnings()

# ============ 配置 ============
BASE_URL = "https://www.x33yq.org"
BOOK_URL = f"{BASE_URL}/read/22360/"
PROXIES = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}
OUTPUT_DIR = Path(__file__).parent / "龙族"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': BOOK_URL,
}

session = requests.Session()
session.proxies.update(PROXIES)
session.verify = False
session.headers.update(HEADERS)

# ============ 分卷定义 ============
# 根据章节编号范围划分各部（基于《龙族》已知章节结构）
VOLUMES = [
    {
        "name": "龙族Ⅰ-火之晨曦",
        "dir": "龙族Ⅰ-火之晨曦",
        "start": 1,
        "end": 54,
        "sub_volumes": []
    },
    {
        "name": "龙族Ⅱ-悼亡者之瞳",
        "dir": "龙族Ⅱ-悼亡者之瞳",
        "start": 55,
        "end": 137,
        "sub_volumes": []
    },
    {
        "name": "龙族Ⅲ-黑月之潮",
        "dir": "龙族Ⅲ-黑月之潮",
        "start": 138,
        "end": 359,
        "sub_volumes": [
            {"name": "上", "dir": "上", "start": 138, "end": 210},
            {"name": "中", "dir": "中", "start": 211, "end": 296},
            {"name": "下", "dir": "下", "start": 297, "end": 359},
        ]
    },
    {
        "name": "龙族Ⅳ-奥丁之渊",
        "dir": "龙族Ⅳ-奥丁之渊",
        "start": 360,
        "end": 397,
        "sub_volumes": []
    },
    {
        "name": "龙族Ⅴ-悼亡者的归来",
        "dir": "龙族Ⅴ-悼亡者的归来",
        "start": 398,
        "end": 419,
        "sub_volumes": []
    },
]


def get_chapter_list():
    """获取完整章节列表（按章节编号正序）"""
    print("📖 获取章节列表...")
    r = session.get(BOOK_URL, timeout=15)
    r.encoding = 'utf-8'
    
    chapters = re.findall(r'<dd><a[^>]*href="(/read/22360/\d+\.html)"[^>]*>(.*?)</a></dd>', r.text)
    
    # 去重：保留每个章节号第一次出现的条目
    seen_nums = set()
    unique_chapters = []
    for href, title_html in chapters:
        title = re.sub(r'<[^>]+>', '', title_html).strip()
        num_match = re.search(r'第(\d+)章', title)
        if num_match:
            num = int(num_match.group(1))
            if num not in seen_nums:
                seen_nums.add(num)
                unique_chapters.append((href, title, num))
    
    # 按章节编号排序
    unique_chapters.sort(key=lambda x: x[2])
    
    print(f"✅ 获取到 {len(unique_chapters)} 个章节（第{unique_chapters[0][2]}章~第{unique_chapters[-1][2]}章）")
    return [(h, t, n) for h, t, n in unique_chapters]


def get_volume_for_chapter(chapter_num):
    """根据章节编号确定属于哪一部"""
    for vol in VOLUMES:
        if vol["start"] <= chapter_num <= vol["end"]:
            for sub in vol.get("sub_volumes", []):
                if sub["start"] <= chapter_num <= sub["end"]:
                    return vol, sub
            return vol, None
    return None, None


def fetch_chapter_content(url):
    """获取单章内容"""
    full_url = f"{BASE_URL}{url}"
    r = session.get(full_url, timeout=15)
    r.encoding = 'utf-8'
    
    # 提取标题
    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', r.text, re.DOTALL)
    title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else "未知标题"
    
    # 提取正文 - <div id="content">
    content_match = re.search(r'<div id="content">(.*?)</div>', r.text, re.DOTALL)
    if not content_match:
        return title, ""
    
    raw_content = content_match.group(1)
    
    # 去掉内容中混入的导航/功能区块
    # 注意：bottem div 可能没有闭合标签，所以从 bottem 开始截断到末尾
    raw_content = re.sub(r'<div class="bottem">.*', '', raw_content, flags=re.DOTALL)
    # 去掉其他可能的导航div
    raw_content = re.sub(r'<div[^>]*class="[^"]*(?:toolbar|link|page|nav)[^"]*"[^>]*>.*?</div>', '', raw_content, flags=re.DOTALL)
    # 去掉广告行（请点击下一页继续阅读 等）
    raw_content = re.sub(r'<p>[^<]*?(?:请点击|继续阅读|没有结束|后面还有)[^<]*<p>', '', raw_content)
    
    # 清洗内容
    text = re.sub(r'<br\s*/?>', '\n', raw_content)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<p[^>]*>', '', text)
    
    # HTML实体解码
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = re.sub(r"&#39;", "'", text)
    
    # 移除剩余HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 清理多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    # 过滤残余的导航文字行（如果还有的话）
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 跳过明显的导航/广告行
        if line in ['上一章', '下一章', '章节目录', '投推荐票', '加入书签', '返回书架']:
            continue
        if '投推荐票' in line and len(line) < 20:
            continue
        cleaned_lines.append(line)
    
    text = '\n\n'.join(cleaned_lines)
    
    return title, text 


def save_as_markdown(title, content, volume_dir, filename):
    """保存为 Markdown 文件"""
    volume_dir.mkdir(parents=True, exist_ok=True)
    filepath = volume_dir / filename
    
    # Markdown 格式：标题 + 内容
    md_content = f"# {title}\n\n{content}\n"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    return filepath


def create_index_md(volume_dir, volume_name, chapters_info):
    """生成卷目录索引文件"""
    lines = [f"# {volume_name}\n", f"\n共 {len(chapters_info)} 章\n"]
    
    for i, (filename, title) in enumerate(chapters_info, 1):
        lines.append(f"{i:03d}. [{title}]({filename})")
    
    content = '\n'.join(lines)
    
    index_path = volume_dir / "index.md"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return index_path


def create_main_index(all_volumes_info):
    """生成总目录索引"""
    lines = [
        "# 《龙族》— 江南\n",
        "\n---\n",
    ]
    
    for vol_name, vol_dir, chapter_count, sub_volumes in all_volumes_info:
        vol_path = vol_dir.name
        lines.append(f"\n## [{vol_name}]({vol_path}/index.md)（{chapter_count}章）")
        
        for sub_name, sub_dir, sub_count in sub_volumes:
            sub_path = f"{vol_path}/{sub_dir.name}"
            lines.append(f"  - [{sub_name}]({sub_path}/index.md)（{sub_count}章）")
    
    lines.append("\n---\n")
    lines.append(f"> 数据来源：{BOOK_URL}")
    lines.append(f"> 爬取时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    content = '\n'.join(lines)
    
    index_path = OUTPUT_DIR.parent / "index.md"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return index_path


def main():
    print("=" * 60)
    print("   《龙族》小说爬虫")
    print("   源站: x33yq.org (33言情)")
    print("   输出: 龙族/ 目录")
    print("=" * 60)
    
    # 1. 获取章节列表
    chapters = get_chapter_list()
    if not chapters:
        print("❌ 未获取到章节列表")
        return
    
    # 2. 加载已爬取进度
    progress_file = OUTPUT_DIR.parent / "crawled_progress.json"
    crawled = set()
    if progress_file.exists():
        try:
            with open(progress_file, 'r') as f:
                crawled = set(json.load(f))
            print(f"📋 已爬取 {len(crawled)} 章（断点续爬）")
        except:
            pass
    
    # 3. 逐个爬取章节
    total = len(chapters)
    
    print(f"\n🚀 开始爬取 {total} 个章节...\n")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, (href, title, chapter_num) in enumerate(chapters, 1):
        # 跳过已爬取
        if str(chapter_num) in crawled:
            skip_count += 1
            if skip_count <= 3 or skip_count % 50 == 0:
                print(f"  [{i}/{total}] ⏭️ 跳过: {title}（已爬取）")
            continue
        
        # 确定分卷
        vol_info, sub_info = get_volume_for_chapter(chapter_num)
        if vol_info is None:
            print(f"  [{i}/{total}] ⚠️ 未找到分卷: {title}（第{chapter_num}章）")
            continue
        
        volume_dir = OUTPUT_DIR / vol_info["dir"]
        if sub_info:
            volume_dir = volume_dir / sub_info["dir"]
        
        # 文件名：3位数字编号-标题.md
        safe_title = re.sub(r'[\\/:*?"<>|]', '', title)
        filename = f"{chapter_num:03d}-{safe_title}.md"
        
        # 爬取内容（带重试）
        max_retries = 3
        success = False
        for attempt in range(max_retries):
            try:
                chap_title, content = fetch_chapter_content(href)
                if content and len(content) > 50:
                    saved_path = save_as_markdown(chap_title, content, volume_dir, filename)
                    crawled.add(str(chapter_num))
                    # 立即保存进度
                    with open(progress_file, 'w') as f:
                        json.dump(sorted(list(crawled)), f)
                    char_count = len(content)
                    print(f"  [{i}/{total}] ✅ {title}（{char_count}字）")
                    success = True
                    success_count += 1
                    break
                else:
                    print(f"  [{i}/{total}] ⚠️ 内容为空或过短: {title}（尝试 {attempt+1}/{max_retries}）")
            except Exception as e:
                print(f"  [{i}/{total}] ❌ {title}: {type(e).__name__}（尝试 {attempt+1}/{max_retries}）")
            
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                time.sleep(wait)
        
        if not success:
            print(f"  [{i}/{total}] ❌❌ 爬取失败（已重试{max_retries}次）: {title}")
            fail_count += 1
        
        # 请求间隔（礼貌爬取）
        time.sleep(random.uniform(0.8, 2.0))
    
    # 4. 生成目录索引
    print("\n📝 生成目录索引...")
    
    all_volumes_info_list = []
    for vol in VOLUMES:
        volume_dir = OUTPUT_DIR / vol["dir"]
        sub_volumes_info = []
        
        for sub in vol.get("sub_volumes", []):
            sub_dir = volume_dir / sub["dir"]
            if sub_dir.exists():
                md_files = sorted([f for f in sub_dir.glob("*.md") if f.name != 'index.md'])
                sub_volumes_info.append((sub["name"], sub_dir, len(md_files)))
                create_index_md(sub_dir, f"{vol['name']} - {sub['name']}", 
                               [(f.name, f.stem) for f in md_files])
        
        if volume_dir.exists():
            md_files = sorted([f for f in volume_dir.glob("*.md") if f.name != 'index.md'])
            all_volumes_info_list.append((vol["name"], volume_dir, len(md_files), sub_volumes_info))
            create_index_md(volume_dir, vol["name"],
                          [(f.name, f.stem) for f in md_files])
    
    create_main_index(all_volumes_info_list)
    
    # 5. 总结
    print(f"\n{'='*60}")
    print(f"  🎉 爬取完成！")
    print(f"  ✅ 成功: {success_count} 章")
    print(f"  ⏭️  跳过: {skip_count} 章")
    print(f"  ❌ 失败: {fail_count} 章")
    print(f"  📁 输出目录: {OUTPUT_DIR}")
    print(f"  📖 总索引: {OUTPUT_DIR.parent / 'index.md'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
