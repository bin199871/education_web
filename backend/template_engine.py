# -*- coding: utf-8 -*-
"""
物理动画模板引擎
职责：模板注册 → 匹配 → 参数提取 → 渲染
"""

import json
import re
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

# 可选：player-core 注入（导入失败则跳过）
try:
    from player_core_util import inject_core, is_available as core_available
except ImportError:
    def inject_core(html): return html
    def core_available(): return False

logger = logging.getLogger(__name__)

# ─── 参数映射表：extract_physics_params() 输出 key → 模板 schema key ───
PARAM_MAP = {
    'electric_pendulum': {
        'mass':            'm',
        'charge':          'q',
        'electric_field':  'E',
        'pendulum_length': 'L',
        'g':               'g',
    },
    'inclined_plane': {
        'mass':         'm',
        'angle_deg':    'theta',
        'slope_length': 'L',
        'mu':           'mu',
        'g':            'g',
    },
    'projectile': {
        'initial_velocity': 'v0',
        'height':           'h',
        'g':                'g',
    },
    'vertical_circular': {
        'mass': 'm',
        'g':    'g',
    },
    'conveyor_belt': {
        'mass': 'm',
        'mu':   'mu',
        'g':    'g',
    },
    'board_block': {
        'mass': 'm',
        'mu':   'mu',
        'g':    'g',
    },
    'collision': {
        'mass_A':          'm1',
        'mass_B':          'm2',
        'initial_velocity':'v1',
        'k_spring':        'k',
    },
    'connected_bodies': {
        'mass_A': 'm1',
        'mass_B': 'm2',
        'g':      'g',
    },
    'conductor_cutting': {
        'mass':            'm',
        'length':          'L',
        'initial_velocity':'v0',
        'magnetic_field':  'B',
        'resistance':      'R',
    },
    'locomotive': {
        'mass':           'm',
        'force':          'f',
        'power':          'P',
        'resistance_force':'f',
    },
    'magnetic_deflection': {
        'mass':           'm',
        'charge':         'q',
        'magnetic_field': 'B',
        'velocity':       'v',
    },
    'spring_oscillator': {
        'mass':      'm',
        'k_spring':  'k',
        'stiffness': 'k',
        'amplitude': 'A',
        'g':         'g',
    },
    'astronomy': {
        'mass':                'm',
        'mass_center':         'M',
        'distance':            'r',
        'gravitational_constant': 'G',
        'temperature':         'T',
    },
    'circuit_analysis': {
        'emf':                'E',
        'internal_resistance':'r',
        'resistance':         'R1',
    },
    'gas_law': {
        'gas_pressure':     'pA',
        'gas_volume':       'VA',
        'gas_temperature':  'TA',
        'substance_amount': 'n',
    },
    'mechanical_wave': {
        'wave_speed':  'v',
        'wavelength':  'lambda',
        'amplitude':   'A',
    },
    'vertical_circular': {
        'mass':      'm',
        'g':         'g',
        'velocity_A':'v1',
        'velocity_B':'v2',
    },
    'collision': {
        'mass_A':          'm1',
        'mass_B':          'm2',
        'initial_velocity':'v1',
        'velocity_B':      'v2',
        'k_spring':        'k',
    },
    'electric_pendulum': {
        'mass':            'm',
        'charge':          'q',
        'electric_field':  'E',
        'pendulum_length': 'L',
        'g':               'g',
        'theta_target':    'theta_target',
    },
    'coulomb_force': {
        'mass_A':         'mA',
        'mass_B':         'mB',
        'charge_A':       'qA',
        'charge_B':       'qB',
        'pendulum_length':'L',
        'g':              'g',
    },
    'light_refraction': {
        'angle_given':     'theta1',
        'refraction_angle':'theta2',
    },
    'atomic_energy': {
        'n_quantum': 'n_level',
    },
    'ac_transformer': {
        'voltage_max':      'Um',
        'period':           'T',
        'turns_primary':    'n1',
        'turns_secondary':  'n2',
        'resistance':       'R',
    },
}


def map_params(template_id: str, extracted: dict) -> dict:
    """将 extract_physics_params() 输出的 params 映射为模板 schema 的 key。
    只返回模板关注的 key，未提取到的参数留空。
    """
    mapping = PARAM_MAP.get(template_id, {})
    result = {}
    for ext_key, schema_key in mapping.items():
        value = extracted.get(ext_key)
        if value is not None:
            result[schema_key] = value
    return result


TEMPLATE_REGISTRY = {
    'electric_pendulum': {
        'file': 'electric_pendulum.html',
        'label': '电场中带电单摆',
        'params': ['m', 'q', 'E', 'L', 'g', 'theta_target'],
        'tags': ['电场', '单摆', '复合场', '圆周运动', '电场力', '带电粒子'],
        'param_schema': {
            'm':            {'type': 'float', 'min': 0.001, 'max': 100,  'default': 0.1,  'unit': 'kg'},
            'q':            {'type': 'float', 'min': 1e-12, 'max': 1,     'default': 5e-4, 'unit': 'C'},
            'E':            {'type': 'float', 'min': 0,     'max': 1e8,   'default': 2000,  'unit': 'N/C'},
            'L':            {'type': 'float', 'min': 0.1,   'max': 100,   'default': 1.0,   'unit': 'm'},
            'g':            {'type': 'float', 'min': 0,     'max': 100,   'default': 10,    'unit': 'm/s²'},
            'theta_target': {'type': 'float', 'min': 0,     'max': 90,    'default': 37,    'unit': '°'}
        }
    },
    'inclined_plane': {
        'file': 'inclined_plane.html',
        'label': '斜面 + 摩擦力',
        'params': ['m', 'theta', 'L', 'mu', 'g'],
        'tags': ['斜面', '摩擦力', '牛顿定律', '能量', '受力分析', '机械能'],
        'param_schema': {
            'm':     {'type': 'float', 'min': 0.001, 'max': 1000, 'default': 2.0, 'unit': 'kg'},
            'theta': {'type': 'float', 'min': 0,     'max': 90,   'default': 37,  'unit': '°'},
            'L':     {'type': 'float', 'min': 0.1,   'max': 100,  'default': 3.0, 'unit': 'm'},
            'mu':    {'type': 'float', 'min': 0,     'max': 1,    'default': 0.2, 'unit': ''},
            'g':     {'type': 'float', 'min': 0,     'max': 100,  'default': 10,  'unit': 'm/s²'}
        }
    },
    'projectile': {
        'file': 'projectile.html',
        'label': '平抛运动',
        'params': ['v0', 'h', 'g'],
        'tags': ['平抛', '曲线运动', '运动的合成与分解', '抛物线', '抛体运动'],
        'param_schema': {
            'v0': {'type': 'float', 'min': 0,   'max': 1000, 'default': 10,  'unit': 'm/s'},
            'h':  {'type': 'float', 'min': 0.1, 'max': 1000, 'default': 5.0, 'unit': 'm'},
            'g':  {'type': 'float', 'min': 0,   'max': 100,  'default': 10,  'unit': 'm/s²'}
        }
    },
    'vertical_circular': {
        'file': 'vertical_circular.html',
        'label': '竖直圆周运动',
        'params': ['m', 'R', 'g', 'v1', 'v2'],
        'tags': ['圆周运动', '向心力', '竖直平面', '过山车', '水流星', '最高点', '最低点'],
        'param_schema': {
            'm':  {'type': 'float', 'min': 0.001, 'max': 1000, 'default': 0.5, 'unit': 'kg'},
            'R':  {'type': 'float', 'min': 0.1,   'max': 100,  'default': 1.0, 'unit': 'm'},
            'g':  {'type': 'float', 'min': 0,     'max': 100,  'default': 10,  'unit': 'm/s²'},
            'v1': {'type': 'float', 'min': 0,     'max': 100,  'default': 5,   'unit': 'm/s'},
            'v2': {'type': 'float', 'min': 0,     'max': 100,  'default': 8,   'unit': 'm/s'}
        }
    },
    'conveyor_belt': {
        'file': 'conveyor_belt.html',
        'label': '传送带问题',
        'params': ['m', 'v0', 'mu', 'g'],
        'tags': ['传送带', '摩擦力', '牛顿定律', '运动学', '相对运动'],
        'param_schema': {
            'm':  {'type': 'float', 'min': 0.001, 'max': 1000, 'default': 2,  'unit': 'kg'},
            'v0': {'type': 'float', 'min': 0,     'max': 100,  'default': 4,  'unit': 'm/s'},
            'mu': {'type': 'float', 'min': 0,     'max': 1,    'default': 0.4,'unit': ''},
            'g':  {'type': 'float', 'min': 0,     'max': 100,  'default': 10, 'unit': 'm/s²'}
        }
    },
    'board_block': {
        'file': 'board_block.html',
        'label': '板块模型',
        'params': ['m', 'M', 'v0', 'mu', 'g'],
        'tags': ['板块', '摩擦力', '动量守恒', '相对运动', '木板', '滑块'],
        'param_schema': {
            'm':  {'type': 'float', 'min': 0.001, 'max': 1000, 'default': 2, 'unit': 'kg'},
            'M':  {'type': 'float', 'min': 0.001, 'max': 1000, 'default': 4, 'unit': 'kg'},
            'v0': {'type': 'float', 'min': 0,     'max': 100,  'default': 6, 'unit': 'm/s'},
            'mu': {'type': 'float', 'min': 0,     'max': 1,    'default': 0.3,'unit': ''},
            'g':  {'type': 'float', 'min': 0,     'max': 100,  'default': 10, 'unit': 'm/s²'}
        }
    },
    'spring_oscillator': {
        'file': 'spring_oscillator.html',
        'label': '弹簧振子',
        'params': ['m', 'k', 'A', 'g'],
        'tags': ['弹簧', '简谐振动', '振子', '胡克定律', '周期', '弹性势能'],
        'param_schema': {
            'm': {'type': 'float', 'min': 0.001, 'max': 100, 'default': 0.5, 'unit': 'kg'},
            'k': {'type': 'float', 'min': 0.1,   'max': 1e5, 'default': 100, 'unit': 'N/m'},
            'A': {'type': 'float', 'min': 0.01,  'max': 10,  'default': 0.2, 'unit': 'm'},
            'g': {'type': 'float', 'min': 0,     'max': 100, 'default': 10,  'unit': 'm/s²'}
        }
    },
    'collision': {
        'file': 'collision.html',
        'label': '动量守恒/碰撞',
        'params': ['m1', 'm2', 'v1', 'v2', 'k'],
        'tags': ['动量守恒', '碰撞', '弹性碰撞', '非弹性碰撞', '动量', '碰后', '冲量'],
        'param_schema': {
            'm1':     {'type': 'float', 'min': 0.001, 'max': 1000, 'default': 2, 'unit': 'kg'},
            'm2':     {'type': 'float', 'min': 0.001, 'max': 1000, 'default': 1, 'unit': 'kg'},
            'v1':     {'type': 'float', 'min': 0,     'max': 100,  'default': 3, 'unit': 'm/s'},
            'v2':     {'type': 'float', 'min': 0,     'max': 100,  'default': 0, 'unit': 'm/s'},
            'k':      {'type': 'float', 'min': 0.1,   'max': 1e5,  'default': 150, 'unit': 'N/m'},
        }
    },
    'magnetic_deflection': {
        'file': 'magnetic_deflection.html',
        'label': '带电粒子在磁场中偏转',
        'params': ['m', 'q', 'v', 'B'],
        'tags': ['磁场', '洛伦兹力', '偏转', '回旋', '带电粒子', '圆周运动'],
        'param_schema': {
            'm': {'type': 'float', 'min': 1e-30, 'max': 1e-20, 'default': 1.67e-27, 'unit': 'kg'},
            'q': {'type': 'float', 'min': 1e-20, 'max': 1e-18, 'default': 1.6e-19,  'unit': 'C'},
            'v': {'type': 'float', 'min': 0,     'max': 1e8,   'default': 1e6,     'unit': 'm/s'},
            'B': {'type': 'float', 'min': 0,     'max': 100,   'default': 0.5,     'unit': 'T'}
        }
    },
    'connected_bodies': {
        'file': 'connected_bodies.html',
        'label': '连接体问题',
        'params': ['m1', 'm2', 'g'],
        'tags': ['连接体', '滑轮', '绳子', '牛顿定律', '加速度'],
        'param_schema': {
            'm1': {'type': 'float', 'min': 0.001, 'max': 1000, 'default': 2, 'unit': 'kg'},
            'm2': {'type': 'float', 'min': 0.001, 'max': 1000, 'default': 1, 'unit': 'kg'},
            'g':  {'type': 'float', 'min': 0,     'max': 100,  'default': 10, 'unit': 'm/s²'}
        }
    },
    'conductor_cutting': {
        'file': 'conductor_cutting.html',
        'label': '导体棒切割磁感线',
        'params': ['m', 'B', 'L', 'v0', 'R'],
        'tags': ['导体棒', '切割', '磁感线', '电磁感应', '安培力', '感应电流'],
        'param_schema': {
            'm':  {'type': 'float', 'min': 0.001, 'max': 1000, 'default': 0.1, 'unit': 'kg'},
            'B':  {'type': 'float', 'min': 0,     'max': 100,  'default': 0.5, 'unit': 'T'},
            'L':  {'type': 'float', 'min': 0.01,  'max': 100,  'default': 1.0, 'unit': 'm'},
            'v0': {'type': 'float', 'min': 0,     'max': 100,  'default': 4,   'unit': 'm/s'},
            'R':  {'type': 'float', 'min': 0.01,  'max': 1000, 'default': 2,   'unit': 'Ω'}
        }
    },
    'locomotive': {
        'file': 'locomotive.html',
        'label': '机车启动',
        'params': ['m', 'P', 'f'],
        'tags': ['机车', '功率', '牵引力', '启动', '恒定功率', '最大速度'],
        'param_schema': {
            'm': {'type': 'float', 'min': 1,    'max': 1e6, 'default': 2000, 'unit': 'kg'},
            'P': {'type': 'float', 'min': 1,    'max': 1e8, 'default': 50000, 'unit': 'W'},
            'f': {'type': 'float', 'min': 0.1,  'max': 1e6, 'default': 2000, 'unit': 'N'}
        }
    },
    'circuit_analysis': {
        'file': 'circuit_analysis.html',
        'label': '电路动态分析',
        'params': ['E', 'r', 'R1', 'R2_max'],
        'tags': ['电路', '滑动变阻器', '电流', '电压', '闭合电路', '动态分析'],
        'param_schema': {
            'E':       {'type': 'float', 'min': 0.1, 'max': 1000, 'default': 12, 'unit': 'V'},
            'r':       {'type': 'float', 'min': 0,   'max': 100,  'default': 1,  'unit': 'Ω'},
            'R1':      {'type': 'float', 'min': 0.1, 'max': 1000, 'default': 5,  'unit': 'Ω'},
            'R2_max':  {'type': 'float', 'min': 0.1, 'max': 1000, 'default': 20, 'unit': 'Ω'}
        }
    },
    'astronomy': {
        'file': 'astronomy.html',
        'label': '万有引力/天体运动',
        'params': ['M', 'm', 'r', 'T', 'G'],
        'tags': ['万有引力', '天体', '卫星', '行星', '轨道', '宇宙速度', '向心加速度'],
        'param_schema': {
            'M': {'type': 'float', 'min': 1e20, 'max': 1e35, 'default': 1.99e30, 'unit': 'kg'},
            'm': {'type': 'float', 'min': 1e15, 'max': 1e30, 'default': 5.97e24, 'unit': 'kg'},
            'r': {'type': 'float', 'min': 1e6,  'max': 1e15, 'default': 1.5e11,  'unit': 'm'},
            'T': {'type': 'float', 'min': 1,    'max': 1e12, 'default': 3.15e7,  'unit': 's'},
            'G': {'type': 'float', 'min': 1e-15,'max': 1e-5, 'default': 6.67e-11,'unit': 'N·m²/kg²'}
        }
    },
    'mechanical_wave': {
        'file': 'mechanical_wave.html',
        'label': '机械波',
        'params': ['v', 'lambda', 'A'],
        'tags': ['机械波', '波形', '波长', '振幅', '频率', '波速', '振动'],
        'param_schema': {
            'v':     {'type': 'float', 'min': 0.1, 'max': 1e5, 'default': 20,  'unit': 'm/s'},
            'lambda':{'type': 'float', 'min': 0.01,'max': 1e5, 'default': 4,   'unit': 'm'},
            'A':     {'type': 'float', 'min': 0.01,'max': 100, 'default': 0.5, 'unit': 'm'}
        }
    },
    'gas_law': {
        'file': 'gas_law.html',
        'label': '气体实验定律',
        'params': ['pA', 'VA', 'TA', 'n', 'R'],
        'tags': ['气体', '理想气体', '状态方程', '等温', '等容', '等压', '气缸'],
        'param_schema': {
            'pA': {'type': 'float', 'min': 1e3, 'max': 1e8, 'default': 2e5,   'unit': 'Pa'},
            'VA': {'type': 'float', 'min': 0.1, 'max': 100, 'default': 3,     'unit': 'L'},
            'TA': {'type': 'float', 'min': 1,   'max': 1e4, 'default': 300,   'unit': 'K'},
            'n':  {'type': 'float', 'min': 0.01,'max': 100, 'default': 0.5,   'unit': 'mol'},
            'R':  {'type': 'float', 'min': 0.1, 'max': 100, 'default': 8.31,  'unit': 'J/(mol·K)'}
        }
    },
    'coulomb_force': {
        'file': 'coulomb_force.html',
        'label': '静电场/库仑力',
        'params': ['mA', 'mB', 'qA', 'qB', 'L', 'g'],
        'tags': ['静电场', '库仑力', '电荷', '库仑定律', '受力分析', '带电小球'],
        'param_schema': {
            'mA': {'type': 'float', 'min': 0.001, 'max': 100,  'default': 0.01, 'unit': 'kg'},
            'mB': {'type': 'float', 'min': 0.001, 'max': 100,  'default': 0.01, 'unit': 'kg'},
            'qA': {'type': 'float', 'min': 1e-12, 'max': 1,    'default': 1e-6, 'unit': 'C'},
            'qB': {'type': 'float', 'min': 1e-12, 'max': 1,    'default': 1e-6, 'unit': 'C'},
            'L':  {'type': 'float', 'min': 0.1,   'max': 10,   'default': 0.5,  'unit': 'm'},
            'g':  {'type': 'float', 'min': 0,     'max': 100,  'default': 10,   'unit': 'm/s²'}
        }
    },
    'light_refraction': {
        'file': 'light_refraction.html',
        'label': '光的折射反射',
        'params': ['theta1', 'theta2'],
        'tags': ['光的折射', '折射定律', '斯涅耳定律', '全反射', '反射定律', '几何光学'],
        'param_schema': {
            'theta1': {'type': 'float', 'min': 0.1, 'max': 89, 'default': 45, 'unit': '°'},
            'theta2': {'type': 'float', 'min': 0.1, 'max': 89, 'default': 30, 'unit': '°'},
        }
    },
    'atomic_energy': {
        'file': 'atomic_energy.html',
        'label': '原子物理/能级跃迁',
        'params': ['n_level'],
        'tags': ['原子物理', '能级跃迁', '氢原子', '玻尔理论', '光谱', '能级'],
        'param_schema': {
            'n_level': {'type': 'int', 'min': 2, 'max': 6, 'default': 4, 'unit': ''},
        }
    },
    'ac_transformer': {
        'file': 'ac_transformer.html',
        'label': '交流电/变压器',
        'params': ['Um', 'T', 'n1', 'n2', 'R'],
        'tags': ['交流电', '变压器', '正弦', '有效值', '理想变压器', '交变电流'],
        'param_schema': {
            'Um': {'type': 'float', 'min': 1,   'max': 1e5, 'default': 311, 'unit': 'V'},
            'T':  {'type': 'float', 'min': 0.001,'max': 100, 'default': 0.02,'unit': 's'},
            'n1': {'type': 'int',   'min': 1,    'max': 1e5, 'default': 1000,'unit': ''},
            'n2': {'type': 'int',   'min': 1,    'max': 1e5, 'default': 100, 'unit': ''},
            'R':  {'type': 'float', 'min': 0.1,  'max': 1e6, 'default': 10,  'unit': 'Ω'},
        }
    }
}


class TemplateEngine:
    def __init__(self, templates_dir: str = None, llm_config: dict = None):
        self.templates_dir = Path(templates_dir or Path(__file__).parent / 'templates')
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.llm_config = llm_config or {}
        self.registry = dict(TEMPLATE_REGISTRY)

    def list_templates(self) -> list:
        result = []
        for tid, tpl in self.registry.items():
            result.append({
                'id': tid, 'label': tpl['label'], 'params': list(tpl['params']),
                'tags': list(tpl['tags']),
                'param_info': {k: {'type': v['type'], 'unit': v.get('unit', ''), 'default': v['default']}
                               for k, v in tpl['param_schema'].items()}
            })
        return result

    def match_template_by_text(self, text: str) -> Optional[str]:
        if not text:
            return None
        text_lower = text.lower()
        scores: List[Tuple[str, int, List[str]]] = []
        for tid, tpl in self.registry.items():
            score = 0
            matched = []
            for tag in tpl['tags']:
                if tag.lower() in text_lower:
                    score += 10
                    matched.append(tag)
            tid_synergies = {
                'electric_pendulum': ['电场', '单摆', '匀强电场', '细线悬挂', '绝缘细线', '带电', '电场力', '电荷量', '悬点'],
                'inclined_plane': ['斜面', '摩擦', '粗糙', '滑下', '下滑', '滑行', 'μ', '动摩擦因数', '倾角', '滑到'],
                'projectile': ['平抛', '抛体', '水平初速度', '水平抛出', '飞行时间', '水平射程', '抛出', '抛物线', '落地时间'],
                'vertical_circular': ['圆周运动', '竖直平面', '圆轨道', '过山车', '水流星', '向心力', '最高点', '最低点', '轨道半径'],
                'conveyor_belt': ['传送带', '皮带', 'μ', '动摩擦因数', '共速', '相对滑动'],
                'board_block': ['木板', '滑块', '板块', '滑上', '相对位移', '共速'],
                'spring_oscillator': ['弹簧', '振子', '简谐振动', '胡克定律', '劲度系数', '周期', '振幅'],
                'collision': ['碰撞', '动量', '弹性碰撞', '非弹性碰撞', '动量守恒', '碰后', '冲量', 'vA', 'vB', '物块 A', '物块 B'],
                'magnetic_deflection': ['磁场', '洛伦兹力', '偏转', '回旋', '带电粒子', '磁感应强度'],
                'connected_bodies': ['连接体', '滑轮', '绳子', '细绳', '轻绳', '定滑轮'],
                'conductor_cutting': ['导体棒', '切割磁感线', '电磁感应', '安培力', '导轨', '感应电流', '平行导轨', '金属棒', '电阻R', '焦耳热'],
                'locomotive': ['机车', '启动', '功率', '牵引力', '额定功率', '最大速度', '恒定功率'],
                'circuit_analysis': ['电路', '滑动变阻器', '滑片', '电流表', '电压表', '内阻', '闭合电路'],
                'astronomy': ['万有引力', '天体', '卫星', '行星', '轨道', '宇宙速度', '地球', '太阳', '向心加速度'],
                'mechanical_wave': ['机械波', '波形', '波长', '振幅', '波速', '振动', '传播', '简谐横波'],
                'gas_law': ['气体', '理想气体', '状态方程', '等温', '等容', '等压', '气缸', '活塞', '压强']
            }
            if tid in tid_synergies:
                for kw in tid_synergies[tid]:
                    if kw.lower() in text_lower:
                        score += 5
                        matched.append('✨' + kw)
            if score > 0:
                scores.append((tid, score, matched))
        if not scores:
            return None
        registry_order = {tid: i for i, tid in enumerate(self.registry.keys())}
        scores.sort(key=lambda x: (-x[1], registry_order.get(x[0], 999)))
        return scores[0][0]

    def render(self, template_id: str, params: dict) -> str:
        tpl = self.registry.get(template_id)
        if not tpl:
            raise ValueError(f'未知模板: {template_id}')
        template_path = self.templates_dir / tpl['file']
        if not template_path.exists():
            raise FileNotFoundError(f'模板文件不存在: {template_path}')
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # 在 <head> 后注入 __INJECTED_PARAMS__
        inject = json.dumps(params, ensure_ascii=False)
        script = f'<script>var __INJECTED_PARAMS__ = {inject};</script>\n'
        html = html.replace('<head>', '<head>\n' + script)

        # 标题替换
        title = params.get('title', tpl['label'])
        html = html.replace('<title>', f'<title>{title} · ')

        # 生成时间
        gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        html = html.replace('</body>', f'<!-- 生成时间: {gen_time} -->\n</body>')

        # player-core 注入（可选：移除模板中的重复公共代码，替换为规范版）
        if core_available():
            try:
                html = inject_core(html)
            except Exception as e:
                logger.warning(f'player-core 注入失败: {e}')

        return html


_engine_instance = None
def get_engine(llm_config: dict = None) -> TemplateEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = TemplateEngine(llm_config=llm_config)
    return _engine_instance
