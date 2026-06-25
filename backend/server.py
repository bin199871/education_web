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
)
from layer2_engine import generate_act_plan
from layer2_solution_steps import generate_solution_steps, solution_steps_to_text
from layer3_storyboard import expand_storyboard, format_as_text
from physics_simulator import simulate_slope_problem
from physics_param_extractor import extract_physics_params, run_simulation_from_text
from layer4_engine import orchestrate, generate_html_timeline

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

# ─── 静态文件服务目录（指向 frontend/） ───
STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend"


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


class AnalyzeResponse(BaseModel):
    success: bool
    data: dict | None = None
    meta: dict | None = None
    error: str | None = None


# ─── API 路由 ───

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


@app.post("/api/analyze/storyboard", response_model=AnalyzeResponse)
async def analyze_storyboard(req: AnalyzeRequest):
    """分析物理题目并生成分镜脚本（Layer 1 + 2 + 3）。"""
    text = req.text.strip() if req.text else ""
    if not text:
        raise HTTPException(status_code=400, detail="题目文本不能为空")

    # 松弛验证：计算题可能没有 A/B/C/D 选项，非空即可
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
        # 松弛验证：计算题可能没有 A/B/C/D 选项
        parsed = TextParser.parse(text)

        layer1_result = await analyze_problem_safe(text, llm_cfg)

        # 🔬 双模式扩展：提取物理参数并注入 Layer 1 结果
        physics_extracted = extract_physics_params(text)
        if physics_extracted["phases"]:
            layer1_result["physics_params"] = physics_extracted["params"]
            layer1_result["physics_phases"] = physics_extracted["phases"]
        layer1_result["_raw_text"] = text  # 供 Layer 2 检测使用

        act_plan = generate_act_plan(layer1_result)

        # Layer 2.5: 解题步骤生成
        solution_steps = generate_solution_steps(layer1_result)
        solution_steps_text = solution_steps_to_text(solution_steps)

        storyboard = expand_storyboard(act_plan)
        storyboard_text = format_as_text(storyboard)

        # Layer 4: 生成 timeline JSON 与 HTML（写入 frontend/）
        try:
            timeline = orchestrate(storyboard)
            timeline_json_str = json.dumps(timeline, ensure_ascii=False, indent=2)
            with open(str(STATIC_DIR / "timeline.json"), "w", encoding="utf-8") as f:
                f.write(timeline_json_str)
            generate_html_timeline(timeline, str(STATIC_DIR / "timeline-player.html"))
            layer4_url = "/"
        except Exception as e4:
            print(f"[Layer 4] 生成失败: {e4}")
            timeline = None
            layer4_url = None

        # 检测是否生成了仿真模式
        has_sim = timeline and any(
            seg.get("mode") == "simulate"
            for seg in timeline.get("timeline", [])
        )
        timeline_mode = "hybrid" if has_sim else "explain_only"

        return AnalyzeResponse(
            success=True,
            data={
                "layer1": layer1_result,
                "layer2": act_plan,
                "layer2_5": solution_steps,
                "layer2_5_text": solution_steps_text,
                "layer3": storyboard,
                "layer3_text": storyboard_text,
                "layer4_url": layer4_url,
                "physics": physics_extracted if physics_extracted["phases"] else None,
                "timeline_mode": timeline_mode,
            },
            meta={
                "mode": "llm_enhanced" if use_llm else "rule_only",
                "llmAvailable": llm_config is not None,
                "llmUsed": use_llm,
                "detectedTopics": detected_info,
                "layers": ["layer1", "layer2", "layer2_5", "layer3", "layer4"],
                "analysisStatus": layer1_result.get("status", "auto_resolved")
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/physics/simulate")
async def physics_simulate():
    """物理仿真：斜面+粗糙面+拉力 经典题型。"""
    try:
        result = simulate_slope_problem(
            mass=2, angle_deg=37, length=3, mu=0.4,
            g=10, pull_force=10, pull_after=1.0, fps=30
        )
        return {
            "success": True,
            "frames": result["frames"],
            "total_frames": result["total_frames"],
            "fps": result["fps"],
            "summary": result["summary"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/physics/demo-timeline")
async def physics_demo_timeline():
    """返回物理仿真 timeline，直接在浏览器中播放。"""
    try:
        from physics_simulator import format_frames_to_timeline
        result = simulate_slope_problem(
            mass=2, angle_deg=37, length=3, mu=0.4,
            g=10, pull_force=10, pull_after=1.0, fps=30
        )
        timeline = format_frames_to_timeline(result["frames"], fps=result["fps"])
        return timeline
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AnalyzeRequestWithModel(AnalyzeRequest):
    """带 model 字段的请求（兼容 analyzer 调用）。"""
    model: str | None = None


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
    # 最后尝试 test-layer1.html（开发便利）
    test_path = STATIC_DIR / "test-layer1.html"
    if test_path.is_file():
        return FileResponse(str(test_path))
    raise HTTPException(status_code=404, detail="Not found")


# ─── 启动 ───

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3001"))
    print("=" * 40)
    print(f"  Layer 1 + 2 + 3 + 4 全栈服务已启动")
    print(f"  http://localhost:{port}/test-layer1.html")
    print(f"  http://localhost:{port}/               (Layer 4 动画播放器)")
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
