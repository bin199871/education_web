# education_web · 物理题目讲解动画自动生成系统

## 目录结构

```
education_web/
├── backend/               # Python 后端代码
│   ├── server.py          # FastAPI 服务入口
│   ├── layer1_agent.py    # Layer 1: 题目分析 Agent
│   ├── layer2_engine.py   # Layer 2: 幕结构匹配引擎
│   ├── layer3_storyboard.py  # Layer 3: 分镜展开器
│   └── layer4_engine.py   # Layer 4: HTML 编排引擎
├── frontend/              # 前端静态文件
│   ├── index.html         # Layer 4 动画播放器
│   ├── test-layer1.html   # Layer 1-4 测试页面
│   ├── components.js      # Canvas 2D 组件库
│   ├── engine.js          # 时间轴渲染引擎
│   └── timeline.json      # 编排数据（由后端自动生成）
├── data/                  # 示例数据和输出
├── .venv/                 # Python 虚拟环境
├── .env                   # 环境变量配置
├── requirements.txt       # 依赖清单
└── 系统设计说明.md          # 系统设计文档
```

## 四层架构

| 层级 | 名称 | 职责 |
|------|------|------|
| **Layer 1** | 题目分析 Agent | 接收题目文本，输出结构化题目分析 JSON |
| **Layer 2** | 幕结构匹配引擎 | 匹配叙事模板，输出各幕参数配置 |
| **Layer 3** | 分镜展开器 | 展开为详细分镜脚本（含画面描述和配音旁白） |
| **Layer 4** | HTML 编排引擎 | 将分镜脚本转换为 timeline JSON + 渲染为 HTML 动画 |

## 启动

```bash
pip install -r requirements.txt
python -m backend.server
# 访问 http://localhost:3001/test-layer1.html 测试
# 访问 http://localhost:3001/ 查看 Layer 4 动画
```

## 配置

编辑 `.env` 文件：

```env
# LLM API 密钥（留空则使用规则模式）
LLM_API_KEY=
LLM_ENDPOINT=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini
# PORT 默认 3001
```

## API

- `POST /api/analyze` — Layer 1 题目分析
- `POST /api/analyze/acts` — Layer 1 + 2 幕结构
- `POST /api/analyze/storyboard` — Layer 1 + 2 + 3 + 4 全流程
- `GET /api/status` — 服务状态

## 独立运行 Layer 4

```bash
python -m backend.layer4_engine
# 从 data/layer3_full_storyboard.json 生成 frontend/timeline.json + frontend/index.html
```

```python
from backend.layer4_engine import orchestrate_from_act_plan
timeline = orchestrate_from_act_plan(act_plan, "frontend/timeline.json")
```
