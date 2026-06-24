"""
Layer 3 — 分镜展开器 (Storyboard Expander)
============================================================
职责：将 Layer 2 的幕结构规划展开为详细分镜脚本。
      输出格式为自然语言，每 2-3 秒一个段落，
      包含画面描述、动画指令、配音旁白。

输入：Layer 2 的幕结构规划 JSON
输出：分镜脚本 JSON（含每幕/每片段/每段落的详细描述）

使用方式：
    from layer3_storyboard import expand_storyboard
    script = expand_storyboard(act_plan)
"""

import json
import math
import copy


# ==================================================================
#  场景模板库
# ==================================================================

# 每个场景类型包含：
#   entries: 生成 storyboard 条目的函数或模板
#   narration: 生成旁白的函数或模板

FPS = 60


def _t(frame: int) -> str:
    """将帧号转为时间字符串。"""
    sec = frame / FPS
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}" if m > 0 else f"{s}s"


def _time_range(start_frame: int, end_frame: int) -> str:
    return f"{_t(start_frame)}-{_t(end_frame)}"


def _chunk_range(total_sec: int, chunk_sec: int, start_offset: int = 0):
    """将总时长分割为若干块，每块 chunk_sec 秒。
    返回 [(start_sec, end_sec), ...] 列表。"""
    chunks = []
    pos = start_offset
    while pos < total_sec:
        end = min(pos + chunk_sec, total_sec)
        chunks.append((pos, end))
        pos = end
    return chunks


def _frame_of(sec: int, seg_start_frame: int) -> int:
    return seg_start_frame + sec * FPS


# ==================================================================
#  各场景类型的故事板模板
# ==================================================================

def _tmpl_introduction(params: dict, seg_start: int, seg_end: int) -> dict:
    """开场引入模板 (10秒)"""
    total = 10
    title = params.get("title", "核心概念")
    subtitle = params.get("subtitle", "物理")
    cube_label = params.get("cube_label", "🔬")
    labels = params.get("concept_labels", [])

    # 2-3秒一段
    entries = [
        {
            "time": _time_range(_frame_of(0, seg_start), _frame_of(3, seg_start)),
            "visual": f"深空背景，中央浮现一个银色{cube_label}（代表研究对象），"
                       f"表面标有「{title}」字样",
            "animation": "立方体从屏幕外旋转飞入，停在中央，轻微上下浮动（周期2秒）"
        },
        {
            "time": _time_range(_frame_of(3, seg_start), _frame_of(6, seg_start)),
            "visual": f"立方体两侧弹出标题框：{labels[0]['text']} & {labels[1]['text']}",
            "animation": f"两个词从立方体左右两侧「生长」出来，"
                         f"带有发光描边效果，颜色{labels[0]['color']}和{labels[1]['color']}"
        },
        {
            "time": _time_range(_frame_of(6, seg_start), _frame_of(10, seg_start)),
            "visual": f"画面底部出现副标题：「{subtitle}」",
            "animation": "副标题以打字机效果逐字打出，背景星星缓慢旋转"
        }
    ]

    narration = (f"同学们好。今天我们从一个核心概念开始——{title}。"
                 f"要理解它，关键要分清这两个概念：{labels[0]['text']}和{labels[1]['text']}。")

    return {"entries": entries, "narration": narration}


def _tmpl_scene_demo_a(params: dict, seg_start: int, seg_end: int) -> dict:
    """场景A展示模板 (20秒)"""
    scene_name = params.get("scene_label", "场景A")
    balance_label = params.get("balance_label", "天平")
    spring_label = params.get("spring_label", "弹簧秤")
    g_value = params.get("g_value", "9.8 m/s²")
    total = 20

    entries = [
        {
            "time": _time_range(_frame_of(0, seg_start), _frame_of(4, seg_start)),
            "visual": f"背景切换为{scene_name}，一个物体落在画面中央的地面上",
            "animation": "场景用淡入淡出切换（1秒过渡），物体落下时有轻微「落地」弹跳效果"
        },
        {
            "time": _time_range(_frame_of(4, seg_start), _frame_of(9, seg_start)),
            "visual": f"物体左上方出现一架天平，托盘上放着物体，指针指向平衡位置",
            "animation": "天平从左侧滑入，指针轻微晃动后稳定，刻度数字用绿色高亮"
        },
        {
            "time": _time_range(_frame_of(9, seg_start), _frame_of(14, seg_start)),
            "visual": f"物体右上方出现一个弹簧秤，钩住物体，指针指向测量值",
            "animation": "弹簧秤从右侧滑入，秤钩伸出钩住物体，指针旋转到对应位置，数字用橙色高亮"
        },
        {
            "time": _time_range(_frame_of(14, seg_start), _frame_of(17, seg_start)),
            "visual": f"两个仪器闪烁，旁边出现标签：{balance_label} | {spring_label}",
            "animation": "标签从仪器上方「弹出」，带有放大缩小的弹性动画（easeOutBack）"
        },
        {
            "time": _time_range(_frame_of(17, seg_start), _frame_of(20, seg_start)),
            "visual": f"画面底部显示标注：{scene_name} g = {g_value}",
            "animation": "标注文字从底部缓缓上浮"
        }
    ]

    narration = (f"现在看{scene_name}。用天平称，质量不变。"
                 f"用弹簧秤称，重力读数如标签所示。"
                 f"记住这个数据，我们马上和另一场景对比。")

    return {"entries": entries, "narration": narration}


def _tmpl_scene_demo_b(params: dict, seg_start: int, seg_end: int) -> dict:
    """场景B展示模板 (20秒)"""
    scene_name = params.get("scene_label", "场景B")
    balance_label = params.get("balance_label", "天平")
    spring_label = params.get("spring_label", "弹簧秤")
    g_value = params.get("g_value", "1.6 m/s²")
    total = 20

    entries = [
        {
            "time": _time_range(_frame_of(0, seg_start), _frame_of(4, seg_start)),
            "visual": f"背景切换为{scene_name}，物体位置不变但环境改变",
            "animation": "场景切换用淡入淡出（1秒过渡），物体颜色微调以匹配新环境光照"
        },
        {
            "time": _time_range(_frame_of(4, seg_start), _frame_of(9, seg_start)),
            "visual": f"天平再次出现，指针依然稳定指向同一位置（读数不变）",
            "animation": "天平滑入，指针快速稳定，与之前读数完全一致，强调「不变」"
        },
        {
            "time": _time_range(_frame_of(9, seg_start), _frame_of(14, seg_start)),
            "visual": f"弹簧秤再次出现，指针快速回摆，停在新的位置",
            "animation": "弹簧秤滑入，指针先抖动一下，再快速旋转到新位置（比场景A更快的动画，体现变化）"
        },
        {
            "time": _time_range(_frame_of(14, seg_start), _frame_of(17, seg_start)),
            "visual": f"两个仪器标签更新：{balance_label}（绿色加粗）| "
                       f"{spring_label}（橙色闪烁）",
            "animation": "标签切换时，质量标签用绿色光晕强调「不变」，重力标签用橙色闪烁强调「变化」"
        },
        {
            "time": _time_range(_frame_of(17, seg_start), _frame_of(20, seg_start)),
            "visual": f"底部显示标注：{scene_name} g = {g_value}",
            "animation": "标注文字从底部上浮，与场景A形成对比"
        }
    ]

    narration = (f"再看{scene_name}。神奇的事情发生了——天平读数仍然不变！"
                 f"但弹簧秤的指针却指向了{g_value}。"
                 f"为什么？因为{scene_name}的引力不同。天平测质量，弹簧秤测重力，这就是区别。")

    return {"entries": entries, "narration": narration}


def _tmpl_comparison(params: dict, seg_start: int, seg_end: int) -> dict:
    """对比结论模板 (20秒)"""
    conclusions = params.get("conclusions", [])
    formula = params.get("formula", "")
    final_line = params.get("final_line", "")
    total = 20

    entries = [
        {
            "time": _time_range(_frame_of(0, seg_start), _frame_of(5, seg_start)),
            "visual": "画面一分为二，左半是场景A，右半是场景B，同时显示测量结果对比",
            "animation": "用滑动分割效果将画面切分（1.5秒），两个场景同屏显示，指针同步跳动"
        },
        {
            "time": _time_range(_frame_of(5, seg_start), _frame_of(12, seg_start)),
            "visual": f"中央出现核心结论（逐行弹出）："
                       f"{' | '.join(c['text'] for c in conclusions[:2])}",
            "animation": "结论文字从中央依次弹出，带有放大和光效，指针同步跳动强化对比"
        },
        {
            "time": _time_range(_frame_of(12, seg_start), _frame_of(16, seg_start)),
            "visual": f"核心公式 {formula} 在画面中央放大显示",
            "animation": "公式从中央放大弹出（弹性效果），变量用不同颜色高亮"
        },
        {
            "time": _time_range(_frame_of(16, seg_start), _frame_of(20, seg_start)),
            "visual": f"底部出现过渡语：「{final_line}」",
            "animation": "文字从底部上浮，画面渐暗准备过渡"
        }
    ]

    narration = (f"结论来了：{'，'.join(c['text'] for c in conclusions[:2])}。"
                 f"核心公式 {formula}。"
                 f"{final_line}。")

    return {"entries": entries, "narration": narration}


def _tmpl_transition(params: dict, seg_start: int, seg_end: int) -> dict:
    """过渡模板 (10秒)"""
    text = params.get("transition_text", "进入下一环节")
    total = 10

    entries = [
        {
            "time": _time_range(_frame_of(0, seg_start), _frame_of(5, seg_start)),
            "visual": "深空背景淡入，星光闪烁，一颗流星划过天际",
            "animation": "背景淡入（1秒），流星从右上向左下划过（拖尾效果），星星闪烁频率降低"
        },
        {
            "time": _time_range(_frame_of(5, seg_start), _frame_of(10, seg_start)),
            "visual": f"画面中央出现过渡文字：「{text}」",
            "animation": "文字以打字机效果逐字打出，随后画面渐暗"
        }
    ]

    narration = f"{text}。"

    return {"entries": entries, "narration": narration}


def _tmpl_problem_display(params: dict, seg_start: int, seg_end: int) -> dict:
    """题目展示模板 (10秒)"""
    stem = params.get("stem", "")
    options = params.get("options", [])
    total = 10

    opt_text = "  ".join(f"{o['label']}. {o['text'][:20]}…" for o in options[:2])

    entries = [
        {
            "time": _time_range(_frame_of(0, seg_start), _frame_of(3, seg_start)),
            "visual": f"深空背景淡出，画面淡入一张试卷纸铺满中央，"
                       f"左上角浮现红色印章「📝 真题演练」",
            "animation": "试卷从中央缩放出现（0.8→1.0，弹性效果），纸张有轻微纹理和折痕"
        },
        {
            "time": _time_range(_frame_of(3, seg_start), _frame_of(7, seg_start)),
            "visual": f"试卷顶部出现题目：{stem[:60]}…",
            "animation": "题目以打字机效果逐字出现，文字用深蓝色加粗"
        },
        {
            "time": _time_range(_frame_of(7, seg_start), _frame_of(10, seg_start)),
            "visual": f"选项显示：{opt_text}",
            "animation": "选项从上方依次落下，每个选项间隔0.3秒"
        }
    ]

    narration = f"来看一道真题。题目是这样的：{stem[:50]}… 请思考正确选项。"

    return {"entries": entries, "narration": narration}


def _tmpl_scene_analysis(params: dict, seg_start: int, seg_end: int) -> dict:
    """场景与受力分析模板 (20秒)"""
    scene_label = params.get("scene_label", "受力分析")
    concept_note = params.get("concept_note", "")
    scenes = params.get("scenes", [])
    total = 20

    scene_lines = "、".join(scenes[:3]) if scenes else "各场景"

    entries = [
        {
            "time": _time_range(_frame_of(0, seg_start), _frame_of(5, seg_start)),
            "visual": f"题目下方展开{scene_label}示意图，展示{scene_lines}",
            "animation": "示意图从左到右逐步绘制（手绘效果，用时2秒），场景标签依次弹出"
        },
        {
            "time": _time_range(_frame_of(5, seg_start), _frame_of(10, seg_start)),
            "visual": f"物体受力分析：各场景中的受力情况标注",
            "animation": "受力箭头从物体中心向外「生长」，每个力用不同颜色区分"
        },
        {
            "time": _time_range(_frame_of(10, seg_start), _frame_of(15, seg_start)),
            "visual": f"将{concept_note}应用到各场景中，高亮对应关系",
            "animation": "概念标签从右侧滑入，与场景建立连线（虚线动画绘制）"
        },
        {
            "time": _time_range(_frame_of(15, seg_start), _frame_of(20, seg_start)),
            "visual": "整合所有信息，展示完整的物理图景",
            "animation": "所有标注汇聚整合，整体闪烁一次后稳定显示"
        }
    ]

    narration = (f"题目涉及{scene_lines}。我们逐一分析每个场景中的物理情况，"
                 f"运用{concept_note}进行受力分析。"
                 f"注意每个场景中力的差异。")

    return {"entries": entries, "narration": narration}


def _tmpl_option_analysis(params: dict, seg_start: int, seg_end: int) -> dict:
    """选项逐个击破模板 (30秒)"""
    options = params.get("options", [])
    total = 30

    if not options:
        return {"entries": [
            {"time": _time_range(seg_start, seg_end), "visual": "暂无选项数据",
             "animation": ""}
        ], "narration": ""}

    # 每个选项分配约 6-7 秒
    opts_per_entry = 4
    chunk = total / max(len(options), 1)

    entries = []
    for i, opt in enumerate(options):
        t_start = seg_start + int(i * chunk * FPS)
        t_end = seg_start + int((i + 1) * chunk * FPS)
        mark = "✅" if opt.get("correct") else "❌"
        reason = opt.get("reason", "")
        entries.append({
            "time": _time_range(t_start, t_end),
            "visual": f"选项 {opt['label']}：「{opt['statement']}」→ {mark}",
            "animation": (f"选项框从左侧滑入（弹性效果），"
                          f"判定标记{mark}从右侧飞入并放大，"
                          f"下方展开解析文字：{reason[:30]}…" if reason
                          else f"选项框从左侧滑入，判定标记{mark}弹出")
        })

    narration_parts = []
    for opt in options:
        mark = "正确" if opt.get("correct") else "错误"
        narration_parts.append(f"{opt['label']}选项{mark}：{opt.get('reason', '')}")
    narration = "逐一分析选项。" + "。".join(narration_parts) + "。"

    return {"entries": entries, "narration": narration}


def _tmpl_answer_confirmation(params: dict, seg_start: int, seg_end: int) -> dict:
    """答案确认模板 (10秒)"""
    answer = params.get("answer", "")
    formula = params.get("formula", "")
    total = 10

    entries = [
        {
            "time": _time_range(_frame_of(0, seg_start), _frame_of(4, seg_start)),
            "visual": f"正确答案「{answer}」在画面中央放大显示，绿色高亮",
            "animation": "答案从中央弹出（缩放0→1.2→1，弹性效果），周围出现闪光特效"
        },
        {
            "time": _time_range(_frame_of(4, seg_start), _frame_of(7, seg_start)),
            "visual": f"答案下方展开详细解析，结合{formula}说明",
            "animation": "解析框从答案下方伸展出现，文字逐行显示"
        },
        {
            "time": _time_range(_frame_of(7, seg_start), _frame_of(10, seg_start)),
            "visual": "其他选项的错误原因简要列出，形成对比",
            "animation": "错误选项列表从底部淡入，每个带❌标记，颜色偏灰"
        }
    ]

    narration = f"因此正确答案是{answer}。应用公式{formula}可以得出正确结论。"

    return {"entries": entries, "narration": narration}


def _tmpl_formula_summary(params: dict, seg_start: int, seg_end: int) -> dict:
    """总结公式模板 (5秒)"""
    formula = params.get("formula", "")
    concept = params.get("concept", "")
    total = 5

    entries = [
        {
            "time": _time_range(_frame_of(0, seg_start), _frame_of(3, seg_start)),
            "visual": f"核心公式 {formula} 在画面中央放大显示，金色边框高亮",
            "animation": "公式从底部放大弹出（弹性效果，0.8秒），每个变量用不同颜色标注"
        },
        {
            "time": _time_range(_frame_of(3, seg_start), _frame_of(5, seg_start)),
            "visual": f"下方标注：「{concept}」",
            "animation": "标注从公式下方展开，与公式形成完整构图后定格"
        }
    ]

    narration = f"总结核心公式：{formula}。记住{concept}的关键。"

    return {"entries": entries, "narration": narration}


def _tmpl_concept_review(params: dict, seg_start: int, seg_end: int) -> dict:
    """核心概念回顾模板 (10秒)"""
    title = params.get("title", "")
    definition = params.get("definition", "")
    formula = params.get("formula", "")
    total = 10

    entries = [
        {
            "time": _time_range(_frame_of(0, seg_start), _frame_of(3, seg_start)),
            "visual": f"深空背景（紫蓝色星云），中央出现发光天平意象，"
                       f"左托盘放「质量」，右托盘放「重力」",
            "animation": "星云从画面两侧蔓延填充（1.5秒），天平从中央旋转放大出现（弹性效果）"
        },
        {
            "time": _time_range(_frame_of(3, seg_start), _frame_of(7, seg_start)),
            "visual": f"天平下方出现大标题：「{title}」",
            "animation": "标题从天平下方弹出（缩放效果），带有金色光晕"
        },
        {
            "time": _time_range(_frame_of(7, seg_start), _frame_of(10, seg_start)),
            "visual": f"副标题显示核心定义：{definition[:40]}…",
            "animation": "定义文字从底部上浮，逐行显示，字体稍小颜色柔和"
        }
    ]

    narration = f"回顾核心概念：{title}。{definition}。公式{formula}。"

    return {"entries": entries, "narration": narration}


def _tmpl_knowledge_transfer(params: dict, seg_start: int, seg_end: int) -> dict:
    """知识迁移模板 (20秒)"""
    title = params.get("title", "知识拓展")
    misconceptions = params.get("misconceptions", [])
    extension = params.get("extension", "")
    total = 20

    entries = [
        {
            "time": _time_range(_frame_of(0, seg_start), _frame_of(5, seg_start)),
            "visual": f"画面淡入三个关键词框并排：「🔬 科学」「🌍 生活」「🚀 探索」，"
                       f"每个框下方有简短解释",
            "animation": "三个框从画面底部依次上浮（间隔0.4秒），半透明玻璃效果，彩色边框"
        },
        {
            "time": _time_range(_frame_of(5, seg_start), _frame_of(12, seg_start)),
            "visual": f"常见误解辨析：" + "、".join(misconceptions[:2]),
            "animation": "每个误解以卡片形式依次弹出，然后以「纠正」动画翻转显示正确理解"
        },
        {
            "time": _time_range(_frame_of(12, seg_start), _frame_of(16, seg_start)),
            "visual": f"知识扩展：{extension}",
            "animation": "背景出现宇宙星云旋转，扩展文字从中央缓缓浮现"
        },
        {
            "time": _time_range(_frame_of(16, seg_start), _frame_of(20, seg_start)),
            "visual": "画面出现三个星球并排（地球、月球、火星），展示不同环境下的物理规律",
            "animation": "三个星球从中央散开（弹性效果），每个星球下方标注关键数值"
        }
    ]

    narration = (f"知识拓展时间。首先纠正几个常见误解："
                 f"{'，'.join(misconceptions[:2])}。"
                 f"{extension}。物理规律在宇宙中处处适用。")

    return {"entries": entries, "narration": narration}


def _tmpl_final_elevation(params: dict, seg_start: int, seg_end: int) -> dict:
    """升华总结模板 (20秒)"""
    title = params.get("title", "")
    subtitle = params.get("subtitle", "")
    closing_words = params.get("closing_words", "")
    total = 20

    entries = [
        {
            "time": _time_range(_frame_of(0, seg_start), _frame_of(5, seg_start)),
            "visual": "深空背景（绚丽星云，紫蓝金色调），"
                       "画面中央出现一个发光的「∞」符号，缓缓旋转",
            "animation": "「∞」符号从中央旋转放大出现（1.5秒），光带带有粒子拖尾效果，星云加速旋转"
        },
        {
            "time": _time_range(_frame_of(5, seg_start), _frame_of(10, seg_start)),
            "visual": f"画面底部出现一句话总结（大号字体，金色发光）："
                       f"「{closing_words}」",
            "animation": "文字从底部缓缓上浮（1.5秒），金色光晕脉动（周期2秒）"
        },
        {
            "time": _time_range(_frame_of(10, seg_start), _frame_of(15, seg_start)),
            "visual": f"最终标题出现（金色大字）：「{title}」{subtitle}",
            "animation": "标题从中央放大弹出（弹性效果），金色光晕持续脉动"
        },
        {
            "time": _time_range(_frame_of(15, seg_start), _frame_of(20, seg_start)),
            "visual": "最终字幕：「📚 感谢观看 · 探索永不止步」，"
                       "然后画面缓缓淡出到黑屏",
            "animation": "最终字幕从底部上浮（1秒），星光粒子飘落，随后整体淡出（2秒）"
        }
    ]

    narration = (f"最后，让我们站在更高的视角回望。{closing_words}"
                 f"记住{title}，这不仅是一道物理题，"
                 f"更是一种认识世界的思维方式。")

    return {"entries": entries, "narration": narration}


# ==================================================================
#  场景类型到模板的映射
# ==================================================================

SCENE_TEMPLATES = {
    "introduction": _tmpl_introduction,
    "scene_demo_a": _tmpl_scene_demo_a,
    "scene_demo_b": _tmpl_scene_demo_b,
    "comparison": _tmpl_comparison,
    "transition": _tmpl_transition,
    "problem_display": _tmpl_problem_display,
    "scene_analysis": _tmpl_scene_analysis,
    "option_analysis": _tmpl_option_analysis,
    "answer_confirmation": _tmpl_answer_confirmation,
    "formula_summary": _tmpl_formula_summary,
    "concept_review": _tmpl_concept_review,
    "knowledge_transfer": _tmpl_knowledge_transfer,
    "final_elevation": _tmpl_final_elevation,
}


def _get_fallback_template(scene_type: str):
    """当场景类型没有匹配模板时返回兜底模板。"""
    def fallback(params, seg_start, seg_end):
        duration = (seg_end - seg_start) / FPS
        entries = [
            {
                "time": _time_range(seg_start, seg_end),
                "visual": f"场景类型「{scene_type}」的详细展开",
                "animation": f"持续{duration}秒，根据参数自动生成动画"
            }
        ]
        return {"entries": entries, "narration": f"正在展开{scene_type}场景。"}
    return fallback


# ==================================================================
#  核心展开引擎
# ==================================================================

class StoryboardExpander:
    """分镜展开器。"""

    def __init__(self, act_plan: dict):
        self.plan = copy.deepcopy(act_plan)

    def expand(self) -> dict:
        """展开完整分镜脚本。"""
        meta = self.plan.get("meta", {})
        acts = self.plan.get("acts", [])

        expanded_acts = []
        for act in acts:
            expanded_acts.append(self._expand_act(act))

        result = {
            "meta": {
                "topic": meta.get("topic", ""),
                "total_duration_sec": meta.get("total_duration_sec", 0),
                "total_frames": meta.get("total_frames", 0),
                "fps": FPS,
                "visual_theme_name": meta.get("visual_theme_name", ""),
                "layers": ["layer1", "layer2", "layer3"]
            },
            "acts": expanded_acts
        }

        return result

    def _expand_act(self, act: dict) -> dict:
        """展开一幕。"""
        segments = act.get("segments", [])
        expanded_segments = []

        for seg in segments:
            expanded_segments.append(self._expand_segment(seg, act["act_number"]))

        return {
            "act_number": act["act_number"],
            "act_name": act["act_name"],
            "core_task": act.get("core_task", ""),
            "suggested_duration": act.get("suggested_duration", ""),
            "total_duration_sec": act.get("total_duration_sec", 0),
            "total_frames": act.get("total_frames", 0),
            "segments": expanded_segments
        }

    def _expand_segment(self, seg: dict, act_num: int) -> dict:
        """展开一个片段为故事板条目列表。"""
        scene_type = seg.get("scene_type", "")
        params = seg.get("params", {})
        start = seg.get("start_frame", 0)
        end = seg.get("end_frame", 0)

        # 查找匹配的模板函数
        tmpl_func = SCENE_TEMPLATES.get(scene_type, _get_fallback_template(scene_type))
        result = tmpl_func(params, start, end)

        # 注入背景配置和配色方案
        bg_config = seg.get("background_config", {})
        color_scheme = seg.get("color_scheme", {})

        return {
            "id": seg["id"],
            "name": seg["name"],
            "scene_type": scene_type,
            "duration_sec": seg["duration_sec"],
            "start_frame": start,
            "end_frame": end,
            "background": bg_config,
            "color_scheme": color_scheme,
            "components": seg.get("components", []),
            "params": seg.get("params", {}),  # 保留结构化参数供 Layer 4 消费
            "storyboard": result["entries"],
            "narration": result["narration"]
        }


# ==================================================================
#  文本格式输出（设计文档中的自然语言格式）
# ==================================================================

def format_as_text(script: dict) -> str:
    """将分镜脚本格式化为自然语言文本（设计文档风格）。"""
    lines = []

    for act in script["acts"]:
        lines.append(f"🎬 第{act['act_number']}幕：{act['act_name']}"
                      f" —— 「{script['meta']['topic']}」")
        lines.append(f"总时长：{act['total_duration_sec']}秒")
        lines.append(f"核心任务：{act.get('core_task', '')}")
        lines.append("")

        for seg in act["segments"]:
            start_t = _t(seg["start_frame"])
            end_t = _t(seg["end_frame"])
            lines.append(f"📍 片段 {seg['id']}：{seg['name']}（{start_t} - {end_t}）")

            # 表格头
            lines.append(f"{'时间':<16}{'画面内容':<40}{'动画/交互指令'}")
            lines.append("-" * 96)

            for entry in seg["storyboard"]:
                time_str = entry["time"]
                visual = entry["visual"]
                anim = entry["animation"]
                lines.append(f"{time_str:<16}{visual:<40}{anim}")

            lines.append("")
            lines.append(f"配音旁白：「{seg['narration']}」")
            lines.append("")

        lines.append("")

    return "\n".join(lines)


# ==================================================================
#  便捷入口
# ==================================================================

def expand_storyboard(act_plan: dict) -> dict:
    """
    展开幕结构规划为详细分镜脚本。

    参数:
        act_plan: Layer 2 输出的幕结构规划 JSON

    返回:
        分镜脚本 JSON（结构化）
    """
    expander = StoryboardExpander(act_plan)
    return expander.expand()


def expand_storyboard_to_text(act_plan: dict) -> str:
    """
    展开幕结构规划为自然语言格式的分镜脚本文本。

    参数:
        act_plan: Layer 2 输出的幕结构规划 JSON

    返回:
        分镜脚本文本（设计文档风格）
    """
    script = expand_storyboard(act_plan)
    return format_as_text(script)


def save_storyboard(act_plan: dict, json_path: str = None,
                    text_path: str = None) -> dict:
    """
    展开并保存分镜脚本（JSON + 文本）。

    参数:
        act_plan: Layer 2 输出的幕结构规划
        json_path: 可选的 JSON 输出路径
        text_path: 可选的文本输出路径

    返回:
        分镜脚本 dict
    """
    script = expand_storyboard(act_plan)

    if json_path:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        print(f"分镜脚本 JSON 已保存: {json_path}")

    if text_path:
        text = format_as_text(script)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"分镜脚本文本已保存: {text_path}")

    return script


# ==================================================================
#  自测
# ==================================================================

if __name__ == "__main__":
    # 加载 Layer 2 示例输出
    from pathlib import Path
    import sys
    ROOT = Path(__file__).resolve().parent.parent
    DATA_DIR = ROOT / "data"
    DATA_DIR.mkdir(exist_ok=True)

    input_path = str(DATA_DIR / "layer2_sample_output.json")
    if len(sys.argv) > 1:
        input_path = sys.argv[1]

    with open(input_path, "r", encoding="utf-8") as f:
        act_plan = json.load(f)

    # 展开分镜脚本
    script = expand_storyboard(act_plan)

    # 输出文本格式
    text = format_as_text(script)

    # 保存
    json_out = str(DATA_DIR / "layer3_sample_storyboard.json")
    txt_out = str(DATA_DIR / "layer3_sample_storyboard.txt")
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    with open(txt_out, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"分镜脚本已生成:")
    print(f"  JSON: {json_out}")
    print(f"  TEXT: {txt_out}")
    print()
    print(f"=== 结构概要 ===")
    print(f"主题: {script['meta']['topic']}")
    print(f"总时长: {script['meta']['total_duration_sec']}秒")
    for act in script["acts"]:
        total_entries = sum(len(s["storyboard"]) for s in act["segments"])
        print(f"  第{act['act_number']}幕: {act['act_name']} "
              f"({len(act['segments'])}片段, {total_entries}条故事板条目)")
    print()
    # 输出第一幕前几个条目作为预览
    print("=== 第一幕预览 ===")
    first_act = script["acts"][0]
    for seg in first_act["segments"][:2]:
        print(f"\n  📍 {seg['name']} ({seg['duration_sec']}秒):")
        for entry in seg["storyboard"][:2]:
            print(f"    [{entry['time']}] {entry['visual'][:50]}…")
        print(f"    🎙️ {seg['narration'][:60]}…")
