"""
Physics Simulator — 物理仿真引擎
==================================
职责：根据物理参数，按帧生成运动数据。
      输出每帧的位置、速度、加速度、能量等。

用法：
    simulator = PhysicsSimulator(fps=60)
    simulator.add_phase("slope", {"angle_deg": 37, "length": 3, "mass": 2, "g": 10})
    simulator.add_phase("rough_surface", {"mu": 0.4, "mass": 2, "g": 10, "v0_from_prev": True})
    simulator.add_phase("horizontal_pull", {"force": 10, "mu": 0.4, "mass": 2, "g": 10, "duration": 2})
    result = simulator.run()

    result["frames"]  # [{t, x, v, a, Ek, Ep, phase}...]
    result["summary"] # 关键物理量（最大速度、停止位置等）
"""

import math
import json


class PhysicsPhase:
    """单个物理过程的定义。"""

    # 支持的阶段类型
    TYPES = {
        "slope": "斜面加速下滑",
        "rough_surface": "粗糙水平面减速",
        "horizontal_pull": "水平拉力加速",
        "free_fall": "自由落体",
        "vertical_throw": "竖直上抛",
        "projectile": "平抛运动",
        "circular": "匀速圆周运动",
        "constant_accel": "匀加速直线运动（通用）",
        "electric_pendulum": "带电单摆在电场中摆动",
    }

    def __init__(self, phase_type, params):
        if phase_type not in self.TYPES:
            raise ValueError(f"不支持的阶段类型: {phase_type}，支持: {list(self.TYPES.keys())}")
        self.type = phase_type
        self.p = params.copy()  # 参数副本

    def calculate_initial_frame(self, t0=0.0, v0=0.0, x0=0.0, y0=0.0):
        """计算阶段的起始帧状态。
        优先使用参数中的 v0（如竖直上抛有自己独立的初速度）。"""
        p = self.p
        # 如果参数指定了 v0，使用它而不是前一个阶段的末速度
        if "v0" in p:
            v0 = p["v0"]
        return {"t": t0, "x": x0, "y": y0, "v": v0, "a": 0,
                "Ek": 0, "Ep": 0, "E_total": 0, "phase": self.type}

    def interpolate(self, state, dt, t_max=None):
        """计算 dt 秒后的状态。

        参数:
            state: 当前帧状态
            dt: 时间步长（秒）
            t_max: 可选，阶段最大持续时间

        返回:
            新 state，或 None 表示阶段结束
        """
        p = self.p
        t = state["t"]
        x = state["x"]
        y = state["y"]
        v = state["v"]

        if self.type == "slope":
            angle = math.radians(p.get("angle_deg", 30))
            g = p.get("g", 10)
            a = g * math.sin(angle)
            length = p.get("length", float("inf"))

            new_v = v + a * dt
            avg_v = (v + new_v) / 2
            ds = avg_v * dt

            # 在斜面上的位置（沿斜面方向）
            slope_pos = x + ds

            # 检查是否到达斜面底部
            if length != float("inf") and slope_pos >= length:
                # 精确计算到达底部的时间
                # v^2 = 2*a*s  → v_final = sqrt(2*a*length)
                v_final = math.sqrt(2 * a * length)
                t_final = (v_final - v) / a if a != 0 else 0
                return None  # 阶段结束

            new_x = slope_pos
            new_y = -new_x * math.sin(angle)
            new_Ek = 0.5 * p.get("mass", 1) * new_v ** 2
            new_Ep = p.get("mass", 1) * g * (length - new_x) * math.sin(angle) if length != float("inf") else 0

            return {"t": t + dt, "x": new_x, "y": new_y, "v": new_v, "a": a,
                    "Ek": round(new_Ek, 3), "Ep": round(new_Ep, 3),
                    "E_total": round(new_Ek + new_Ep, 3), "phase": self.type}

        elif self.type == "rough_surface":
            g = p.get("g", 10)
            mu = p.get("mu", 0.3)
            a = -mu * g

            new_v = v + a * dt
            if new_v <= 0:
                # 速度降为 0，停止
                new_v = 0
                avg_v = (v + new_v) / 2
                ds = v ** 2 / (2 * -a) if a != 0 else 0  # 精确停止距离
                new_x = x + v * dt + 0.5 * a * dt ** 2
                new_Ek = 0
                return {"t": t + dt, "x": x + ds, "y": y, "v": 0, "a": a,
                        "Ek": 0, "Ep": 0, "E_total": 0, "phase": self.type, "stopped": True}

            avg_v = (v + new_v) / 2
            ds = avg_v * dt
            new_x = x + ds
            new_Ek = 0.5 * p.get("mass", 1) * new_v ** 2

            return {"t": t + dt, "x": new_x, "y": y, "v": new_v, "a": a,
                    "Ek": round(new_Ek, 3), "Ep": 0, "E_total": round(new_Ek, 3),
                    "phase": self.type}

        elif self.type == "horizontal_pull":
            g = p.get("g", 10)
            mu = p.get("mu", 0)
            mass = p.get("mass", 1)
            force = p.get("force", 0)
            friction = mu * mass * g
            a = (force - friction) / mass

            new_v = v + a * dt
            avg_v = (v + new_v) / 2
            ds = avg_v * dt
            new_x = x + ds
            new_Ek = 0.5 * mass * new_v ** 2
            friction_work = friction * ds if ds > 0 else 0

            return {"t": t + dt, "x": new_x, "y": y, "v": new_v, "a": a,
                    "Ek": round(new_Ek, 3), "Ep": 0, "E_total": round(new_Ek, 3),
                    "friction_work": round(friction_work, 3), "phase": self.type}

        elif self.type == "free_fall":
            g = p.get("g", 10)
            a = g
            height = p.get("height", float("inf"))
            new_v = v + a * dt
            avg_v = (v + new_v) / 2
            ds = avg_v * dt
            new_y = y - ds
            if new_y <= -height:
                return None
            new_Ek = 0.5 * p.get("mass", 1) * new_v ** 2
            new_Ep = p.get("mass", 1) * g * (height + new_y)
            return {"t": t + dt, "x": x, "y": new_y, "v": new_v, "a": a,
                    "Ek": round(new_Ek, 3), "Ep": round(new_Ep, 3),
                    "E_total": round(new_Ek + new_Ep, 3), "phase": self.type}

        elif self.type == "projectile":
            v0 = p.get("v0", 10)
            g = p.get("g", 10)
            mass = p.get("mass", 1)
            init_height = p.get("height", 10)
            a = -g  # 竖直方向加速度

            # 水平匀速，竖直匀加速
            vx = v0 if 'vx' not in state else state.get('vx', v0)
            vy = state.get('vy', 0)
            new_vy = vy + a * dt
            avg_vy = (vy + new_vy) / 2
            dx = vx * dt
            dy = avg_vy * dt
            new_x = x + dx
            new_y = y + dy  # y向下为负

            # 检查是否落地
            if new_y <= -init_height:
                # 精确计算落地时间
                t_total = math.sqrt(2 * init_height / g) if init_height > 0 else 0
                final_vx = vx
                final_vy = g * t_total
                final_v = math.sqrt(final_vx ** 2 + final_vy ** 2)
                return None

            new_v = math.sqrt(vx ** 2 + new_vy ** 2)
            new_Ek = 0.5 * mass * new_v ** 2
            new_Ep = mass * g * (init_height + new_y)

            return {"t": t + dt, "x": new_x, "y": new_y, "v": new_v, "a": a,
                    "vx": vx, "vy": new_vy,
                    "Ek": round(new_Ek, 3), "Ep": round(new_Ep, 3),
                    "E_total": round(new_Ek + new_Ep, 3), "phase": self.type}

        elif self.type == "vertical_throw":
            v0 = p.get("v0", 10)
            g = p.get("g", 10)
            mass = p.get("mass", 1)
            a = -g
            new_v = v + a * dt
            if new_v <= 0:
                # 精确到达最高点
                t_top = v / g
                d_top = v * t_top - 0.5 * g * t_top ** 2
                return None  # 阶段结束（到达最高点）

            avg_v = (v + new_v) / 2
            ds = avg_v * dt
            new_y = y + ds
            new_Ek = 0.5 * mass * new_v ** 2
            new_Ep = mass * g * max(new_y, 0)

            return {"t": t + dt, "x": x, "y": new_y, "v": new_v, "a": a,
                    "Ek": round(new_Ek, 3), "Ep": round(new_Ep, 3),
                    "E_total": round(new_Ek + new_Ep, 3), "phase": self.type}

        elif self.type == "constant_accel":
            a = p.get("a", 0)
            duration = p.get("duration", float("inf"))
            if t - state.get("phase_start_t", t) >= duration:
                return None
            new_v = v + a * dt
            avg_v = (v + new_v) / 2
            ds = avg_v * dt
            new_x = x + ds
            new_Ek = 0.5 * p.get("mass", 1) * new_v ** 2
            return {"t": t + dt, "x": new_x, "y": y, "v": new_v, "a": a,
                    "Ek": round(new_Ek, 3), "Ep": 0, "E_total": round(new_Ek, 3),
                    "phase": self.type}

        elif self.type == "electric_pendulum":
            """带电单摆在水平匀强电场中摆动。
            运动方程：θ'' = -(g/L) sin(θ) + (qE/(mL)) cos(θ)
            使用子步进 + 半隐式 Euler 保持能量守恒。
            """
            mass = p.get("mass", 0.1)
            q = p.get("charge", 5e-4)
            E = p.get("electric_field", 2000)
            L = p.get("length", 1.0)
            g = p.get("g", 10)
            max_duration = p.get("duration", float("inf"))
            phase_start = state.get("phase_start_t")
            if phase_start is not None and t - phase_start >= max_duration:
                return None

            theta = state.get("theta", 0.0)
            omega = state.get("omega", 0.0)

            # 子步进：每帧分 N 步，提高精度
            sub_steps = 8
            sub_dt = dt / sub_steps
            for _ in range(sub_steps):
                alpha = -(g / L) * math.sin(theta) + (q * E / (mass * L)) * math.cos(theta)
                omega = omega + alpha * sub_dt
                theta = theta + omega * sub_dt

            if abs(theta) > math.pi * 0.95:
                return None

            bob_x = L * math.sin(theta)
            bob_y = -L * math.cos(theta)
            v_linear = L * abs(omega)

            Ek = 0.5 * mass * v_linear ** 2
            Ep_gravity = mass * g * L * (1 - math.cos(theta))
            Ep_electric = -q * E * L * math.sin(theta)
            E_total = Ek + Ep_gravity + Ep_electric

            return {
                "t": round(t + dt, 3),
                "theta": round(theta, 5),
                "omega": round(omega, 5),
                "x": round(bob_x, 4),
                "y": round(bob_y, 4),
                "v": round(v_linear, 4),
                "a": round(alpha, 4),
                "Ek": round(Ek, 4),
                "Ep_gravity": round(Ep_gravity, 4),
                "Ep_electric": round(Ep_electric, 4),
                "E_total": round(E_total, 4),
                "phase": self.type,
            }

        # 兜底
        return None


class PhysicsSimulator:
    """物理仿真器：串联多个物理阶段，逐帧生成运动数据。"""

    def __init__(self, fps=60):
        self.fps = fps
        self.phases = []  # [(phase, max_duration)]
        self.dt = 1.0 / fps

    def add_phase(self, phase_type, params, max_duration=None):
        """添加一个物理阶段。

        参数:
            phase_type: 阶段类型
            params: 物理参数字典
            max_duration: 最大持续时间（秒），None=自动结束
        """
        phase = PhysicsPhase(phase_type, params)
        self.phases.append((phase, max_duration))

    def run(self):
        """执行仿真，返回所有帧数据。"""
        frames = []
        state = {"t": 0.0, "x": 0.0, "y": 0.0, "v": 0.0, "a": 0,
                 "Ek": 0, "Ep": 0, "E_total": 0, "phase": "start"}
        frame_num = 0
        phase_idx = 0

        while phase_idx < len(self.phases):
            phase, max_dur = self.phases[phase_idx]
            elapsed_in_phase = 0

            # 记录阶段起始状态
            if frame_num == 0:
                state = phase.calculate_initial_frame()
                state["phase_start_t"] = 0
                frames.append(self._state_to_frame(state, frame_num))
                frame_num += 1

            while True:
                elapsed_in_phase += self.dt

                if max_dur and elapsed_in_phase >= max_dur:
                    break

                new_state = phase.interpolate(state, self.dt)
                if new_state is None:
                    # 阶段结束（如到达斜面底端）
                    break

                # 保留 phase_start_t（并非所有 phase 都返回它）
                if "phase_start_t" in state:
                    new_state["phase_start_t"] = state["phase_start_t"]
                state = new_state
                frames.append(self._state_to_frame(state, frame_num))
                frame_num += 1

                # 检查是否停止
                if state.get("stopped"):
                    break

            # 进入下一阶段
            phase_idx += 1
            if phase_idx < len(self.phases):
                # 用当前状态初始化下一阶段
                next_phase, _ = self.phases[phase_idx]
                next_state = next_phase.calculate_initial_frame(
                    t0=state["t"], v0=state["v"],
                    x0=state["x"], y0=state["y"]
                )

        result = {
            "frames": frames,
            "total_frames": len(frames),
            "total_duration_sec": round(len(frames) / self.fps, 2),
            "fps": self.fps,
            "summary": self._compute_summary(frames)
        }

        return result

    def _state_to_frame(self, state, frame_num):
        """将内部状态转换为帧数据格式。"""
        frame = {
            "frame": frame_num,
            "t": round(state["t"], 3),
            "x": round(state["x"], 4),
            "y": round(state.get("y", 0), 4),
            "v": round(state["v"], 4),
            "a": round(state["a"], 4),
            "Ek": round(state.get("Ek", 0), 4),
            "Ep": round(state.get("Ep_gravity", state.get("Ep", 0)), 4),
            "E_total": round(state.get("E_total", 0), 4),
            "phase": state.get("phase", ""),
        }
        # 带电单摆额外字段
        if "theta" in state:
            frame["theta"] = round(state["theta"], 5)
            frame["omega"] = round(state["omega"], 5)
        if "Ep_electric" in state:
            frame["Ep_electric"] = round(state["Ep_electric"], 4)
            frame["Ep_gravity"] = round(state.get("Ep_gravity", 0), 4)
        return frame

    def _compute_summary(self, frames):
        """计算关键物理量摘要。"""
        if not frames:
            return {}

        max_v = max(f["v"] for f in frames)
        max_v_frame = next(f for f in frames if f["v"] == max_v)
        max_Ek = max(f["Ek"] for f in frames)
        final_frame = frames[-1]

        return {
            "max_velocity": round(max_v, 3),
            "max_velocity_at_frame": max_v_frame["frame"],
            "max_kinetic_energy": round(max_Ek, 3),
            "final_position": round(final_frame["x"], 3),
            "final_velocity": round(final_frame["v"], 3),
            "total_frames": len(frames),
        }


# ==================================================================
#  便捷入口：从题目参数直接生成仿真数据
# ==================================================================

def simulate_slope_problem(mass=2, angle_deg=37, length=3, mu=0.4,
                           g=10, pull_force=10, pull_after=1.0,
                           fps=60):
    """
    斜面+粗糙面+拉力 经典题型的仿真。

    返回:
        simulator.run() 的结果
    """
    sim = PhysicsSimulator(fps)

    # 阶段1：斜面加速下滑
    sim.add_phase("slope", {
        "angle_deg": angle_deg, "length": length,
        "mass": mass, "g": g
    })

    # 阶段2：粗糙水平面减速
    sim.add_phase("rough_surface", {
        "mu": mu, "mass": mass, "g": g
    }, max_duration=pull_after)

    # 阶段3：施加拉力
    sim.add_phase("horizontal_pull", {
        "force": pull_force, "mu": mu,
        "mass": mass, "g": g
    }, max_duration=2.0)

    return sim.run()


def format_frames_to_timeline(frames, fps=60, canvas_width=960, canvas_height=640):
    """将仿真帧数据转换为 timeline.json 格式。"""
    # 这里只生成核心数据，实际转换在 scene_builder 中完成
    return {
        "meta": {
            "totalFrames": len(frames),
            "fps": fps,
            "width": canvas_width,
            "height": canvas_height,
            "type": "physics_simulation"
        },
        "physics_data": frames
    }


def simulate_electric_pendulum(mass=0.1, charge=5e-4, electric_field=2000,
                                length=1.0, g=10, duration=3.0, fps=60):
    """
    带电单摆在水平匀强电场中运动的仿真。

    参数同 electric_pendulum 阶段。

    返回:
        simulator.run() 的结果
    """
    sim = PhysicsSimulator(fps)
    sim.add_phase("electric_pendulum", {
        "mass": mass, "charge": charge, "electric_field": electric_field,
        "length": length, "g": g, "duration": duration,
    }, max_duration=duration)
    return sim.run()


# ==================================================================
#  自测
# ==================================================================

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    print("=== 斜面问题仿真 ===\n")

    result = simulate_slope_problem(
        mass=2, angle_deg=37, length=3, mu=0.4,
        g=10, pull_force=10, pull_after=1.0, fps=30
    )

    print(f"总帧数: {result['total_frames']}")
    print(f"总时长: {result['total_duration_sec']} 秒")
    print(f"最大速度: {result['summary']['max_velocity']} m/s")
    print(f"最大动能: {result['summary']['max_kinetic_energy']} J")
    print(f"最终位置: {result['summary']['final_position']} m")
    print(f"最终速度: {result['summary']['final_velocity']} m/s")
    print()

    # 关键帧展示
    print("关键帧:")
    key_frames = []
    for i, f in enumerate(result["frames"]):
        if f["frame"] % (result["total_frames"] // 10 + 1) == 0:
            key_frames.append(f)

    for f in key_frames[:15]:
        print(f"  帧{f['frame']:4d} t={f['t']:5.2f}s "
              f"x={f['x']:6.3f}m v={f['v']:6.3f}m/s "
              f"a={f['a']:6.2f}m/s² "
              f"Ek={f['Ek']:6.2f}J Ep={f['Ep']:6.2f}J "
              f"阶段:{f['phase']}")
