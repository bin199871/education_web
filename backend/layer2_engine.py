"""
Layer 2 — 幕结构匹配引擎
============================================================
职责：根据 Layer 1 的题目分析结果，匹配预定义的叙事模板，
      输出各幕的参数配置（供 Layer 3 分镜展开器使用）。

输入：Layer 1 的结构化 JSON
输出：三幕结构规划 JSON（含每幕的片段配置、组件需求、场景参数）

使用方式：
    from layer2_engine import generate_act_plan
    plan = generate_act_plan(layer1_result)
"""

import copy
import json


# ==================================================================
#  幕结构模板
# ==================================================================

# 每帧时长（秒）
FPS = 60


def _frames(seconds: int) -> int:
    """将秒转换为帧数。"""
    return seconds * FPS


# 第一幕：知识点讲解模板
ACT1_TEMPLATE = {
    "act_number": 1,
    "act_name": "知识点讲解",
    "core_task": "用直观对比讲透题目涉及的核心概念",
    "suggested_duration": "60-80秒",
    "segments": [
        {
            "id": "1-1",
            "name": "开场引入",
            "description": "物体出场 + 概念标签浮现",
            "duration_sec": 10,
            "scene_type": "introduction",
            "components": ["drawCube", "drawTypewriterText", "drawPopupLabel"],
            "background": "star_field",
            "transitions": {
                "in": {"type": "fade_in", "duration_frames": _frames(1)},
                "out": {"type": "fade_out", "duration_frames": _frames(1)}
            }
        },
        {
            "id": "1-2",
            "name": "场景A展示",
            "description": "第一个场景的仪器测量展示",
            "duration_sec": 20,
            "scene_type": "scene_demo_a",
            "components": ["drawBalance", "drawSpringScale", "drawPopupLabel"],
            "background": "earth_background",
            "transitions": {
                "in": {"type": "fade_in", "duration_frames": _frames(1)},
                "out": {"type": "fade_out", "duration_frames": _frames(1)}
            }
        },
        {
            "id": "1-3",
            "name": "场景B展示",
            "description": "第二个场景的仪器测量展示（与A形成对比）",
            "duration_sec": 20,
            "scene_type": "scene_demo_b",
            "components": ["drawBalance", "drawSpringScale", "drawPopupLabel"],
            "background": "moon_background",
            "transitions": {
                "in": {"type": "fade_in", "duration_frames": _frames(1)},
                "out": {"type": "fade_out", "duration_frames": _frames(1)}
            }
        },
        {
            "id": "1-4",
            "name": "对比结论",
            "description": "分屏对比 + 核心结论弹出",
            "duration_sec": 20,
            "scene_type": "comparison",
            "components": ["drawSplitScreenDivider", "drawPopupLabel",
                           "drawTypewriterText"],
            "background": "split_screen",
            "transitions": {
                "in": {"type": "slide_split", "duration_frames": _frames(1.5)},
                "out": {"type": "fade_out", "duration_frames": _frames(1)}
            }
        },
        {
            "id": "1-5",
            "name": "过渡到题目",
            "description": "画面渐暗，过渡语出现，准备进入第二幕",
            "duration_sec": 10,
            "scene_type": "transition",
            "components": ["drawTypewriterText", "drawMeteor"],
            "background": "deep_space",
            "transitions": {
                "in": {"type": "fade_in", "duration_frames": _frames(1)},
                "out": {"type": "fade_out", "duration_frames": _frames(2)}
            }
        }
    ]
}


# 第二幕：题目套入与解题模板
ACT2_TEMPLATE = {
    "act_number": 2,
    "act_name": "题目套入与解题",
    "core_task": "将知识点代入题目情境，动态分析选项",
    "suggested_duration": "70-90秒",
    "segments": [
        {
            "id": "2-1",
            "name": "题目展示",
            "description": "试卷纸张效果，题目文字逐字打出",
            "duration_sec": 10,
            "scene_type": "problem_display",
            "components": ["drawTypewriterText", "drawPopupLabel"],
            "background": "paper_texture",
            "transitions": {
                "in": {"type": "zoom_in", "duration_frames": _frames(1)},
                "out": {"type": "fade_out", "duration_frames": _frames(1)}
            }
        },
        {
            "id": "2-2",
            "name": "场景与受力分析",
            "description": "将题目情境可视化，展示受力分析",
            "duration_sec": 20,
            "scene_type": "scene_analysis",
            "components": ["drawCube", "drawPopupLabel", "drawTypewriterText"],
            "background": "paper_texture",
            "transitions": {
                "in": {"type": "fade_in", "duration_frames": _frames(1)},
                "out": {"type": "fade_out", "duration_frames": _frames(1)}
            }
        },
        {
            "id": "2-3",
            "name": "选项逐个击破",
            "description": "每个选项逐一分析，显示对错判断和解析",
            "duration_sec": 30,
            "scene_type": "option_analysis",
            "components": ["drawPopupLabel", "drawTypewriterText"],
            "background": "paper_texture",
            "transitions": {
                "in": {"type": "fade_in", "duration_frames": _frames(0.5)},
                "out": {"type": "fade_out", "duration_frames": _frames(0.5)}
            }
        },
        {
            "id": "2-4",
            "name": "答案确认",
            "description": "正确答案高亮显示，批注给出完整解析",
            "duration_sec": 10,
            "scene_type": "answer_confirmation",
            "components": ["drawPopupLabel", "drawTypewriterText"],
            "background": "paper_texture",
            "transitions": {
                "in": {"type": "pop_in", "duration_frames": _frames(0.5)},
                "out": {"type": "fade_out", "duration_frames": _frames(1)}
            }
        },
        {
            "id": "2-5",
            "name": "总结公式",
            "description": "核心公式再次强调，加深记忆",
            "duration_sec": 5,
            "scene_type": "formula_summary",
            "components": ["drawPopupLabel"],
            "background": "deep_space",
            "transitions": {
                "in": {"type": "fade_in", "duration_frames": _frames(0.5)},
                "out": {"type": "fade_out", "duration_frames": _frames(1)}
            }
        }
    ]
}


# 第三幕：总结升华模板
ACT3_TEMPLATE = {
    "act_number": 3,
    "act_name": "总结升华",
    "core_task": "提炼核心结论，知识迁移扩展",
    "suggested_duration": "50-60秒",
    "segments": [
        {
            "id": "3-1",
            "name": "核心概念回顾",
            "description": "天平意象展示概念对比，回顾核心结论",
            "duration_sec": 10,
            "scene_type": "concept_review",
            "components": ["drawPopupLabel", "drawTypewriterText",
                           "drawStarField"],
            "background": "nebula",
            "transitions": {
                "in": {"type": "fade_in", "duration_frames": _frames(1)},
                "out": {"type": "fade_out", "duration_frames": _frames(1)}
            }
        },
        {
            "id": "3-2",
            "name": "知识迁移",
            "description": "拓展到更广阔的物理世界，关联其他知识点",
            "duration_sec": 20,
            "scene_type": "knowledge_transfer",
            "components": ["drawTypewriterText", "drawPopupLabel",
                           "drawStarField"],
            "background": "nebula",
            "transitions": {
                "in": {"type": "fade_in", "duration_frames": _frames(1)},
                "out": {"type": "fade_out", "duration_frames": _frames(1)}
            }
        },
        {
            "id": "3-3",
            "name": "升华总结",
            "description": "哲理金句 + 宇宙视角，升华主题",
            "duration_sec": 20,
            "scene_type": "final_elevation",
            "components": ["drawTypewriterText", "drawStarField",
                           "drawPopupLabel", "drawMeteor"],
            "background": "nebula",
            "transitions": {
                "in": {"type": "fade_in", "duration_frames": _frames(1.5)},
                "out": {"type": "fade_out", "duration_frames": _frames(2)}
            }
        }
    ]
}


# ==================================================================
#  视觉主题映射
# ==================================================================

# 不同物理主题映射到不同的视觉风格 / 背景组件
VISUAL_THEMES = {
    "quality_gravity": {
        "name": "宇宙探索",
        "backgrounds": {
            "star_field": {"component": "drawStarField",
                          "params": {"stars": 80, "rotationSpeed": 0.001,
                                    "twinkleIntensity": 0.5}},
            "earth_background": {"component": "drawEarthBackground",
                                "params": {"clouds": [
                                    {"x": 100, "y": 60, "w": 80, "h": 25,
                                     "speed": 0.3},
                                    {"x": 400, "y": 80, "w": 100, "h": 30,
                                     "speed": 0.2},
                                    {"x": 650, "y": 50, "w": 70, "h": 20,
                                     "speed": 0.35}
                                ]}},
            "moon_background": {"component": "drawMoonBackground",
                               "params": {"craters": [
                                   {"x": 200, "y": 350, "rx": 30, "ry": 15,
                                    "depth": 0.5},
                                   {"x": 500, "y": 320, "rx": 20, "ry": 10,
                                    "depth": 0.3},
                                   {"x": 700, "y": 370, "rx": 40, "ry": 18,
                                    "depth": 0.4},
                                   {"x": 350, "y": 380, "rx": 15, "ry": 8,
                                    "depth": 0.6}
                               ], "earthPosition": {"x": 120, "y": 60}}},
            "deep_space": {"component": "drawStarField",
                          "params": {"stars": 100, "rotationSpeed": 0.0005,
                                    "twinkleIntensity": 0.3}},
            "split_screen": {"component": "drawStarField",
                            "params": {"stars": 60, "rotationSpeed": 0.0005,
                                      "twinkleIntensity": 0.2}},
            "paper_texture": {"component": "drawStarField",
                             "params": {"stars": 20, "rotationSpeed": 0,
                                       "twinkleIntensity": 0}},
            "nebula": {"component": "drawStarField",
                      "params": {"stars": 120, "rotationSpeed": 0.0008,
                                "twinkleIntensity": 0.6}}
        },
        "colors": {
            "primary": "#0D47A1",
            "secondary": "#42A5F5",
            "accent": "#FF9800",
            "success": "#4CAF50",
            "text": "#FFFFFF",
            "highlight": "#FFD54F"
        },
        "ambient": {
            "music": "peaceful_exploration",
            "particle_effects": ["stars", "meteor"]
        }
    },
    "newton_law": {
        "name": "力学世界",
        "backgrounds": {
            "star_field": {"component": "drawEarthBackground",
                          "params": {"skyGradient": [
                              {"pos": 0, "color": "#1A237E"},
                              {"pos": 0.3, "color": "#283593"},
                              {"pos": 0.55, "color": "#5C6BC0"},
                              {"pos": 0.65, "color": "#3949AB"}
                          ]}},
            "earth_background": {"component": "drawEarthBackground",
                                "params": {"grassColor": "#558B2F"}},
            "moon_background": {"component": "drawMoonBackground",
                               "params": {"craters": []}},
            "deep_space": {"component": "drawEarthBackground",
                          "params": {"skyGradient": [
                              {"pos": 0, "color": "#1A237E"},
                              {"pos": 0.65, "color": "#283593"}
                          ]}},
            "split_screen": {"component": "drawEarthBackground",
                            "params": {"skyGradient": [
                                {"pos": 0, "color": "#1A237E"},
                                {"pos": 0.65, "color": "#283593"}
                            ]}},
            "paper_texture": {"component": "drawEarthBackground",
                             "params": {"skyGradient": [
                                 {"pos": 0, "color": "#F5F5F5"},
                                 {"pos": 0.65, "color": "#E0E0E0"}
                             ], "grassColor": "#E0E0E0"}},
            "nebula": {"component": "drawEarthBackground",
                      "params": {"skyGradient": [
                          {"pos": 0, "color": "#1A237E"},
                          {"pos": 0.65, "color": "#4A148C"}
                      ]}}
        },
        "colors": {
            "primary": "#1A237E",
            "secondary": "#5C6BC0",
            "accent": "#FF5722",
            "success": "#66BB6A",
            "text": "#FFFFFF",
            "highlight": "#FFAB40"
        },
        "ambient": {
            "music": "dynamic_experiment",
            "particle_effects": ["force_arrows", "grid"]
        }
    },
    "circular_motion": {
        "name": "轨道宇宙",
        "backgrounds": {
            "star_field": {"component": "drawStarField",
                          "params": {"stars": 100, "rotationSpeed": 0.002,
                                    "twinkleIntensity": 0.6}},
            "earth_background": {"component": "drawEarthBackground",
                                "params": {}},
            "moon_background": {"component": "drawMoonBackground",
                               "params": {"craters": [], "earthPosition": None}},
            "deep_space": {"component": "drawStarField",
                          "params": {"stars": 120, "rotationSpeed": 0.001,
                                    "twinkleIntensity": 0.4}},
            "split_screen": {"component": "drawStarField",
                            "params": {"stars": 80, "rotationSpeed": 0.001,
                                      "twinkleIntensity": 0.3}},
            "paper_texture": {"component": "drawStarField",
                             "params": {"stars": 30, "rotationSpeed": 0,
                                       "twinkleIntensity": 0}},
            "nebula": {"component": "drawStarField",
                      "params": {"stars": 150, "rotationSpeed": 0.0015,
                                "twinkleIntensity": 0.7}}
        },
        "colors": {
            "primary": "#4A148C",
            "secondary": "#7B1FA2",
            "accent": "#00E5FF",
            "success": "#69F0AE",
            "text": "#FFFFFF",
            "highlight": "#FFD740"
        },
        "ambient": {
            "music": "orbital_rhythm",
            "particle_effects": ["orbits", "trails"]
        }
    },
    "energy": {
        "name": "能量变换",
        "backgrounds": {
            "star_field": {"component": "drawStarField",
                          "params": {"stars": 60, "rotationSpeed": 0.0005,
                                    "twinkleIntensity": 0.3}},
            "earth_background": {"component": "drawEarthBackground", "params": {}},
            "moon_background": {"component": "drawMoonBackground",
                               "params": {"craters": [], "earthPosition": None}},
            "deep_space": {"component": "drawStarField",
                          "params": {"stars": 80, "rotationSpeed": 0.0005,
                                    "twinkleIntensity": 0.2}},
            "split_screen": {"component": "drawStarField",
                            "params": {"stars": 50, "rotationSpeed": 0.0003,
                                      "twinkleIntensity": 0.2}},
            "paper_texture": {"component": "drawStarField",
                             "params": {"stars": 20, "rotationSpeed": 0,
                                       "twinkleIntensity": 0}},
            "nebula": {"component": "drawStarField",
                      "params": {"stars": 100, "rotationSpeed": 0.001,
                                "twinkleIntensity": 0.5}}
        },
        "colors": {
            "primary": "#E65100",
            "secondary": "#FF9800",
            "accent": "#00BCD4",
            "success": "#8BC34A",
            "text": "#FFFFFF",
            "highlight": "#FFEB3B"
        },
        "ambient": {
            "music": "energy_flow",
            "particle_effects": ["energy_particles", "waves"]
        }
    },
    "electricity": {
        "name": "电学世界",
        "backgrounds": {
            "star_field": {"component": "drawStarField",
                          "params": {"stars": 50, "rotationSpeed": 0.0003,
                                    "twinkleIntensity": 0.2}},
            "earth_background": {"component": "drawEarthBackground",
                                "params": {}},
            "moon_background": {"component": "drawMoonBackground",
                               "params": {"craters": [], "earthPosition": None}},
            "deep_space": {"component": "drawStarField",
                          "params": {"stars": 60, "rotationSpeed": 0.0003,
                                    "twinkleIntensity": 0.2}},
            "split_screen": {"component": "drawStarField",
                            "params": {"stars": 40, "rotationSpeed": 0,
                                      "twinkleIntensity": 0.1}},
            "paper_texture": {"component": "drawStarField",
                             "params": {"stars": 15, "rotationSpeed": 0,
                                       "twinkleIntensity": 0}},
            "nebula": {"component": "drawStarField",
                      "params": {"stars": 80, "rotationSpeed": 0.0005,
                                "twinkleIntensity": 0.4}}
        },
        "colors": {
            "primary": "#01579B",
            "secondary": "#0288D1",
            "accent": "#FF1744",
            "success": "#76FF03",
            "text": "#FFFFFF",
            "highlight": "#FFFF00"
        },
        "ambient": {
            "music": "circuit_hum",
            "particle_effects": ["electrons", "sparks"]
        }
    },
    "momentum": {
        "name": "动量碰撞",
        "backgrounds": {
            "star_field": {"component": "drawStarField",
                          "params": {"stars": 70, "rotationSpeed": 0.0008,
                                    "twinkleIntensity": 0.4}},
            "earth_background": {"component": "drawEarthBackground", "params": {}},
            "moon_background": {"component": "drawMoonBackground",
                               "params": {"craters": [], "earthPosition": None}},
            "deep_space": {"component": "drawStarField",
                          "params": {"stars": 90, "rotationSpeed": 0.0008,
                                    "twinkleIntensity": 0.3}},
            "split_screen": {"component": "drawStarField",
                            "params": {"stars": 60, "rotationSpeed": 0.0005,
                                      "twinkleIntensity": 0.2}},
            "paper_texture": {"component": "drawStarField",
                             "params": {"stars": 20, "rotationSpeed": 0,
                                       "twinkleIntensity": 0}},
            "nebula": {"component": "drawStarField",
                      "params": {"stars": 110, "rotationSpeed": 0.0012,
                                "twinkleIntensity": 0.6}}
        },
        "colors": {
            "primary": "#B71C1C",
            "secondary": "#E53935",
            "accent": "#FFD600",
            "success": "#00E676",
            "text": "#FFFFFF",
            "highlight": "#FF9100"
        },
        "ambient": {
            "music": "impact_rhythm",
            "particle_effects": ["debris", "trails"]
        }
    }
}

# 默认视觉主题（当未匹配到特定主题时使用）
DEFAULT_VISUAL_THEME = {
    "name": "通用课堂",
    "backgrounds": {
        "star_field": {"component": "drawStarField",
                      "params": {"stars": 60, "rotationSpeed": 0.001,
                                "twinkleIntensity": 0.4}},
        "earth_background": {"component": "drawEarthBackground", "params": {}},
        "moon_background": {"component": "drawMoonBackground",
                           "params": {"craters": [], "earthPosition": None}},
        "deep_space": {"component": "drawStarField",
                      "params": {"stars": 80, "rotationSpeed": 0.0008,
                                "twinkleIntensity": 0.3}},
        "split_screen": {"component": "drawStarField",
                        "params": {"stars": 50, "rotationSpeed": 0.0005,
                                  "twinkleIntensity": 0.2}},
        "paper_texture": {"component": "drawStarField",
                         "params": {"stars": 15, "rotationSpeed": 0,
                                   "twinkleIntensity": 0}},
        "nebula": {"component": "drawStarField",
                  "params": {"stars": 100, "rotationSpeed": 0.001,
                            "twinkleIntensity": 0.5}}
    },
    "colors": {
        "primary": "#1565C0",
        "secondary": "#42A5F5",
        "accent": "#FFA726",
        "success": "#66BB6A",
        "text": "#FFFFFF",
        "highlight": "#FFF176"
    },
    "ambient": {
        "music": "classroom",
        "particle_effects": []
    }
}


# ==================================================================
#  场景标签与主题词映射
# ==================================================================

# 根据题目场景生成 Act 1 中场景 A/B 的标签文字
SCENE_LABEL_TEMPLATES = {
    "地球表面": {"a_label": "⚖️ 质量 = 1.0 kg（不变）",
               "b_label": "📏 重力 = 9.8 N（地球）"},
    "月球表面": {"a_label": "⚖️ 质量 = 1.0 kg（不变！）",
               "b_label": "📏 重力 ≈ 1.6 N（月球）"},
    "水平面运动": {"a_label": "📐 受力分析图",
                 "b_label": "📊 合力计算"},
    "自由落体": {"a_label": "⏱ 位置随时间变化",
               "b_label": "📈 速度随时间变化"},
    "碰撞": {"a_label": "碰撞前",
            "b_label": "碰撞后"},
}

DEFAULT_SCENE_LABELS = {
    "a_label": "场景 A",
    "b_label": "场景 B"
}


# ==================================================================
#  核心引擎
# ==================================================================

class ActPlanGenerator:
    """幕结构规划生成器。"""

    def __init__(self, layer1_result: dict):
        self.layer1 = layer1_result
        self.topic = layer1_result.get("topic", "")
        self.core_concept = layer1_result.get("core_concept", {})
        self.scenario = layer1_result.get("scenario_analysis", {})
        self.options = layer1_result.get("options_analysis", [])
        self.answer = layer1_result.get("answer", "")
        self.subject = layer1_result.get("subject", "物理")

        # 匹配视觉主题
        self.visual_theme = self._match_visual_theme()
        # 提取场景名称
        self.scene_names = [s["name"] for s in self.scenario.get("scenes", [])]

    def _match_visual_theme(self) -> dict:
        """根据 Layer 1 的核心概念匹配视觉主题。"""
        concept_name = self.core_concept.get("name", "")
        for topic_id, theme in VISUAL_THEMES.items():
            # 从 PHYSICS_TOPICS 匹配（通过概念名称关联）
            from layer1_agent import PHYSICS_TOPICS
            if topic_id in PHYSICS_TOPICS:
                if PHYSICS_TOPICS[topic_id]["concept_name"] == concept_name:
                    return copy.deepcopy(theme)
        # 用关键词模糊匹配
        for topic_id, theme in VISUAL_THEMES.items():
            from layer1_agent import PHYSICS_TOPICS
            if topic_id in PHYSICS_TOPICS:
                for kw in PHYSICS_TOPICS[topic_id]["keywords"]:
                    if kw in self.topic or kw in concept_name:
                        return copy.deepcopy(theme)
        return copy.deepcopy(DEFAULT_VISUAL_THEME)

    def _scene_a_name(self) -> str:
        """第一个演示场景的名称。"""
        if len(self.scene_names) >= 1:
            return self.scene_names[0]
        return "场景A"

    def _scene_b_name(self) -> str:
        """第二个演示场景的名称。"""
        if len(self.scene_names) >= 2:
            return self.scene_names[1]
        return "场景B"

    def _get_scene_labels(self) -> dict:
        """获取场景标签文字。"""
        for name_tmpl, labels in SCENE_LABEL_TEMPLATES.items():
            for sn in self.scene_names:
                if name_tmpl in sn or sn in name_tmpl:
                    return labels
        return dict(DEFAULT_SCENE_LABELS)

    def _build_act1(self) -> dict:
        """构建第一幕配置。"""
        act = copy.deepcopy(ACT1_TEMPLATE)
        scene_a = self._scene_a_name()
        scene_b = self._scene_b_name()
        labels = self._get_scene_labels()
        formula = self.core_concept.get("key_formula", "")
        concept_name = self.core_concept.get("name", "")

        # 填充片段参数
        seg_map = {s["id"]: s for s in act["segments"]}

        # 1-1 开场引入
        if "1-1" in seg_map:
            seg_map["1-1"]["params"] = {
                "title": concept_name,
                "subtitle": f"{self.subject} · 核心概念",
                "cube_label": "🔬",
                "concept_labels": [
                    {"text": "质量", "color": "#4CAF50"},
                    {"text": "重力", "color": "#FF9800"}
                ]
            }

        # 1-2 场景A
        if "1-2" in seg_map:
            seg_map["1-2"]["scene_name"] = scene_a
            seg_map["1-2"]["params"] = {
                "scene_label": scene_a,
                "balance_label": labels.get("a_label", f"⚖️ {scene_a}"),
                "spring_label": labels.get("b_label", f"📏 {scene_a}"),
                "balance_weight": 2.0,
                "spring_weight": 5.0,
                "g_value": "9.8 m/s²"
            }
            # 如有场景分析，填充 motion/force 信息
            for scene in self.scenario.get("scenes", []):
                if scene["name"] == scene_a:
                    seg_map["1-2"].setdefault("annotations", {})
                    seg_map["1-2"]["annotations"]["motion"] = scene.get("motion", "")
                    seg_map["1-2"]["annotations"]["force"] = scene.get("force", "")
                    break

        # 1-3 场景B
        if "1-3" in seg_map:
            seg_map["1-3"]["scene_name"] = scene_b
            seg_map["1-3"]["params"] = {
                "scene_label": scene_b,
                "balance_label": f"⚖️ 质量 = 1.0 kg（不变！）",
                "spring_label": f"📏 重力（{scene_b}）",
                "balance_weight": 2.0,
                "spring_weight": 1.0,
                "g_value": "1.6 m/s²"
            }
            for scene in self.scenario.get("scenes", []):
                if scene["name"] == scene_b:
                    seg_map["1-3"].setdefault("annotations", {})
                    seg_map["1-3"]["annotations"]["motion"] = scene.get("motion", "")
                    seg_map["1-3"]["annotations"]["force"] = scene.get("force", "")
                    break

        # 1-4 对比结论
        if "1-4" in seg_map:
            seg_map["1-4"]["params"] = {
                "conclusions": [
                    {"text": "✅ 质量 —— 不随位置改变", "color": "#4CAF50"},
                    {"text": "✅ 重力 —— 随引力变化", "color": "#FF9800"}
                ],
                "formula": formula,
                "final_line": "接下来，我们看一道真题如何运用这两个概念"
            }

        # 1-5 过渡
        if "1-5" in seg_map:
            seg_map["1-5"]["params"] = {
                "transition_text": "接下来，让我们用这道题检验所学",
                "meteor_count": 1
            }

        # 计算帧
        self._apply_frames(act)
        return act

    def _build_act2(self) -> dict:
        """构建第二幕配置。"""
        act = copy.deepcopy(ACT2_TEMPLATE)
        formula = self.core_concept.get("key_formula", "")
        concept_name = self.core_concept.get("name", "")

        seg_map = {s["id"]: s for s in act["segments"]}

        # 2-1 题目展示
        if "2-1" in seg_map:
            seg_map["2-1"]["params"] = {
                "stem": self.scenario.get("context", ""),
                "options": [
                    {"label": o["label"], "text": o["statement"]}
                    for o in self.options
                ]
            }

        # 2-2 场景与受力分析
        if "2-2" in seg_map:
            seg_map["2-2"]["params"] = {
                "scene_label": "受力分析",
                "concept_note": concept_name,
                "scenes": self.scene_names
            }

        # 2-3 选项逐个击破
        if "2-3" in seg_map:
            seg_map["2-3"]["params"] = {
                "options": [
                    {
                        "label": o["label"],
                        "statement": o["statement"],
                        "correct": o["correct"],
                        "reason": o.get("reason", "")
                    }
                    for o in self.options
                ]
            }

        # 2-4 答案确认
        if "2-4" in seg_map:
            correct_opt = None
            for o in self.options:
                if o.get("correct"):
                    correct_opt = o
                    break
            seg_map["2-4"]["params"] = {
                "answer": self.answer or correct_opt.get("label", "") if correct_opt else "",
                "correct_option": correct_opt,
                "formula": formula
            }

        # 2-5 总结公式
        if "2-5" in seg_map:
            seg_map["2-5"]["params"] = {
                "formula": formula,
                "concept": concept_name
            }

        self._apply_frames(act)
        return act

    def _build_act3(self) -> dict:
        """构建第三幕配置。"""
        act = copy.deepcopy(ACT3_TEMPLATE)
        formula = self.core_concept.get("key_formula", "")
        concept_name = self.core_concept.get("name", "")
        misconceptions = self.core_concept.get("common_misconceptions", [])

        seg_map = {s["id"]: s for s in act["segments"]}

        # 3-1 核心概念回顾
        if "3-1" in seg_map:
            seg_map["3-1"]["params"] = {
                "title": f"⚖️ {concept_name}",
                "definition": self.core_concept.get("definition", ""),
                "formula": formula
            }

        # 3-2 知识迁移
        if "3-2" in seg_map:
            seg_map["3-2"]["params"] = {
                "title": "知识拓展",
                "misconceptions": misconceptions[:3],  # 最多展示3个
                "extension": f"掌握了{concept_name}，"
                             f"就能理解更多物理现象"
            }

        # 3-3 升华总结
        if "3-3" in seg_map:
            seg_map["3-3"]["params"] = {
                "title": f"{concept_name}",
                "subtitle": "—— 一堂关于宇宙的物理课",
                "closing_words": "宇宙的答案，藏在你对世界的每一次提问中",
                "show_meteor": True
            }

        self._apply_frames(act)
        return act

    def _apply_frames(self, act: dict) -> None:
        """为每个片段计算起止帧号。"""
        current_frame = 0
        for seg in act["segments"]:
            duration_f = _frames(seg["duration_sec"])
            seg["start_frame"] = current_frame
            seg["end_frame"] = current_frame + duration_f
            current_frame += duration_f + 1  # +1 帧间隔

        # 更新总帧数
        total_sec = sum(s["duration_sec"] for s in act["segments"])
        act["total_frames"] = _frames(total_sec)
        act["total_duration_sec"] = total_sec

    def _get_background_for(self, act_number: int, segment_id: str) -> dict:
        """为指定片段获取背景配置。"""
        act_key = f"act{act_number}"
        templates = {1: ACT1_TEMPLATE, 2: ACT2_TEMPLATE, 3: ACT3_TEMPLATE}
        tmpl = templates.get(act_number, ACT1_TEMPLATE)
        bg_key = "star_field"
        for seg in tmpl["segments"]:
            if seg["id"] == segment_id:
                bg_key = seg.get("background", "star_field")
                break
        bg = self.visual_theme.get("backgrounds", {}).get(bg_key)
        if bg:
            return bg
        # fallback
        return DEFAULT_VISUAL_THEME["backgrounds"].get(bg_key,
                   DEFAULT_VISUAL_THEME["backgrounds"]["star_field"])

    def generate(self) -> dict:
        """
        生成完整的幕结构规划。

        返回:
            {
                "meta": { ... 全局元信息 },
                "acts": [ Act1, Act2, Act3 ]
            }
        """
        # 三幕列表
        acts = [
            self._build_act1(),
            self._build_act2(),
            self._build_act3()
        ]

        total_duration_sec = sum(a.get("total_duration_sec", 0) for a in acts)

        # 为每幕注入背景配置
        for act in acts:
            for seg in act["segments"]:
                seg["background_config"] = self._get_background_for(
                    act["act_number"], seg["id"]
                )
                seg["color_scheme"] = self.visual_theme.get("colors", {})

        plan = {
            "meta": {
                "topic": self.topic,
                "subject": self.subject,
                "core_concept": self.core_concept.get("name", ""),
                "key_formula": self.core_concept.get("key_formula", ""),
                "total_duration_sec": total_duration_sec,
                "total_frames": _frames(total_duration_sec),
                "fps": FPS,
                "visual_theme_name": self.visual_theme.get("name", "通用课堂"),
                "color_scheme": self.visual_theme.get("colors", {}),
                "ambient": self.visual_theme.get("ambient", {})
            },
            "acts": acts
        }

        return plan


# ==================================================================
#  便捷入口
# ==================================================================

def generate_act_plan(layer1_result: dict) -> dict:
    """
    根据 Layer 1 的分析结果生成幕结构规划。

    参数:
        layer1_result: Layer 1 输出的结构化 JSON（dict）

    返回:
        三幕结构规划 JSON（dict）
    """
    generator = ActPlanGenerator(layer1_result)
    return generator.generate()


def generate_act_plan_from_file(input_path: str,
                                output_path: str = None) -> dict:
    """
    从文件读取 Layer 1 结果并生成幕结构规划。

    参数:
        input_path: Layer 1 结果的 JSON 文件路径
        output_path: 可选，输出文件路径
    返回:
        幕结构规划 dict
    """
    with open(input_path, "r", encoding="utf-8") as f:
        layer1_result = json.load(f)

    plan = generate_act_plan(layer1_result)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        print(f"幕结构规划已保存到: {output_path}")

    return plan


# ==================================================================
#  自测
# ==================================================================

if __name__ == "__main__":
    # 用内置的嫦娥示例测试
    sample_layer1 = {
        "topic": "质量与重力的区别",
        "subject": "物理",
        "question_type": "选择题",
        "core_concept": {
            "name": "质量与重力的区别",
            "definition": "质量是物体固有属性，不随位置改变；"
                          "重力是万有引力的表现，G=mg，随g值改变",
            "key_formula": "G = mg",
            "variables": {
                "m": {"name": "质量", "unit": "kg",
                      "property": "不随位置改变"},
                "g": {"name": "重力加速度", "unit": "m/s²",
                      "property": "随星球变化"},
                "G": {"name": "重力", "unit": "N",
                      "property": "随g值变化"}
            },
            "common_misconceptions": [
                "质量会随重力变化",
                "失重状态下物体质量为零",
                "质量和重量是同一概念"
            ]
        },
        "scenario_analysis": {
            "context": "嫦娥六号月背采样返回",
            "key_conditions": "月球g值约为地球的1/6",
            "scenes": [
                {"name": "地球表面", "motion": "静止",
                 "force": "受重力 G=mg，对支持面有压力"},
                {"name": "月球表面", "motion": "静止",
                 "force": "受重力 G=mg/6，对支持面有压力"},
                {"name": "环绕飞行", "motion": "匀速圆周运动",
                 "force": "引力提供向心力，合力不为零"}
            ]
        },
        "options_analysis": [
            {"label": "A", "statement": "环月飞行时样品合力为零",
             "correct": False,
             "reason": "匀速圆周运动需要向心力，合力不等于零"},
            {"label": "B", "statement": "样品在月球正面时对月面压力为零",
             "correct": False,
             "reason": "样品受重力，对月面压力等于重力，不为零"},
            {"label": "C", "statement": "引力不同所以质量也不同",
             "correct": False,
             "reason": "质量是固有属性，不随引力变化"},
            {"label": "D", "statement": "月球表面对月球的压力比地球表面时小",
             "correct": True,
             "reason": "F压=G=mg，月球g是地球的1/6，所以压力也是1/6"}
        ],
        "answer": "D"
    }

    plan = generate_act_plan(sample_layer1)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
