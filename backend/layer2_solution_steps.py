"""
Layer 2.5 — 解题步骤生成器
============================================================
职责：将 Layer 1 的结构化分析结果，转为线性的解题步骤。
      每步包含：标题、说明、公式、动画提示、旁白。

位置：Layer 2（幕结构）→ Layer 2.5（解题步骤）→ Layer 3（分镜）

使用方式：
    from layer2_solution_steps import generate_solution_steps
    steps = generate_solution_steps(layer1_result)
"""

import copy
import json
from typing import Optional


# ==================================================================
#  解题步骤模板库（按主题 + 答案模式匹配）
# ==================================================================

# 每个模板是一个 dict，包含：
#   match: 匹配条件函数 (topic, answer, options) → bool
#   steps: 步骤列表生成函数 → [Step, ...]
#   method: 解题方法名称

# 通用步骤结构：
#   {
#       "step_number": int,
#       "title": str,
#       "content": str,
#       "formula": str,
#       "step_type": str,
#       "animation_hint": str,
#       "narration": str,
#       "duration_sec": int
#   }


def _steps_quality_gravity(layer1: dict) -> dict:
    """质量与重力的区别→解题步骤。"""
    opts = layer1.get("options_analysis", [])
    answer = layer1.get("answer", "")
    concept = layer1.get("core_concept", {})
    formula = concept.get("key_formula", "G = mg")
    scenes = layer1.get("scenario_analysis", {}).get("scenes", [])

    # 确定哪个选项是正确来分析
    correct_opt = None
    for o in opts:
        if o.get("correct"):
            correct_opt = o
            break

    g_earth = "9.8 m/s²"
    g_moon = "1.6 m/s²"

    steps = [
        {
            "step_number": 1,
            "title": "明确质量和重力的本质区别",
            "content": "质量是物体的固有属性，不随位置改变。"
                       "重力是物体在星球上受到的引力，由 G=mg 决定。",
            "formula": "",
            "step_type": "concept_clarification",
            "animation_hint": "分屏展示「质量不变，重力随g变化」",
            "narration": "首先明确一个核心概念：质量是物体的固有属性，"
                         "无论在哪个星球都不会改变。而重力则不同，"
                         "它由公式 G=mg 决定，随重力加速度 g 的变化而变化。",
            "duration_sec": 10
        },
        {
            "step_number": 2,
            "title": "比较地球和月球的g值",
            "content": f"地球表面 g = {g_earth}，"
                       f"月球表面 g ≈ {g_moon}（约为地球的1/6）。"
                       f"同一物体在月球上的重力只有地球上的1/6。",
            "formula": formula,
            "step_type": "formula_application",
            "animation_hint": f"展示两地g值对比：{g_earth} vs {g_moon}",
            "narration": f"地球表面的重力加速度是{g_earth}，"
                         f"而月球表面只有约{g_moon}，约为地球的六分之一。"
                         f"根据公式 G=mg，质量不变时，重力与g值成正比。",
            "duration_sec": 10
        },
        {
            "step_number": 3,
            "title": "逐一分析选项",
            "content": "",
            "formula": "",
            "step_type": "option_analysis",
            "animation_hint": "每个选项依次展开分析",
            "narration": "现在我们来逐一分析每个选项。",
            "duration_sec": 5
        }
    ]

    # 为每个选项生成子步骤
    for i, opt in enumerate(opts):
        mark = "正确" if opt.get("correct") else "错误"
        steps.append({
            "step_number": 3 + i + 1,
            "title": f"选项{opt['label']}：{'✅' if opt.get('correct') else '❌'} {opt.get('statement', '')[:25]}",
            "content": opt.get("reason", ""),
            "formula": formula if opt.get("correct") else "",
            "step_type": "option_check",
            "animation_hint": f"显示选项{opt['label']}，{'打勾' if opt.get('correct') else '打叉'}",
            "narration": f"选项{opt['label']}：{opt.get('statement', '')}——"
                         f"这个选项是{mark}的。"
                         f"原因是：{opt.get('reason', '')}",
            "duration_sec": 8
        })

    # 总结步骤
    conclusion = ""
    if correct_opt:
        conclusion = (f"因此答案为{correct_opt['label']}。"
                      f"{correct_opt.get('reason', '')}")

    steps.append({
        "step_number": len(opts) + 4,
        "title": f"得出结论：答案 {answer}",
        "content": conclusion,
        "formula": formula,
        "step_type": "conclusion",
        "animation_hint": f"答案{answer}放大高亮，显示推理总结",
        "narration": f"综上，正确答案是{answer}。{conclusion}",
        "duration_sec": 8
    })

    return {"steps": steps, "method": "概念辨析法",
            "approach": "先明确核心概念，再应用公式G=mg，逐一排除错误选项"}


def _steps_newton_law(layer1: dict) -> dict:
    """牛顿运动定律→解题步骤。"""
    opts = layer1.get("options_analysis", [])
    answer = layer1.get("answer", "")
    concept = layer1.get("core_concept", {})
    formula = concept.get("key_formula", "F = ma")

    steps = [
        {
            "step_number": 1,
            "title": "分析物体受力情况",
            "content": "明确物体受到哪些力：重力、支持力、摩擦力、外力等。",
            "formula": "",
            "step_type": "concept_clarification",
            "animation_hint": "画出物体的受力分析图，各力用箭头标注",
            "narration": "第一步，对物体进行受力分析。"
                         "明确物体受到的所有力，包括方向和作用点。",
            "duration_sec": 10
        },
        {
            "step_number": 2,
            "title": "应用牛顿第二定律 F=ma",
            "content": "合外力 = 质量 × 加速度。"
                       "先求合力，再求加速度。",
            "formula": formula,
            "step_type": "formula_application",
            "animation_hint": "显示公式 F=ma，各变量依次高亮",
            "narration": f"根据牛顿第二定律 F=ma，"
                         f"物体所受合外力等于质量乘以加速度。",
            "duration_sec": 8
        },
        {
            "step_number": 3,
            "title": "逐项判断选项",
            "content": "",
            "formula": formula,
            "step_type": "option_analysis",
            "animation_hint": "显示各选项及判断",
            "narration": "现在逐一分析每个选项。",
            "duration_sec": 5
        }
    ]

    for i, opt in enumerate(opts):
        mark = "正确" if opt.get("correct") else "错误"
        steps.append({
            "step_number": 4 + i,
            "title": f"选项{opt['label']}：{'✅' if opt.get('correct') else '❌'}",
            "content": opt.get("reason", ""),
            "formula": formula if opt.get("correct") else "",
            "step_type": "option_check",
            "animation_hint": f"选项{opt['label']}判断",
            "narration": f"选项{opt['label']}：{opt.get('statement', '')}"
                         f"——{mark}。{opt.get('reason', '')}",
            "duration_sec": 8
        })

    steps.append({
        "step_number": len(opts) + 4,
        "title": f"答案确认：{answer}",
        "content": f"综合以上分析，正确答案是{answer}。",
        "formula": formula,
        "step_type": "conclusion",
        "animation_hint": f"答案{answer}高亮显示",
        "narration": f"因此正确答案是{answer}。",
        "duration_sec": 5
    })

    return {"steps": steps, "method": "受力分析法",
            "approach": "先受力分析→再应用F=ma→判断各选项"}


def _steps_circular_motion(layer1: dict) -> dict:
    """匀速圆周运动→解题步骤。"""
    opts = layer1.get("options_analysis", [])
    answer = layer1.get("answer", "")
    concept = layer1.get("core_concept", {})
    formula = concept.get("key_formula", "F = mv²/r")

    steps = [
        {
            "step_number": 1,
            "title": "明确圆周运动的特点",
            "content": "匀速圆周运动的速度大小不变、方向不断改变，"
                       "因此需要向心力维持。合力不为零。",
            "formula": "",
            "step_type": "concept_clarification",
            "animation_hint": "展示圆周运动轨迹，速度方向变化动画",
            "narration": "匀速圆周运动有一个关键点：速度方向时刻在变，"
                         "所以物体一定有加速度，合力一定不为零。",
            "duration_sec": 8
        },
        {
            "step_number": 2,
            "title": "应用向心力公式",
            "content": "向心力 F = mv²/r = mω²r，"
                       "由真实力的合力提供（不是独立力）。",
            "formula": formula,
            "step_type": "formula_application",
            "animation_hint": "向心力公式展开，标出各变量含义",
            "narration": f"向心力由公式 {formula} 给出，"
                         f"它是由其他力的合力提供的效果力。",
            "duration_sec": 8
        },
        {
            "step_number": 3,
            "title": "分析各选项",
            "content": "",
            "formula": formula,
            "step_type": "option_analysis",
            "animation_hint": "显示选项列表",
            "narration": "根据以上知识分析各选项。",
            "duration_sec": 5
        }
    ]

    for i, opt in enumerate(opts):
        mark = "正确" if opt.get("correct") else "错误"
        steps.append({
            "step_number": 4 + i,
            "title": f"选项{opt['label']}：{'✅' if opt.get('correct') else '❌'}",
            "content": opt.get("reason", ""),
            "formula": formula if opt.get("correct") else "",
            "step_type": "option_check",
            "animation_hint": f"选项{opt['label']}判断",
            "narration": f"选项{opt['label']}：{opt.get('statement', '')}——"
                         f"{mark}。{opt.get('reason', '')}",
            "duration_sec": 8
        })

    steps.append({
        "step_number": len(opts) + 4,
        "title": f"答案：{answer}",
        "content": f"正确答案是{answer}。",
        "formula": formula,
        "step_type": "conclusion",
        "animation_hint": f"答案{answer}放大显示",
        "narration": f"因此正确答案是{answer}。",
        "duration_sec": 5
    })

    return {"steps": steps, "method": "圆周运动分析法",
            "approach": "明确圆周运动特性→向心力公式→逐项判断"}


def _steps_electricity(layer1: dict) -> dict:
    """欧姆定律与电路→解题步骤。"""
    opts = layer1.get("options_analysis", [])
    answer = layer1.get("answer", "")
    concept = layer1.get("core_concept", {})
    formula = concept.get("key_formula", "I = U/R")

    steps = [
        {
            "step_number": 1,
            "title": "分析电路连接方式",
            "content": "判断电阻是串联还是并联，明确总电阻计算方法。",
            "formula": "R_总 = R₁ + R₂ (串联)",
            "step_type": "concept_clarification",
            "animation_hint": "画出电路图，标注电阻连接方式",
            "narration": "首先分析电路的连接方式，"
                         "串联还是并联决定了总电阻的计算方法。",
            "duration_sec": 8
        },
        {
            "step_number": 2,
            "title": "应用欧姆定律 I=U/R",
            "content": "根据总电压和总电阻计算干路电流。",
            "formula": formula,
            "step_type": "formula_application",
            "animation_hint": "电路中依次高亮电压、电阻、电流",
            "narration": f"根据欧姆定律 I=U/R，"
                         f"用总电压除以总电阻得到电流。",
            "duration_sec": 8
        },
        {
            "step_number": 3,
            "title": "判断各选项",
            "content": "",
            "formula": formula,
            "step_type": "option_analysis",
            "animation_hint": "显示选项",
            "narration": "逐个判断选项。",
            "duration_sec": 5
        }
    ]

    for i, opt in enumerate(opts):
        mark = "正确" if opt.get("correct") else "错误"
        steps.append({
            "step_number": 4 + i,
            "title": f"选项{opt['label']}：{'✅' if opt.get('correct') else '❌'}",
            "content": opt.get("reason", ""),
            "formula": formula if opt.get("correct") else "",
            "step_type": "option_check",
            "animation_hint": f"选项{opt['label']}判断",
            "narration": f"选项{opt['label']}：{opt.get('statement', '')}——"
                         f"{mark}。{opt.get('reason', '')}",
            "duration_sec": 8
        })

    steps.append({
        "step_number": len(opts) + 4,
        "title": f"结论：{answer}",
        "content": f"正确答案是{answer}。",
        "formula": formula,
        "step_type": "conclusion",
        "animation_hint": f"答案{answer}放大",
        "narration": f"因此正确答案是{answer}。",
        "duration_sec": 5
    })

    return {"steps": steps, "method": "电路分析法",
            "approach": "分析电路→欧姆定律→逐项判断"}


def _steps_energy(layer1: dict) -> dict:
    """能量与功→解题步骤。"""
    opts = layer1.get("options_analysis", [])
    answer = layer1.get("answer", "")
    concept = layer1.get("core_concept", {})
    formula = concept.get("key_formula", "W = ΔEk")

    steps = [
        {
            "step_number": 1,
            "title": "明确能量转化路径",
            "content": "分析题目中涉及的能量形式：动能、势能、内能等，"
                       "以及它们之间的转化关系。",
            "formula": "",
            "step_type": "concept_clarification",
            "animation_hint": "展示能量转化流程图",
            "narration": "首先分析题目中的能量转化路径。",
            "duration_sec": 8
        },
        {
            "step_number": 2,
            "title": "应用能量守恒/动能定理",
            "content": "W = ΔEk，或机械能守恒：ΔE = 0。",
            "formula": formula,
            "step_type": "formula_application",
            "animation_hint": "显示公式和守恒条件",
            "narration": f"根据{formula}分析能量变化。",
            "duration_sec": 8
        },
        {
            "step_number": 3,
            "title": "判断选项",
            "content": "",
            "formula": formula,
            "step_type": "option_analysis",
            "animation_hint": "逐项显示选项",
            "narration": "分析各选项。",
            "duration_sec": 5
        }
    ]

    for i, opt in enumerate(opts):
        mark = "正确" if opt.get("correct") else "错误"
        steps.append({
            "step_number": 4 + i,
            "title": f"选项{opt['label']}：{'✅' if opt.get('correct') else '❌'}",
            "content": opt.get("reason", ""),
            "formula": formula if opt.get("correct") else "",
            "step_type": "option_check",
            "animation_hint": f"选项{opt['label']}判断",
            "narration": f"选项{opt['label']}——{mark}。{opt.get('reason', '')}",
            "duration_sec": 8
        })

    steps.append({
        "step_number": len(opts) + 4,
        "title": f"结论：{answer}",
        "content": f"正确答案是{answer}。",
        "formula": formula,
        "step_type": "conclusion",
        "animation_hint": f"答案{answer}高亮",
        "narration": f"因此正确答案是{answer}。",
        "duration_sec": 5
    })

    return {"steps": steps, "method": "能量分析法",
            "approach": "能量转化分析→应用定理→判断选项"}


def _steps_momentum(layer1: dict) -> dict:
    """动量与碰撞→解题步骤。"""
    opts = layer1.get("options_analysis", [])
    answer = layer1.get("answer", "")
    concept = layer1.get("core_concept", {})
    formula = concept.get("key_formula", "p = mv")

    steps = [
        {
            "step_number": 1,
            "title": "明确系统与守恒条件",
            "content": "判断系统是否满足动量守恒条件：合外力为零。",
            "formula": "",
            "step_type": "concept_clarification",
            "animation_hint": "圈出系统边界，标注外力",
            "narration": "第一步判断系统动量是否守恒。",
            "duration_sec": 8
        },
        {
            "step_number": 2,
            "title": "应用动量守恒/动量定理",
            "content": "碰撞前后动量守恒，或 Ft = Δp。",
            "formula": formula,
            "step_type": "formula_application",
            "animation_hint": "显示动量和冲量公式",
            "narration": f"根据公式 {formula} 分析。",
            "duration_sec": 8
        },
        {
            "step_number": 3,
            "title": "逐一判断选项",
            "content": "",
            "formula": formula,
            "step_type": "option_analysis",
            "animation_hint": "显示选项",
            "narration": "分析各选项。",
            "duration_sec": 5
        }
    ]

    for i, opt in enumerate(opts):
        mark = "正确" if opt.get("correct") else "错误"
        steps.append({
            "step_number": 4 + i,
            "title": f"选项{opt['label']}：{'✅' if opt.get('correct') else '❌'}",
            "content": opt.get("reason", ""),
            "formula": formula if opt.get("correct") else "",
            "step_type": "option_check",
            "animation_hint": f"选项{opt['label']}判断",
            "narration": f"选项{opt['label']}——{mark}。{opt.get('reason', '')}",
            "duration_sec": 8
        })

    steps.append({
        "step_number": len(opts) + 4,
        "title": f"结论：{answer}",
        "content": f"正确答案是{answer}。",
        "formula": formula,
        "step_type": "conclusion",
        "animation_hint": f"答案{answer}高亮",
        "narration": f"因此正确答案是{answer}。",
        "duration_sec": 5
    })

    return {"steps": steps, "method": "动量分析法",
            "approach": "判断守恒条件→应用公式→逐项判断"}


# 通用兜底模板（当没有匹配的特定主题时）
def _steps_generic(layer1: dict) -> dict:
    """通用解题步骤。"""
    opts = layer1.get("options_analysis", [])
    answer = layer1.get("answer", "")
    concept = layer1.get("core_concept", {})
    formula = concept.get("key_formula", "")

    steps = [
        {
            "step_number": 1,
            "title": "理解题目考查的核心概念",
            "content": f"本题主要考查：{concept.get('name', '物理概念')}。"
                       f"{concept.get('definition', '')}",
            "formula": "",
            "step_type": "concept_clarification",
            "animation_hint": "显示核心概念定义",
            "narration": f"这道题主要考查{concept.get('name', '物理概念')}。"
                         f"{concept.get('definition', '')}",
            "duration_sec": 8
        }
    ]

    if formula:
        steps.append({
            "step_number": 2,
            "title": "应用核心公式",
            "content": f"需要使用的公式：{formula}",
            "formula": formula,
            "step_type": "formula_application",
            "animation_hint": f"显示公式 {formula}",
            "narration": f"核心公式是：{formula}。",
            "duration_sec": 6
        })

    steps.append({
        "step_number": 3,
        "title": "逐项分析选项",
        "content": "",
        "formula": formula,
        "step_type": "option_analysis",
        "animation_hint": "逐个显示选项",
        "narration": "下面逐一分析。",
        "duration_sec": 4
    })

    for i, opt in enumerate(opts):
        mark = "正确" if opt.get("correct") else "错误"
        steps.append({
            "step_number": 4 + i,
            "title": f"选项{opt['label']}：{'✅' if opt.get('correct') else '❌'}",
            "content": opt.get("reason", ""),
            "formula": formula,
            "step_type": "option_check",
            "animation_hint": f"选项{opt['label']}判断",
            "narration": f"选项{opt['label']}——{mark}。{opt.get('reason', '')}",
            "duration_sec": 8
        })

    steps.append({
        "step_number": len(opts) + 4,
        "title": f"答案：{answer}",
        "content": f"正确答案是{answer}。",
        "formula": formula,
        "step_type": "conclusion",
        "animation_hint": f"答案{answer}高亮",
        "narration": f"因此正确答案是{answer}。",
        "duration_sec": 5
    })

    return {"steps": steps, "method": "通用分析法",
            "approach": "理解概念→应用公式→逐项判断"}


# ==================================================================
#  主题到步骤模板的映射
# ==================================================================

TOPIC_STEP_MAP = {
    "quality_gravity": _steps_quality_gravity,
    "newton_law": _steps_newton_law,
    "circular_motion": _steps_circular_motion,
    "energy": _steps_energy,
    "electricity": _steps_electricity,
    "momentum": _steps_momentum,
}


# ==================================================================
#  主入口
# ==================================================================

def generate_solution_steps(layer1_result: dict) -> dict:
    """
    从 Layer 1 的结构化分析结果生成解题步骤。

    参数:
        layer1_result: Layer 1 输出的结构化分析 dict

    返回:
        {
            "steps": [Step, ...],      # 解题步骤列表
            "method": str,             # 解题方法名称
            "approach": str,           # 解题思路描述
            "total_steps": int,        # 总步数
            "total_duration_sec": int  # 建议总时长
        }
    """
    # 从 core_concept 推断主题 ID
    topic_id = _detect_topic_id(layer1_result)

    # 获取对应的步骤生成函数
    step_func = TOPIC_STEP_MAP.get(topic_id, _steps_generic)

    # 生成步骤
    result = step_func(layer1_result)

    # 计算总时长和步数
    result["total_steps"] = len(result["steps"])
    result["total_duration_sec"] = sum(s["duration_sec"] for s in result["steps"])

    return result


def _detect_topic_id(layer1: dict) -> Optional[str]:
    """从 Layer 1 结果推断物理主题 ID。"""
    # 先从 confidence 里找
    conf = layer1.get("confidence", {})
    td = conf.get("topic_detection", {})
    primary = td.get("primary")
    if primary and primary in TOPIC_STEP_MAP:
        return primary

    # 再从 topic 名称反向匹配
    topic_name = layer1.get("topic", "")
    for tid, t in _get_topic_name_map().items():
        if t == topic_name:
            return tid

    # 最后尝试关键词匹配
    text = f"{topic_name} {_collect_concept_text(layer1)}"
    for tid, func in TOPIC_STEP_MAP.items():
        from layer1_agent import PHYSICS_TOPICS
        if tid in PHYSICS_TOPICS:
            for kw in PHYSICS_TOPICS[tid]["keywords"]:
                if kw in text:
                    return tid

    return None


def _get_topic_name_map() -> dict:
    """获取主题 ID → 名称 映射。"""
    try:
        from layer1_agent import PHYSICS_TOPICS
        return {tid: t["concept_name"] for tid, t in PHYSICS_TOPICS.items()}
    except ImportError:
        return {}


def _collect_concept_text(layer1: dict) -> str:
    """收集 Layer 1 中的关键文本用于主题匹配。"""
    texts = []
    cc = layer1.get("core_concept", {})
    if cc.get("name"):
        texts.append(cc["name"])
    if cc.get("definition"):
        texts.append(cc["definition"])
    sa = layer1.get("scenario_analysis", {})
    for s in sa.get("scenes", []):
        if s.get("name"):
            texts.append(s["name"])
    return " ".join(texts)


def solution_steps_to_text(solution: dict) -> str:
    """将解题步骤格式化为可读文本。"""
    lines = []
    lines.append(f"解题方法：{solution.get('method', '通用')}")
    lines.append(f"解题思路：{solution.get('approach', '')}")
    lines.append(f"共 {solution['total_steps']} 步，"
                 f"约 {solution['total_duration_sec']} 秒")
    lines.append("")

    for step in solution["steps"]:
        lines.append(f"步骤{step['step_number']}：{step['title']}")
        if step.get("formula"):
            lines.append(f"  公式：{step['formula']}")
        lines.append(f"  说明：{step['content']}")
        lines.append(f"  动画：{step.get('animation_hint', '')}")
        lines.append(f"  旁白：{step.get('narration', '')}")
        lines.append(f"  时长：{step['duration_sec']}秒")
        lines.append("")

    return "\n".join(lines)


# ==================================================================
#  自测
# ==================================================================

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    # 加载 Layer 1 示例输出
    test_text = {
        "topic": "质量与重力的区别",
        "subject": "物理",
        "question_type": "选择题",
        "core_concept": {
            "name": "质量与重力的区别",
            "definition": "质量是物体固有属性，不随位置改变；"
                          "重力是万有引力的表现，G=mg，随g值改变",
            "key_formula": "G = mg"
        },
        "scenario_analysis": {
            "context": "嫦娥六号月背采样返回",
            "key_conditions": "月球g值约为地球的1/6",
            "scenes": [
                {"name": "地球表面", "motion": "静止", "force": "受重力"},
                {"name": "月球表面", "motion": "静止", "force": "受重力"}
            ]
        },
        "options_analysis": [
            {"label": "A", "statement": "环月飞行时样品合力为零",
             "correct": False,
             "reason": "匀速圆周运动需要向心力，合力不为零"},
            {"label": "B", "statement": "样品在月球正面时对月面压力为零",
             "correct": False,
             "reason": "样品受重力，对月面压力等于重力"},
            {"label": "C", "statement": "引力不同所以质量也不同",
             "correct": False,
             "reason": "质量是固有属性，不随引力变化"},
            {"label": "D", "statement": "月球表面对月球的压力比地球表面时小",
             "correct": True,
             "reason": "F压=G=mg，月球g是地球的1/6，所以压力也是1/6"}
        ],
        "answer": "D"
    }

    solution = generate_solution_steps(test_text)
    text = solution_steps_to_text(solution)
    print(text)
    print("=" * 40)
    print(f"生成 {solution['total_steps']} 步解题步骤，"
          f"总时长 {solution['total_duration_sec']} 秒")
