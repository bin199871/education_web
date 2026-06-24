"""
Layer 1 — 题目分析 Agent (Python 版)
============================================================
混合模式：规则解析框架 + 可插拔 LLM 后端

用法:
    from layer1_agent import analyze_problem

    # 纯规则模式
    result = analyze_problem("题目文本...")

    # LLM 增强模式
    result = await analyze_problem("题目文本...", llm_config={...})
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
            "g": {"name": "重力加速度", "unit": "m/s²", "property": "随星球和位置变化"},
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
            "a": {"name": "加速度", "unit": "m/s²",
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
                     "角速度", "线速度", "周期", "F=mv²/r"],
        "concept_name": "匀速圆周运动",
        "concept_desc": "物体沿圆周运动，速度大小不变、方向不断改变，需要向心力维持",
        "key_formula": "F = mv²/r = mω²r",
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
                     "守恒", "动能定理", "W=Fs", "Ep=mgh", "Ek=mv²/2"],
        "concept_name": "能量与功",
        "concept_desc": "功是能量转化的量度，机械能包括动能和势能，"
                        "在只有保守力做功时机械能守恒",
        "key_formula": "W = ΔEk = Fs·cosθ",
        "variables": {
            "W": {"name": "功", "unit": "J",
                  "property": "力在位移方向上的累积效应"},
            "Ek": {"name": "动能", "unit": "J",
                   "property": "Ek = ½mv²，与速度平方成正比"},
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
#  文本解析引擎
# ==================================================================

class TextParser:
    """解析题目文本，提取题干和选项。"""

    @staticmethod
    def parse(raw_text: str) -> dict:
        """
        将原始题目文本解析为结构化片段。
        返回 {"stem": str, "options": [{"label":str, "text":str}]}
        """
        if not raw_text or not isinstance(raw_text, str):
            return {"stem": "", "options": []}

        text = raw_text.strip()

        # 匹配选项标签：A. / A、 / A) / A． (全角点) 等
        option_pattern = re.compile(r'([A-Da-d])[.、)）．\s]\s*')
        matches = list(option_pattern.finditer(text))

        if len(matches) < 2:
            return {"stem": text, "options": []}

        # 取前 4 个按 A,B,C,D 顺序出现的选项
        abcd = []
        for i, m in enumerate(matches):
            expected = chr(65 + i)  # A, B, C, D
            if m.group(1).upper() == expected and i < 4:
                abcd.append(m)

        if len(abcd) < 2:
            return {"stem": text, "options": []}

        # 题干 = 文本开始到第一个选项之前
        stem = text[:abcd[0].start()].strip()

        options = []
        for i, match in enumerate(abcd):
            # 选项文本从标签之后开始
            label_end = match.start() + len(match.group(0))
            while label_end < len(text) and text[label_end] == ' ':
                label_end += 1

            if i + 1 < len(abcd):
                end = abcd[i + 1].start()
            else:
                end = len(text)

            opt_text = text[label_end:end].strip()
            opt_text = re.sub(r'[；;。，,]+$', '', opt_text).strip()
            options.append({"label": match.group(1).upper(), "text": opt_text})

        return {"stem": stem, "options": options}

    @staticmethod
    def extract_conditions(text: str) -> list:
        """从题干中提取数值条件（数字+单位）。"""
        pattern = re.compile(r'(\d+\.?\d*)\s*'
                             r'(m/s²|m/s|m|kg|N|J|W|V|A|Ω|s|h|km|g|cm|mm)')
        return [m.group(0).strip() for m in pattern.finditer(text)]


# ==================================================================
#  规则分析引擎
# ==================================================================

class RuleEngine:
    """基于规则库的物理题目分析。"""

    @staticmethod
    def detect_topics(text: str) -> list:
        """
        检测题目涉及的物理主题。
        返回按匹配关键词数量排序的列表：
            [{"topic_id": str, "score": int, "matched_keywords": [str]}]
        """
        scores = []
        for topic_id, topic in PHYSICS_TOPICS.items():
            matched = [kw for kw in topic["keywords"] if kw in text]
            if matched:
                scores.append({
                    "topic_id": topic_id,
                    "score": len(matched),
                    "matched_keywords": matched
                })
        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores

    @staticmethod
    def build_core_concept(topic_id: str) -> Optional[dict]:
        """基于检测到的主题生成核心概念 JSON。"""
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
    def analyze_scenario(text: str, topic_id: str) -> dict:
        """基于题目文本和主题生成场景分析。"""
        topic = PHYSICS_TOPICS.get(topic_id)
        scenes = []
        if topic and topic.get("scene_templates"):
            for tmpl in topic["scene_templates"]:
                scenes.append({
                    "name": tmpl["name"],
                    "motion": tmpl["motion"],
                    "force": tmpl["force"]
                })

        conditions = TextParser.extract_conditions(text)
        context = (text[:80] + '…') if len(text) > 80 else text

        return {
            "context": context,
            "key_conditions": "；".join(conditions) if conditions else "需进一步分析",
            "scenes": scenes
        }

    @staticmethod
    def analyze_options(options: list) -> list:
        """对选项进行初步分析（规则版无法判断对错）。"""
        return [
            {"label": o["label"], "statement": o["text"],
             "correct": False, "reason": "需 LLM 或人工判断"}
            for o in options
        ]

    @staticmethod
    def guess_answer_from_markers(options: list) -> str:
        """尝试从特殊标记猜测正确答案（如 ✅/✔ 前缀）。"""
        for opt in options:
            if re.match(r'^[✅✔✓○●]', opt["text"]):
                return opt["label"]
        return ""


# ==================================================================
#  LLM 接口
# ==================================================================

# LLM 调用尝试导入 httpx（优先）或 urllib
try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False


def _build_llm_prompt(parsed: dict, topic_hints: list) -> list:
    """构建发送给 LLM 的消息列表。"""
    option_lines = "\n".join(
        f"{o['label']}. {o['text']}" for o in parsed["options"]
    )

    hint_text = ""
    if topic_hints:
        names = []
        for t in topic_hints:
            topic = PHYSICS_TOPICS.get(t.get("topic_id", ""))
            if topic:
                names.append(topic["concept_name"])
        if names:
            hint_text = f'（提示：该题可能涉及 "{", ".join(names)}"）'

    # 构造输出格式示例
    output_example = json.dumps({
        "topic": "知识点名称（如「质量与重力辨析」）",
        "subject": "物理",
        "question_type": "选择题",
        "core_concept": {
            "name": "核心概念名称",
            "definition": "概念定义（一句话）",
            "key_formula": "核心公式",
            "variables": {
                "变量名如 m": {"name": "中文名", "unit": "单位",
                            "property": "关键属性说明"}
            },
            "common_misconceptions": ["常见误解1（含澄清）", "常见误解2"]
        },
        "scenario_analysis": {
            "context": "题目背景情境描述（一句话概括）",
            "key_conditions": "关键已知条件",
            "scenes": [
                {"name": "场景名", "motion": "运动状态", "force": "受力情况"}
            ]
        },
        "options_analysis": [
            {"label": "A", "statement": "选项原文",
             "correct": False, "reason": "判断理由"}
        ],
        "answer": "正确的选项字母（如 A/B/C/D）"
    }, ensure_ascii=False, indent=2)

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个物理题目分析专家。你需要分析一道物理选择题，"
                "输出结构化的 JSON 分析结果。\n\n"
                "输出必须严格遵循以下 JSON 格式"
                "（不加 markdown 代码块标记，直接输出纯 JSON）：\n"
                f"{output_example}"
            )
        },
        {
            "role": "user",
            "content": (
                f"请分析以下物理选择题：\n\n"
                f"【题干】\n{parsed['stem']}\n\n"
                f"【选项】\n{option_lines}\n"
                f"{hint_text}\n\n"
                f"请严格按照上述 JSON 格式输出分析结果。"
            )
        }
    ]
    return messages


async def call_llm(messages: list, llm_config: dict) -> str:
    """
    调用 LLM API（兼容 OpenAI Chat Completion 格式）。

    参数:
        messages: [{"role": str, "content": str}]
        llm_config: {"api_key": str, "endpoint": str, "model": str, ...}
    返回:
        LLM 返回的文本内容
    """
    api_key = llm_config.get("api_key", "")
    if not api_key:
        raise ValueError("LLM 未配置：缺少 api_key")

    endpoint = llm_config.get(
        "endpoint", "https://api.openai.com/v1/chat/completions"
    )
    model = llm_config.get("model", "gpt-4o-mini")
    max_tokens = llm_config.get("max_tokens", 4096)
    temperature = llm_config.get("temperature", 0.1)

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    if _HAS_HTTPX:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    else:
        # fallback to urllib (同步，仅用于无法安装 httpx 的环境)
        import urllib.request
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(endpoint, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))

    if not data.get("choices"):
        raise ValueError("LLM 返回结果为空")

    return data["choices"][0]["message"]["content"] or ""


def parse_llm_response(content: str) -> Optional[dict]:
    """解析 LLM 返回的 JSON，兼容可能的 markdown 包裹。"""
    if not content:
        return None

    text = content.strip()

    # 去掉 markdown 代码块标记 ```json ... ```
    code_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if code_match:
        text = code_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试提取最外层 {} 的内容
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError(f"无法解析 LLM 返回的 JSON: {text[:200]}")


# ==================================================================
#  结果合并器
# ==================================================================

class ResultMerger:
    """合并规则分析结果和 LLM 分析结果。"""

    @staticmethod
    def merge(rule_result: dict, llm_result: Optional[dict],
              parsed: dict) -> dict:
        """以规则结果为基线，LLM 结果补充增强。"""
        final = copy.deepcopy(rule_result)

        if llm_result:
            if llm_result.get("topic"):
                final["topic"] = llm_result["topic"]
            if llm_result.get("subject"):
                final["subject"] = llm_result["subject"]

            # 核心概念 — 合并
            if llm_result.get("core_concept"):
                lc = llm_result["core_concept"]
                rc = final.get("core_concept") or {}
                merged = copy.deepcopy(rc)
                if lc.get("name"):
                    merged["name"] = lc["name"]
                if lc.get("definition"):
                    merged["definition"] = lc["definition"]
                if lc.get("key_formula"):
                    merged["key_formula"] = lc["key_formula"]
                if lc.get("variables"):
                    merged.setdefault("variables", {})
                    merged["variables"].update(lc["variables"])
                if lc.get("common_misconceptions"):
                    merged["common_misconceptions"] = lc["common_misconceptions"]
                final["core_concept"] = merged

            # 场景分析
            if llm_result.get("scenario_analysis"):
                ls = llm_result["scenario_analysis"]
                rs = final.get("scenario_analysis") or {}
                merged = copy.deepcopy(rs)
                if ls.get("context"):
                    merged["context"] = ls["context"]
                if ls.get("key_conditions"):
                    merged["key_conditions"] = ls["key_conditions"]
                if ls.get("scenes"):
                    merged["scenes"] = ls["scenes"]
                final["scenario_analysis"] = merged

            # 选项分析 — 用 LLM 的（包含对错判断）
            if llm_result.get("options_analysis"):
                llm_opts = llm_result["options_analysis"]
                # 验证标签一致性
                parsed_labels = [o["label"] for o in parsed["options"]]
                llm_labels = [o["label"] for o in llm_opts]
                if llm_labels == parsed_labels:
                    final["options_analysis"] = llm_opts

            # 答案
            if llm_result.get("answer"):
                final["answer"] = llm_result["answer"]

        # 补齐字段
        return ResultMerger._ensure_complete(final, parsed)

    @staticmethod
    def _ensure_complete(result: dict, parsed: dict) -> dict:
        """确保输出结构的完整性。"""
        result.setdefault("topic", "未识别的物理主题")
        result.setdefault("subject", "物理")
        result.setdefault("question_type", "选择题")

        # 核心概念
        result.setdefault("core_concept", {
            "name": "待分析",
            "definition": "需进一步分析",
            "key_formula": "",
            "variables": {},
            "common_misconceptions": []
        })
        cc = result["core_concept"]
        cc.setdefault("variables", {})
        cc.setdefault("common_misconceptions", [])

        # 场景分析
        result.setdefault("scenario_analysis", {
            "context": (parsed["stem"][:80] + '…')
                       if len(parsed["stem"]) > 80 else parsed["stem"],
            "key_conditions": "",
            "scenes": []
        })
        result["scenario_analysis"].setdefault("scenes", [])

        # 选项分析
        if (not result.get("options_analysis")
                or len(result["options_analysis"]) == 0):
            result["options_analysis"] = [
                {"label": o["label"], "statement": o["text"],
                 "correct": False, "reason": "待分析"}
                for o in parsed["options"]
            ]

        result.setdefault("answer", "")

        return result


# ==================================================================
#  主入口
# ==================================================================

def analyze_problem(text: str, llm_config: Optional[dict] = None,
                    verbose: bool = False) -> dict:
    """
    分析一道物理题目（纯规则模式，同步）。

    参数:
        text: 原始题目文本
        llm_config: 可选，配置为 {"api_key": str, ...} 时返回 LLM 增强版本
        verbose: 是否输出详细日志
    返回:
        结构化分析结果 dict
    """
    if verbose:
        print("[Layer1] 开始分析题目…")

    # 第1步：文本解析
    parsed = TextParser.parse(text)
    if verbose:
        print(f"[Layer1] 文本解析完成，题干: {parsed['stem'][:50]}…")

    if not parsed["stem"]:
        raise ValueError("无法解析题目文本，请检查格式")

    # 第2步：规则分析
    detected = RuleEngine.detect_topics(text)
    primary_id = (detected[0]["topic_id"] if detected else None)
    if verbose:
        print(f"[Layer1] 检测到的主题: "
              f"{[d['topic_id'] for d in detected]}")

    topic = PHYSICS_TOPICS.get(primary_id, {})
    rule_result = {
        "topic": topic.get("concept_name", "未识别的物理主题"),
        "subject": "物理",
        "question_type": "选择题",
        "core_concept": (RuleEngine.build_core_concept(primary_id)
                         if primary_id else {
                             "name": "待分析", "definition": "需进一步分析",
                             "key_formula": "", "variables": {},
                             "common_misconceptions": []
                         }),
        "scenario_analysis": (RuleEngine.analyze_scenario(text, primary_id)
                              if primary_id else {
                                  "context": (parsed["stem"][:80] + '…'
                                              if len(parsed["stem"]) > 80
                                              else parsed["stem"]),
                                  "key_conditions": "", "scenes": []
                              }),
        "options_analysis": RuleEngine.analyze_options(parsed["options"]),
        "answer": RuleEngine.guess_answer_from_markers(parsed["options"])
    }

    # 第3步：合并（此处无 LLM，直接返回规则结果）
    if verbose:
        print("[Layer1] 分析完成")
    return ResultMerger.merge(rule_result, None, parsed)


async def analyze_problem_async(text: str,
                                llm_config: Optional[dict] = None,
                                verbose: bool = False) -> dict:
    """
    分析一道物理题目（支持 LLM 增强，异步）。

    参数:
        text: 原始题目文本
        llm_config: LLM 配置 {"api_key": str, "endpoint": str, "model": str}
                    为 None 时等同于同步纯规则模式
        verbose: 是否输出详细日志
    返回:
        结构化分析结果 dict
    """
    if verbose:
        print("[Layer1] 开始分析题目…")

    parsed = TextParser.parse(text)
    if verbose:
        print(f"[Layer1] 文本解析完成，{len(parsed['options'])} 个选项")

    if not parsed["stem"]:
        raise ValueError("无法解析题目文本，请检查格式")

    detected = RuleEngine.detect_topics(text)
    primary_id = (detected[0]["topic_id"] if detected else None)

    topic = PHYSICS_TOPICS.get(primary_id, {})
    rule_result = {
        "topic": topic.get("concept_name", "未识别的物理主题"),
        "subject": "物理",
        "question_type": "选择题",
        "core_concept": (RuleEngine.build_core_concept(primary_id)
                         if primary_id else {
                             "name": "待分析", "definition": "需进一步分析",
                             "key_formula": "", "variables": {},
                             "common_misconceptions": []
                         }),
        "scenario_analysis": (RuleEngine.analyze_scenario(text, primary_id)
                              if primary_id else {
                                  "context": (parsed["stem"][:80] + '…'
                                              if len(parsed["stem"]) > 80
                                              else parsed["stem"]),
                                  "key_conditions": "", "scenes": []
                              }),
        "options_analysis": RuleEngine.analyze_options(parsed["options"]),
        "answer": RuleEngine.guess_answer_from_markers(parsed["options"])
    }

    # LLM 增强
    llm_result = None
    if llm_config and llm_config.get("api_key"):
        if verbose:
            print("[Layer1] 调用 LLM 进行深度分析…")
        try:
            hints = [{"topic_id": d["topic_id"]} for d in detected]
            messages = _build_llm_prompt(parsed, hints)
            response = await call_llm(messages, llm_config)
            llm_result = parse_llm_response(response)
            if verbose:
                print(f"[Layer1] LLM 分析完成")
        except Exception as e:
            if verbose:
                print(f"[Layer1] LLM 分析失败: {e}")
            llm_result = None

    final = ResultMerger.merge(rule_result, llm_result, parsed)
    return final


def get_supported_topics() -> list:
    """获取支持的物理主题列表。"""
    return [
        {"id": tid, "name": t["concept_name"],
         "keywords": t["keywords"]}
        for tid, t in PHYSICS_TOPICS.items()
    ]
