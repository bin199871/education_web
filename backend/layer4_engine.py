"""
Layer 4 — HTML编排引擎 (Timeline Orchestrator)
=================================================
职责：将 Layer 3 的分镜脚本 (storyboard JSON) 转换为 timeline JSON，
      供 engine.js + components.js 渲染为 HTML 动画。

使用方式：
    from layer4_engine import orchestrate
    timeline = orchestrate(storyboard)
    # timeline 可直接 json.dump 到 timeline.json

编排 JSON 结构（engine.js 消费格式）：
    {
      "meta": { "totalFrames", "fps", "width", "height", "title" },
      "timeline": [
        {
          "id", "name",
          "startFrame", "endFrame",
          "background": { "type": ..., "component": ..., "params": ... },
          "transition_in": { "duration", "easing" },
          "transition": { "duration", "easing" },
          "layers": [ { "component": "drawXxx", "params": {...} }, ... ]
        }
      ]
    }
"""

import json
import math
import copy
from physics_simulator import simulate_slope_problem
from physics_param_extractor import run_simulation_from_text

FPS = 60
CANVAS_W = 960
CANVAS_H = 640
CENTER_X = CANVAS_W // 2
CENTER_Y = CANVAS_H // 2


# ==================================================================
#  工具函数
# ==================================================================

def _clamp(v, lo=0, hi=1):
    return max(lo, min(hi, v))


def _lerp(a, b, t):
    return a + (b - a) * t


def _make_animate(from_val, to_val, duration=30, delay=0, easing="easeOut"):
    """生成 engine.js 动画参数字段。"""
    return {"animate": {"from": from_val, "to": to_val,
                        "duration": duration, "delay": delay, "easing": easing}}


def _make_sin(amplitude, period=60, center=0, offset=0):
    """生成正弦波动参数字段。"""
    return {"type": "sin", "amplitude": amplitude, "period": period,
            "center": center, "offset": offset}


def _frame(sec: int, seg_start: int = 0) -> int:
    """将秒转换为帧号（相对 seg_start 偏移）。"""
    return seg_start + sec * FPS


def _seg_duration_frames(seg: dict) -> int:
    return seg["end_frame"] - seg["start_frame"]


def _seg_duration_sec(seg: dict) -> int:
    return max(1, round(_seg_duration_frames(seg) / FPS))


# ==================================================================
#  场景渲染器
#    每个 render_xxx(seg, cw, ch) -> list[dict]
#    返回该片段中所有 layer 的定义。
# ==================================================================


def render_introduction(seg, cw, ch):
    """开场引入：深空背景 + 旋转立方体 + 打字标题 + 概念标签。"""
    params = seg.get("params", {})
    title = params.get("title", "核心概念")
    subtitle = params.get("subtitle", "")
    cube_label = params.get("cube_label", "🔬")
    labels = params.get("concept_labels", [])
    s = seg["start_frame"]
    layers = []

    # 立方体（中央，带缓慢自转）
    layers.append({
        "component": "drawCube",
        "params": {
            "cx": CENTER_X, "cy": CENTER_Y - 30,
            "size": 90,
            "rotX": _make_sin(0.3, 180, center=0.5),
            "rotY": _make_sin(0.4, 240, center=0.8),
            "color": "#88bbdd",
            "label": cube_label,
        }
    })

    # 概念标签（从两侧生长）
    for i, lbl in enumerate(labels[:2]):
        side = -1 if i == 0 else 1
        delay_f = 3 * FPS
        layers.append({
            "component": "drawPopupLabel",
            "params": {
                "cx": CENTER_X + side * 200,
                "cy": CENTER_Y - 30,
                "width": 140, "height": 44,
                "text": lbl.get("text", ""),
                "textColor": "#ffffff",
                "bgColor": lbl.get("color", "#333"),
                "popStartFrame": s + delay_f,
                "popDuration": 20,
            }
        })

    # 副标题（底部打字）
    if subtitle:
        layers.append({
            "component": "drawTypewriterText",
            "params": {
                "cx": CENTER_X, "cy": ch - 60,
                "text": subtitle,
                "startFrame": s + 5 * FPS,
                "charsPerSecond": 8,
                "color": "#ffffff",
                "font": "22px sans-serif",
            }
        })

    return layers


def render_scene_demo(seg, cw, ch):
    """场景演示：地球/月球背景 + 天平(左) + 弹簧秤(右) + 标注。"""
    params = seg.get("params", {})
    scene_label = params.get("scene_label", "场景")
    balance_label = params.get("balance_label", "⚖️ 质量 = 1.0 kg")
    spring_label = params.get("spring_label", "📏 重力 = 9.8 N")
    g_value = params.get("g_value", "g = 9.8 m/s²")
    s = seg["start_frame"]
    layers = []

    # 天平（左半，相对于 cx=280, cy=380）
    layers.append({
        "component": "drawBalance",
        "params": {
            "cx": 280, "cy": 380,
            "scale": 0.75,
            "weight": 1.0,
            "label": balance_label,
            "highlight": True,
        }
    })

    # 弹簧秤（右半，相对于 cx=680, cy=380）
    weight_val = 9.8 if "9.8" in g_value else 1.6
    layers.append({
        "component": "drawSpringScale",
        "params": {
            "cx": 680, "cy": 380,
            "scale": 0.75,
            "weight": weight_val,
            "label": spring_label,
            "highlight": True,
        }
    })

    # g 值标注（底部浮动）
    layers.append({
        "component": "floatUpText",
        "params": {
            "cx": CENTER_X, "cy": ch - 40,
            "targetY": ch - 60,
            "text": scene_label + " " + g_value,
            "color": "#FFD54F",
            "font": "20px sans-serif",
            "startFrame": s + 16 * FPS,
            "floatDuration": 25,
            "stayDuration": _seg_duration_frames(seg),
        }
    })

    # 场景标识（左上角）
    layers.append({
        "component": "sceneLabel",
        "params": {
            "cx": 80, "cy": 30,
            "text": scene_label,
            "color": "#ffffff",
            "bgColor": "rgba(0,0,0,0.5)",
            "fontSize": 14,
        }
    })

    return layers


def render_comparison(seg, cw, ch):
    """对比结论：分屏 + 核心结论 + 公式。"""
    params = seg.get("params", {})
    conclusions = params.get("conclusions", [])
    formula = params.get("formula", "")
    final_line = params.get("final_line", "")
    s = seg["start_frame"]
    layers = []

    # 分屏分割线
    layers.append({
        "component": "drawSplitScreenDivider",
        "params": {"splitX": CENTER_X}
    })

    # 左侧场景标识
    layers.append({
        "component": "sceneLabel",
        "params": {
            "cx": CENTER_X // 2, "cy": 30,
            "text": "🌍 地球",
            "color": "#81C784",
            "fontSize": 14,
        }
    })

    # 右侧场景标识
    layers.append({
        "component": "sceneLabel",
        "params": {
            "cx": CENTER_X + CENTER_X // 2, "cy": 30,
            "text": "🌙 月球",
            "color": "#FFB74D",
            "fontSize": 14,
        }
    })

    # 核心结论（逐行弹出）
    for i, c in enumerate(conclusions[:3]):
        y_offset = ch // 2 - 40 + i * 50
        color = "#4CAF50" if "不变" in c.get("text", "") else "#FF9800"
        layers.append({
            "component": "drawPopupLabel",
            "params": {
                "cx": CENTER_X, "cy": y_offset,
                "width": 360, "height": 40,
                "text": c.get("text", ""),
                "textColor": color,
                "bgColor": "rgba(0,0,0,0.7)",
                "borderColor": color,
                "popStartFrame": s + 5 * FPS + i * 15,
                "popDuration": 18,
            }
        })

    # 公式
    if formula:
        layers.append({
            "component": "drawTypewriterText",
            "params": {
                "cx": CENTER_X, "cy": ch - 100,
                "text": "核心公式: " + formula,
                "startFrame": s + 12 * FPS,
                "charsPerSecond": 6,
                "color": "#FFD700",
                "font": "bold 26px sans-serif",
            }
        })

    # 过渡语
    if final_line:
        layers.append({
            "component": "floatUpText",
            "params": {
                "cx": CENTER_X, "cy": ch - 30,
                "targetY": ch - 50,
                "text": final_line,
                "color": "#aaaaaa",
                "font": "16px sans-serif",
                "startFrame": s + 16 * FPS,
                "floatDuration": 20,
            }
        })

    return layers


def render_transition(seg, cw, ch):
    """过渡：流星 + 过渡文字。"""
    params = seg.get("params", {})
    text = params.get("transition_text", "进入下一环节")
    s = seg["start_frame"]
    layers = []

    # 流星
    layers.append({
        "component": "drawMeteor",
        "params": {
            "fromX": cw * 1.2, "fromY": -20,
            "toX": -80, "toY": ch * 0.6,
            "startFrame": s + 2 * FPS,
            "duration": 40,
        }
    })

    # 过渡文字
    layers.append({
        "component": "drawTypewriterText",
        "params": {
            "cx": CENTER_X, "cy": CENTER_Y,
            "text": text,
            "startFrame": s + 5 * FPS,
            "charsPerSecond": 8,
            "color": "#ffffff",
            "font": "bold 28px sans-serif",
        }
    })

    return layers


def render_problem_display(seg, cw, ch):
    """题目展示：试卷风格。"""
    params = seg.get("params", {})
    stem = params.get("stem", "")
    options = params.get("options", [])
    s = seg["start_frame"]
    layers = []

    # 题目标题（左上角）
    layers.append({
        "component": "sceneLabel",
        "params": {
            "cx": 120, "cy": 40,
            "text": "📝 真题演练",
            "color": "#D32F2F",
            "bgColor": "rgba(255,255,255,0.9)",
            "fontSize": 18,
        }
    })

    # 题目内容
    if stem:
        max_chars = 40
        display_text = stem[:max_chars] + ("…" if len(stem) > max_chars else "")
        layers.append({
            "component": "drawTypewriterText",
            "params": {
                "cx": CENTER_X, "cy": 120,
                "text": display_text,
                "startFrame": s + 3 * FPS,
                "charsPerSecond": 12,
                "color": "#1A237E",
                "font": "20px sans-serif",
            }
        })

    # 选项
    for i, opt in enumerate(options[:4]):
        label = opt.get("label", "?")
        text = opt.get("text", opt.get("statement", ""))[:30]
        y_pos = 220 + i * 55
        layers.append({
            "component": "drawTypewriterText",
            "params": {
                "cx": CENTER_X - 200, "cy": y_pos,
                "text": f"{label}. {text}",
                "startFrame": s + (5 + i) * FPS,
                "charsPerSecond": 15,
                "color": "#333333",
                "font": "18px sans-serif",
                "align": "left",
            }
        })

    # 引导思考
    layers.append({
        "component": "floatUpText",
        "params": {
            "cx": CENTER_X, "cy": ch + 20,
            "targetY": ch - 40,
            "text": "🤔 请思考：哪个选项是正确的？",
            "color": "#666",
            "font": "16px sans-serif",
            "startFrame": s + 12 * FPS,
            "floatDuration": 20,
        }
    })

    return layers


def render_scene_analysis(seg, cw, ch):
    """场景/受力分析。"""
    params = seg.get("params", {})
    scene_label = params.get("scene_label", "受力分析")
    concept_note = params.get("concept_note", "")
    scenes = params.get("scenes", [])
    s = seg["start_frame"]
    layers = []

    # 标题
    layers.append({
        "component": "sceneLabel",
        "params": {
            "cx": CENTER_X, "cy": 50,
            "text": f"📍 {scene_label}",
            "color": "#81D4FA",
            "fontSize": 18,
        }
    })

    # 场景列表
    for i, sc in enumerate(scenes[:5]):
        y_pos = 140 + i * 80
        if isinstance(sc, dict):
            sc_name = sc.get("name", f"场景{i+1}")
            sc_desc = sc.get("motion", sc.get("force", ""))[:40]
        else:
            sc_name = str(sc)[:30]
            sc_desc = ""

        layers.append({
            "component": "drawPopupLabel",
            "params": {
                "cx": CENTER_X, "cy": y_pos,
                "width": 500, "height": 50,
                "text": f"{sc_name}: {sc_desc}",
                "textColor": "#E0E0E0",
                "bgColor": "rgba(30,30,60,0.85)",
                "borderColor": "#5C6BC0",
                "popStartFrame": s + 2 * FPS + i * 18,
                "popDuration": 16,
            }
        })

    # 概念标注（底部）
    if concept_note:
        layers.append({
            "component": "floatUpText",
            "params": {
                "cx": CENTER_X, "cy": ch + 20,
                "targetY": ch - 40,
                "text": f"💡 {concept_note}",
                "color": "#FFD54F",
                "font": "18px sans-serif",
                "startFrame": s + 14 * FPS,
                "floatDuration": 20,
            }
        })

    return layers


def render_option_analysis(seg, cw, ch):
    """选项逐个击破。"""
    params = seg.get("params", {})
    options = params.get("options", [])
    s = seg["start_frame"]
    layers = []

    if not options:
        layers.append({
            "component": "drawTypewriterText",
            "params": {
                "cx": CENTER_X, "cy": CENTER_Y,
                "text": "暂无选项数据",
                "startFrame": s,
                "color": "#ffffff",
            }
        })
        return layers

    # 每个选项一个标签框
    per_height = min(90, (ch - 100) // max(len(options), 1))
    start_y = (ch - len(options) * per_height) // 2

    for i, opt in enumerate(options):
        label = opt.get("label", "?")
        statement = opt.get("statement", opt.get("text", ""))[:35]
        correct = opt.get("correct", False)
        reason = opt.get("reason", "")[:40]
        mark = "✅" if correct else "❌"
        color = "#4CAF50" if correct else "#EF5350"
        border = "#4CAF50" if correct else "#EF5350"

        y_pos = start_y + i * per_height
        layers.append({
            "component": "drawPopupLabel",
            "params": {
                "cx": CENTER_X, "cy": y_pos,
                "width": 550, "height": 55,
                "text": f"{mark} {label}. {statement}",
                "textColor": color,
                "bgColor": "rgba(0,0,0,0.7)",
                "borderColor": border,
                "popStartFrame": s + i * 20,
                "popDuration": 14,
            }
        })

        # 原因（小字在下方）
        if reason:
            layers.append({
                "component": "drawTypewriterText",
                "params": {
                    "cx": CENTER_X, "cy": y_pos + 35,
                    "text": reason,
                    "startFrame": s + i * 20 + 10,
                    "charsPerSecond": 15,
                    "color": "#B0BEC5",
                    "font": "14px sans-serif",
                }
            })

    return layers


def render_answer_confirmation(seg, cw, ch):
    """答案确认。"""
    params = seg.get("params", {})
    answer = params.get("answer", "")
    formula = params.get("formula", "")
    s = seg["start_frame"]
    layers = []

    # 正确答案（大号弹出）
    layers.append({
        "component": "drawPopupLabel",
        "params": {
            "cx": CENTER_X, "cy": CENTER_Y - 40,
            "width": 350, "height": 70,
            "text": f"✅ 正确答案: {answer}",
            "textColor": "#4CAF50",
            "bgColor": "rgba(0,40,0,0.85)",
            "borderColor": "#4CAF50",
            "popStartFrame": s,
            "popDuration": 20,
        }
    })

    # 公式说明
    if formula:
        layers.append({
            "component": "drawTypewriterText",
            "params": {
                "cx": CENTER_X, "cy": CENTER_Y + 60,
                "text": f"依据公式: {formula}",
                "startFrame": s + 4 * FPS,
                "charsPerSecond": 8,
                "color": "#FFD700",
                "font": "22px sans-serif",
            }
        })

    return layers


def render_formula_summary(seg, cw, ch):
    """总结公式。"""
    params = seg.get("params", {})
    formula = params.get("formula", "")
    concept = params.get("concept", "")
    s = seg["start_frame"]
    layers = []

    # 核心公式主显示
    layers.append({
        "component": "drawTypewriterText",
        "params": {
            "cx": CENTER_X, "cy": CENTER_Y - 20,
            "text": formula,
            "startFrame": s,
            "charsPerSecond": 6,
            "color": "#FFD700",
            "font": "bold 36px sans-serif",
        }
    })

    # 概念说明
    if concept:
        layers.append({
            "component": "floatUpText",
            "params": {
                "cx": CENTER_X, "cy": CENTER_Y + 60,
                "targetY": CENTER_Y + 40,
                "text": f"💡 {concept}",
                "color": "#B0BEC5",
                "font": "18px sans-serif",
                "startFrame": s + 3 * FPS,
                "floatDuration": 20,
            }
        })

    # 金色边框装饰
    layers.append({
        "component": "staticLabel",
        "params": {
            "cx": CENTER_X, "cy": CENTER_Y,
            "width": 460, "height": 120,
            "text": "",
            "bgColor": "rgba(0,0,0,0.3)",
            "borderColor": "#FFD700",
            "borderRadius": 12,
            "opacity": 0.6,
        }
    })

    return layers


def render_concept_review(seg, cw, ch):
    """核心概念回顾。"""
    params = seg.get("params", {})
    title = params.get("title", "")
    definition = params.get("definition", "")
    formula = params.get("formula", "")
    s = seg["start_frame"]
    layers = []

    # 中央天平（隐喻）
    layers.append({
        "component": "drawBalance",
        "params": {
            "cx": CENTER_X, "cy": CENTER_Y + 40,
            "scale": 0.7,
            "weight": 1.0,
            "label": "⚖️",
            "highlight": False,
        }
    })

    # 大标题
    if title:
        layers.append({
            "component": "drawTypewriterText",
            "params": {
                "cx": CENTER_X, "cy": 80,
                "text": title,
                "startFrame": s + 2 * FPS,
                "charsPerSecond": 5,
                "color": "#FFD700",
                "font": "bold 30px sans-serif",
            }
        })

    # 定义
    if definition:
        display_def = definition[:60] + ("…" if len(definition) > 60 else "")
        layers.append({
            "component": "drawTypewriterText",
            "params": {
                "cx": CENTER_X, "cy": 130,
                "text": display_def,
                "startFrame": s + 6 * FPS,
                "charsPerSecond": 12,
                "color": "#E0E0E0",
                "font": "16px sans-serif",
            }
        })

    # 公式
    if formula:
        layers.append({
            "component": "drawTypewriterText",
            "params": {
                "cx": CENTER_X, "cy": ch - 80,
                "text": f"公式: {formula}",
                "startFrame": s + 10 * FPS,
                "charsPerSecond": 6,
                "color": "#81D4FA",
                "font": "bold 22px sans-serif",
            }
        })

    return layers


def render_knowledge_transfer(seg, cw, ch):
    """知识迁移。"""
    params = seg.get("params", {})
    misconceptions = params.get("misconceptions", [])
    extension = params.get("extension", "")
    s = seg["start_frame"]
    layers = []

    # 标题
    layers.append({
        "component": "sceneLabel",
        "params": {
            "cx": CENTER_X, "cy": 40,
            "text": "🔬 科学 · 🌍 生活 · 🚀 探索",
            "color": "#ffffff",
            "fontSize": 18,
        }
    })

    # 常见误解卡片
    for i, mc in enumerate(misconceptions[:3]):
        y_pos = 110 + i * 80
        layers.append({
            "component": "drawPopupLabel",
            "params": {
                "cx": CENTER_X, "cy": y_pos,
                "width": 600, "height": 50,
                "text": f"❌ 常见误解: {mc[:50]}",
                "textColor": "#FFAB91",
                "bgColor": "rgba(60,20,20,0.85)",
                "borderColor": "#FF5722",
                "popStartFrame": s + i * 20,
                "popDuration": 14,
            }
        })

    # 知识扩展
    if extension:
        ext_y = 110 + max(len(misconceptions[:3]), 1) * 80
        layers.append({
            "component": "floatUpText",
            "params": {
                "cx": CENTER_X, "cy": ch + 20,
                "targetY": min(ext_y, ch - 60),
                "text": f"🌌 {extension[:50]}",
                "color": "#B2EBF2",
                "font": "18px sans-serif",
                "startFrame": s + 12 * FPS,
                "floatDuration": 20,
            }
        })

    return layers


def render_final_elevation(seg, cw, ch):
    """升华总结。"""
    params = seg.get("params", {})
    title = params.get("title", "")
    subtitle = params.get("subtitle", "")
    closing_words = params.get("closing_words", "")
    s = seg["start_frame"]
    layers = []

    # 结论金句
    if closing_words:
        layers.append({
            "component": "drawTypewriterText",
            "params": {
                "cx": CENTER_X, "cy": CENTER_Y - 30,
                "text": closing_words,
                "startFrame": s + 3 * FPS,
                "charsPerSecond": 6,
                "color": "#FFD700",
                "font": "bold 28px sans-serif",
            }
        })

    # 最终标题
    if title:
        display_full = title + ((" " + subtitle) if subtitle else "")
        layers.append({
            "component": "drawTypewriterText",
            "params": {
                "cx": CENTER_X, "cy": CENTER_Y + 50,
                "text": display_full,
                "startFrame": s + 10 * FPS,
                "charsPerSecond": 5,
                "color": "#ffffff",
                "font": "bold 22px sans-serif",
            }
        })

    # 感谢语
    layers.append({
        "component": "floatUpText",
        "params": {
            "cx": CENTER_X, "cy": ch + 20,
            "targetY": ch - 40,
            "text": "📚 感谢观看 · 探索永不止步",
            "color": "#90A4AE",
            "font": "16px sans-serif",
            "startFrame": s + 16 * FPS,
            "floatDuration": 25,
        }
    })

    return layers


# ==================================================================
#  🔬 双模式：物理仿真渲染器
# ==================================================================

def render_simulate_physics(seg, cw, ch):
    """物理仿真渲染器。

    运行物理仿真并返回 mode=simulate 的片段数据。
    返回 dict 而非普通 layers list，含 physics 帧数据供 engine.js 消费。
    """
    physics = seg.get("physics", {})
    phases = physics.get("phases", [])
    fps = physics.get("fps", 30)
    visual = physics.get("visual_config", {})
    params = physics.get("params", {})

    if not phases:
        return {
            "_mode": "simulate",
            "layers": [],
            "_physics_empty": True,
            "message": "无物理阶段数据",
        }

    # 运行仿真
    from physics_simulator import PhysicsSimulator
    sim = PhysicsSimulator(fps=fps)
    for ph in phases:
        sim.add_phase(ph["type"], ph.get("params", {}),
                      max_duration=ph.get("max_duration"))
    result = sim.run()
    frames = result["frames"]
    total_frames = result["total_frames"]
    summary = result["summary"]

    # 物理参数（优先用仿真结果，fallback到输入参数）
    mass = params.get("mass", 2)
    angle = params.get("angle_deg", 37)
    mu_val = params.get("mu", 0.4)

    # 确定含有哪种阶段
    types = [p["type"] for p in phases]
    has_slope = "slope" in types
    has_rough = "rough_surface" in types
    has_pull = "horizontal_pull" in types
    has_electric = "electric_pendulum" in types

    # 🔌 电场单摆渲染
    if has_electric:
        ep = phases[0]["params"]  # electric_pendulum phase params
        mass = ep.get("mass", 0.1)
        q_val = ep.get("charge", 5e-4)
        e_val = ep.get("electric_field", 2000)
        L_val = ep.get("length", 1.0)
        g_val = ep.get("g", 10)
        fs = ep.get("force_summary", {})

        # 预计算力值
        Fq = q_val * e_val  # F电 = qE
        Fg = mass * g_val   # G = mg
        Fr_val = (Fq**2 + Fg**2) ** 0.5  # F合 = √(F电²+G²)

        total_cinematic_frames = int(max(total_frames * 15, 100 * fps))  # 总时长约 100s
        # 限制最大帧数避免异常
        total_cinematic_frames = min(total_cinematic_frames, 7200)

        layers = [
            {
                "component": "drawCinematicElectricPendulum",
                "params": {
                    "frames": frames,
                    "totalFrames": total_cinematic_frames,
                    "mass": mass, "q": q_val,
                    "E": e_val, "g": g_val, "L": L_val,
                    "Fq": round(Fq, 3),
                    "Fg": round(Fg, 3),
                    "Fr": round(Fr_val, 3),
                    "captions": {
                        "intro": "在竖直平面内，存在水平向右的匀强电场… 一个带正电的小球悬挂于 O 点",
                        "forces": "小球受到三个力：电场力 F电、重力 G、以及它们的合力 F合",
                        "swing": "由静止释放后，小球在电场力和重力共同作用下开始摆动",
                        "energy": "能量在电势能、动能和重力势能之间相互转化，总能量保持不变",
                        "solution": "由动能定理：W电 + W重 = ½mv²，代入数据得 v = 4 m/s",
                        "ending": "电场中的摆 — 力与能量的完美结合",
                    },
                }
            },
        ]

        return {
            "_mode": "cinematic",
            "layers": layers,
            "_physics_frames": frames,
            "_physics_total_frames": total_cinematic_frames,
            "_physics_fps": fps,
            "_physics_summary": {**summary, "force_summary": fs},
        }

    # 场景配置（根据阶段类型自适应）
    origin_x, origin_y = 80, 520
    scale = 110
    stage_type = "slope+surface" if has_slope else "surface"

    # HUD位置（右上角或右下角）
    hud_x, hud_y = cw - 240, 50
    if has_pull or has_rough:
        hud_x = cw - 260

    # 构建层
    layers = [
        {
            "component": "drawPhysicsStage",
            "params": {
                "type": stage_type,
                "angle": angle,
                "slopeLength": params.get("slope_length", 3),
                "scale": scale,
                "originX": origin_x,
                "originY": origin_y,
                "mu": mu_val,
                # 在仿真模式下由帧数据驱动，但这些静态参数需要传给绘制函数
            }
        },
        {
            "component": "drawPhaseLabel",
            "params": {
                "frames_meta": {
                    "frame_count": total_frames,
                    "phases": [{"type": p["type"], "start": 0,
                                "end": total_frames // len(phases)}
                               for p in phases],
                },
                "x": 16, "y": 16,
            }
        },
        {
            "component": "drawPhysicsHUD",
            "params": {
                "frames_meta": {
                    "frame_count": total_frames,
                    "phases": phases,
                },
                "panelX": hud_x,
                "panelY": hud_y,
                "showEnergy": True,
                "showVelocity": True,
                "showAcceleration": True,
            }
        },
        {
            "component": "drawPhysicsObject",
            "params": {
                "frames_meta": {
                    "frame_count": total_frames,
                    "phases": phases,
                },
                "scale": scale,
                "originX": origin_x,
                "originY": origin_y,
                "angle": angle,
                "slopeLength": params.get("slope_length", 3),
                "objectSize": 22,
                "mass": mass,
                "showVelocity": True,
            }
        },
    ]

    return {
        "_mode": "simulate",
        "layers": layers,
        "_physics_frames": frames,
        "_physics_total_frames": total_frames,
        "_physics_fps": fps,
        "_physics_summary": summary,
        "_stage_config": {
            "type": stage_type, "angle": angle,
            "originX": origin_x, "originY": origin_y,
            "scale": scale, "mu": mu_val,
        }
    }


def render_simulate_insight(seg, cw, ch):
    """关键洞察渲染器：仿真后弹出结论文字。"""
    params = seg.get("params", {})
    insights = params.get("insights", [])
    formula = params.get("formula", "")
    s = seg["start_frame"]
    layers = []

    for i, text in enumerate(insights[:3]):
        y_pos = ch // 2 - 40 + i * 60
        color = "#FFD700" if "⚡" in text else "#4FC3F7"
        layers.append({
            "component": "drawPopupLabel",
            "params": {
                "cx": CENTER_X, "cy": y_pos,
                "width": 420, "height": 44,
                "text": text,
                "textColor": color,
                "bgColor": "rgba(0,20,40,0.85)",
                "borderColor": color,
                "popStartFrame": s + i * 15,
                "popDuration": 20,
            }
        })

    if formula:
        layers.append({
            "component": "drawTypewriterText",
            "params": {
                "cx": CENTER_X, "cy": ch - 80,
                "text": f"📐 {formula}",
                "startFrame": s + len(insights) * 15 + 10,
                "charsPerSecond": 6,
                "color": "#FFD700",
                "font": "bold 24px sans-serif",
            }
        })

    return layers


# ==================================================================
#  场景类型 → 渲染器映射
# ==================================================================

SCENE_RENDERERS = {
    "introduction": render_introduction,
    "scene_demo_a": render_scene_demo,
    "scene_demo_b": render_scene_demo,
    "comparison": render_comparison,
    "transition": render_transition,
    "problem_display": render_problem_display,
    "scene_analysis": render_scene_analysis,
    "option_analysis": render_option_analysis,
    "answer_confirmation": render_answer_confirmation,
    "formula_summary": render_formula_summary,
    "concept_review": render_concept_review,
    "knowledge_transfer": render_knowledge_transfer,
    "final_elevation": render_final_elevation,
    # 🔬 双模式扩展
    "simulate_physics": render_simulate_physics,
    "simulate_insight": render_simulate_insight,
}


def _get_fallback_renderer(seg, cw, ch):
    """当场景类型无匹配渲染器时返回兜底。"""
    scene_type = seg.get("scene_type", "unknown")
    s = seg["start_frame"]
    return [
        {
            "component": "drawTypewriterText",
            "params": {
                "cx": CENTER_X, "cy": CENTER_Y,
                "text": f"场景: {scene_type}",
                "startFrame": s,
                "color": "#ffffff",
                "font": "24px sans-serif",
            }
        }
    ]


# ==================================================================
#  背景解析
# ==================================================================

def _resolve_background(seg: dict) -> dict:
    """将 segment 的 background 配置转为 engine.js 可识别的格式。"""
    bg = seg.get("background", {})
    scene_type = seg.get("scene_type", "")

    # 已有显式配置
    if isinstance(bg, dict) and bg.get("component") or bg.get("type"):
        return bg

    # 按场景类型推断
    if scene_type in ("scene_demo_a",):
        return {
            "component": "drawEarthBackground",
            "params": {
                "clouds": [
                    {"x": 100, "y": 60, "w": 70, "h": 22, "speed": 0.15},
                    {"x": 400, "y": 80, "w": 90, "h": 26, "speed": 0.1},
                    {"x": 700, "y": 50, "w": 60, "h": 18, "speed": 0.2},
                ]
            }
        }
    elif scene_type in ("scene_demo_b",):
        return {
            "component": "drawMoonBackground",
            "params": {
                "craters": [
                    {"x": 200, "y": 520, "rx": 30, "ry": 14, "depth": 0.4},
                    {"x": 500, "y": 540, "rx": 22, "ry": 10, "depth": 0.3},
                    {"x": 750, "y": 530, "rx": 16, "ry": 8, "depth": 0.35},
                    {"x": 350, "y": 560, "rx": 12, "ry": 6, "depth": 0.25},
                ],
                "earthPosition": {"x": 160, "y": 70},
                "starOpacity": 0.6,
            }
        }
    elif scene_type in ("problem_display",):
        # 试卷风格浅色背景
        return {
            "type": "color",
            "color": "#FFF8E1",
        }
    elif scene_type in ("formula_summary", "answer_confirmation"):
        return {
            "type": "color",
            "color": "#0D0D1A",
        }
    elif scene_type in ("simulate_physics",):
        return {
            "type": "color",
            "color": "#0a0e1a",
        }
    elif scene_type in ("simulate_insight",):
        return {
            "type": "color",
            "color": "#0b0e1a",
        }
    else:
        # 默认深空背景
        return {
            "component": "drawStarField",
            "params": {
                "stars": _generate_stars(80),
                "rotationSpeed": 0.0005,
                "twinkleIntensity": 0.3,
            }
        }


def _generate_stars(count=60):
    """生成随机星星数组用于 drawStarField。"""
    import random
    random.seed(42)
    stars = []
    for i in range(count):
        stars.append({
            "x": random.uniform(0, CANVAS_W),
            "y": random.uniform(0, CANVAS_H * 0.8),
            "r": random.uniform(0.5, 1.8),
            "baseAlpha": random.uniform(0.2, 0.8),
            "twinkleSpeed": random.uniform(0.02, 0.08),
            "twinklePhase": random.uniform(0, 6.28),
        })
    return stars


# ==================================================================
#  核心编排函数
# ==================================================================

def orchestrate(storyboard: dict) -> dict:
    """
    将 Layer 3 分镜脚本转换为 timeline JSON（支持 explain + simulate 双模式）。

    对 simulate 模式的片段：
    1. 调用 physics_simulator 生成帧数据
    2. 嵌入帧数据到 timeline 中
    3. 按实际帧数调整片段 endFrame
    4. 后续片段 startFrame 顺延
    """
    meta = storyboard.get("meta", {})
    acts = storyboard.get("acts", [])

    canvas_w = CANVAS_W
    canvas_h = CANVAS_H

    timeline = []
    total_frames = 0
    current_pos = 0  # 当前已使用的帧数（用于紧凑排列）

    for act in acts:
        segments = act.get("segments", [])

        for seg in segments:
            scene_type = seg.get("scene_type", "")
            original_duration = seg.get("end_frame", FPS * 5) - seg.get("start_frame", 0)

            # 背景
            background = _resolve_background(seg)

            # 层（支持 explain 和 simulate）
            renderer = SCENE_RENDERERS.get(scene_type, _get_fallback_renderer)
            render_result = renderer(seg, canvas_w, canvas_h)

            render_mode = render_result.get("_mode") if isinstance(render_result, dict) else "explain"
            is_cinematic = render_mode == "cinematic"
            is_simulate = render_mode == "simulate"

            if is_cinematic:
                sim_data = render_result
                layers = sim_data.get("layers", [])
                physics_total = sim_data.get("_physics_total_frames", 0)
                actual_frames = max(physics_total, 30)
                start = current_pos; end = start + actual_frames; current_pos = end + 1
                entry = {
                    "id": f"{act['act_number']}-{seg['id']}",
                    "name": seg.get("name", ""),
                    "mode": "cinematic", "startFrame": start, "endFrame": end,
                    "background": background, "transition_in": None,
                    "transition": {"duration": 10, "easing": "easeOut"},
                    "layers": layers,
                }

            elif is_simulate:
                # ── 仿真模式处理 ──
                sim_data = render_result
                layers = sim_data.get("layers", [])
                physics_frames = sim_data.get("_physics_frames", [])
                physics_total = sim_data.get("_physics_total_frames", 0)
                physics_fps = sim_data.get("_physics_fps", 30)
                physics_summary = sim_data.get("_physics_summary", {})

                # 仿真片段时长 = 实际帧数（至少30帧）
                actual_frames = max(physics_total, 30)
                start = current_pos
                end = start + actual_frames
                current_pos = end + 1  # +1 gap

                # 构建 timeline 条目
                entry = {
                    "id": f"{act['act_number']}-{seg['id']}",
                    "name": seg.get("name", ""),
                    "mode": "simulate",
                    "startFrame": start,
                    "endFrame": end,
                    "background": background,
                    "transition_in": None,
                    "transition": {"duration": 10, "easing": "easeOut"},
                    "layers": layers,
                    "physics": {
                        "frames": physics_frames,
                        "fps": physics_fps,
                        "total_frames": physics_total,
                        "summary": physics_summary,
                    }
                }
            else:
                # ── 讲解模式 ──
                start = current_pos
                end = start + original_duration
                current_pos = end + 1  # +1 gap
                layers = render_result if isinstance(render_result, list) else []

                transition_in = None
                if act["act_number"] == 1 and seg == segments[0]:
                    transition_in = {"duration": 20, "easing": "easeOut"}

                entry = {
                    "id": f"{act['act_number']}-{seg['id']}",
                    "name": seg.get("name", ""),
                    "mode": seg.get("mode", "explain"),
                    "startFrame": start,
                    "endFrame": end,
                    "background": background,
                    "transition_in": transition_in,
                    "transition": {"duration": 20, "easing": "easeOut"},
                    "layers": layers,
                }

            timeline.append(entry)
            total_frames = max(total_frames, end)

    # 检查是否包含 simulation
    has_sim = any(t.get("mode") == "simulate" for t in timeline)
    mode_label = "hybrid" if has_sim else "explain_only"

    result = {
        "meta": {
            "totalFrames": total_frames,
            "fps": FPS,
            "width": canvas_w,
            "height": canvas_h,
            "title": meta.get("topic", "物理动画"),
            "mode": mode_label,
        },
        "timeline": timeline
    }

    return result


# ==================================================================
#  便捷入口
# ==================================================================

def orchestrate_from_file(storyboard_path: str, output_path: str = None) -> dict:
    """
    从文件加载分镜脚本并生成 timeline JSON。

    参数:
        storyboard_path: Layer 3 storyboard JSON 文件路径
        output_path: 可选的 timeline JSON 输出路径

    返回:
        timeline JSON dict
    """
    with open(storyboard_path, "r", encoding="utf-8") as f:
        storyboard = json.load(f)

    timeline = orchestrate(storyboard)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(timeline, f, ensure_ascii=False, indent=2)
        print(f"timeline JSON 已保存: {output_path}")

    return timeline


def orchestrate_from_act_plan(act_plan: dict, output_path: str = None) -> dict:
    """
    从 Layer 2 幕结构规划直接生成 timeline JSON
    （自动先运行 Layer 3 展开）。

    参数:
        act_plan: Layer 2 幕结构规划 JSON
        output_path: 可选的 timeline JSON 输出路径

    返回:
        timeline JSON dict
    """
    from layer3_storyboard import expand_storyboard
    storyboard = expand_storyboard(act_plan)
    timeline = orchestrate(storyboard)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(timeline, f, ensure_ascii=False, indent=2)
        print(f"timeline JSON 已保存: {output_path}")

    return timeline


def generate_html_timeline(timeline: dict, output_html: str = None) -> str:
    """
    生成完整的独立 HTML 文件（内联 timeline JSON），
    可直接在浏览器中打开播放。

    参数:
        timeline: timeline JSON dict
        output_html: 可选的 HTML 输出路径

    返回:
        HTML 字符串
    """
    timeline_json = json.dumps(timeline, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{timeline['meta'].get('title', '物理动画')}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #000;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    overflow: hidden;
  }}
  #app {{
    position: relative;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 0 40px rgba(0,0,0,0.5);
  }}
  canvas {{
    display: block;
    background: #0a0a1a;
    width: 960px;
    height: 640px;
  }}
  #controls {{
    position: absolute;
    bottom: 0; left: 0; right: 0;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 20px;
    background: linear-gradient(transparent, rgba(0,0,0,0.85));
    transition: opacity 0.3s;
  }}
  #controls button {{
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    color: #fff;
    width: 36px; height: 36px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s;
  }}
  #controls button:hover {{ background: rgba(255,255,255,0.3); }}
  #controls input[type="range"] {{
    flex: 1;
    height: 4px;
    -webkit-appearance: none;
    appearance: none;
    background: rgba(255,255,255,0.2);
    border-radius: 2px;
    outline: none;
  }}
  #controls input[type="range"]::-webkit-slider-thumb {{
    -webkit-appearance: none;
    width: 14px; height: 14px;
    border-radius: 50%;
    background: #4FC3F7;
    cursor: pointer;
  }}
  #time-display {{
    color: rgba(255,255,255,0.7);
    font-size: 13px;
    min-width: 90px;
    text-align: right;
    font-variant-numeric: tabular-nums;
  }}
  #segment-name {{
    color: rgba(255,255,255,0.5);
    font-size: 12px;
    text-align: center;
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  #controls.hidden {{ opacity: 0; pointer-events: none; }}
  #app:hover #controls {{ opacity: 1; pointer-events: auto; }}
  #physics-data {{
    display: none;
    color: #60a5fa;
    font-size: 11px;
    font-variant-numeric: tabular-nums;
    margin-left: auto;
    white-space: nowrap;
    gap: 12px;
    align-items: center;
  }}
  #physics-data.show {{ display: flex; }}
  #physics-data .label {{ color: #64748b; }}
  #physics-data .val {{ color: #fbbf24; font-weight: bold; }}
</style>
</head>
<body>
<div id="app">
  <canvas id="stage"></canvas>
  <div id="controls">
    <button id="btn-play" title="播放/暂停">▶</button>
    <input type="range" id="seek-bar" min="0" max="100" value="0">
    <span id="time-display">00:00 / 00:00</span>
    <span id="segment-name"></span>
    <span id="physics-data">
      <span><span class="label">v=</span><span id="phy-vel" class="val">0</span></span>
      <span><span class="label">a=</span><span id="phy-acc" class="val">0</span></span>
      <span><span class="label">Ek=</span><span id="phy-ek" class="val">0</span></span>
    </span>
  </div>
</div>

<script src="components.js"></script>
<script src="engine.js"></script>
<script>
var TIMELINE = {timeline_json};

(function() {{
  var engine = startEngine('stage', TIMELINE, {{
    onFrameUpdate: function(frame, total) {{
      var seekBar = document.getElementById('seek-bar');
      if (seekBar && total > 0) {{
        seekBar.value = (frame / total * 100);
      }}
      updateDisplay(frame, total);
      updatePhysicsData(frame, total);
    }},
    onSegmentChange: function(seg, prev) {{
      var nameEl = document.getElementById('segment-name');
      if (nameEl && seg) {{
        var actMatch = seg.id ? seg.id.split('-')[0] : '';
        var prefix = actMatch ? '第' + actMatch + '幕 · ' : '';
        nameEl.textContent = prefix + seg.name;
      var phyEl = document.getElementById('physics-data');
      if (phyEl) {{
        phyEl.classList.toggle('show', seg && seg.mode === 'simulate');
      }}
      }}
    }},
    onComplete: function() {{
      var btn = document.getElementById('btn-play');
      if (btn) btn.textContent = '↺';
    }}
  }});

  function updateDisplay(frame, total) {{
    var el = document.getElementById('time-display');
    if (!el) return;
    var f = Math.min(frame, total);
    var sec = Math.floor(f / (TIMELINE.meta.fps || 60));
    var totalSec = Math.floor(total / (TIMELINE.meta.fps || 60));
    el.textContent = fmtTime(sec) + ' / ' + fmtTime(totalSec);
  }}

  function fmtTime(s) {{
    var m = Math.floor(s / 60);
    var sec = s % 60;
    return (m < 10 ? '0' : '') + m + ':' + (sec < 10 ? '0' : '') + sec;
  }}


  /** Dual-mode: update physics data bar */
  function updatePhysicsData(frame, total) {{
    if (typeof findSegment !== "function") return;
    var seg = findSegment(frame, TIMELINE.timeline);
    if (!seg || seg.mode !== "simulate") return;
    var localFrame = frame - seg.startFrame;
    if (!seg.physics || !seg.physics.frames) return;
    var d = seg.physics.frames[localFrame];
    if (!d) return;
    var vel = document.getElementById("phy-vel");
    if (vel) vel.textContent = (d.v ? d.v.toFixed(2) + "m/s" : "0");
    var acc = document.getElementById("phy-acc");
    if (acc) acc.textContent = (d.a ? d.a.toFixed(2) + "m/s²" : "0");
    var ek = document.getElementById("phy-ek");
    if (ek) ek.textContent = (d.Ek ? d.Ek.toFixed(1) + "J" : "0");
  }}
  // 播放/暂停
  document.getElementById('btn-play').addEventListener('click', function() {{
    var state = engine.getState();
    if (state.isComplete) {{
      engine.seek(0);
      engine.resume();
      this.textContent = '⏸';
    }} else if (state.isPaused) {{
      engine.resume();
      this.textContent = '⏸';
    }} else {{
      engine.pause();
      this.textContent = '▶';
    }}
  }});

  // 进度条
  var seekBar = document.getElementById('seek-bar');
  var isSeeking = false;
  seekBar.addEventListener('mousedown', function() {{ isSeeking = true; }});
  seekBar.addEventListener('touchstart', function() {{ isSeeking = true; }});
  seekBar.addEventListener('input', function() {{
    if (isSeeking) {{
      var total = TIMELINE.meta.totalFrames || 1;
      var target = Math.round(this.value / 100 * total);
      engine.seek(target);
      updateDisplay(target, total);
    }}
  }});
  seekBar.addEventListener('change', function() {{
    isSeeking = false;
  }});

  // 自动播放
  engine.resume();
  document.getElementById('btn-play').textContent = '⏸';
}})();
</script>
</body>
</html>"""

    if output_html:
        with open(output_html, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML 已保存: {output_html}")

    return html


# ==================================================================
#  自测
# ==================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parent.parent
    DATA_DIR = ROOT / "data"
    FRONTEND_DIR = ROOT / "frontend"
    DATA_DIR.mkdir(exist_ok=True)
    FRONTEND_DIR.mkdir(exist_ok=True)

    # 从文件加载 storyboard
    input_path = str(DATA_DIR / "layer3_full_storyboard.json")
    if len(sys.argv) > 1:
        input_path = sys.argv[1]

    # 生成 timeline JSON
    timeline = orchestrate_from_file(input_path, str(FRONTEND_DIR / "timeline.json"))

    # 生成独立 HTML
    generate_html_timeline(timeline, str(FRONTEND_DIR / "index.html"))

    print()
    print(f"=== 编排概要 ===")
    print(f"标题: {timeline['meta']['title']}")
    print(f"总帧数: {timeline['meta']['totalFrames']}")
    total_sec = timeline['meta']['totalFrames'] // timeline['meta']['fps']
    print(f"总时长: {total_sec // 60}:{total_sec % 60:02d}")
    print(f"片段数: {len(timeline['timeline'])}")
    print(f"画布: {timeline['meta']['width']}x{timeline['meta']['height']}")
    print()
    print("各片段:")
    for seg in timeline["timeline"]:
        layers = [l["component"] for l in seg.get("layers", [])]
        print(f"  {seg['id']}: {seg['name']} "
              f"({seg['startFrame']}-{seg['endFrame']}) "
              f"[{', '.join(layers[:3])}{'…' if len(layers) > 3 else ''}]")
