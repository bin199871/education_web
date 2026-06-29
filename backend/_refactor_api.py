#!/usr/bin/env python3
"""Rewrite /api/analyze/storyboard to use simplified LLM flow."""
import re, json

with open('backend/server.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Replace the analyze_storyboard function
start = c.find('@app.post("/api/analyze/storyboard", response_model=AnalyzeResponse)')
next_func = c.find('\n@app.post(', start + 10)
end = next_func

new_func = '''
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

'''

c = c[:start] + new_func + c[end:]

# 2. Add call_llm_analyze function before first API route
first_api = c.find('\n@app.post(')
insert_point = c.rfind('\n', 0, first_api) + 1

llm_func = '''

import json as _json
import re as _re

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
        "你是一位物理教师。请分析以下物理题目，输出 JSON 格式：\\n"
        + '{"solution_text": "完整的解题过程", "problem_type": "题目类型标识"}\\n\\n'
        + "要求：\\n"
        + "1. solution_text 不要使用 LaTeX 符号（不要用 \\\\( 或 \\\\)）\\n"
        + "2. 解题过程包括公式、代入数值、计算过程、最终答案\\n"
        + "3. 每个小问用（1）（2）（3）编号，末尾用「答：」给出答案\\n"
        + "4. 公式用纯文本表示，例如 F = qE、1/2 mv^2\\n"
        + "5. problem_type 从以下列表选择最匹配的一个：\\n"
        + "   " + types_list
    )
    messages = [
        {"role": "system", "content": prompt_system},
        {"role": "user", "content": "请解答以下物理题，输出 JSON：\\n\\n" + text}
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

'''

c = c[:insert_point] + llm_func + c[insert_point:]

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('Done')
