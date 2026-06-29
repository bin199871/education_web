# Phase B+C 改进方案

## B：模板步骤质量提升

### 现状

| 模板 | 场景数 | 总步骤 | 均步/场景 | 评级 |
|------|--------|--------|----------|------|
| spring_oscillator | 4 | 3 | 0.8 | ❌ 严重不足 |
| conductor_cutting | 3 | 3 | 1.0 | ❌ 严重不足 |
| conveyor_belt | 3 | 4 | 1.3 | ⚠️ 偏少 |
| mechanical_wave | 2 | 3 | 1.5 | ⚠️ 偏少 |
| circuit_analysis | 3 | 5 | 1.7 | ⚠️ 偏少 |
| inclined_plane | 3 | 5 | 1.7 | ⚠️ 偏少 |
| astronomy | 4 | 8 | 2.0 | ⚠️ 偏少 |
| board_block | 2 | 4 | 2.0 | ⚠️ 偏少 |
| connected_bodies | 2 | 4 | 2.0 | ⚠️ 偏少 |
| gas_law | 2 | 4 | 2.0 | ⚠️ 偏少 |
| magnetic_deflection | 2 | 4 | 2.0 | ⚠️ 偏少 |
| projectile | 3 | 6 | 2.0 | ⚠️ 偏少 |
| collision | 4 | 9 | 2.2 | ⚠️ 偏少 |

参考标准：每个 sol_* 场景应至少 3 步推导（公式→代入数值→结果）

### 改进方案

按严重程度分两批：

#### 第一批：严重不足（3个模板）

**1. spring_oscillator.html**
当前 Q1~Q4 各只有 1 步，需要补全：
- 周期 T：`ω = √(k/m)` → `T = 2π/ω` → 代入数值
- 频率 f：`f = 1/T` → 代入
- 能量 E：`E = ½kA²` → 代入
- 速度 v：`v = ω·A`（过平衡点时）

**2. conductor_cutting.html**
当前 3 个场景各 1 步：
- 动生电动势：`E = BLv` → 代入 → 结果
- 感应电流：`I = E/R` → 代入 → 结果
- 安培力：`F = BIL` → 代入 → 结果

**3. conveyor_belt.html**
当前 Q1=2步、Q2=1步、Q3=1步：
- Q1 加速度：`a = μg` → 代入 → `t = v₀/a` → 代入 → 结果 ✅
- Q2 相对位移：`x₁ = ½at²` → 计算 → `x₂ = v₀t` → 计算 → `Δx = |x₂−x₁|` → 结果（补全到3步）
- Q3 摩擦生热：`Q = f·Δx = μmg·Δx` → 代入 → 结果（补全到2步）

#### 第二批：偏少（10个模板）

每个模板增加 1~2 步中间推导（公式→代入数据→中间结果→最终结果），需要逐一审阅。

---

## C：LLM 参数提取补齐

### 现状

PARAM_MAP 当前覆盖 7/16 模板：

| 模板 | PARAM_MAP | extract_physics_params 输出映射 |
|------|-----------|-------------------------------|
| electric_pendulum | ✅ mass→m, charge→q, E→E, L→L, g→g | |
| inclined_plane | ✅ mass→m, angle→theta, L→L, mu→mu, g→g | |
| projectile | ✅ v0→v0, h→h, g→g | |
| vertical_circular | ✅ mass→m, g→g | |
| conveyor_belt | ✅ mass→m, mu→mu, g→g | |
| board_block | ✅ mass→m, mu→mu, g→g | |
| collision | ✅ m1→m1, m2→m2, v1→v1, k→k | |
| **astronomy** | ❌ | M, m, r, G, T |
| **circuit_analysis** | ❌ | E, r, R1, R2_max |
| **conductor_cutting** | ❌ | m, B, L, v0, R |
| **connected_bodies** | ❌ | m1, m2, g |
| **gas_law** | ❌ | pA, VA, TA, n, R |
| **locomotive** | ❌ | m, P, f |
| **magnetic_deflection** | ❌ | m, q, v, B |
| **mechanical_wave** | ❌ | v, lambda, A |
| **spring_oscillator** | ❌ | m, k, A, g |

### 改方案

对缺失的 9 个模板增加 PARAM_MAP 条目。需要对照 `extract_physics_params` 的输出 key 映射到模板的 param_schema key。

从 `template_engine.py` 中已有的 `param_schema` 可推导映射关系：

```python
PARAM_MAP = {
    ...
    'astronomy': {
        'mass': 'm',
        'mass_center': 'M',   # 若 extract 输出 center_mass
        'distance': 'r',
        'gravitational_constant': 'G',
    },
    'circuit_analysis': {
        'emf': 'E',
        'internal_resistance': 'r',
        'resistance': 'R1',
        'max_resistance': 'R2_max',
    },
    'conductor_cutting': {
        'mass': 'm',
        'magnetic_field': 'B',
        'length': 'L',
        'velocity': 'v0',
        'resistance': 'R',
    },
    'connected_bodies': {
        'mass_A': 'm1',
        'mass_B': 'm2',
        'g': 'g',
    },
    'gas_law': {
        'initial_pressure': 'pA',
        'initial_volume': 'VA',
        'initial_temperature': 'TA',
        'amount': 'n',
        'gas_constant': 'R',
    },
    'locomotive': {
        'mass': 'm',
        'power': 'P',
        'resistance_force': 'f',
    },
    'magnetic_deflection': {
        'mass': 'm',
        'charge': 'q',
        'velocity': 'v',
        'magnetic_field': 'B',
    },
    'mechanical_wave': {
        'wave_speed': 'v',
        'wavelength': 'lambda',
        'amplitude': 'A',
    },
    'spring_oscillator': {
        'mass': 'm',
        'stiffness': 'k',
        'amplitude': 'A',
        'g': 'g',
    },
}
```

注意：映射的**左值**（extract key）需要和 `layer2_engine.py` / `physics_param_extractor.py` 中 `extract_physics_params` 函数的输出 key 一致。需要确认实际输出 key 名称后再定稿。

---

## 实施顺序

1. **C：补齐 PARAM_MAP** — 纯配置修改，无需审阅模板内容，风险低
2. **B 第一批：3 个严重不足模板** — 可独立修改，互不影响
3. **B 第二批：10 个偏少模板** — 需要逐模板审阅步骤质量
