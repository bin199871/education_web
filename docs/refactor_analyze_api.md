# 重构 /api/analyze/storyboard 接口设计

## 一、现状与问题

### 当前流程（过于复杂）

```
用户输入题目
    ↓
RuleEngine.detect_topics()  ← 关键词匹配，经常误判
    ↓
analyze_problem_safe()      ← 多步: 解析→主题检测→LLM分析→合并→置信度评估
    ↓
generate_act_plan()         ← 基于 layer1 生成幕结构
    ↓
generate_solution_steps()   ← 基于 layer1 生成解题步骤（主题错了全错）
    ↓
expand_storyboard()         ← 展开分镜
    ↓
orchestrate()               ← 生成 timeline / HTML
    ↓
返回 10+ 个字段的 JSON
```

### 核心问题
1. 流程过长，多个环节耦合，一个环节出错后续全错
2. 主题检测用关键词匹配，容易把电场题判成"质量与重力"
3. 解题步骤生成依赖主题检测结果，主题错了步骤也错了
4. 返回字段过多（layer1~layer4），前端只用到其中几个

---

## 二、目标流程（简化后）

```
用户输入题目
    ↓
调用 LLM（带结构化输出 prompt）
    ↓
LLM 返回 JSON（仅 2 个字段）
    ├── solution_text: 完整解题过程（纯文本）
    └── problem_type: 题目类型标识（如 "electric_pendulum"）
    ↓
API 返回前端
    ├── solution_text → 右侧「分析题目」tab 显示
    └── problem_type → 左侧状态栏显示「已匹配：xxx」
```

## 三、LLM Prompt 设计

### System Prompt

```
你是一位物理教师。请分析以下物理题目，输出 JSON 格式：

{
  "solution_text": "完整的解题过程",
  "problem_type": "题目类型标识"
}

要求：
1. solution_text 用纯文本，不用 LaTeX 符号（不用 \( \) 等）
2. 解题过程包括：公式、代入数值、计算过程、最终答案
3. 每个小问用（1）（2）（3）编号
4. 每个小问末尾用「答：」给出答案
5. 格式参考如下（缩进和空行保持可读性）：

解：

（1）步骤标题
  推导过程...
  公式：...
  代入数值...
  答：...

（2）步骤标题
  推导过程...
  公式：...
  代入数值...
  答：...

6. problem_type 从以下列表中选择最匹配的一个：
  - electric_pendulum（电场中带电单摆）
  - conveyor_belt（传送带问题）
  - collision（动量碰撞/弹簧碰撞）
  - projectile（平抛运动）
  - inclined_plane（斜面+摩擦力）
  - vertical_circular（竖直圆周运动）
  - board_block（板块模型）
  - spring_oscillator（弹簧振子）
  - magnetic_deflection（带电粒子在磁场中偏转）
  - connected_bodies（连接体问题）
  - conductor_cutting（导体棒切割磁感线）
  - locomotive（机车启动）
  - circuit_analysis（电路动态分析）
  - astronomy（万有引力/天体运动）
  - mechanical_wave（机械波）
  - gas_law（气体实验定律）
  - coulomb_force（静电场/库仑力）
  - light_refraction（光的折射反射）
  - atomic_energy（原子物理/能级跃迁）
  - ac_transformer（交流电/变压器）
  - unknown（无法确定类型时）
```

### User Prompt

```
请解答以下物理题，输出 JSON：

{用户输入的题目文本}
```

## 四、接口变更

### 请求

```
POST /api/analyze/storyboard
{
  "text": "题目文本...",
  "useLLM": true
}
```

### 响应

```json
{
  "success": true,
  "data": {
    "solution_text": "解：\n\n（1）判断小物块的运动性质\n小物块轻放在传送带上时...\n答：...",
    "problem_type": "conveyor_belt"
  }
}
```

### 删除的字段
- `layer1` — 不再需要
- `layer2` — 不再需要
- `layer2_5` — 不再需要
- `layer2_5_text` — 被 `solution_text` 替代
- `layer3` — 不再需要
- `layer3_text` — 不再需要
- `layer4_url` — 不再需要
- `physics` — 不再需要
- `timeline_mode` — 不再需要
- `meta` — 不再需要

## 五、前端变更

### index.html

1. `renderAnalysis(data)` 改为从 `data.solution_text` 读取解题文本
2. 从 `data.problem_type` 读取模板类型（替代 `data.physics.problem_type`）
3. 删除不再使用的字段引用

### 展示规则

`solution_text` 直接显示在「分析题目」tab，按原格式保留换行和缩进。

### 参数预览

左侧参数预览区改为显示 `problem_type`（模板匹配结果），不再展示具体参数值（因为参数展示需要额外逻辑，当前可降级）。

## 六、实施步骤

1. 重写 `analyze_storyboard` 函数（删除旧逻辑，替换为新逻辑）
2. 删除不再需要的数据处理层调用
3. 修改前端 `renderAnalysis` 适配新字段名
4. 验证：用电场单摆、传送带、碰撞三道题测试

## 七、注意事项

- 不修改任何模板 HTML 文件 ✅
- 不修改 player-core.js / engine.js ✅
- 不修改 components.js ✅
- 只在 `server.py` 中修改 API 逻辑
- 只在 `index.html` 中修改前端展示逻辑
