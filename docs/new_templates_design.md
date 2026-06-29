# 新模板开发详细设计

---

## 一、静电场/库仑力（静电单摆）

### 1.1 题目场景

> 在真空中，两个带正电的小球 A 和 B 分别用绝缘细线悬挂于同一点 O。A 的质量为 m，电荷量为 qA，B 的质量为 mB，电荷量为 qB。两球静止时，细线与竖直方向的夹角分别为 α 和 β。已知静电力常量 k = 9.0×10⁹ N·m²/C²，重力加速度 g = 10 m/s²。

### 1.2 求什么（3 小问）

1. A 球所受的库仑力大小 F库
2. 两球之间的距离 r
3. 某球的电荷量（已知距离求电荷量）

### 1.3 物理公式

```
F库 = k · qA · qB / r²
tan α = F库 / (mA · g)   （A 球受力平衡）
r = L · (sin α + sin β)   （几何关系，L 为绳长）
```

### 1.4 参数设计

| key | 含义 | 默认值 | 提取器 key |
|-----|------|--------|-----------|
| mA | A球质量 | 0.01 kg | mass_A |
| mB | B球质量 | 0.01 kg | mass_B |
| qA | A球电荷量 | 1e-6 C | charge_A（新增） |
| qB | B球电荷量 | 1e-6 C | charge_B（新增） |
| L | 绳长 | 0.5 m | pendulum_length |
| k | 静电力常量 | 9e9 | -（固定值） |
| g | 重力加速度 | 10 | g |

新增提取器 key：`charge_A`、`charge_B`

### 1.5 动画设计

| 场景 | 持续 | 图层 | 描述 |
|------|------|------|------|
| intro | 6% | bg,env,object,title,known | 显示两个悬挂小球 |
| balance | 25% | bg,env,object,force_arrows,data,title | 展示受力分析 + 库仑力/重力/拉力箭头 |
| sol_force | 8% | bg,env,object,force_arrows,title,panel | 求库仑力 |
| sol_distance | 8% | bg,env,object,title,panel | 求距离 |
| sol_charge | 8% | bg,env,object,title,panel | 求电荷量 |
| ending | 5% | bg,ending | 答案汇总 |

**可视化要素：**
- 两个小球用细线悬挂（弧线 + 小球）
- 库仑力箭头（红色，水平方向）
- 重力箭头（蓝色，竖直方向）
- 拉力箭头（紫色，沿绳方向）
- 角度标注 α、β
- 距离标注 r（两球球心连线）

### 1.6 步骤推导

**sol_force：**
```
对 A 受力分析：F库 = mA · g · tan α
F库 = {mA} × {g} × tan{α}
F库 = {value} N
```

**sol_distance：**
```
由库仑定律：F库 = k · qA · qB / r²
r = √(k · qA · qB / F库)
r = {value} m
```

**sol_charge：**
```
由 F库 = k · qA · qB / r²
qA = F库 · r² / (k · qB)
qA = {value} C
```

### 1.7 文件

`backend/templates/coulomb_force.html`

---

## 二、光的折射反射（几何光学）

### 2.1 题目场景

> 如图所示，一束单色光从空气射入某种透明介质，入射角为 θ₁ = 45°，折射角为 θ₂ = 30°。已知真空中的光速 c = 3.0×10⁸ m/s。求：

### 2.2 求什么（4 小问）

1. 介质的折射率 n
2. 光在介质中的传播速度 v
3. 发生全反射的临界角 C
4. 反射光线的方向（或反射角）

### 2.3 物理公式

```
n = sin θ₁ / sin θ₂           （折射定律）
v = c / n                      （光速与折射率关系）
sin C = 1 / n                  （全反射临界角）
θ₁' = θ₁                       （反射定律：反射角等于入射角）
```

### 2.4 参数设计

| key | 含义 | 默认值 | 提取器 key |
|-----|------|--------|-----------|
| theta1 | 入射角 | 45° | angle_given |
| theta2 | 折射角 | 30° | refraction_angle（新增） |
| c | 光速 | 3e8 m/s | -（固定值） |

> 注：n₂ 为介质折射率（待求），n₁ 为空气折射率（=1）

新增提取器 key：`refraction_angle`

### 2.5 动画设计

**可视化要素（关键）：**
- 水平界面（空气/介质分界线）
- 法线（虚线，垂直于界面）
- 入射光线（带箭头，从左上射向界面）
- 反射光线（带箭头，从界面射向左上）
- 折射光线（带箭头，从界面射向右下）
- 入射角标注 θ₁（弧线 + 标签）
- 反射角标注 θ₁'（弧线 + 标签）
- 折射角标注 θ₂（弧线 + 标签）
- 标注空气（"空气 n=1"）和介质（"介质 n=?"）

**场景编排：**

| 场景 | 持续 | 图层 | 描述 |
|------|------|------|------|
| intro | 6% | bg,env,rays,title,known | 显示入射/反射/折射光线 |
| sol_n | 8% | bg,env,rays,angles,title,panel | 求折射率 n |
| sol_v | 8% | bg,env,rays,title,panel | 求介质中光速 v |
| sol_critical | 8% | bg,env,rays,critical_angle,title,panel | 求全反射临界角 |
| sol_reflection | 7% | bg,env,rays,angles,title,panel | 求反射角 |
| ending | 5% | bg,ending | 答案汇总 |

### 2.6 步骤推导

**sol_n：**
```
n = sin θ₁ / sin θ₂
n = sin{theta1}° / sin{theta2}°
n = {value}
```

**sol_v：**
```
v = c / n
v = 3.0×10⁸ / {n}
v = {value} m/s
```

**sol_critical：**
```
sin C = 1 / n
C = arcsin(1/{n})
C = {value}°
```

**sol_reflection：**
```
反射角 = 入射角
θ₁' = θ₁ = {theta1}°
```

### 2.7 文件

`backend/templates/light_refraction.html`

---

## 三、原子物理/能级跃迁

### 3.1 题目场景

> 氢原子能级图如图所示（E₁ = -13.6 eV，E₂ = -3.40 eV，E₃ = -1.51 eV，E₄ = -0.85 eV）。大量处于 n=4 激发态的氢原子向低能级跃迁时，求：

### 3.2 求什么（4 小问）

1. 最多可以辐射出几种频率的光子
2. 波长最长的光子对应的能级跃迁
3. 该光子的波长（已知普朗克常量 h = 6.63×10⁻³⁴ J·s）
4. 该光子属于哪个波段（可见光/红外/紫外）

### 3.3 物理公式

```
N = C(n, 2) = n(n-1)/2      （光谱线条数）
E = Em - En                  （能级差）
λ = hc / E = hc / (Em - En) （波长）
E(eV) → E(J)：1 eV = 1.6×10⁻¹⁹ J
```

### 3.4 参数设计

| key | 含义 | 默认值 | 提取器 key |
|-----|------|--------|-----------|
| n_level | 初始能级 | 4 | n_quantum（新增） |
| E1 | n=1能量 | -13.6 eV | 固定值 |
| E2 | n=2能量 | -3.40 eV | 固定值 |
| E3 | n=3能量 | -1.51 eV | 固定值 |
| E4 | n=4能量 | -0.85 eV | 固定值 |

> 能级值固定为氢原子真实值，后续可扩展

新增提取器 key：`n_quantum`

### 3.5 动画设计（规模最大）

**可视化要素（4 个层次）：**
1. **能级图**：竖直方向排列的能级线（E₁, E₂, E₃, E₄）
   - 每条线带能量标签
   - 能级间距按实际比例绘制
2. **跃迁箭头**：从高能级指向低能级的带箭头竖直线
   - 大量跃迁时显示 6 条线（4→3, 4→2, 4→1, 3→2, 3→1, 2→1）
   - 当前计算的那条跃迁高亮
3. **光谱线**：在底部显示对应的谱线位置
   - 波长越长越靠右
   - 可见光区域标出颜色
4. **动画过程**：电子从高能级"跳"到低能级，释放光子闪烁

**场景编排：**

| 场景 | 持续 | 图层 | 描述 |
|------|------|------|------|
| intro | 6% | bg,energy_levels,title,known | 显示能级图 |
| transition | 20% | bg,energy_levels,electrons,all_arrows,title | 电子从 n=4 逐步跃迁到各低能级，显示所有 6 种跃迁 |
| sol_count | 8% | bg,energy_levels,all_arrows,title,panel | 求光谱线条数 |
| hilight_longest | 6% | bg,energy_levels,hilight_arrow,title | 高亮波长最长的跃迁（4→3，能级差最小） |
| sol_wavelength | 8% | bg,energy_levels,hilight_arrow,title,panel | 求该光子波长 |
| sol_band | 7% | bg,energy_levels,hilight_arrow,title,panel | 判断波段 |
| ending | 5% | bg,ending | 答案汇总 |

### 3.6 步骤推导

**sol_count：**
```
光谱线条数 N = C(n, 2) = n(n-1)/2
N = {4}×{3}/2
N = {value} 条
```

**sol_wavelength：**
```
波长最长的跃迁：4 → 3（能级差最小）
ΔE = E₄ − E₃ = ... eV
ΔE(J) = ΔE(eV) × 1.6×10⁻¹⁹ = ... J
λ = hc / E = 6.63×10⁻³⁴ × 3×10⁸ / ... = {value} m
```

**sol_band：**
```
波长 {value} m = {value} nm
在 {范围} 范围内 → 属于 {可见光/红外/紫外}
```

### 3.7 文件

`backend/templates/atomic_energy.html`

---

## 四、交流电/变压器（规模最大，最详细）

### 4.1 题目场景

> 一正弦交变电流的电压随时间变化的图像如图所示。已知电压的最大值为 U_m，周期为 T。将该交变电流通过一个理想变压器（原线圈匝数 n₁，副线圈匝数 n₂），副线圈接有电阻 R。求：

### 4.2 求什么（4~5 小问）

1. 交变电流的频率 f 和角频率 ω
2. 电压的有效值 U_eff
3. 变压器副线圈的电压 U₂ 和电流 I₂
4. 变压器的输入功率 P₁ 和输出功率 P₂
5. （可选）若副线圈接电容/电感，相位关系

### 4.3 物理公式

```
f = 1/T                     （频率与周期）
ω = 2πf = 2π/T              （角频率）
U_eff = U_m / √2            （正弦交流电有效值）
U₁/U₂ = n₁/n₂               （理想变压器电压关系）
I₁/I₂ = n₂/n₁               （理想变压器电流关系）
P₁ = U₁·I₁，P₂ = U₂·I₂      （功率）
P₁ = P₂                     （理想变压器无损耗）
```

### 4.4 参数设计

| key | 含义 | 默认值 | 提取器 key |
|-----|------|--------|-----------|
| Um | 最大电压 | 311 V | voltage_max（新增） |
| T | 周期 | 0.02 s | period（新增） |
| n1 | 原线圈匝数 | 1000 | turns_primary（新增） |
| n2 | 副线圈匝数 | 100 | turns_secondary（新增） |
| R | 负载电阻 | 10 Ω | resistance |

新增提取器 key：`voltage_max`、`period`、`turns_primary`、`turns_secondary`

### 4.5 动画设计（最复杂）

**可视化要素（5 个区域）：**
1. **波形图**（画布左侧 60%）：
   - 正弦曲线 u(t) = U_m · sin(ωt)
   - 标注峰值 U_m、周期 T
   - 画半个周期以上的完整波形
   - 用箭头标注有效值 U_eff（虚线）
2. **变压器示意图**（画布右侧 40%）：
   - 铁芯（矩形线框）
   - 原线圈（左侧绕线，标注 n₁）
   - 副线圈（右侧绕线，标注 n₂）
   - 负载电阻 R
   - 电流方向箭头
3. **电压/电流实时数据**（左下角浮动面板）
4. **功率数据**（右下角浮动面板）
5. **指针/表盘**表示有效值（模拟万用表）

**场景编排（9 个场景）：**

| 场景 | 持续 | 图层 | 描述 |
|------|------|------|------|
| intro | 5% | bg,env,wave,title,known | 显示波形图，标注 U_m、T |
| sol_freq | 7% | bg,env,wave,title,panel | 求 f 和 ω |
| sol_eff | 7% | bg,env,wave,eff_marker,title,panel | 求有效值，波形上画 U_eff 虚线 |
| hilight_transformer | 6% | bg,env,transformer,title | 切换到变压器视图 |
| sol_voltage | 8% | bg,env,transformer,data,title,panel | 求副线圈电压，显示电流 |
| sol_current | 8% | bg,env,transformer,data,current_arrows,title,panel | 求原副线圈电流 |
| sol_power | 8% | bg,env,transformer,data,title,panel | 求输入输出功率 |
| sol_phase | 7% | bg,env,wave,title,panel | 电容/电感相位（可选） |
| ending | 5% | bg,ending | 答案汇总 |

### 4.6 步骤推导

**sol_freq：**
```
f = 1/T = 1/{T}
f = {value} Hz
ω = 2πf = 2π × {f}
ω = {value} rad/s
```

**sol_eff：**
```
U_eff = U_m / √2 = {Um} / √2
U_eff = {value} V
```

**sol_voltage：**
```
U₁/U₂ = n₁/n₂
U₂ = (n₂/n₁) · U₁ = ({n2}/{n1}) × {U_eff}
U₂ = {value} V
```

**sol_current：**
```
I₂ = U₂ / R = {U2} / {R}
I₂ = {value} A
I₁/I₂ = n₂/n₁ → I₁ = (n₂/n₁) · I₂
I₁ = {value} A
```

**sol_power：**
```
P₂ = U₂ · I₂ = {U2} × {I2}
P₂ = {value} W
P₁ = P₂ = {value} W（理想变压器）
```

### 4.7 文件

`backend/templates/ac_transformer.html`

---

## 五、实施计划

| 序号 | 模板 | 预估工作量 | 依赖 |
|------|------|-----------|------|
| 1 | 静电场/库仑力 | ~3h | 新增 charge_A/charge_B 提取器 |
| 2 | 光的折射反射 | ~4h | 需处理光线绘制、角度标注 |
| 3 | 原子物理/能级跃迁 | ~5h | 能级图绘制、跃迁动画 |
| 4 | 交流电/变压器 | ~6h | 波形图、变压器绘制、9 个场景 |

### 每步必须完成：

1. 新增提取器 key → `physics_param_extractor.py`
2. 新增 PARAM_MAP → `template_engine.py`
3. 新增模板文件 → `backend/templates/xxx.html`
4. 注册模板 → `template_engine.py` 的 `TEMPLATE_REGISTRY`
5. 生成测试文件 → 验证语法 + 模拟运行
6. 添加到回归测试 → `tests/run_tests.py`
