# 公共代码抽取方案：player-core.js

## 目标

将 16 个模板中完全一致的 ~200 行公共框架代码抽取为 `frontend/player-core.js`，由 `template_engine.py` 渲染时自动注入。

## 风险控制原则

1. **不改模板文件**——模板本身仍是自包含的有效 HTML（直接双击也能播放）
2. **渐进式推进**——先改 1 个模板验证，确认没问题再铺开
3. **一键回滚**——引擎配置改为 `inject_core=false` 即回到原样

---

## 阶段 0：确定抽取边界

### 可抽取（16 个模板中完全一致）

| 模块 | 约多少行 | 说明 |
|------|---------|------|
| `FC` 帧控制器 | 30 | `_loop`、`play`、`pause`、`toggle`、`seek`、`setSlow`、`clrSlow` |
| `SD` 场景调度 | 10 | `get`、`prog`、`update` |
| `Panel` 解题面板 | 45 | `renderSteps`、`update`、`_evalAll` |
| `End` 答案汇总 | 25 | `init`、`update` |
| `UI` 控制栏 | 35 | 播放/重播/进度条/速度控制/键盘快捷键 |
| `_renderMath` | 6 | KaTeX 渲染 |
| `_convertMath` | 10 | 数学符号转 LaTeX |
| `R.rc` | 10 | Canvas 圆角矩形工具 |
| `R.arrow` | 12 | Canvas 箭头绘制工具 |
| `onFrame` 主循环 | 15 | `onFrame` + `FC._onFrame` + `FC._onDone` 设置 |
| 星星生成 | 10 | 背景星星生成 |

**合计约 200 行可抽取代码（每模板）。**

### 不可抽取（每个模板不同）

- `R.render` + 所有 `draw*` 方法——场景特有绘图
- `_BRICKS`——场景积木定义
- `composeScenes`——场景编排
- `allocateTime`——时间分配
- `KP`——已知量面板（不同模板显示不同参数）
- `PHYS/P`——物理常量定义
- `traj` 等预计算数据
- 各种全局变量 (`CX`, `CY`, `SC`, `TOTAL`, `FPS` 等)
- 物理引擎函数（`swing1`, `swing2`, `flightData` 等）

### 模板特有但可参数化的部分

- `stars` 生成：部分模板用 60 颗、部分用 80 颗，统一为 60

---

## 阶段 1：创建 player-core.js + 修改引擎

### 1.1 创建 `frontend/player-core.js`

内容：所有可抽取代码，用全局变量/函数暴露。模板 `<script>` 中的代码与它通过全局对象通信。

```javascript
// player-core.js v1
// 被 template_engine.py 注入到模板 <script> 之前
(function(){
'use strict';

// ================================================================
// 全局错误捕获
// ================================================================
window.onerror = function(msg,url,l,c,e){...};

// ================================================================
// 帧控制器 FC
// ================================================================
const FC = { frame:0, total:10800, fps:60, isPlay:false, speed:1, isComp:false, ... };

// ================================================================
// 场景调度 SD
// ================================================================
const SD = { cur:null, get(f){...}, prog(f,id){...}, update(f){...} };

// ================================================================
// 解题面板 Panel
// ================================================================
const Panel = { el:null, cur:null, _evalAll(h){...}, renderSteps(sc){...}, update(sid,prog,sc){...} };

// ================================================================
// 答案汇总 End
// ================================================================
const End = { el:null, _inited:false, init(){...}, update(id,prog,sc){...} };

// ================================================================
// 已知量面板 KP (共享容器，内容由模板填充)
// ================================================================
const KP = { el:null, _inited:false, init(content){...}, update(id){...} };

// ================================================================
// 控制栏 UI
// ================================================================
const UI = { _ready:false, init(){...}, updBtn(){...}, updProg(f,t){...}, sync(){...} };

// ================================================================
// 数学渲染工具
// ================================================================
const _renderMath = function(el){...};
var _convertMath = function(t){...};   // var 暴露给 eval 作用域

// ================================================================
// Canvas 工具函数（挂到 R 上）
// ================================================================
// R.rc、R.arrow 仍然保留在每个模板的 R 中，因为它们是 R 的方法
// 但提供独立函数供注入：
function rc(x,y,w,h,r){...}
function arrow(ctx,x1,y1,x2,y2,color,w){...}

// 注意：R 对象本身不能抽取，因为 R.render 是模板特有的
// 但 R.rc 和 R.arrow 可以作为独立函数共享
})();
```

### 1.2 修改 `template_engine.py`

在 `render()` 方法中：
```python
def render(self, template_id, params):
    html = super().render(template_id, params)
    
    # 读取 player-core.js
    core_path = self.static_dir / 'player-core.js'
    core_js = core_path.read_text(encoding='utf-8')
    
    # 在模板</head>前注入 core.js
    html = html.replace('</head>', f'<script>{core_js}</script>\n</head>')
    
    return html
```

不对——这样 `<script>` 标签嵌套了。应该把 core.js 作为单独的资源加载：

```python
# 在 <head> 中注入 <script src="/static/player-core.js"></script>
html = html.replace('<head>', '<head><script src="player-core.js"></script>\n')
```

但这样直接双击 HTML 文件时依赖外部 JS，不满足"自包含"要求。

**更好的方案**：将 core.js 内容直接内联注入到模板的 `<script>` 标签前面：

```python
def render(self, template_id, params):
    # 1. 读取模板文件
    # 2. 读取 player-core.js
    # 3. 在模板 <script> 标签内部，模板自己的代码前面插入 core 代码
    # 4. 这样最终 HTML 仍然是自包含的
```

---

## 阶段 2：测试验证（先改 conveyor_belt）

### 验证清单

1. **语法验证**：Node `new Function()` 通过
2. **播放功能**：点击播放按钮，动画正常推进
3. **暂停/继续**：⏸▶ 切换
4. **重播**：完成后点击↺回到开头
5. **速度切换**：0.5× / 1× / 1.5× / 2×
6. **进度条**：点击进度条跳转
7. **键盘快捷键**：Space（播放/暂停）、← →（进退）、R（重播）
8. **场景切换**：intro → accelerate → co_speed → sol_time → sol_disp → sol_heat → ending 全部正常
9. **解题面板**：每一步渐显正常
10. **答案汇总**：结束画面正确

### 失败回滚

```python
# template_engine.py
INJECT_CORE = True  # 改为 False 即回滚

def render(self, template_id, params):
    if INJECT_CORE:
        # 新路径：注入 core
    else:
        # 旧路径：不注入，模板自包含
```

---

## 阶段 3：全面铺开

确认 conveyor_belt 正常后，对所有模板执行：

1. 从模板 `<script>` 中**删除**已抽取的公共代码（~200行/模板）
2. 在模板开头保留 `const _IN=...; const P=...;` 等特有代码
3. 引擎渲染时自动注入公共代码

铺开顺序（按复杂程度）：

| 序号 | 模板 | 风险 |
|------|------|------|
| 1 | conveyor_belt | 低（已验证） |
| 2 | collision | 低 |
| 3 | projectile | 中 |
| 4 | inclined_plane | 中 |
| 5 | board_block | 中 |
| 6 | connected_bodies | 中 |
| 7~16 | 其余模板 | 中 |

---

## 阶段 4：回归测试

创建 `tests/test_templates.py`：

```python
for template_id in all_templates:
    for params in [defaults, edge_cases]:
        html = engine.render(template_id, params)
        assert validate_syntax(html)
        assert simulate_frames(html, 10)  # 模拟 10 帧不抛异常
```

模拟 `requestAnimationFrame` 的方法：

```javascript
// 测试脚本：在 Node 中模拟基本环境
global.document = { getElementById: () => ({}) };
global.requestAnimationFrame = (cb) => { cb(0); };
// 然后执行生成的 HTML 脚本
new Function(scriptContent)();
```

---

## 时间估算

| 阶段 | 内容 | 预估 |
|------|------|------|
| 0 | 确认抽取边界 | ~30min |
| 1 | 创建 player-core.js + 改引擎 | ~2h |
| 2 | conveyor_belt 验证 | ~1h |
| 3 | 铺开 15 个模板 | ~4h |
| 4 | 回归测试 | ~1h |
| **合计** | | **~8.5h** |
