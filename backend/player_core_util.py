"""
player_core_util.py — 模板公共代码剥离 + player-core 注入

策略：
1. 找到模板脚本中的公共模块声明（const FC=, const Panel= 等）
2. 用位置级括号匹配移除整个块（跳过正则字符类中的 }）
3. 注入 canonical player-core.js
"""
import re
from pathlib import Path

CORE_PATH = Path(__file__).parent.parent / 'frontend' / '2d' / 'js' / 'player-core.js'
_core_cache = None

_COMMON_CONST = frozenset(['FC', 'SD', 'Panel', 'End', 'Ending', 'KP', 'KnownPanel', 'UI'])


def get_core_js():
    global _core_cache
    if _core_cache is None:
        with open(CORE_PATH, 'r', encoding='utf-8') as f:
            _core_cache = f.read()
    return _core_cache


def _find_anim_script(html: str):
    search_from = 0
    while True:
        si = html.find('<script>', search_from)
        if si < 0: return None
        sj = html.find('</script>', si)
        if sj < 0: return None
        inner = html[si+8:sj]
        if 'function(){' in inner or '(function(){' in inner:
            return (si, sj)
        search_from = sj + 9


def _brace_count(text: str) -> int:
    """
    统计 text 中的 { 和 } 数量，跳过 JS 正则字符类 [^}...] 内的 }。
    """
    count = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '[' and i + 1 < len(text) and text[i+1] in ('^', '=', '!'):
            # 跳过字符类 [...] 直到匹配的 ]
            i += 1
            while i < len(text) and text[i] != ']':
                if text[i] == '\\':
                    i += 1
                i += 1
        elif ch == '{':
            count += 1
        elif ch == '}':
            count -= 1
        i += 1
    return count


def _find_common_blocks(script: str):
    """
    找到所有公共模块块的位置。
    返回 [(start, end), ...] 列表（闭区间）。
    """
    lines = script.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 检测 const X= 声明
        m = re.match(r'const\s+(\w+)\s*=\s*\{', line)
        if m and m.group(1) in _COMMON_CONST:
            start = i
            depth = _brace_count(line)
            i += 1
            while i < len(lines) and depth > 0:
                depth += _brace_count(lines[i])
                i += 1
            # depth <= 0 时块结束
            end = i  # exclusive
            blocks.append((start, end))
            continue

        # 检测 var _renderMath= / var _convertMath=
        m2 = re.match(r'var\s+(\w+)\s*=\s*function', line)
        if m2 and m2.group(1) in ('_renderMath', '_convertMath'):
            start = i
            depth = _brace_count(line)
            i += 1
            while i < len(lines) and depth > 0:
                depth += _brace_count(lines[i])
                i += 1
            blocks.append((start, i))
            continue

        # 检测 if(!SCENES|| 初始化块（跨行，用括号跟踪）
        if line.startswith('if(!SCENES||SCENES.length===0)'):
            start = i
            depth = _brace_count(line)
            i += 1
            while i < len(lines) and depth > 0:
                depth += _brace_count(lines[i])
                i += 1
            blocks.append((start, i))
            continue

        # 检测 function onFrame（跨行——声明+函数体）
        if line.startswith('function onFrame('):
            start = i
            depth = _brace_count(line)
            i += 1
            while i < len(lines) and depth > 0:
                depth += _brace_count(lines[i])
                i += 1
            blocks.append((start, i))
            continue

        # 检测单行公共代码（这些块本身就在一行内）
        if (line.startswith('FC._onFrame=') or
            line.startswith('FC._onDone=') or
            line.startswith('(function(){var e=document.getElementById("stars")')):
            blocks.append((i, i+1))
            i += 1
            continue

        i += 1

    return blocks


def strip_common(script: str) -> str:
    """移除脚本中的公共模块代码。"""
    blocks = _find_common_blocks(script)
    if not blocks:
        return script

    lines = script.split('\n')
    # 从后往前删，保持索引有效
    result = list(lines)
    for start, end in reversed(blocks):
        del result[start:end]
    return '\n'.join(result)


def inject_core(html: str) -> str:
    pos = _find_anim_script(html)
    if not pos:
        return html

    si, sj = pos
    inner = html[si+8:sj]

    # 移除公共模块
    stripped = strip_common(inner)

    # 找到 IIFE 闭包
    iife_close = stripped.rfind('})();')
    template_code = stripped[:iife_close].rstrip() if iife_close >= 0 else stripped.rstrip()

    # 注入 core
    core = get_core_js()
    inner = template_code + '\n' + core + '\n})();'

    return html[:si+8] + inner + html[sj:]


def is_available() -> bool:
    return CORE_PATH.exists()
