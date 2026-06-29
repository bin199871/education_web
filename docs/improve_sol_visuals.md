# 解题场景视觉标注改进方案

## 问题描述

部分模板中，Q1 解题场景有对应的视觉元素（如高度指示线、速度箭头、数据面板），但 Q2/Q3 的解题场景只显示纯面板，缺少与问题相关的视觉标注（B 模式）。

---

## 一、conveyor_belt.html

### 现状
| 场景 | layers | 视觉元素 |
|------|--------|---------|
| sol_time (Q1 共速时间) | bg,env,object,title,panel | block + 传送带 + 速度箭头 ✅ |
| sol_disp (Q2 相对位移) | bg,env,object,title,panel | 同上，无 Δx 标注 ❌ |
| sol_heat (Q3 摩擦生热) | bg,env,object,title,panel | 同上，无热能示意 ❌ |

### 修改方案

#### Q2: 加 `disp_marker` 层
在传送带上方画两条水平标注线：
- 蓝色线：block 位移 x₁（从起点到 block 位置）
- 橙色线：belt 位移 x₂（从起点到 belt 对应位置）  
- 中间用红色双箭头标注 `Δx = |x₁ - x₂|`

需要数据：`x1`（block 位移），`x2 = v₀·t`（belt 位移）

#### Q3: 加 `heat_area` 层  
在 block 与传送带接触面画一个红色半透明矩形区域，大小正比于 Q = f·Δx，旁边标注 `Q = xx J`

---

## 二、collision.html

### 现状
| 场景 | layers | 视觉元素 |
|------|--------|---------|
| sol_vel (Q1 碰后速度) | bg,env,object,title,panel | 两球 + 速度箭头 ✅ |
| sol_eloss (Q2 能量损失) | bg,env,object,title,panel | 无能量对比 ❌ |
| sol_impulse (Q3 冲量) | bg,env,object,title,panel | 无力箭头 ❌ |
| sol_spring (Q4 弹簧压缩) | bg,env,object,title,panel | 无弹簧形变示意 ❌ |

### 修改方案

#### Q2: 加 `energy_bar` 层
在左下角画两个并列的竖直能量条：
- 蓝色：碰前动能 Ek₀
- 橙色：碰后动能 Ek'  
- 红色差值标注 ΔE

#### Q3: 加 `impulse_arrow` 层
在球 m₁ 上方画紫色箭头表示冲量方向：
- 箭头长度 ∝ I = m₁(v₁ − v₁′)
- 标注 `I = xx N·s`

#### Q4: 加 `spring_label` 层
在弹簧位置画一个压缩标注线，标注最大形变量 `xmax = xx m`

---

## 三、inclined_plane.html

### 现状
| 场景 | layers | 视觉元素 |
|------|--------|---------|
| sol_sm_vel (Q1 光滑面速度) | bg,env,object,title,panel | 斜面 + block + 速度箭头 ✅ |
| sol_friction (Q2 摩擦力) | bg,env,object,title,panel | 无摩擦力箭头 ❌ |
| sol_rh_vel (Q3 粗糙面速度) | bg,env,object,title,panel | 无摩擦力示意 ❌ |

说明：`forces` 层只画 G（重力），没有摩擦力 f。

### 修改方案

#### Q2: `sol_friction` 加 `friction_arrow` 层
在 block 上画沿斜面向上的摩擦力箭头：
- 红色箭头 f，与运动方向相反
- 标注 `f = μmg·cosθ = xx N`

#### Q3: `sol_rh_vel` 加 `friction_arrow` 层 + `thermal` 层
- 同上画摩擦力箭头
- 在斜面与 block 接触面加红色半透明矩形示意摩擦生热
- 标注 `Q = f·L = xx J`

---

## 四、vertical_circular.html

### 现状
| 场景 | physics（球位置） | 视觉元素 |
|------|-------------------|---------|
| sol_N1 (Q1 最高点 N₁) | 球在顶部 (CX, CY-SC) | 数据面板显示 N₁ ✅，但无力箭头 ❌ |
| sol_N2 (Q2 最低点 N₂) | 球在底部 (CX, CY+SC) | 数据面板显示 N₂ ✅，但无力箭头 ❌ |
| sol_dN (Q3 压力差 ΔN) | 球在侧面 (CX+SC, CY) | 数据面板显示 ΔN，无力箭头 ❌ |

关键问题：三个场景球在不同位置（已在 physics 中正确设置），但**没有力矢量箭头**展示 G、N、向心力的关系。

### 修改方案

#### 通用：加 `force_arrow` 层
在球位置画两个力箭头：
- 蓝色向下：重力 G = mg（始终竖直向下）
- 紫色沿绳方向：支持力 N（指向圆心）
- 标注力的数值

#### Q1 (sol_N1): layers 加 `force_arrow` —— G 向下 + N₁ 向下（指向圆心）
#### Q2 (sol_N2): layers 加 `force_arrow` —— G 向下 + N₂ 向上（指向圆心）
#### Q3 (sol_dN): 只显示数据面板，球在侧面，不需要力箭头

---

## 五、实施顺序

1. conveyor_belt — 改动最小，效果直观
2. inclined_plane — 摩擦力箭头容易实现
3. collision — 能量条和冲量箭头需新增渲染逻辑
4. vertical_circular — 力矢量箭头改动最大
