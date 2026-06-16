#!/usr/bin/env python3
"""Build script for 龙族 novel reading website - generates static HTML from markdown files."""
import os
import re
import sys
import json
import shutil

BOOKS_DIR = '龙族'
OUTPUT_DIR = '_site'
SITE_NAME = '龙族'
SITE_DESC = '江南《龙族》系列小说在线阅读'

try:
    import markdown as md_lib
    def md_to_html(text):
        return md_lib.markdown(text, extensions=['extra', 'smarty'])
except ImportError:
    print("Warning: 'markdown' package not found, using basic conversion")
    def md_to_html(text):
        lines = text.split('\n')
        paragraphs = []
        current = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current:
                    paragraphs.append(' '.join(current))
                    current = []
            else:
                if stripped.startswith('#'):
                    if current:
                        paragraphs.append(' '.join(current))
                        current = []
                    level = len(stripped) - len(stripped.lstrip('#'))
                    content = stripped.lstrip('#').strip()
                    paragraphs.append(f'<h{level}>{content}</h{level}>')
                else:
                    current.append(stripped)
        if current:
            paragraphs.append(' '.join(current))
        result = []
        for p in paragraphs:
            if p.startswith('<h'):
                result.append(p)
            else:
                result.append(f'<p>{p}</p>')
        return '\n'.join(result)


def split_paragraphs(text):
    """Split long single-line paragraphs into readable chunks for Chinese novel text."""
    LQ = '\u201d'  # closing curly quote "
    # Split after closing quote followed by space + non-punctuation character
    text = re.sub(r'(?<=' + LQ + r')\s+(?=[^\s\uff0c\u3002\uff01\uff1f\u3001\uff1b\uff1a\uff08])', '\n\n', text)
    # Also split after closing quote directly followed by Chinese/English char (no space)
    text = re.sub(r'(?<=' + LQ + r')(?=[\u4e00-\u9fffA-Za-z])', '\n\n', text)

    parts = [p.strip() for p in text.split('\n\n') if p.strip()]

    # Further split long paragraphs (> 250 chars) at sentence boundaries every ~3 sentences
    final = []
    for p in parts:
        if len(p) > 250:
            sentences = re.split('([\u3002\uff01\uff1f])', p)
            chunks, current, count = [], '', 0
            for i in range(0, len(sentences) - 1, 2):
                seg = sentences[i] + sentences[i + 1]
                current += seg
                count += 1
                if count >= 3 and len(current) > 120:
                    chunks.append(current)
                    current, count = '', 0
            if current:
                chunks.append(current)
            final.extend(chunks)
        else:
            final.append(p)

    # Merge very short fragments (< 25 chars) with previous paragraph
    merged = []
    for p in final:
        if merged and len(p) < 25:
            merged[-1] += p
        else:
            merged.append(p)
    return '\n\n'.join(merged)


def slugify(text):
    text = re.sub(r'[^\w\u4e00-\u9fff]+', '-', text)
    text = text.strip('-').lower()
    return text or 'untitled'


def extract_title(content):
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('#'):
            return re.sub(r'^#+\s*', '', line).strip()
    return None


def parse_chapter_num(filename):
    m = re.match(r'(\d+)', filename)
    return int(m.group(1)) if m else 0


def read_chapters(book_dir):
    chapters = []
    for f in sorted(os.listdir(book_dir)):
        if f.endswith('.md') and f != 'index.md':
            path = os.path.join(book_dir, f)
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read().strip()
            title = extract_title(content)
            if not title:
                title = os.path.splitext(f)[0]
            # Remove the leading # title from content for display
            body = re.sub(r'^#+\s+.*?\n+', '', content, count=1).strip()
            body = split_paragraphs(body)
            html = md_to_html(body)
            num = parse_chapter_num(f)
            chapters.append({
                'num': num,
                'title': title,
                'slug': slugify(os.path.splitext(f)[0]),
                'html': html,
            })
    chapters.sort(key=lambda c: c['num'])
    return chapters


def read_books():
    books = []
    for entry in sorted(os.listdir(BOOKS_DIR)):
        path = os.path.join(BOOKS_DIR, entry)
        if os.path.isdir(path):
            parts = entry.split('-', 1)
            if len(parts) == 2:
                title, subtitle = parts
            else:
                title, subtitle = entry, ''
            chapters = read_chapters(path)
            books.append({
                'title': title.strip(),
                'subtitle': subtitle.strip(),
                'slug': slugify(entry),
                'chapters': chapters,
                'dir': entry,
            })
    return books


# ─── HTML Templates ────────────────────────────────────────

def page_shell(title, content, back_url=None, body_class='', extra_head=''):
    back = f'<a href="{back_url}" class="top-back">&larr;</a>' if back_url else ''
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=5">
<title>{title} - {SITE_NAME}</title>
<meta name="description" content="{title} - {SITE_DESC}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🐉</text></svg>">
<link rel="stylesheet" href="/longzu/style.css">
{extra_head}
</head>
<body class="{body_class}">
<header class="top-bar">
  <div class="top-inner">
    {back}
    <h1 class="top-title">{title}</h1>
    <button class="menu-btn" onclick="document.getElementById('nav-overlay').classList.toggle('open')">&#9776;</button>
  </div>
</header>
{content}
<script src="/longzu/script.js"></script>
</body>
</html>'''


def chapter_nav(book_slug, chapters, idx):
    parts = ['<nav class="ch-nav">']
    if idx > 0:
        prev = chapters[idx - 1]
        parts.append(f'<a href="/longzu/{book_slug}/{prev["slug"]}.html" class="ch-prev">&larr; 上一章</a>')
    else:
        parts.append('<span class="ch-prev disabled">&larr; 上一章</span>')
    parts.append(f'<a href="/longzu/{book_slug}/" class="ch-toc">目录</a>')
    if idx < len(chapters) - 1:
        nxt = chapters[idx + 1]
        parts.append(f'<a href="/longzu/{book_slug}/{nxt["slug"]}.html" class="ch-next">下一章 &rarr;</a>')
    else:
        parts.append('<span class="ch-next disabled">下一章 &rarr;</span>')
    parts.append('</nav>')
    return '\n'.join(parts)


def gen_chapter(book_slug, book_title, chapter, chapters, idx):
    nav = chapter_nav(book_slug, chapters, idx)
    progress = f'<div class="ch-progress"><span>{idx + 1}</span> / {len(chapters)}</div>'
    content = f'''
{nav}
{progress}
<article class="reading">
  <h2 class="ch-title">{chapter["title"]}</h2>
  <div class="ch-body">{chapter["html"]}</div>
</article>
{nav}
<div class="overlay" id="nav-overlay">
  <div class="overlay-panel">
    <div class="overlay-head">{book_title}</div>
    <ul class="overlay-list">'''
    for i, ch in enumerate(chapters):
        cls = ' class="current"' if i == idx else ''
        content += f'\n      <li{cls}><a href="/longzu/{book_slug}/{ch["slug"]}.html">{ch["title"]}</a></li>'
    content += '''
    </ul>
    <div class="overlay-foot">
      <button onclick="toggleDark()" id="dark-btn">🌙 夜间模式</button>
      <div class="font-ctrl">
        <button onclick="changeFont(-1)">A-</button>
        <button onclick="changeFont(1)">A+</button>
      </div>
    </div>
  </div>
</div>
<div class="scroll-bar" id="scroll-bar"></div>'''
    return page_shell(chapter['title'], content, f'/longzu/{book_slug}/', 'reading-page')


def gen_book_page(book):
    title = f'{book["title"]} · {book["subtitle"]}' if book['subtitle'] else book['title']
    content = f'''
<div class="container book-page">
  <div class="book-hero">
    <h2 class="book-hero-title">{book["title"]}</h2>
    <p class="book-hero-sub">{book["subtitle"]}</p>
    <p class="book-hero-count">共 {len(book["chapters"])} 章</p>
  </div>
  {f'<a href="/longzu/{book["slug"]}/{book["chapters"][0]["slug"]}.html" class="start-btn">开始阅读</a>' if book["chapters"] else ""}
  <ul class="ch-list" id="chapter-list">'''
    for ch in book['chapters']:
        content += f'\n    <li><a href="/longzu/{book["slug"]}/{ch["slug"]}.html"><span class="ch-num">{ch["num"]}</span>{ch["title"]}</a></li>'
    content += '''
  </ul>
</div>'''
    return page_shell(title, content, '/longzu/', 'list-page')


def gen_home(books):
    total = sum(len(b['chapters']) for b in books)
    cards = ''
    for b in books:
        first = f'/{b["chapters"][0]["slug"]}.html' if b['chapters'] else '/'
        url = f'/longzu/{b["slug"]}'
        cards += f'''
    <a href="{url}" class="book-card">
      <div class="bc-body">
        <h3 class="bc-title">{b["title"]}</h3>
        <p class="bc-sub">{b["subtitle"]}</p>
        <p class="bc-count">{len(b["chapters"])} 章</p>
      </div>
      <span class="bc-arrow">&rarr;</span>
    </a>'''
    content = f'''
<div class="container home">
  <div class="home-hero">
    <h2 class="home-title">🐉 {SITE_NAME}</h2>
    <p class="home-desc">{SITE_DESC}</p>
    <p class="home-stat">{len(books)} 部作品 · {total} 章</p>
  </div>
  <div class="book-list">{cards}
  </div>
</div>'''
    return page_shell('首页', content, body_class='home-page')


# ─── Build ────────────────────────────────────────

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    # Copy static assets
    if os.path.isdir('site'):
        for f in os.listdir('site'):
            src = os.path.join('site', f)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(OUTPUT_DIR, f))

    books = read_books()
    total = 0

    # Home
    write(os.path.join(OUTPUT_DIR, 'index.html'), gen_home(books))
    print("✓ Home page")

    for book in books:
        # Book index
        write(os.path.join(OUTPUT_DIR, book['slug'], 'index.html'), gen_book_page(book))
        print(f"✓ {book['title']}")

        # Chapters
        for i, ch in enumerate(book['chapters']):
            html = gen_chapter(book['slug'], book['title'], ch, book['chapters'], i)
            write(os.path.join(OUTPUT_DIR, book['slug'], f'{ch["slug"]}.html'), html)
            total += 1

    # Generate a simple sitemap
    sitemap_urls = ['<url><loc>https://raingor-ye.github.io/longzu/</loc></url>']
    for book in books:
        sitemap_urls.append(f'<url><loc>https://raingor-ye.github.io/longzu/{book["slug"]}/</loc></url>')
        for ch in book['chapters']:
            sitemap_urls.append(f'<url><loc>https://raingor-ye.github.io/longzu/{book["slug"]}/{ch["slug"]}.html</loc></url>')
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(sitemap_urls) + '\n</urlset>'
    write(os.path.join(OUTPUT_DIR, 'sitemap.xml'), sitemap)

    print(f"\n✅ Build complete: {len(books)} books, {total} chapters → {OUTPUT_DIR}/")


if __name__ == '__main__':
    main()
