"""
Physics Parameter Extractor — 物理参数提取器
==============================================
从题目文本中自动提取物理参数，并匹配对应的仿真模板。

用法：
    from physics_param_extractor import extract_physics_params
    result = extract_physics_params(problem_text)
    # result = {
    #     "params": { "mass": 2, "angle_deg": 37, ... },
    #     "phases": [ {"type": "slope", ...}, {"type": "rough_surface", ...} ],
    #     "problem_type": "slope_friction_pull"
    # }
"""

import re
import math


# ==================================================================
#  物理量正则提取
# ==================================================================

# 常见的物理量标记模式
PATTERNS = {
    "mass": [
        r'(?:质量|m|mass)\s*[=∶:]\s*(\d+\.?\d*[eE]?[+-]?\d*)\s*(kg|千克)',
        r'(?:质量|m|mass)\s*[=∶:]\s*(\d+\.?\d*[eE]?[+-]?\d*)',
        r'质量[为是]\s*(\d+\.?\d*[eE]?[+-]?\d*)\s*(kg|千克)',
        r'质量\s*(\d+\.?\d*[eE]?[+-]?\d*)\s*(?:kg|千克)',
    ],
    "mass_A": [
        r'm[Aa]\s*[=∶:]\s*(\d+\.?\d*[eE]?[+-]?\d*)\s*(kg|千克)',
        r'(?:物块 A|物体 A|滑块 A).*?质量[为是]?\s*(\d+\.?\d*[eE]?[+-]?\d*)\s*(kg|千克)',
    ],
    "mass_B": [
        r'm[Bb]\s*[=∶:]\s*(\d+\.?\d*[eE]?[+-]?\d*)\s*(kg|千克)',
        r'(?:物块 B|物体 B|滑块 B).*?质量[为是]?\s*(\d+\.?\d*[eE]?[+-]?\d*)\s*(kg|千克)',
    ],
    # mass_A / mass_B added above for collision problems

    "angle_deg": [
        # θ = 37°, 倾角 θ = 37°, 斜面倾角 37°
        r'(?:倾角|θ|角度)\s*[=∶:]\s*(\d+\.?\d*)\s*°',
        r'(?:倾角|θ)[为是]\s*(\d+\.?\d*)\s*°',
        r'斜面[与和]?水平[面]?[的]?夹角[为是]?\s*(\d+\.?\d*)\s*°',
    ],
    "slope_length": [
        # L = 3 m, 斜面长度 L = 3m, 斜面长 3 米
        r'(?:斜面[长长度]|L|l)\s*[=∶:]\s*(\d+\.?\d*)\s*(m|米)',
        r'(?:斜面[长长度]|L|l)\s*[=∶:]\s*(\d+\.?\d*)',
        r'斜面长[度]?[为是]?\s*(\d+\.?\d*)\s*(m|米)',
    ],
    "mu": [
        # μ = 0.4, 动摩擦因数 μ = 0.4, 摩擦系数 0.4
        r'(?:μ|u|摩擦系数|动摩擦因数)\s*[=∶:]\s*(\d+\.?\d*)',
        r'(?:μ|u)[为是]\s*(\d+\.?\d*)',
        r'摩擦[因系数][数]?[为是]?\s*(\d+\.?\d*)',
    ],
    "g": [
        # g = 10 m/s², 重力加速度 g = 10
        r'(?:g|重力加速度)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:m/s²|m/s[2²]|N/kg)',
        r'(?:g|重力加速度)\s*[=∶:]\s*(\d+\.?\d*)',
        r'重力加速度[为取是]\s*(\d+\.?\d*)',
    ],
    "force": [
        # F = 10 N, 拉力 F = 10N, 恒定拉力 10 N
        r'(?:F|拉力|推力|外力)\s*[=∶:]\s*(\d+\.?\d*)\s*(N|牛)',
        r'(?:拉力|推力|外力)[为是]?\s*(\d+\.?\d*)\s*(N|牛)',
        r'(?:施加|加上)[一了]?个?.*?(?:拉力|推力|外力).*?[=∶:]?\s*(\d+\.?\d*)\s*(N|牛)',
    ],
    "height": [
        # h = 20m, 高度 h = 20, 竖直高度 20 m
        r'(?:h|高度|竖直高度|下落高度)\s*[=∶:]\s*(\d+\.?\d*)\s*(m|米)',
        r'(?:高度|h)[为是]\s*(\d+\.?\d*)\s*(m|米)',
        r'从[高距].*?(\d+\.?\d*)\s*(m|米)',
    ],
    "initial_velocity": [
        # v0 = 5 m/s, 初速度 v0 = 5
        r'(?:v0|v_0|初速度|初速)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:m/s|m\b)?',
        r'以.*?(\d+\.?\d*)\s*(?:m/s|m\b).*?速度',
    ],
    "time": [
        # t = 2s, 滑行 1 s 后, 经过 2 秒
        r'(?:t|时间)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:s|秒)',
        r'滑行\s*(\d+\.?\d*)\s*(?:s|秒)',
        r'经过\s*(\d+\.?\d*)\s*(?:s|秒)',
        r'(\d+\.?\d*)\s*(?:s|秒)\s*后',
    ],
    # 🔌 电场 + 单摆参数
    "electric_field": [
        # E = 100 N/C, E = 2000 N/C
        r'(?:E|电场强度)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:N/C|V/m|N·C⁻¹)',
        r'(?:电场强度|匀强电场)[大小]?[为是]?\s*(\d+\.?\d*)\s*(?:N/C|V/m)',
        r'E\s*=\s*(\d+\.?\d*)',
    ],
    "charge": [
        # q = 0.1 C, q = 5e-4 C
        r'(?:q|电荷量|电荷)\s*[=∶:]\s*(\d+\.?\d*)\s*C',
        r'(?:q|电荷量|电荷)\s*[=∶:]\s*(\d+\.?\d*)',
        r'(?:q|电荷量|电荷)[为是]?\s*(\d+\.?\d*)',
    ],
    "charge_A": [
        r'(?:q[Aa]|A.*?电荷量)\s*[=∶:]\s*(\d+\.?\d*)\s*C',
        r'(?:q[Aa]|A.*?电荷量)\s*[=∶:]\s*(\d+\.?\d*)',
    ],
    "charge_B": [
        r'(?:q[Bb]|B.*?电荷量)\s*[=∶:]\s*(\d+\.?\d*)\s*C',
        r'(?:q[Bb]|B.*?电荷量)\s*[=∶:]\s*(\d+\.?\d*)',
    ],
    "k_spring": [
        r'(?:k|劲度系数)\s*[=∶:]\s*(\d+\.?\d*)',
    ],
    "pendulum_length": [
        # L = 1.0 m (在单摆/细线上下文中)
        r'(?:L|摆长|细线长度|绳长|长度)\s*[=∶:]\s*(\d+\.?\d*)\s*m',
        r'(?:细线|摆线|绳子|绝缘细线)[长长度]?[为是]?\s*(\d+\.?\d*)\s*m',
    ],
    "angle_given": [
        # θ = 37° (题目给定角度，不是倾角)
        r'(?:θ|夹角|偏角)\s*=\s*(\d+)\s*°',
        r'与竖直方向夹角.*?(\d+)\s*°',
        r'(\d+)\s*°.*?时',
    ],
    # 🔋 磁场参数
    "magnetic_field": [
        r'(?:B|磁感应强度)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:T|特)',
        r'磁感应强度[大小]?[为是]?\s*(\d+\.?\d*)\s*(?:T|特)',
        r'匀强磁场[大小]?[为是]?\s*(\d+\.?\d*)\s*(?:T|特)',
    ],
    # ⚡ 电路参数
    "emf": [
        r'(?:E|电动势|电源电动势)\s*[=∶:]\s*(\d+\.?\d*[eE]?[+-]?\d*)\s*(?:V|伏)',
        r'电动势[为是]?\s*(\d+\.?\d*[eE]?[+-]?\d*)\s*(?:V|伏)',
    ],
    "internal_resistance": [
        r'(?:r|内阻)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:Ω|欧|ohm)',
        r'内阻[为是]?\s*(\d+\.?\d*)\s*(?:Ω|欧|ohm)',
    ],
    "resistance": [
        r'(?:R[12₁₂]?|电阻)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:Ω|欧|ohm)',
        r'电阻[为是]?\s*(\d+\.?\d*)\s*(?:Ω|欧|ohm)',
        r'R[12]?\s*[=∶:]\s*(\d+\.?\d*)',
    ],
    # 🚂 机车参数
    "power": [
        r'(?:P|功率|额定功率)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:W|瓦|kW|千瓦)',
        r'(?:功率|额定功率)[为是]?\s*(\d+\.?\d*)\s*(?:W|瓦|kW|千瓦)',
    ],
    "resistance_force": [
        r'(?:f|阻力|恒定阻力)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:N|牛)',
        r'阻力[大小]?[为是]?\s*(\d+\.?\d*)\s*(?:N|牛)',
        r'受到.*?(\d+\.?\d*)\s*(?:N|牛).*?阻力',
    ],
    # 🌀 简谐振动参数
    "stiffness": [
        r'(?:k|劲度系数)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:N/m|N·m⁻¹)',
        r'劲度系数[为是]?\s*(\d+\.?\d*)\s*(?:N/m)',
    ],
    "amplitude": [
        r'(?:A|振幅)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:m|米)',
        r'振幅[为是]?\s*(\d+\.?\d*)\s*(?:m|米)',
        r'偏离[了]?.*?最大距离[为是]?\s*(\d+\.?\d*)',
    ],
    # 🌊 波动参数
    "wave_speed": [
        r'(?:v|波速)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:m/s)',
        r'波速[为是]?\s*(\d+\.?\d*)\s*(?:m/s)',
    ],
    "wavelength": [
        r'(?:λ|lambda|波长)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:m|米)',
        r'波长[为是]?\s*(\d+\.?\d*)\s*(?:m|米)',
    ],
    # 🌌 万有引力参数
    "mass_center": [
        r'(?:M|中心天体质量|恒星质量|地球质量)\s*[=∶:]\s*(\d+\.?\d*[eE]?[+-]?\d*)\s*(?:kg|千克)',
        r'中心天体质量[为是]?\s*(\d+\.?\d*[eE]?[+-]?\d*)',
    ],
    "distance": [
        r'(?:r|轨道半径|距离)\s*[=∶:]\s*(\d+\.?\d*[eE]?[+-]?\d*)\s*(?:m|米)',
        r'轨道半径[为是]?\s*(\d+\.?\d*[eE]?[+-]?\d*)',
    ],
    "gravitational_constant": [
        r'(?:G|引力常量|万有引力常量)\s*[=∶:]\s*(\d+\.?\d*[eE]?[+-]?\d*)',
    ],
    # 🧪 气体参数
    "gas_pressure": [
        r'(?:p[Aa]?|压强|气体压强)\s*[=∶:]\s*(\d+\.?\d*[eE]?[+-]?\d*)\s*(?:Pa|帕)',
        r'初始压强[为是]?\s*(\d+\.?\d*[eE]?[+-]?\d*)',
    ],
    "gas_volume": [
        r'(?:V[Aa]?|体积|气体体积)\s*[=∶:]\s*(\d+\.?\d*[eE]?[+-]?\d*)\s*(?:L|l|升|m³)',
        r'初始体积[为是]?\s*(\d+\.?\d*)\s*(?:L|l)',
    ],
    "gas_temperature": [
        r'(?:T[Aa]?|温度|气体温度|热力学温度)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:K|开)',
        r'初始温度[为是]?\s*(\d+\.?\d*)\s*(?:K|开)',
    ],
    "substance_amount": [
        r'(?:n|物质的量|摩尔数)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:mol|摩)',
    ],
    # 🧲 速度（通用）
    "velocity": [
        r'(?:v|速度)\s*[=∶:]\s*(\d+\.?\d*[eE]?[+-]?\d*)\s*(?:m/s)',
        r'以.*?(\d+\.?\d*[eE]?[+-]?\d*)\s*m/s.*?速度',
    ],
    "velocity_A": [
        r'(?:v[Aa]|A.*?速度)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:m/s)',
    ],
    "velocity_B": [
        r'(?:v[Bb]|B.*?速度)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:m/s)',
    ],
    # 🌡 温度（通用）
    "temperature": [
        r'(?:T|温度)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:K|开|℃|°C)',
    ],
    # 📐 角度目标值
    "theta_target": [
        r'(?:与竖直方向夹角|偏角|θ)\s*[=∶:]\s*(\d+)\s*°',
        r'(\d+)\s*°.*?(?:时|处|位置)',
    ],
    "refraction_angle": [
        r'(?:折射角|θ₂|theta2)\s*[=∶:]\s*(\d+\.?\d*)\s*°',
        r'折射角[为是]\s*(\d+\.?\d*)\s*°',
    ],
    "n_quantum": [
        r'(?:n|主量子数|量子数|能级)\s*[=∶:]\s*(\d+)',
        r'处于\s*n\s*=\s*(\d+)',
        r'大量.*?n\s*=\s*(\d+)',
    ],
    "voltage_max": [
        r'(?:U[_]?[mM]|最大电压|峰值电压|电压最大值)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:V|伏)',
        r'电压最大值[为是]?\s*(\d+\.?\d*)\s*(?:V|伏)',
        r'(?:U|电压).*?峰值[为是]?\s*(\d+\.?\d*)',
    ],
    "period": [
        r'(?:T|周期)\s*[=∶:]\s*(\d+\.?\d*)\s*(?:s|秒)',
        r'周期[为是]?\s*(\d+\.?\d*)\s*(?:s|秒)',
    ],
    "turns_primary": [
        r'(?:n₁|原线圈[匝]?[数]?|原绕组)\s*[=∶:]\s*(\d+)',
        r'原线圈匝数[为是]?\s*(\d+)',
    ],
    "turns_secondary": [
        r'(?:n₂|副线圈[匝]?[数]?|副绕组)\s*[=∶:]\s*(\d+)',
        r'副线圈匝数[为是]?\s*(\d+)',
    ],
}


def extract_param(text, patterns, default=None):
    """尝试多个正则模式提取参数，返回第一个匹配的值。"""
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            try:
                return float(m.group(1))
            except (ValueError, IndexError):
                pass
    return default


SUPERSCRIPT_MAP = {
    '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
    '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
    '⁻': '-', '⁺': '',
}

def _parse_superscript_number(s: str) -> float:
    """将上标数字字符串转为 float，如 '³' → 3, '⁻⁴' → -4。"""
    result = ''
    for ch in s:
        if ch in SUPERSCRIPT_MAP:
            result += SUPERSCRIPT_MAP[ch]
        else:
            result += ch
    try:
        return float(result)
    except ValueError:
        return 0.0


def _extract_sci_notation(text, prefix_pattern, unit_pattern):
    """从文本中提取科学计数法数值。

    匹配 "E = 2.0 × 10³ N/C" → 2000.0
    返回 (value, rest_text) 或 None
    """
    # Pattern: prefix digits × 10^superscript unit
    m = re.search(
        rf'({prefix_pattern})\s*[=∶:]\s*(\d+\.?\d*)\s*[×x]\s*10([⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+)\s*({unit_pattern})',
        text
    )
    if m:
        mantissa = float(m.group(2))
        exponent = _parse_superscript_number(m.group(3))
        return mantissa * (10 ** exponent)
    return None


def extract_all_params(text):
    """从题目文本中提取所有物理参数。"""
    params = {}

    # 先处理科学计数法参数（优先级高）
    sci_e = _extract_sci_notation(text, r'(?:E|电场强度)', r'(?:N/C|V/m|N·C⁻¹)')
    if sci_e is not None:
        params["electric_field"] = sci_e
    sci_q = _extract_sci_notation(text, r'(?:q|电荷量|电荷)', r'C')
    if sci_q is not None:
        params["charge"] = sci_q

    # 正则提取其余参数
    for key, patterns in PATTERNS.items():
        if key in ("electric_field", "charge") and key in params:
            continue  # 已用科学计数法提取
        val = extract_param(text, patterns)
        if val is not None:
            params[key] = val

    # 如果没有找到 g，默认 10
    if "g" not in params:
        params["g"] = 10.0

    return params


# ==================================================================
#  物理过程检测
# ==================================================================

def detect_phases(text, params):
    """检测题目包含哪些物理过程阶段。"""
    phases = []
    mass = params.get("mass", 1)
    g = params.get("g", 10)

    # 关键词检测（含正则）
    def _re_in_text(patterns, t):
        for p in patterns:
            if re.search(p, t):
                return True
        return False

    has_slope = any(kw in text for kw in ["斜面", "倾角", "斜坡", "滑梯"])
    has_rough = any(kw in text for kw in ["粗糙", "摩擦", "μ="])
    has_smooth = "光滑" in text
    has_pull = any(kw in text for kw in ["拉力", "推力", "施加", "恒力"])
    has_free_fall = _re_in_text([
        r'自由落?下?体?', r'自由下落', r'从.*?高处.*?释放',
        r'从.*?高处.*?落下', r'从.*?高度.*?释放', r'自由落下',
    ], text)
    has_projectile = any(kw in text for kw in ["平抛", "水平抛出", "水平射"])
    has_circular = any(kw in text for kw in ["圆周", "向心", "轨道", "细线悬挂"])
    has_vertical_throw = _re_in_text([
        r'竖直上抛', r'竖直向上抛', r'竖直下抛', r'向上.*?抛出',
    ], text)

    # 粗检：是否有"求："或"计算"指示这是计算题
    is_calc_problem = any(kw in text for kw in ["求：", "求:", "试求", "计算"])

    if has_slope and params.get("angle_deg"):
        slope_params = {
            "angle_deg": params["angle_deg"],
            "length": params.get("slope_length", 3),
            "mass": mass,
            "g": g,
        }
        # 光滑斜面 → 无摩擦
        if has_smooth:
            slope_params["friction"] = 0
        phases.append({"type": "slope", "params": slope_params})

    if has_rough and (has_slope or phases):
        # 斜面之后的粗糙面
        rough_params = {
            "mu": params.get("mu", 0.3),
            "mass": mass,
            "g": g,
        }
        phases.append({"type": "rough_surface", "params": rough_params})

        # 检测是否有拉力（第三阶段）
        if has_pull and params.get("force"):
            pull_params = {
                "force": params["force"],
                "mu": params.get("mu", 0.3),
                "mass": mass,
                "g": g,
            }
            pull_after = params.get("time", 1.0)
            phases.append({
                "type": "horizontal_pull",
                "params": pull_params,
                "max_duration": 2.0,  # 默认拉2秒
            })

    # 单独粗糙面 + 拉力（无斜面）
    elif has_rough and not has_slope:
        rough_params = {
            "mu": params.get("mu", 0.3),
            "mass": mass, "g": g,
        }
        phases.append({"type": "rough_surface", "params": rough_params})
        if has_pull and params.get("force"):
            phases.append({
                "type": "horizontal_pull",
                "params": {"force": params["force"], "mu": params.get("mu", 0.3),
                          "mass": mass, "g": g},
            })

    elif has_free_fall:
        phases.append({
            "type": "free_fall",
            "params": {
                "mass": mass,
                "g": g,
                "height": params.get("height", 10),
            }
        })

    elif has_vertical_throw:
        v0 = params.get("initial_velocity", 10)
        phases.append({
            "type": "vertical_throw",
            "params": {
                "v0": v0,
                "mass": mass,
                "g": g,
            }
        })

    elif has_projectile:
        v0 = params.get("initial_velocity", 10)
        height = params.get("height", 10)
        phases.append({
            "type": "projectile",
            "params": {
                "v0": v0,
                "mass": mass,
                "g": g,
                "height": height,
            }
        })

    # 🔌 带电单摆在电场中摆动
    has_electric = any(kw in text for kw in ["匀强电场", "电场强度", "带电", "正电", "负电", "电荷量"])
    has_pendulum = any(kw in text for kw in ["细线", "悬挂", "摆长", "绝缘细线", "悬点", "摆"])
    if has_electric and has_pendulum and params.get("mass"):
        # 自动计算电场力
        q = params.get("charge", 5e-4)
        E_val = params.get("electric_field", 2000)
        g = params.get("g", 10)
        mass = params.get("mass", 0.1)
        electric_force = q * E_val
        gravity_force = mass * g
        resultant_force = math.sqrt(electric_force**2 + gravity_force**2)
        eq_angle = math.degrees(math.atan2(electric_force, gravity_force))
        duration = params.get("time", 3.0)  # 默认3秒

        phases.append({
            "type": "electric_pendulum",
            "params": {
                "mass": mass,
                "charge": q,
                "electric_field": E_val,
                "length": params.get("pendulum_length", 1.0),
                "g": g,
                "duration": duration,
                # 元信息（不直接参与仿真，但传给前端显示）
                "_electric_force": round(electric_force, 3),
                "_gravity_force": round(gravity_force, 3),
                "_resultant_force": round(resultant_force, 3),
                "_equilibrium_angle": round(eq_angle, 1),
                "force_summary": {
                    "F_electric": round(electric_force, 3),
                    "F_gravity": round(gravity_force, 3),
                    "F_resultant": round(resultant_force, 3),
                    "equilibrium_angle_deg": round(eq_angle, 1),
                },
            },
        })

    # 兜底：如果有加速度参数，做匀加速
    if not phases and params.get("mass"):
        a_val = params.get("a", None)
        if a_val:
            phases.append({
                "type": "constant_accel",
                "params": {"a": a_val, "mass": mass},
            })

    return phases


# ==================================================================
#  主入口
# ==================================================================

def extract_physics_params(text):
    """
    从题目文本中提取物理参数并检测过程阶段。

    返回:
        {
            "params": {...},          # 所有提取到的物理量
            "phases": [...],          # 物理过程阶段
            "problem_type": str,      # 问题类型标识
            "is_calc_problem": bool   # 是否是计算题
        }
    """
    params = extract_all_params(text)
    phases = detect_phases(text, params)

    # 问题类型标识
    problem_type = "unknown"
    if phases:
        type_names = [p["type"] for p in phases]
        problem_type = "_".join(type_names)

    # 是否明显是计算题
    is_calc = any(kw in text for kw in ["求：", "求:", "试求", "计算", "试计算"])

    return {
        "params": params,
        "phases": phases,
        "problem_type": problem_type,
        "is_calc_problem": is_calc,
    }


# ==================================================================
#  仿真调度：参数 + 阶段 → 运行仿真
# ==================================================================

def run_simulation_from_text(text, fps=30):
    """
    从题目文本直接运行物理仿真。

    返回:
        simulator.run() 的结果，或 None（无法仿真）
    """
    extracted = extract_physics_params(text)

    if not extracted["phases"]:
        return None

    from physics_simulator import PhysicsSimulator

    sim = PhysicsSimulator(fps=fps)
    for phase in extracted["phases"]:
        phase_type = phase["type"]
        phase_params = phase["params"]
        max_dur = phase.get("max_duration")
        sim.add_phase(phase_type, phase_params, max_duration=max_dur)

    result = sim.run()
    result["extracted_params"] = extracted["params"]
    result["problem_type"] = extracted["problem_type"]
    return result


# ==================================================================
#  自测
# ==================================================================

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    tests = [
        "一质量 m = 2 kg 的小物块从光滑斜面顶端由静止释放，"
        "斜面倾角 θ = 37°，斜面长度 L = 3 m。物块滑到斜面底端后，"
        "进入粗糙水平面 BC，动摩擦因数 μ = 0.4。水平面 BC 足够长，"
        "重力加速度 g = 10 m/s²。求物块在水平面上滑行的最大距离。",

        "一质量 m=0.5kg 的小球从 h=20m 的高处自由落下，"
        "重力加速度 g=10m/s²，求小球落地时的速度。",

        "以 v0=10m/s 的初速度竖直上抛一个质量为 0.2kg 的小球，"
        "g=10m/s²，求小球上升的最大高度。",
    ]

    for text in tests:
        print("=" * 60)
        print("题目:", text[:80] + "...")
        result = extract_physics_params(text)
        print("参数:", result["params"])
        print("阶段:", [(p["type"], p["params"]) for p in result["phases"]])
        print("类型:", result["problem_type"])
        print()
