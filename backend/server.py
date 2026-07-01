"""
Layer 1 — 后端分析服务 (Python / FastAPI)
============================================================
职责：接收前端题目文本 → 调用 layer1_agent.py 分析
       → 如配置了 LLM_API_KEY 且请求启用了 LLM，则进行 LLM 增强

启动：
    pip install -r requirements.txt
    python server.py              # http://localhost:3001

开发热重载：
    pip install uvicorn
    uvicorn server:app --reload --port 3001
"""

import os
import sys
import json
from pathlib import Path

# 确保 backend/ 在模块搜索路径中
_backend_dir = str(Path(__file__).resolve().parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import uvicorn

from layer1_agent import (
    analyze_problem_safe,
    get_supported_topics,
    PHYSICS_TOPICS,
    TextParser,
    RuleEngine,
    call_llm,
)
from layer2_engine import generate_act_plan
from layer2_solution_steps import generate_solution_steps, solution_steps_to_text
from layer3_storyboard import expand_storyboard, format_as_text
from physics_simulator import simulate_slope_problem
from physics_param_extractor import extract_physics_params, run_simulation_from_text
from layer4_engine import orchestrate, generate_html_timeline
from template_engine import get_engine, map_params

# ─── 加载 .env ───
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Layer 1 题目分析服务", version="1.0.0")

# ─── CORS ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 静态文件服务目录（指向 frontend/2d/） ───
STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / "2d"


# ─── LLM 配置 ───
def get_llm_config() -> dict | None:
    api_key = (os.environ.get("LLM_API_KEY") or "").strip()
    if not api_key:
        return None
    return {
        "api_key": api_key,
        "endpoint": (os.environ.get("LLM_ENDPOINT")
                     or "https://api.openai.com/v1/chat/completions").strip(),
        "model": (os.environ.get("LLM_MODEL") or "gpt-4o-mini").strip(),
    }


# ─── 请求/响应模型 ───

class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="题目文本")
    useLLM: bool = Field(default=False, description="是否启用 LLM 增强")


class AnalyzeRequestWithModel(AnalyzeRequest):
    model: str | None = Field(None, description="LLM 模型名称")


class AnalyzeResponse(BaseModel):
    success: bool
    data: dict | None = None
    meta: dict | None = None
    error: str | None = None


# ─── API 路由 ───


import json as _json
import re as _re


async def call_llm_analyze(text: str, llm_config: dict) -> dict:
    """调用 LLM 分析物理题目，返回 {solution_text, problem_type}。"""
    prompt = (
        "你是一位物理教师。请分析以下物理题，输出 JSON（严格只输出 JSON，不要用 markdown 代码块）。\n\n"
        'JSON 格式：{"solution_text": "完整解题过程", "problem_type": "题目类型"}\n\n'
        "要求：\n"
        "1. solution_text 用中文，不要用 LaTeX 符号\n"
        "2. 每个小问用（1）（2）（3）编号，末尾用「答：」给出答案\n"
        "3. 公式用纯文本，如 F = qE、1/2 mv^2\n"
        "4. 问题类型从以下选择：electric_pendulum, conveyor_belt, collision, projectile, inclined_plane, vertical_circular, board_block, spring_oscillator, magnetic_deflection, connected_bodies, conductor_cutting, locomotive, circuit_analysis, astronomy, mechanical_wave, gas_law, coulomb_force, light_refraction, atomic_energy, ac_transformer, unknown\n\n"
        "题目：" + text
    )
    messages = [
        {"role": "user", "content": prompt}
    ]
    raw = await call_llm(messages, llm_config)
    print(f"[LLM_DEBUG] raw response ({len(raw)} chars): {raw[:500]}")
    if not raw:
        raise ValueError("LLM 返回空")
    import json, re
    m = re.search(r"\{" + r"[\s\S]*" + r"\}", raw)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return {"solution_text": raw.strip(), "problem_type": "unknown"}


async def call_llm_analyze(text: str, llm_config: dict) -> dict:
    """调用 LLM 分析物理题目，返回 {solution_text, problem_type}。"""
    types_list = (
        "electric_pendulum, conveyor_belt, collision, projectile, inclined_plane, "
        "vertical_circular, board_block, spring_oscillator, magnetic_deflection, "
        "connected_bodies, conductor_cutting, locomotive, circuit_analysis, "
        "astronomy, mechanical_wave, gas_law, coulomb_force, light_refraction, "
        "atomic_energy, ac_transformer, unknown"
    )
    prompt_system = (
        "你是一位物理教师。请分析以下物理题目，输出 JSON 格式：\n"
        + '{"solution_text": "完整的解题过程", "problem_type": "题目类型标识"}\n\n'
        + "要求：\n"
        + "1. solution_text 不要使用 LaTeX 符号（不要用 \\( 或 \\)）\n"
        + "2. 解题过程包括公式、代入数值、计算过程、最终答案\n"
        + "3. 每个小问用（1）（2）（3）编号，末尾用「答：」给出答案\n"
        + "4. 公式用纯文本表示，例如 F = qE、1/2 mv^2\n"
        + "5. problem_type 从以下列表选择最匹配的一个：\n"
        + "   " + types_list
    )
    messages = [
        {"role": "system", "content": prompt_system},
        {"role": "user", "content": "请解答以下物理题，输出 JSON：\n\n" + text}
    ]
    raw = await call_llm(messages, llm_config)
    if not raw:
        raise ValueError("LLM 返回空")
    m = _re.search(r'\{[\s\S]*\}', raw)
    if m:
        try:
            return _json.loads(m.group(0))
        except _json.JSONDecodeError:
            pass
    raise ValueError("LLM 返回的不是有效 JSON: " + raw[:200])


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """分析物理题目。"""
    text = req.text.strip() if req.text else ""
    if not text:
        raise HTTPException(status_code=400, detail="题目文本不能为空")

    parsed = TextParser.parse(text)
    if not parsed["stem"]:
        raise HTTPException(
            status_code=400,
            detail="无法解析题目格式，请确保包含题干和 A/B/C/D 选项"
        )

    # 检测主题（用于 meta）
    detected = RuleEngine.detect_topics(text)
    detected_info = []
    for d in detected:
        topic = PHYSICS_TOPICS.get(d["topic_id"])
        detected_info.append({
            "id": d["topic_id"],
            "name": topic["concept_name"] if topic else d["topic_id"],
            "score": d["score"],
        })

    # LLM 配置
    llm_config = get_llm_config()
    use_llm = req.useLLM and llm_config is not None

    llm_cfg = llm_config if use_llm else None

    try:
        result = await analyze_problem_safe(text, llm_cfg)
        return AnalyzeResponse(
            success=True,
            data=result,
            meta={
                "mode": "llm_enhanced" if use_llm else "rule_only",
                "llmAvailable": llm_config is not None,
                "llmUsed": use_llm,
                "detectedTopics": detected_info,
                "analysisStatus": result.get("status", "auto_resolved"),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/acts", response_model=AnalyzeResponse)
async def analyze_acts(req: AnalyzeRequest):
    """分析物理题目并生成幕结构规划（Layer 1 + Layer 2）。"""
    text = req.text.strip() if req.text else ""
    if not text:
        raise HTTPException(status_code=400, detail="题目文本不能为空")

    parsed = TextParser.parse(text)
    if not parsed["stem"]:
        raise HTTPException(
            status_code=400,
            detail="无法解析题目格式，请确保包含题干和 A/B/C/D 选项"
        )

    detected = RuleEngine.detect_topics(text)
    detected_info = []
    for d in detected:
        topic = PHYSICS_TOPICS.get(d["topic_id"])
        detected_info.append({
            "id": d["topic_id"],
            "name": topic["concept_name"] if topic else d["topic_id"],
            "score": d["score"],
        })

    llm_config = get_llm_config()
    use_llm = req.useLLM and llm_config is not None
    llm_cfg = llm_config if use_llm else None

    try:
        layer1_result = await analyze_problem_safe(text, llm_cfg)
        act_plan = generate_act_plan(layer1_result)
        return AnalyzeResponse(
            success=True,
            data={
                "layer1": layer1_result,
                "layer2": act_plan
            },
            meta={
                "mode": "llm_enhanced" if use_llm else "rule_only",
                "llmAvailable": llm_config is not None,
                "llmUsed": use_llm,
                "detectedTopics": detected_info,
                "layers": ["layer1", "layer2"]
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 模板类型 → 预期主题关键词（用于检测 topic 是否匹配）
_TOPIC_ALIASES = {
    "electric_pendulum": ["电场", "带电", "单摆", "电场力", "电荷"],
    "conveyor_belt": ["传送带", "皮带", "摩擦"],
    "collision": ["碰撞", "动量", "弹簧"],
    "projectile": ["平抛", "抛体", "水平抛出"],
    "inclined_plane": ["斜面", "斜坡"],
    "coulomb_force": ["库仑", "电荷", "静电力"],
    "light_refraction": ["折射", "反射", "光线", "光"],
    "atomic_energy": ["能级", "跃迁", "氢原子", "光谱"],
    "ac_transformer": ["交流电", "变压器", "正弦"],
}

async def generate_llm_solution(text: str, llm_config: dict) -> str | None:
    """调用 LLM 直接生成详细的解题过程文本。"""
    messages = [
        {"role": "system", "content": "你是一位物理教师，请根据题目生成详细的解题过程。按以下格式输出：\n\n"
         "（1）步骤标题\n"
         "  公式：相关公式\n"
         "  推导过程和计算\n"
         "  答：最终答案\n\n"
         "（2）步骤标题\n"
         "  公式：相关公式\n"
         "  推导过程和计算\n"
         "  答：最终答案\n\n"
         "要求：\n"
         "1. 每个小问一个步骤，使用（1）（2）（3）编号\n"
         "2. 每个步骤包含公式、代入数值、计算过程、最终答案\n"
         "3. 用中文输出\n"
         "4. 如果题目有多个小问，每个小问独立成段\n"
         "5. 关键数字和公式用 **加粗** 标注"},
        {"role": "user", "content": f"请解答以下物理题，给出完整解题过程：\n\n{text}"}
    ]
    result = await call_llm(messages, llm_config)
    if result and len(result) > 50:
        return result.strip()
    return None




@app.post("/api/analyze/storyboard", response_model=AnalyzeResponse)
async def analyze_storyboard(req: AnalyzeRequest):
    """分析物理题目：调用 LLM 获取解题过程和题目类型。"""
    text = req.text.strip() if req.text else ""
    if not text:
        raise HTTPException(status_code=400, detail="题目文本不能为空")

    llm_config = get_llm_config()
    use_llm = req.useLLM and llm_config is not None
    llm_cfg = llm_config if use_llm else None

    if not llm_cfg:
        return AnalyzeResponse(
            success=True,
            data={
                "solution_text": "需要配置 LLM API Key 才能分析题目",
                "problem_type": "unknown",
            }
        )

    try:
        result = await call_llm_analyze(text, llm_cfg)
        return AnalyzeResponse(
            success=True,
            data={
                "solution_text": result.get("solution_text", "暂无解题过程"),
                "problem_type": result.get("problem_type", "unknown"),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/physics/simulate-from-text")
async def physics_simulate_from_text(req: AnalyzeRequestWithModel):
    """从题目文本提取物理参数并运行仿真。"""
    text = req.text.strip() if req.text else ""
    if not text:
        raise HTTPException(status_code=400, detail="题目文本不能为空")

    try:
        # 提取参数
        extracted = extract_physics_params(text)
        if not extracted["phases"]:
            return {
                "success": True,
                "simulatable": False,
                "extracted": extracted,
                "message": "未能自动匹配到物理仿真模板"
            }

        # 运行仿真
        result = run_simulation_from_text(text)
        if result is None:
            return {
                "success": True,
                "simulatable": False,
                "extracted": extracted,
                "message": "仿真运行失败"
            }

        return {
            "success": True,
            "simulatable": True,
            "extracted": extracted,
            "frames": result["frames"],
            "total_frames": result["total_frames"],
            "fps": result["fps"],
            "summary": result["summary"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── 题目目标检测（覆盖全部 16 种题型） ───

GOAL_PATTERNS = {
    # ── 通用力学 ──
    'force_analysis':    [r'电场力', r'F电', r'电磁力', r'安培力', r'F安', r'洛伦兹力'],
    'resultant_force':   [r'合力', r'F合', r'合外力'],
    'velocity':          [r'(?<!最低点)(?<!底端)(?<!末端)(?<!A点)速度(?!.*最低点)(?!.*底端)', r'v='],
    'velocity_bottom':   [r'最低点.*速度', r'底端速度', r'末端速度', r'速度.*A点', r'vA', r'v_A'],
    'acceleration':      [r'加速度', r'a=', r'a\s*='],
    'tension_force':     [r'拉力', r'张力', r'T=', r'绳子.*拉力'],
    'friction':          [r'摩擦力', r'f=', r'摩擦因数'],
    'displacement':      [r'位移', r'滑行距离', r'滑行.*长度', r'移动.*距离'],
    'work_energy':       [r'做功', r'功W', r'W=', r'动能', r'动能定理'],

    # ── 电场 / 单摆 ──
    'electric_force':    [r'电场力', r'F电'],
    'energy_change':     [r'电势能', r'ΔEp', r'能量变', r'能量转化'],
    'tension_max':       [r'拉力.*最大', r'最大拉力', r'Tmax', r'T_max'],

    # ── 斜面 / 粗糙面 ──
    'slide_velocity':    [r'底端速度', r'底部速度', r'滑到.*速度', r'到底.*速度'],
    'rough_friction':    [r'摩擦力大小', r'摩擦力f', r'摩擦生热', r'Q='],

    # ── 平抛 ──
    'landing_time':      [r'落地时间', r'飞行时间', r'空中运动时间', r't='],
    'horizontal_range':  [r'水平射程', r'水平距离', r'落地点', r'x='],
    'landing_velocity':  [r'落地速度', r'末速度', r'着地速度'],

    # ── 竖直圆周 ──
    'force_top':         [r'最高点.*压力', r'最高点.*拉力', r'N₁', r'N1'],
    'force_bottom':      [r'最低点.*压力', r'最低点.*拉力', r'N₂', r'N2'],
    'force_diff':        [r'压力差', r'ΔN'],

    # ── 传送带 / 板块 ──
    'co_speed_time':     [r'共速.*时间', r'达到.*速度.*时间', r'时间t'],
    'relative_disp':     [r'相对位移', r'划痕', r'痕迹长度', r'Δx'],
    'co_velocity':       [r'共同速度', r'共速.*速度', r'v共', r'一起运动.*速度'],

    # ── 弹簧振子 ──
    'oscillation_period':   [r'振动周期', r'周期T\b', r'振动.*周期'],
    'oscillation_freq':     [r'振动频率', r'频率f\b'],
    'amplitude':            [r'振幅A', r'A=', r'振幅'],
    'elastic_energy':       [r'弹性势能', r'Ep弹', r'弹簧.*能量'],

    # ── 碰撞 / 动量 ──
    'post_velocity':     [r'碰后速度', r'碰撞.*速度', r'vA', r'vB', r'v₁\'', r"v1'", r'v₂\'', r"v2'"],
    'impulse':           [r'冲量', r'I=', r'I\s*='],
    'spring_compress':   [r'弹簧.*压缩', r'最大形变', r'xmax', r'x_max', r'压缩.*形变'],
    'energy_loss':       [r'能量损失', r'ΔE', r'损失.*动能', r'机械能损失'],
    'collision_elastic': [r'弹性碰撞'],
    'collision_inelastic': [r'非弹性碰撞', r'完全非弹性'],

    # ── 连接体 ──
    'sys_acceleration':  [r'加速度a', r'整体加速度', r'系统加速度'],
    'rope_tension':      [r'绳子拉力', r'细绳.*拉力', r'T='],

    # ── 磁场偏转 ──
    'orbit_radius':      [r'轨道半径', r'回旋半径', r'r=', r'圆周半径'],
    'deflect_angle':     [r'偏转角', r'偏转.*角度', r'偏转.*θ'],

    # ── 导体棒切割 ──
    'induced_emf':       [r'电动势', r'E=', r'感应电动势'],
    'induced_current':   [r'电流', r'I=', r'感应电流'],
    'amp_force':         [r'安培力', r'F安'],
    'terminal_velocity': [r'终极速度', r'最大速度', r'稳定速度', r'匀速.*速度'],

    # ── 机车启动 ──
    'max_speed':         [r'最大速度', r'v_m', r'vm='],
    'engine_power':      [r'功率P', r'P=', r'额定功率', r'牵引力功率'],

    # ── 电路 ──
    'circuit_current':   [r'电流I', r'I=', r'电流表示数', r'通过.*电流'],
    'circuit_voltage':   [r'电压U', r'U=', r'电压表示数', r'路端电压'],
    'circuit_power':     [r'功率P', r'P=', r'电功率', r'热功率', r'输出功率'],

    # ── 万有引力 ──
    'orbit_speed':       [r'线速度', r'轨道速度', r'v='],
    'orbit_period':      [r'公转周期', r'周期T', r'T=', r'环绕周期'],
    'cosmic_speed':      [r'宇宙速度', r'第一宇宙速度', r'第二宇宙速度'],
    'gravity_force':     [r'万有引力', r'F万', r'引力大小'],

    # ── 机械波 ──
    'wavelength':        [r'波长λ', r'λ=', r'波长'],
    'wave_speed':        [r'波速v', r'v=', r'波速', r'传播速度'],
    'wave_frequency':    [r'频率f', r'f=', r'ν='],

    # ── 气体 ──
    'gas_pressure':      [r'压强p', r'p=', r'气体压强'],
    'gas_volume':        [r'体积V', r'V=', r'气体体积'],
    'gas_temperature':   [r'气体温度', r'温度T\b', r'气体.*温度'],
    'gas_work':          [r'气体做功', r'W=', r'对外做功'],
}


def extract_goals(text: str) -> list:
    """从题目文本中提取问题目标列表。"""
    import re as _re2
    goals = []
    for goal_id, patterns in GOAL_PATTERNS.items():
        for p in patterns:
            if _re2.search(p, text):
                goals.append(goal_id)
                break
    return goals


# ─── 模板引擎 API ───

from pydantic import Field as PydanticField

class TemplateGenRequest(BaseModel):
    text: str = PydanticField(..., description="题目文本")
    template_id: str | None = PydanticField(None, description="指定模板ID，null则自动匹配")
    useLLM: bool = PydanticField(False, description="是否启用 LLM 辅助匹配")


# ─── LLM 辅助匹配（可选） ───

TEMPLATE_LIST = [
    ("electric_pendulum", "电场中带电单摆"),
    ("inclined_plane", "斜面+摩擦力"),
    ("projectile", "平抛运动"),
    ("vertical_circular", "竖直圆周运动"),
    ("conveyor_belt", "传送带问题"),
    ("board_block", "板块模型"),
    ("spring_oscillator", "弹簧振子"),
    ("collision", "动量守恒/碰撞"),
    ("connected_bodies", "连接体问题"),
    ("magnetic_deflection", "带电粒子在磁场中偏转"),
    ("conductor_cutting", "导体棒切割磁感线"),
    ("locomotive", "机车启动"),
    ("circuit_analysis", "电路动态分析"),
    ("astronomy", "万有引力/天体运动"),
    ("mechanical_wave", "机械波"),
    ("gas_law", "气体实验定律"),
]


async def llm_match_template(text: str, llm_cfg: dict) -> str | None:
    """使用 LLM 匹配题型，返回 template_id 或 None。"""
    import httpx

    type_list = "\n".join([f'{i+1}. {tid} - {label}' for i, (tid, label) in enumerate(TEMPLATE_LIST)])

    prompt = f"""你是一个物理题目分类助手。分析以下物理题目，判断它最匹配哪种题型。

可选题型：
{type_list}

题目：
{text[:1500]}

请只返回一个JSON对象：{{"template_id": "题型ID"}}
不要返回其他内容。"""

    headers = {
        "Authorization": f"Bearer {llm_cfg['api_key']}",
        "Content-Type": "application/json",
    }
    body = {
        "model": llm_cfg["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 100,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(llm_cfg["endpoint"], json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()

            import json as _json
            # 尝试从返回中提取 JSON
            if content.startswith("{"):
                result = _json.loads(content)
            else:
                start = content.find("{")
                end = content.rfind("}") + 1
                result = _json.loads(content[start:end])

            tid = result.get("template_id", "")
            # 验证返回的 template_id 是否有效
            valid_ids = [t[0] for t in TEMPLATE_LIST]
            return tid if tid in valid_ids else None
    except Exception as e:
        print(f"[LLM匹配] 失败: {e}")
        return None


def _build_param_prompt(tid: str, engine) -> str:
    """根据模板 ID 构建参数提取提示。"""
    tpl = engine.registry.get(tid)
    if not tpl:
        return ""
    schema = tpl.get("param_schema", {})
    lines = [f'"{key}": {schema["type"]} 类型, 单位 {schema.get("unit","")}, 例如 {schema["default"]}'
             for key, schema in schema.items()]
    return "需要提取的参数：\n" + "\n".join(lines)


async def llm_extract_params(text: str, tid: str, engine, llm_cfg: dict) -> dict | None:
    """使用 LLM 从题目文本中提取物理参数。"""
    import httpx, json as _json

    param_desc = _build_param_prompt(tid, engine)
    if not param_desc:
        return None

    prompt = f"""你是一个物理参数提取助手。从以下物理题目中提取指定的参数值。

{param_desc}

题目：
{text[:2000]}

请只返回一个JSON对象，包含你能找到的所有参数值（数值类型）。找不到的参数不要包含。例如：
{{"m": 0.2, "q": 0.0005}}
不要返回其他内容。"""

    headers = {
        "Authorization": f"Bearer {llm_cfg['api_key']}",
        "Content-Type": "application/json",
    }
    body = {
        "model": llm_cfg["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 300,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(llm_cfg["endpoint"], json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()

            if content.startswith("{"):
                result = _json.loads(content)
            else:
                start = content.find("{")
                end = content.rfind("}") + 1
                result = _json.loads(content[start:end])

            # 只保留数值类型的值
            clean = {k: v for k, v in result.items() if isinstance(v, (int, float))}
            return clean if clean else None
    except Exception as e:
        print(f"[LLM参数] 提取失败: {e}")
        return None


@app.post("/api/template/generate")
async def template_generate(req: TemplateGenRequest):
    """从题目文本生成模板讲解动画。"""
    text = req.text.strip() if req.text else ""
    if not text:
        raise HTTPException(status_code=400, detail="题目文本不能为空")

    engine = get_engine()
    llm_cfg = get_llm_config()

    # 先尝试 LLM 匹配（如果开启且配置了 LLM）
    tid = None
    if req.useLLM and llm_cfg:
        tid = await llm_match_template(text, llm_cfg)
        if tid:
            print(f"[模板] LLM匹配: {tid}")

    # LLM 未匹配到时降级到规则匹配
    if not tid:
        tid = engine.match_template_by_text(text)
        if tid:
            print(f"[模板] 规则匹配: {tid}")

    if not tid:
        return {"success": False, "fallback": True, "message": "未匹配到动画模板"}

    # 从题目提取物理参数（正则 + 可选 LLM 增强）
    physics = extract_physics_params(text)
    mapped = map_params(tid, physics.get("params", {}))

    # 可选：LLM 参数提取增强（LLM 值优先于正则）
    if req.useLLM and llm_cfg and tid:
        llm_params = await llm_extract_params(text, tid, engine, llm_cfg)
        if llm_params:
            tpl_schema = engine.registry.get(tid, {}).get('param_schema', {})
            for key, val in llm_params.items():
                if val is not None and key in tpl_schema:
                    mapped[key] = val
                    print(f"[参数] LLM设定 {key}={val}")

    # 注入物理过程阶段信息（用于模板场景裁剪）
    mapped["_phases"] = [p["type"] for p in physics.get("phases", [])]

    # 检测题目问数（用于动态面板）
    import re as _re
    questions = _re.findall(r'[（(]\d+[）)）]\s*', text)
    mapped["_question_count"] = max(len(questions), 1)

    # 检测初始角度（用于场景编排）
    angle_match = _re.search(
        r'(?:θ₀|θ_0|初[始]?[位]?[角]?|与竖直方向夹角)\s*[=∶:：]?\s*(\d+)\s*[°度]',
        text
    )
    if angle_match:
        mapped["theta0"] = float(angle_match.group(1))

    # 检测问题目标（用于场景积木编排）
    mapped["_goals"] = extract_goals(text)

    # 将模板默认值填入未提取到的参数
    tpl = engine.registry.get(tid)
    if tpl:
        for key, schema in tpl.get("param_schema", {}).items():
            if key not in mapped:
                mapped[key] = schema.get("default")

    try:
        html = engine.render(tid, mapped)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    try:
        output_path = STATIC_DIR / "pages" / "premium-output.html"
        with open(str(output_path), "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        print(f"[模板] 写入失败: {e}")
    return {"success": True, "template_id": tid, "html": html, "fallback": False, "message": "生成成功"}


@app.get("/api/template/list")
async def template_list():
    """获取所有可用模板列表。"""
    engine = get_engine()
    return {"templates": engine.list_templates()}


@app.get("/api/status")
async def status():
    """服务器状态和 LLM 配置情况。"""
    llm_config = get_llm_config()
    return {
        "status": "running",
        "version": "3.0.0",
        "llm": {
            "configured": llm_config is not None,
            "endpoint": llm_config["endpoint"] if llm_config else None,
            "model": llm_config["model"] if llm_config else None,
        },
        "topics": [t["name"] for t in get_supported_topics()],
    }


# ─── 静态文件兜底路由（必须在 API 路由之后） ───

@app.api_route("/{path:path}", methods=["GET"])
async def serve_static(path: str):
    """提供静态文件服务。"""
    file_path = STATIC_DIR / path
    if file_path.is_file():
        return FileResponse(str(file_path))
    # 如果路径是目录或不存在，尝试 index.html
    index_path = file_path / "index.html"
    if index_path.is_file():
        return FileResponse(str(index_path))
    # 最后尝试 pages/test-layer1.html（开发便利）
    test_path = STATIC_DIR / "pages" / "test-layer1.html"
    if test_path.is_file():
        return FileResponse(str(test_path))
    raise HTTPException(status_code=404, detail="Not found")


# ─── 启动 ───

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3001"))
    print("=" * 40)
    print(f"  Layer 1 + 2 + 3 + 4 全栈服务已启动")
    print(f"  http://localhost:{port}/                (Layer 4 动画播放器)")
    print(f"  http://localhost:{port}/pages/test-layer1.html  (Layer 1 测试页)")
    print(f"  API: POST /api/analyze              (Layer 1)")
    print(f"  API: POST /api/analyze/acts         (Layer 1 + 2)")
    print(f"  API: POST /api/analyze/storyboard   (Layer 1 + 2 + 3)")
    print(f"  API: GET  /api/status")
    print("-" * 40)
    llm_cfg = get_llm_config()
    if llm_cfg:
        print(f"  LLM: 已配置 ({llm_cfg['model']})")
    else:
        print(f"  LLM: 未配置（仅规则模式）")
        print(f"  提示：在 .env 中设置 LLM_API_KEY 开启 LLM 增强")
    print("=" * 40)
    uvicorn.run(app, host="0.0.0.0", port=port)
