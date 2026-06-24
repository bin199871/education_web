"""
Layer 1 — 题目分析 Agent (Python 版)
============================================================
混合模式：规则解析框架 + 可插拔 LLM 后端

置信度体系：每次分析附带置信度评分，不确定时主动拒绝，
           宁可不答，不错答。

用法:
    from layer1_agent import analyze_problem_safe

    # 纯规则模式
    result = analyze_problem_safe("题目文本...")
    if result["status"] == "needs_review":
        print("需人工审核:", result["warnings"])

    # LLM 增强模式
    result = await analyze_problem_safe("题目文本...", llm_config={...})
"""

import re
import json
import copy
from typing import Optional


# ==================================================================
#  物理知识规则库
# ==================================================================

PHYSICS_TOPICS = {
    "quality_gravity": {
        "keywords": ["质量", "重力", "引力", "g值", "自由落体加速度",
                     "月球", "天平", "弹簧秤", "称重", "重量", "G=mg"],
        "concept_name": "质量与重力的区别",
        "concept_desc": "质量是物体固有属性，不随位置改变；"
                        "重力是万有引力的表现，G = mg，随 g 值改变",
        "key_formula": "G = mg",
        "variables": {
            "m": {"name": "质量", "unit": "kg", "property": "不随位置改变，固有属性"},
            "g": {"name": "重力加速度", "unit": "m/s", "property": "随星球和位置变化"},
            "G": {"name": "重力", "unit": "N", "property": "随 g 值变化，G=mg"}
        },
        "misconceptions": [
            "质量会随重力变化（质量是固有属性，不随位置改变）",
            "失重状态下物体质量为零（失重时重力表现为零，但质量不变）",
            "质量和重量是同一概念（质量是标量，重量是力）",
            "天平在月球上读数会变（天平测质量，读数不变）"
        ],
        "scene_templates": [
            {"name": "地球表面", "motion": "静止或匀速",
             "force": "受重力 G=mg，对支持面有压力"},
            {"name": "月球表面", "motion": "静止或匀速",
             "force": "受重力 G=mg/6，对支持面有压力"},
            {"name": "环绕飞行", "motion": "匀速圆周运动",
             "force": "引力提供向心力，合力不为零"}
        ]
    },
    "newton_law": {
        "keywords": ["牛顿", "力", "加速度", "F=ma", "惯性", "作用力",
                     "反作用力", "合外力", "牛顿第一", "牛顿第二", "牛顿第三"],
        "concept_name": "牛顿运动定律",
        "concept_desc": "牛顿三定律描述了力与运动的关系：惯性定律、F=ma、作用力与反作用力",
        "key_formula": "F = ma",
        "variables": {
            "F": {"name": "合外力", "unit": "N",
                  "property": "物体所受所有力的矢量和"},
            "m": {"name": "质量", "unit": "kg", "property": "物体的惯性量度"},
            "a": {"name": "加速度", "unit": "m/s",
                  "property": "与合外力同向，大小正比于力"}
        },
        "misconceptions": [
            "力是维持运动的原因（力是改变运动状态的原因，不是维持）",
            "质量大的物体重力加速度更大（所有物体自由落体加速度相同）",
            "作用力与反作用力相互抵消（它们作用在不同物体上）"
        ],
        "scene_templates": [
            {"name": "水平面运动", "motion": "匀加速直线",
             "force": "受推力/拉力、摩擦力、支持力、重力"},
            {"name": "斜面运动", "motion": "匀加速直线",
             "force": "受重力分力、摩擦力、支持力"},
            {"name": "竖直运动", "motion": "匀变速直线",
             "force": "受重力和外力（若有）"}
        ]
    },
    "circular_motion": {
        "keywords": ["圆周", "向心", "离心", "匀速圆周", "轨道", "环绕",
                     "角速度", "线速度", "周期", "F=mv/r"],
        "concept_name": "匀速圆周运动",
        "concept_desc": "物体沿圆周运动，速度大小不变、方向不断改变，需要向心力维持",
        "key_formula": "F = mv/r = mωr",
        "variables": {
            "F": {"name": "向心力", "unit": "N",
                  "property": "指向圆心，不是独立力而是合力效果"},
            "v": {"name": "线速度", "unit": "m/s",
                  "property": "沿切线方向，大小不变"},
            "ω": {"name": "角速度", "unit": "rad/s",
                  "property": "单位时间转过的角度"},
            "r": {"name": "半径", "unit": "m", "property": "圆周轨道半径"}
        },
        "misconceptions": [
            "匀速圆周运动合力为零（合力提供向心力，不为零）",
            "向心力是独立力（向心力是效果力，由其他力提供）",
            "圆周运动速度不变（速度方向不断变化）"
        ],
        "scene_templates": [
            {"name": "水平转弯", "motion": "匀速圆周运动",
             "force": "摩擦力或支持力分力提供向心力"},
            {"name": "竖直圆周", "motion": "变速圆周运动",
             "force": "重力与支持力的合力提供向心力"},
            {"name": "卫星轨道", "motion": "匀速圆周运动",
             "force": "万有引力提供向心力"}
        ]
    },
    "energy": {
        "keywords": ["能量", "功", "功率", "动能", "势能", "机械能",
                     "守恒", "动能定理", "W=Fs", "Ep=mgh", "Ek=mv/2"],
        "concept_name": "能量与功",
        "concept_desc": "功是能量转化的量度，机械能包括动能和势能，"
                        "在只有保守力做功时机械能守恒",
        "key_formula": "W = ΔEk = Fs·cosθ",
        "variables": {
            "W": {"name": "功", "unit": "J",
                  "property": "力在位移方向上的累积效应"},
            "Ek": {"name": "动能", "unit": "J",
                   "property": "Ek = mv/2，与速度平方成正比"},
            "Ep": {"name": "势能", "unit": "J",
                   "property": "重力势能 Ep = mgh"},
            "P": {"name": "功率", "unit": "W", "property": "P = W/t = Fv"}
        },
        "misconceptions": [
            "有力就一定有做功（需要有位移，且力与位移不垂直）",
            "机械能守恒时动能不变（动能和势能可以相互转化）",
            "功率越大做功越多（功 = 功率×时间）"
        ],
        "scene_templates": [
            {"name": "自由落体", "motion": "匀加速直线",
             "force": "重力做功，势能转化为动能"},
            {"name": "斜面滑下", "motion": "匀加速直线",
             "force": "重力分力做功，可能有摩擦生热"},
            {"name": "竖直上抛", "motion": "匀减速到最高点",
             "force": "重力做功，动能转化为势能"}
        ]
    },
    "electricity": {
        "keywords": ["电流", "电压", "电阻", "电路", "欧姆", "串联",
                     "并联", "电荷", "I=U/R", "电功率", "P=UI"],
        "concept_name": "欧姆定律与电路",
        "concept_desc": "通过导体的电流与导体两端电压成正比，与导体电阻成反比",
        "key_formula": "I = U/R",
        "variables": {
            "I": {"name": "电流", "unit": "A",
                  "property": "电荷定向移动形成，串联处处相等"},
            "U": {"name": "电压", "unit": "V", "property": "电路两端的电势差"},
            "R": {"name": "电阻", "unit": "Ω",
                  "property": "导体固有属性，与电压电流无关"}
        },
        "misconceptions": [
            "电阻大小由电压和电流决定（R=U/I是计算式，电阻是导体属性）",
            "电流从正极流到负极消耗完了（串联电流处处相等）",
            "短路时电流极大（正确，但需区分电源短路和局部短路）"
        ],
        "scene_templates": [
            {"name": "串联电路", "motion": "—",
             "force": "电流处处相等，电压之和等于总电压"},
            {"name": "并联电路", "motion": "—",
             "force": "电压相等，电流之和等于干路电流"},
            {"name": "混联电路", "motion": "—",
             "force": "先串后并或先并后串，逐级分析"}
        ]
    },
    "momentum": {
        "keywords": ["动量", "冲量", "碰撞", "守恒", "Ft=mv",
                     "弹性碰撞", "非弹性碰撞", "动量定理"],
        "concept_name": "动量与碰撞",
        "concept_desc": "动量是物体运动量的量度，系统不受外力时动量守恒",
        "key_formula": "p = mv, Ft = Δp",
        "variables": {
            "p": {"name": "动量", "unit": "kg·m/s",
                  "property": "矢量，方向与速度相同"},
            "I": {"name": "冲量", "unit": "N·s",
                  "property": "力对时间的累积效应，矢量"},
            "v": {"name": "速度", "unit": "m/s",
                  "property": "碰撞前后速度变化"}
        },
        "misconceptions": [
            "动量守恒时动能也守恒（只有弹性碰撞动能守恒）",
            "质量大的物体动量一定大（动量 p=mv，还与速度有关）",
            "碰撞后物体都停止运动（需要满足动量守恒条件）"
        ],
        "scene_templates": [
            {"name": "一维碰撞", "motion": "匀速直线（碰撞前后）",
             "force": "碰撞内力远大于外力"},
            {"name": "爆炸/反冲", "motion": "向相反方向运动",
             "force": "内力作用，系统动量守恒"}
        ]
    }
}


# ==================================================================
#  关键词权重与消歧规则
# ==================================================================

KEYWORD_WEIGHTS = {
    "质量": 3, "重力": 3, "引力": 3, "g值": 5,
    "自由落体加速度": 5, "月球": 2, "天平": 4,
    "弹簧秤": 4, "称重": 3, "重量": 2, "G=mg": 6,
    "牛顿": 3, "力": 1, "加速度": 3, "F=ma": 6,
    "惯性": 3, "作用力": 2, "反作用力": 3, "合外力": 4,
    "牛顿第一": 5, "牛顿第二": 5, "牛顿第三": 5,
    "圆周": 4, "向心": 4, "离心": 3, "匀速圆周": 5,
    "轨道": 2, "环绕": 2, "角速度": 5, "线速度": 4,
    "周期": 2, "F=mv/r": 6,
    "能量": 2, "功": 2, "功率": 2, "动能": 3, "势能": 3,
    "机械能": 3, "守恒": 2, "动能定理": 4, "W=Fs": 5,
    "Ep=mgh": 5, "Ek=mv/2": 5,
    "电流": 4, "电压": 4, "电阻": 4, "电路": 3,
    "欧姆": 4, "串联": 3, "并联": 3, "电荷": 3,
    "I=U/R": 6, "电功率": 3, "P=UI": 5,
    "动量": 4, "冲量": 4, "碰撞": 3, "Ft=mv": 5,
    "弹性碰撞": 5, "非弹性碰撞": 5, "动量定理": 4,
}

NEGATIVE_KEYWORDS = {
    "quality_gravity": [],
    "newton_law": ["电流", "电压", "电阻", "电路", "欧姆",
                    "电荷", "串联", "并联", "I=U/R"],
    "circular_motion": ["电流", "电压", "电阻", "电路",
                         "欧姆", "I=U/R"],
    "energy": [],
    "electricity": ["牛顿", "惯性", "碰撞", "动量", "冲量",
                     "弹性碰撞", "动量定理"],
    "momentum": ["电流", "电压", "电阻", "电路", "欧姆",
                  "I=U/R", "串联", "并联"],
}

TOPIC_DOMINANCE_THRESHOLD = 1.8
CONFIDENCE_REJECT_THRESHOLD = 0.6


# ==================================================================
#  多策略文本解析器
# ==================================================================

class TextParser:
    """多策略文本解析器（支持选择题/判断题/填空题/解答题）。"""

    PARSER_STRATEGIES = [
        {
            "name": "standard_dot",
            "pattern": re.compile(r'([A-Da-d])[.、)） ]\s*'),
            "min_matches": 2,
            "base_confidence": 0.80,
        },
        {
            "name": "paren_first",
            "pattern": re.compile(r'[（(]([A-Da-d])[）)]\s*'),
            "min_matches": 2,
            "base_confidence": 0.70,
        },
        {
            "name": "chinese_num",
            "pattern": re.compile(r'([①②③④])[.、)） ]\s*'),
            "min_matches": 2,
            "base_confidence": 0.60,
            "label_map": {"①": "A", "②": "B", "③": "C", "④": "D"}
        },
        {
            "name": "spaced",
            "pattern": re.compile(r'([A-Da-d])\s{2,}(\S)'),
            "min_matches": 2,
            "base_confidence": 0.50,
        },
    ]

    # ── 判断题模式 ──
    JUDGMENT_PATTERNS = [
        # A.正确 B.错误 / A.对 B.错 / A.√ B.×
        re.compile(r'([A-Da-d])[.、)） ]\s*((?:正确|错误|对|错|√|×|✓|✗|true|false|T|F))',
                   re.IGNORECASE),
        # (正确/错误) / (对/错) 出现在选项中
    ]

    JUDGMENT_KEYWORDS = [
        "判断", "是否正确", "是否正确", "说法正确", "说法错误",
        "对还是错", "true", "false", "正误",
    ]

    # ── 填空题模式 ──
    FILL_BLANK_PATTERNS = [
        re.compile(r'__{3,}'),           # ____ 或 ___
        re.compile(r'（\s*）'),          # （ ）
        re.compile(r'\(\s*\)'),          # ( )
        re.compile(r'\[?\s*_+\s*\]?'),   # [___]
    ]

    FILL_KEYWORDS = [
        "填空", "填空中", "在横线上", "在____", "____",
    ]

    # ── 解答题模式 ──
    FREE_RESPONSE_KEYWORDS = [
        "求", "计算", "试求", "试计算", "试分析", "证明", "求证",
        "推导", "列出", "写出", "说明", "简述", "论述", "分析",
        "求解", "解答",
    ]

    @staticmethod
    def _try_strategy(text, strategy):
        matches = list(strategy["pattern"].finditer(text))
        if len(matches) < strategy["min_matches"]:
            return None

        label_map = strategy.get("label_map", None)
        confidence = strategy["base_confidence"]

        abcd = []
        for i, m in enumerate(matches):
            raw = m.group(1).upper() if not label_map else label_map.get(m.group(1), "")
            if raw == chr(65 + i) and i < 4:
                abcd.append((raw, m.start(), m.end()))

        if len(abcd) < 2:
            return None

        stem = text[:abcd[0][1]].strip()
        options = []
        for i, (label, ms, me) in enumerate(abcd):
            le = me
            while le < len(text) and text[le] == " ":
                le += 1
            end = abcd[i + 1][1] if i + 1 < len(abcd) else len(text)
            opt_text = text[le:end].strip()
            opt_text = re.sub(r'[；;]。，,]+$', "", opt_text).strip()
            options.append({"label": label, "text": opt_text})

        if len(options) == 4:
            confidence = min(1.0, confidence + 0.10)
        if len(stem) >= 30:
            confidence = min(1.0, confidence + 0.05)

        return stem, options, round(confidence, 2)

    @staticmethod
    def _try_judgment(text):
        """尝试解析判断题（A.正确 B.错误 / 判断对错 / 对不对等）。"""
        # 方式1：A.正确 B.错误 格式
        for pattern in TextParser.JUDGMENT_PATTERNS[:1]:
            matches = list(pattern.finditer(text))
            if len(matches) >= 2:
                pairs = []
                for m in matches:
                    label = m.group(1).upper()
                    value = m.group(2).lower()
                    pairs.append((label, m.start(), m.end(), value))

                if len(pairs) >= 2:
                    stem = text[:pairs[0][1]].strip()
                    stem = re.sub(r'^判断[：:]\s*', '', stem)

                    options = []
                    for i, (label, ms, me, value) in enumerate(pairs[:2]):
                        le = me
                        end = pairs[i + 1][1] if i + 1 < len(pairs) else len(text)
                        opt_text = text[le:end].strip()
                        opt_text = re.sub(r'[；;。，,]+$', '', opt_text).strip()
                        options.append({"label": label, "text": opt_text})

                    conf = 0.75
                    if len(stem) >= 20:
                        conf += 0.10
                    return stem, options, round(min(conf, 1.0), 2)

        # 方式2：无选项的判断题（检测关键词）
        text_clean = text.strip()
        has_keyword = any(kw in text_clean for kw in TextParser.JUDGMENT_KEYWORDS)
        if has_keyword and len(text_clean) < 80:
            # 短文本 + 判断关键词 → 判断题
            stem = re.sub(r'^判断[：:]\s*', '', text_clean)
            stem = re.sub(r'[。！？]+$', '', stem)
            return stem, [], 0.55

        return None

    @staticmethod
    def _try_fill_blank(text):
        """尝试解析填空题（检测 ____ 或 填空 关键词）。"""
        for pattern in TextParser.FILL_BLANK_PATTERNS:
            if pattern.search(text):
                stem = text.strip()
                # 检测有几个空
                blanks = [m for m in pattern.finditer(text)]
                options = []
                for i in range(len(blanks)):
                    label = chr(65 + i)  # A, B, C...
                    options.append({"label": label, "text": ""})
                conf = 0.60 + min(len(blanks) * 0.05, 0.20)
                if any(kw in text for kw in TextParser.FILL_KEYWORDS):
                    conf += 0.10
                return stem, options, round(min(conf, 1.0), 2)
        return None

    @staticmethod
    def _try_free_response(text):
        """尝试解析解答题（检测 求/计算/证明 等关键词）。"""
        text_clean = text.strip()
        # 必须有足够的字数（解答题一般较长）
        if len(text_clean) < 15:
            return None
        # 检测关键词
        has_keyword = any(kw in text_clean for kw in TextParser.FREE_RESPONSE_KEYWORDS)
        # 检测是否包含物理量纲或公式
        has_condition = bool(re.search(
            r'\d+\.?\d*\s*(m/s|kg|N|J|W|V|A|Ω|m|g|km|h|s)', text_clean))
        if has_keyword or has_condition:
            return text_clean, [], 0.55
        return None

    @staticmethod
    def detect_question_type(parsed: dict, raw_text: str = "") -> str:
        """
        根据解析结果自动检测题型。
        返回: "选择题" | "判断题" | "填空题" | "解答题"
        """
        options = parsed.get("options", [])
        opt_count = len(options)
        parser_used = parsed.get("_parser_used", "none")

        # 如果标准解析器检测到4个选项，肯定是选择题
        if opt_count == 4 and parser_used != "none":
            return "选择题"

        # 如果有2个选项，检查是否是判断题
        if opt_count == 2:
            opt_texts = [o.get("text", "").lower() for o in options]
            judgment_markers = {"正确", "错误", "对", "错", "√", "×", "✓", "✗",
                                "true", "false", "t", "f", "是", "否"}
            match_count = sum(1 for t in opt_texts if t in judgment_markers or
                             any(m in t for m in judgment_markers))
            if match_count >= 1:
                return "判断题"

        # 检查是否有填空标记
        if opt_count == 0:
            for pattern in TextParser.FILL_BLANK_PATTERNS:
                if pattern.search(raw_text or parsed.get("stem", "")):
                    return "填空题"

        # 检查是否有解答题关键词
        if opt_count == 0:
            text = raw_text or parsed.get("stem", "")
            has_kw = any(kw in text for kw in TextParser.FREE_RESPONSE_KEYWORDS)
            has_condition = bool(re.search(
                r'\d+\.?\d*\s*(m/s|kg|N|J|W|V|A|Ω|m|g|km|h|s)', text))
            if has_kw or has_condition:
                return "解答题"

        # 2个选项但未匹配到判断题标记 → 仍然是选择题（如 A.方案一 B.方案二）
        if opt_count >= 2:
            return "选择题"

        # 以上都不是
        return "选择题"

    @staticmethod
    def parse(raw_text):
        if not raw_text or not isinstance(raw_text, str):
            return {"stem": "", "options": [],
                    "_parser_used": "none", "_parser_confidence": 0.0,
                    "_question_type": "选择题"}
        text = raw_text.strip()
        if not text:
            return {"stem": "", "options": [],
                    "_parser_used": "none", "_parser_confidence": 0.0,
                    "_question_type": "选择题"}

        # 1. 先尝试标准选择题策略
        best = None
        best_conf = 0.0
        best_name = "none"

        for strategy in TextParser.PARSER_STRATEGIES:
            result = TextParser._try_strategy(text, strategy)
            if result:
                stem, opts, conf = result
                if conf > best_conf:
                    best = (stem, opts)
                    best_conf = conf
                    best_name = strategy["name"]

        if best:
            parsed = {"stem": best[0], "options": best[1],
                      "_parser_used": best_name, "_parser_confidence": best_conf}
            parsed["_question_type"] = TextParser.detect_question_type(parsed, text)
            return parsed

        # 2. 尝试判断题
        j_result = TextParser._try_judgment(text)
        if j_result:
            stem, opts, conf = j_result
            parsed = {"stem": stem, "options": opts,
                      "_parser_used": "judgment", "_parser_confidence": conf}
            parsed["_question_type"] = "判断题"
            return parsed

        # 3. 尝试填空题
        f_result = TextParser._try_fill_blank(text)
        if f_result:
            stem, opts, conf = f_result
            parsed = {"stem": stem, "options": opts,
                      "_parser_used": "fill_blank", "_parser_confidence": conf}
            parsed["_question_type"] = "填空题"
            return parsed

        # 4. 尝试解答题
        fr_result = TextParser._try_free_response(text)
        if fr_result:
            stem, opts, conf = fr_result
            parsed = {"stem": stem, "options": opts,
                      "_parser_used": "free_response", "_parser_confidence": conf}
            parsed["_question_type"] = "解答题"
            return parsed

        return {"stem": text, "options": [],
                "_parser_used": "none", "_parser_confidence": 0.0,
                "_question_type": "选择题"}

    @staticmethod
    def extract_conditions(text):
        pattern = re.compile(r"(\d+\.?\d*)\s*(m/s|m/s|m|kg|N|J|W|V|A|Ω|s|h|km|g|cm|mm)")
        return [m.group(0).strip() for m in pattern.finditer(text)]


# ==================================================================
#  规则分析引擎（加权版）
# ==================================================================

class RuleEngine:
    """基于加权关键词的物理题目分析，含负向消歧。"""

    @staticmethod
    def detect_topics(text):
        scores = []
        for tid, topic in PHYSICS_TOPICS.items():
            matched = [kw for kw in topic["keywords"] if kw in text]
            weighted = sum(KEYWORD_WEIGHTS.get(kw, 1) for kw in matched)
            neg_hits = [nk for nk in NEGATIVE_KEYWORDS.get(tid, []) if nk in text]
            for _ in neg_hits:
                weighted *= 0.5
            if matched or neg_hits:
                scores.append({
                    "topic_id": tid,
                    "score": len(matched),
                    "weighted_score": round(weighted, 1),
                    "matched_keywords": matched,
                    "negative_hits": neg_hits
                })
        scores.sort(key=lambda x: x["weighted_score"], reverse=True)
        return scores

    @staticmethod
    def build_core_concept(topic_id):
        topic = PHYSICS_TOPICS.get(topic_id)
        if not topic:
            return None
        return {
            "name": topic["concept_name"],
            "definition": topic["concept_desc"],
            "key_formula": topic["key_formula"],
            "variables": copy.deepcopy(topic["variables"]),
            "common_misconceptions": list(topic["misconceptions"])
        }

    @staticmethod
    def analyze_scenario(text, topic_id):
        topic = PHYSICS_TOPICS.get(topic_id)
        scenes = []
        if topic and topic.get("scene_templates"):
            for tmpl in topic["scene_templates"]:
                scenes.append({"name": tmpl["name"], "motion": tmpl["motion"],
                               "force": tmpl["force"]})
        conditions = TextParser.extract_conditions(text)
        ctx = (text[:80] + "...") if len(text) > 80 else text
        return {"context": ctx,
                "key_conditions": "；".join(conditions) if conditions else "需进一步分析",
                "scenes": scenes}

    @staticmethod
    def analyze_options(options):
        return [{"label": o["label"], "statement": o["text"],
                 "correct": False, "reason": "需 LLM 或人工判断"}
                for o in options]

    @staticmethod
    def guess_answer_from_markers(options):
        for opt in options:
            if re.match(r"^[✅✔✓○●]", opt["text"]):
                return opt["label"]
        return ""


# ==================================================================
#  LLM 接口
# ==================================================================

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False


def _build_llm_prompt(parsed, topic_hints):
    """根据题型构建动态 LLM Prompt。"""
    question_type = parsed.get("_question_type", "选择题")
    option_lines = "\n".join(f"{o['label']}. {o['text']}" for o in parsed["options"])
    hint_text = ""
    if topic_hints:
        names = []
        for t in topic_hints:
            topic = PHYSICS_TOPICS.get(t.get("topic_id", ""))
            if topic:
                names.append(topic["concept_name"])
        if names:
            hint_text = f'（提示：该题可能涉及 "{", ".join(names)}"）'

    # ---- 根据不同题型构建不同的 output_example ----
    if question_type == "判断题":
        output_example = json.dumps({
            "topic": "知识点名称",
            "subject": "物理",
            "question_type": "判断题",
            "core_concept": {"name": "", "definition": "", "key_formula": "",
                            "variables": {}, "common_misconceptions": []},
            "scenario_analysis": {"context": "", "key_conditions": "", "scenes": []},
            "judgment": {"statement": "原判断句", "is_correct": False,
                         "explanation": "解析说明"},
            "answer": "正确/错误"
        }, ensure_ascii=False, indent=2)

        system_prompt = (
            "You are a physics problem analyzer. Output ONLY valid JSON.\n"
            "Rules:\n"
            "1. Determine if the given statement is correct or incorrect\n"
            '2. Set judgment.is_correct to true/false accordingly\n'
            "3. Provide a clear physics-based explanation\n"
            '4. Set answer to "正确" or "错误"\n'
            "5. No markdown formatting, pure JSON only\n"
            f"Format:\n{output_example}")
        user_prompt = (
            f"Analyze this physics true/false question:\n\n"
            f"【Stem】\n{parsed['stem']}\n\n"
            f"{hint_text}\n\n"
            f"Output the analysis in the specified JSON format.")

    elif question_type == "填空题":
        output_example = json.dumps({
            "topic": "知识点名称",
            "subject": "物理",
            "question_type": "填空题",
            "core_concept": {"name": "", "definition": "", "key_formula": "",
                            "variables": {}, "common_misconceptions": []},
            "scenario_analysis": {"context": "", "key_conditions": "", "scenes": []},
            "fill_blanks": [
                {"position": 1, "answer": "答案内容", "explanation": "解析说明"}
            ],
            "answer": "答案内容"
        }, ensure_ascii=False, indent=2)

        system_prompt = (
            "You are a physics problem analyzer. Output ONLY valid JSON.\n"
            "Rules:\n"
            "1. Fill in each blank with the correct physics answer\n"
            "2. Provide explanation for each answer\n"
            "3. Include units where applicable\n"
            "4. No markdown formatting, pure JSON only\n"
            f"Format:\n{output_example}")
        user_prompt = (
            f"Analyze this physics fill-in-the-blank question:\n\n"
            f"【Stem】\n{parsed['stem']}\n\n"
            f"{hint_text}\n\n"
            f"Output the analysis in the specified JSON format.")

    elif question_type == "解答题":
        output_example = json.dumps({
            "topic": "知识点名称",
            "subject": "物理",
            "question_type": "解答题",
            "core_concept": {"name": "", "definition": "", "key_formula": "",
                            "variables": {}, "common_misconceptions": []},
            "scenario_analysis": {"context": "", "key_conditions": "", "scenes": []},
            "solution_steps": [
                {"step": 1, "description": "解题步骤", "formula": "", "result": ""}
            ],
            "answer": "最终答案"
        }, ensure_ascii=False, indent=2)

        system_prompt = (
            "You are a physics problem analyzer. Output ONLY valid JSON.\n"
            "Rules:\n"
            "1. Break down the solution into clear steps\n"
            "2. Show formulas used at each step\n"
            "3. Provide the final answer with units\n"
            "4. No markdown formatting, pure JSON only\n"
            f"Format:\n{output_example}")
        user_prompt = (
            f"Analyze this physics free-response question:\n\n"
            f"【Question】\n{parsed['stem']}\n\n"
            f"{hint_text}\n\n"
            f"Output the solution steps in the specified JSON format.")

    else:
        # 选择题（默认）
        output_example = json.dumps({
            "topic": "知识点名称",
            "subject": "物理",
            "question_type": "选择题",
            "core_concept": {"name": "", "definition": "", "key_formula": "",
                            "variables": {}, "common_misconceptions": []},
            "scenario_analysis": {"context": "", "key_conditions": "", "scenes": []},
            "options_analysis": [{"label": "A", "statement": "", "correct": False, "reason": ""}],
            "answer": ""
        }, ensure_ascii=False, indent=2)

        system_prompt = (
            "You are a physics problem analyzer. Output ONLY valid JSON.\n"
            "Rules:\n"
            "1. Mark exactly ONE option as correct (correct: true)\n"
            "2. The answer field must match the correct option's label\n"
            "3. Each option must have a reason field with physics basis\n"
            "4. If unsure, set answer to empty string\n"
            "5. No markdown formatting, pure JSON only\n"
            f"Format:\n{output_example}")
        user_prompt = (
            f"Analyze this physics multiple-choice question:\n\n"
            f"【Stem】\n{parsed['stem']}\n\n"
            f"【Options】\n{option_lines}\n{hint_text}\n\n"
            f"Output the analysis in the specified JSON format.")

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


async def call_llm(messages, llm_config):
    api_key = llm_config.get("api_key", "")
    if not api_key:
        raise ValueError("LLM not configured: missing api_key")
    endpoint = llm_config.get("endpoint", "https://api.openai.com/v1/chat/completions")
    model = llm_config.get("model", "gpt-4o-mini")
    max_tokens = llm_config.get("max_tokens", 4096)
    temperature = llm_config.get("temperature", 0.0)

    payload = {"model": model, "messages": messages,
               "max_tokens": max_tokens, "temperature": temperature}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    if _HAS_HTTPX:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    else:
        import urllib.request
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(endpoint, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))

    if not data.get("choices"):
        raise ValueError("LLM returned empty")
    return data["choices"][0]["message"]["content"] or ""


def parse_llm_response(content):
    if not content:
        return None
    text = content.strip()
    cm = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if cm:
        text = cm.group(1).strip()
    try:
        result = json.loads(text)
        return _repair_llm_result(result)
    except json.JSONDecodeError:
        bm = re.search(r"\{[\s\S]*\}", text)
        if bm:
            try:
                result = json.loads(bm.group(0))
                return _repair_llm_result(result)
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Cannot parse LLM JSON: {text[:200]}")


def _repair_llm_result(result: dict) -> dict:
    """修复 LLM 返回结果中常见的结构问题。"""
    if not isinstance(result, dict):
        return result

    # 修复 scenes 字段：LLM 可能返回字符串或缺失字段的 dict
    sa = result.get("scenario_analysis")
    if isinstance(sa, dict):
        scenes = sa.get("scenes", [])
        if scenes:
            if isinstance(scenes[0], str):
                sa["scenes"] = [{"name": s, "motion": "", "force": ""} for s in scenes]
            elif isinstance(scenes[0], dict) and "name" not in scenes[0]:
                # LLM 返回了缺 name 的场景（如只有 description/analysis）
                for s in scenes:
                    if "description" in s and "name" not in s:
                        s.setdefault("name", s["description"][:20])
                    elif "analysis" in s and "name" not in s:
                        s.setdefault("name", s["analysis"][:20])

    # 修复 question_type
    result.setdefault("question_type", "选择题")

    # 修复 options_analysis: 确保每个选项有 label, statement, correct, reason
    opts = result.get("options_analysis", [])
    for i, opt in enumerate(opts):
        if isinstance(opt, str):
            import string as _s
            label = _s.ascii_uppercase[i] if i < 26 else "?"
            opts[i] = {"label": label, "statement": opt,
                       "correct": False, "reason": ""}
        if not isinstance(opt.get("correct"), bool):
            opt["correct"] = False
        if not opt.get("reason"):
            opt["reason"] = ""
        if not opt.get("statement"):
            opt["statement"] = ""

    return result


# ==================================================================
#  结果合并器
# ==================================================================

class ResultMerger:
    @staticmethod
    def merge(rule_result, llm_result, parsed):
        final = copy.deepcopy(rule_result)
        if llm_result:
            if llm_result.get("topic"): final["topic"] = llm_result["topic"]
            if llm_result.get("subject"): final["subject"] = llm_result["subject"]
            if llm_result.get("core_concept"):
                lc = llm_result["core_concept"]
                rc = final.get("core_concept") or {}
                merged = copy.deepcopy(rc)
                for k in ("name", "definition", "key_formula"):
                    if lc.get(k): merged[k] = lc[k]
                if lc.get("variables"):
                    merged.setdefault("variables", {}).update(lc["variables"])
                if lc.get("common_misconceptions"):
                    merged["common_misconceptions"] = lc["common_misconceptions"]
                final["core_concept"] = merged
            if llm_result.get("scenario_analysis"):
                ls = llm_result["scenario_analysis"]
                rs = final.get("scenario_analysis") or {}
                merged = copy.deepcopy(rs)
                if ls.get("context"): merged["context"] = ls["context"]
                if ls.get("key_conditions"): merged["key_conditions"] = ls["key_conditions"]
                if ls.get("scenes"): merged["scenes"] = ls["scenes"]
                final["scenario_analysis"] = merged
            if llm_result.get("options_analysis"):
                lopts = llm_result["options_analysis"]
                plabels = [o["label"] for o in parsed["options"]]
                llabels = [o["label"] for o in lopts]
                if llabels == plabels:
                    final["options_analysis"] = lopts
            if llm_result.get("answer"):
                final["answer"] = llm_result["answer"]
        return ResultMerger._ensure_complete(final, parsed)

    @staticmethod
    def _ensure_complete(result, parsed):
        qtype = parsed.get("_question_type", result.get("question_type", "选择题"))
        result.setdefault("topic", "未识别的物理主题")
        result.setdefault("subject", "物理")
        # 保留自动检测的题型，不硬编码
        if "question_type" not in result or result["question_type"] == "选择题":
            result["question_type"] = qtype
        result.setdefault("core_concept", {"name": "待分析",
            "definition": "需进一步分析",
            "key_formula": "", "variables": {}, "common_misconceptions": []})
        cc = result["core_concept"]
        cc.setdefault("variables", {})
        cc.setdefault("common_misconceptions", [])
        result.setdefault("scenario_analysis", {
            "context": (parsed["stem"][:80] + "...") if len(parsed["stem"]) > 80 else parsed["stem"],
            "key_conditions": "", "scenes": []})
        result["scenario_analysis"].setdefault("scenes", [])
        # 非选择题型不强制要求 options_analysis
        if not result.get("options_analysis") or len(result["options_analysis"]) == 0:
            if qtype in ("选择题", "判断题"):
                result["options_analysis"] = [
                    {"label": o["label"], "statement": o["text"],
                     "correct": False, "reason": "待分析"}
                    for o in parsed["options"]]
            else:
                result["options_analysis"] = []
        result.setdefault("answer", "")
        return result


# ==================================================================
#  LLM 验证器
# ==================================================================

class LLMValidator:
    @staticmethod
    def validate(llm_result, parsed, rule_hints=None):
        issues = []
        if not llm_result:
            return {"valid": False, "issues": ["LLM returned empty"], "score": 0.0}

        qtype = parsed.get("_question_type", "选择题")

        # 非选择题：放宽验证
        if qtype in ("解答题", "填空题"):
            # 只需检查 topic 存在
            if not llm_result.get("topic"):
                issues.append("Missing topic")
            return {"valid": len(issues) == 0, "issues": issues,
                    "score": max(0.0, 1.0 - len(issues) * 0.25)}

        # 选择题/判断题：严格验证选项
        answer = llm_result.get("answer", "")
        valid_labels = [o["label"] for o in parsed.get("options", [])]
        if answer and answer not in valid_labels:
            issues.append(f"Answer '{answer}' not in options ({valid_labels})")
        lopts = llm_result.get("options_analysis", [])
        if len(lopts) != len(valid_labels):
            issues.append(f"Option count mismatch: LLM {len(lopts)} vs expected {len(valid_labels)}")
        else:
            llabels = [o["label"] for o in lopts]
            if llabels != valid_labels:
                issues.append(f"Label mismatch: {llabels} vs {valid_labels}")
        correct_count = sum(1 for o in lopts if o.get("correct"))
        if correct_count == 0:
            issues.append("No correct option marked")
        elif correct_count > 1:
            issues.append(f"{correct_count} correct options (should be 1)")
        if answer and lopts:
            for o in lopts:
                if o["label"] == answer and not o.get("correct"):
                    issues.append(f"Answer {answer} but correct=false")
                if o.get("correct") and o["label"] != answer:
                    issues.append(f"{o['label']} correct but answer={answer}")
        for o in lopts:
            if o.get("correct") and not o.get("reason", "").strip():
                issues.append(f"Correct option {o['label']} missing reason")
        score = max(0.0, 1.0 - len(issues) * 0.25)
        return {"valid": len(issues) == 0, "issues": issues, "score": round(score, 2)}


# ==================================================================
#  置信度评估器
# ==================================================================

class ConfidenceScorer:
    @staticmethod
    def evaluate(parsed, detected, llm_used=False, llm_valid=False, answer_verified=False):
        scores = {}
        qtype = parsed.get("_question_type", "选择题")

        parser_conf = parsed.get("_parser_confidence", 0.0)
        opt_count = len(parsed.get("options", []))
        stem_len = len(parsed.get("stem", ""))
        parsing_score = parser_conf
        if opt_count == 4:
            parsing_score = min(1.0, parsing_score + 0.15)
        elif opt_count >= 2:
            parsing_score = min(1.0, parsing_score + 0.05)
        elif qtype in ("填空题", "解答题"):
            # 填空题/解答题不需要选项，给予基础分
            parsing_score = max(parsing_score, 0.45)
        if stem_len >= 20:
            parsing_score = min(1.0, parsing_score + 0.10)
        scores["parsing"] = {"score": round(parsing_score, 3),
            "method": parsed.get("_parser_used", "unknown"),
            "options_found": opt_count, "stem_length": stem_len}

        if detected:
            primary = detected[0]
            primary_ws = primary.get("weighted_score", 0)
            dominance = 3.0
            if len(detected) > 1:
                second_ws = detected[1].get("weighted_score", 0)
                if second_ws > 0:
                    dominance = primary_ws / second_ws
            raw_conf = min(1.0, primary_ws / 15.0)
            dom_bonus = 0.15 if dominance >= TOPIC_DOMINANCE_THRESHOLD else (0.05 if dominance >= 1.2 else -0.10)
            topic_score = min(1.0, max(0.0, raw_conf + dom_bonus))
            scores["topic_detection"] = {"score": round(topic_score, 3),
                "primary": detected[0]["topic_id"], "dominance": round(dominance, 2),
                "alternatives": [d["topic_id"] for d in detected[1:3]]}
        else:
            scores["topic_detection"] = {"score": 0.0, "primary": None,
                                          "dominance": 0.0, "alternatives": []}

        if qtype in ("解答题", "填空题"):
            # 非选择题型：选项维度权重降低
            opt_score = 0.60 if (llm_used and llm_valid) else (0.40 if llm_used else 0.30)
            scores["options"] = {"score": round(opt_score, 3),
                "verified_by_llm": llm_used and llm_valid, "count": opt_count}
        else:
            opt_score = 0.90 if (llm_used and llm_valid) else (0.50 if llm_used else 0.30)
            if opt_count >= 2:
                opt_score = min(1.0, opt_score + 0.05)
            scores["options"] = {"score": round(opt_score, 3),
                "verified_by_llm": llm_used and llm_valid, "count": opt_count}

        ans_score = 0.90 if answer_verified else (0.75 if (llm_used and llm_valid) else (0.40 if llm_used else 0.10))
        scores["answer"] = {"score": round(ans_score, 3),
            "method": "llm+rule" if answer_verified else ("llm" if llm_used else "rule_only")}

        # 非选择题：降低 options 权重，提高 topic 权重
        if qtype in ("解答题", "填空题"):
            weights = {"parsing": 0.25, "topic_detection": 0.30, "options": 0.20, "answer": 0.25}
        else:
            weights = {"parsing": 0.25, "topic_detection": 0.15, "options": 0.35, "answer": 0.25}
        overall = sum(scores[k]["score"] * weights[k] for k in weights)
        scores["overall"] = round(overall, 3)
        return scores


# ==================================================================
#  拒绝守卫
# ==================================================================

class RejectionGuard:
    @staticmethod
    def decide(confidence, parsed):
        warnings = []
        overall = confidence.get("overall", 0.0)
        parsing = confidence.get("parsing", {}).get("score", 0.0)
        topic = confidence.get("topic_detection", {}).get("score", 0.0)
        answer = confidence.get("answer", {}).get("score", 0.0)
        opt_count = len(parsed.get("options", []))
        qtype = parsed.get("_question_type", "选择题")

        # 解析置信度检查（不同题型不同阈值）
        if qtype in ("解答题", "填空题"):
            # 解答题/填空题允许无选项，降低解析门槛
            if parsing < 0.3:
                warnings.append(f"题目解析置信度偏低（{parsing:.2f}）")
        else:
            # 选择题/判断题需要选项
            if parsing < 0.4:
                return {"accepted": False, "status": "rejected",
                        "warnings": ["无法解析题目格式：未能识别选项标记（A/B/C/D）"],
                        "rejection_reason": "题目格式无法解析"}
            if opt_count < 2:
                return {"accepted": False, "status": "rejected",
                        "warnings": [f"选项数量不足（{opt_count}个）"],
                        "rejection_reason": "选项不足"}

        if overall < CONFIDENCE_REJECT_THRESHOLD:
            warnings.append(f"整体置信度不足（{overall:.2f}），建议人工复核")
        if topic < 0.3:
            warnings.append("未能准确匹配物理主题")
        if answer < 0.3:
            warnings.append("无法确定正确答案，需要人工判断")

        if warnings:
            return {"accepted": False, "status": "needs_review",
                    "warnings": warnings, "rejection_reason": warnings[0]}
        return {"accepted": True, "status": "auto_resolved",
                "warnings": [], "rejection_reason": None}


# ==================================================================
#  主入口
# ==================================================================

def analyze_problem(text, llm_config=None, verbose=False):
    """同步模式分析（纯规则）。"""
    if verbose:
        print("[Layer1] analyze_problem (sync)")
    parsed = TextParser.parse(text)
    if not parsed["stem"]:
        raise ValueError("无法解析题目文本")
    qtype = parsed.get("_question_type", "选择题")
    detected = RuleEngine.detect_topics(text)
    primary_id = (detected[0]["topic_id"] if detected else None)
    topic = PHYSICS_TOPICS.get(primary_id, {})
    rule_result = {
        "topic": topic.get("concept_name", "未识别的物理主题"),
        "subject": "物理", "question_type": qtype,
        "core_concept": RuleEngine.build_core_concept(primary_id) if primary_id else {},
        "scenario_analysis": RuleEngine.analyze_scenario(text, primary_id) if primary_id else {},
        "options_analysis": RuleEngine.analyze_options(parsed["options"]),
        "answer": RuleEngine.guess_answer_from_markers(parsed["options"])
    }
    return ResultMerger.merge(rule_result, None, parsed)


async def analyze_problem_async(text, llm_config=None, verbose=False):
    """异步模式分析（支持 LLM）。"""
    if verbose:
        print("[Layer1] analyze_problem_async")
    parsed = TextParser.parse(text)
    if not parsed["stem"]:
        raise ValueError("无法解析题目文本")
    qtype = parsed.get("_question_type", "选择题")
    detected = RuleEngine.detect_topics(text)
    primary_id = (detected[0]["topic_id"] if detected else None)
    topic = PHYSICS_TOPICS.get(primary_id, {})
    rule_result = {
        "topic": topic.get("concept_name", "未识别的物理主题"),
        "subject": "物理", "question_type": qtype,
        "core_concept": RuleEngine.build_core_concept(primary_id) if primary_id else {},
        "scenario_analysis": RuleEngine.analyze_scenario(text, primary_id) if primary_id else {},
        "options_analysis": RuleEngine.analyze_options(parsed["options"]),
        "answer": RuleEngine.guess_answer_from_markers(parsed["options"])
    }
    llm_result = None
    if llm_config and llm_config.get("api_key"):
        try:
            hints = [{"topic_id": d["topic_id"]} for d in detected]
            messages = _build_llm_prompt(parsed, hints)
            response = await call_llm(messages, llm_config)
            llm_result = parse_llm_response(response)
        except Exception as e:
            if verbose:
                print(f"[Layer1] LLM error: {e}")
    return ResultMerger.merge(rule_result, llm_result, parsed)


async def analyze_problem_safe(text, llm_config=None, verbose=False):
    """
    [推荐] 安全模式分析 —— 带置信度评估和拒绝机制。

    返回结果包含 status 字段：
        "auto_resolved"  - 自动分析完成，可信任
        "needs_review"   - 置信度不足，需要人工复核
        "rejected"       - 无法解析，需要人工处理

    调用方应优先检查 status：
        if result["status"] != "auto_resolved":
            # 显示人工审核提示
    """
    if verbose:
        print("[Layer1] analyze_problem_safe")

    # 1. 多策略解析
    parsed = TextParser.parse(text)
    qtype = parsed.get("_question_type", "选择题")
    if not parsed["stem"]:
        return {"status": "rejected",
                "confidence": {"overall": 0.0},
                "warnings": ["无法解析题目文本，请检查格式"],
                "rejection_reason": "格式无法解析",
                "topic": "", "subject": "物理", "question_type": qtype,
                "core_concept": {}, "scenario_analysis": {},
                "options_analysis": [], "answer": ""}

    # 2. 加权主题检测
    detected = RuleEngine.detect_topics(text)
    primary_id = (detected[0]["topic_id"] if detected else None)

    # 3. 规则分析
    topic = PHYSICS_TOPICS.get(primary_id, {})
    rule_result = {
        "topic": topic.get("concept_name", "未识别的物理主题"),
        "subject": "物理", "question_type": qtype,
        "core_concept": RuleEngine.build_core_concept(primary_id) if primary_id else {},
        "scenario_analysis": RuleEngine.analyze_scenario(text, primary_id) if primary_id else {},
        "options_analysis": RuleEngine.analyze_options(parsed["options"]),
        "answer": RuleEngine.guess_answer_from_markers(parsed["options"])
    }

    # 4. LLM 增强 + 验证
    llm_result = None
    llm_valid = False
    llm_used = False

    if llm_config and llm_config.get("api_key"):
        llm_used = True
        try:
            hints = [{"topic_id": d["topic_id"]} for d in detected]
            messages = _build_llm_prompt(parsed, hints)
            response = await call_llm(messages, llm_config)
            llm_result = parse_llm_response(response)
            validation = LLMValidator.validate(llm_result, parsed)
            llm_valid = validation["valid"]
            if verbose and not llm_valid:
                print(f"[Layer1] LLM validation: {validation['issues']}")
        except Exception as e:
            if verbose:
                print(f"[Layer1] LLM error: {e}")

    # 5. 合并
    final = ResultMerger.merge(rule_result, llm_result, parsed)

    # 6. 置信度评估
    answer_verified = llm_valid and llm_result is not None and bool(llm_result.get("answer"))
    confidence = ConfidenceScorer.evaluate(parsed, detected, llm_used, llm_valid, answer_verified)

    # 7. 拒绝决策
    guard = RejectionGuard.decide(confidence, parsed)

    final["confidence"] = confidence
    final["warnings"] = guard["warnings"]
    final["status"] = guard["status"]

    if verbose:
        print(f"[Layer1] status={guard['status']}, confidence={confidence['overall']:.3f}")

    return final


def get_supported_topics():
    return [{"id": tid, "name": t["concept_name"], "keywords": t["keywords"]}
            for tid, t in PHYSICS_TOPICS.items()]
