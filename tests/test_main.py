from manim import *
import numpy as np

class HelicalMotion(ThreeDScene):
    """
    带电粒子在匀强磁场中的螺旋运动 - 3D 可视化
    知识点：速度分解为 v⊥（圆周运动）和 v∥（匀速直线）
    """
    def construct(self):
        # ---------- 1. 设置 3D 场景 ----------
        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES, distance=10)
        self.begin_ambient_camera_rotation(rate=0.15)  # 缓慢自动旋转，展示 3D 效果

        # ---------- 2. 物理参数 ----------
        B = 1.2           # 磁感应强度
        v_perp = 2.0      # 垂直速度分量
        v_par = 1.2       # 平行速度分量
        omega = B         # 角速度 (q/m = 1)
        radius = v_perp / B  # 回旋半径 r = mv⊥/(qB)

        # ---------- 3. 绘制磁场区域（半透明圆柱） ----------
        cylinder = Cylinder(
            radius=radius * 1.3,
            height=8,
            fill_opacity=0.08,
            fill_color=BLUE,
            stroke_color=BLUE_D,
            stroke_opacity=0.2
        )
        cylinder.move_to(ORIGIN)
        self.add(cylinder)

        # ---------- 4. 磁场方向标注（B 箭头） ----------
        b_arrow = Arrow3D(
            start=UP * 3.5,
            end=UP * 4.8,
            color=BLUE_C,
            thickness=0.04
        )
        b_label = Text("B", color=BLUE_C, font_size=36).next_to(b_arrow, UP, buff=0.1)
        self.add(b_arrow, b_label)

        # ---------- 5. 创建粒子（发光小球） ----------
        particle = Sphere(radius=0.25, color=YELLOW, fill_opacity=1)
        particle.set_glow(radius=0.6, color=YELLOW, intensity=0.3)
        self.add(particle)

        # ---------- 6. 轨迹线（动态绘制） ----------
        trail = VMobject(stroke_color=YELLOW, stroke_width=2, stroke_opacity=0.6)
        self.add(trail)

        # ---------- 7. 速度箭头（随粒子移动） ----------
        # 我们将在更新函数中动态创建

        # ---------- 8. 信息显示（公式和数值） ----------
        formula = MathTex(
            r"r = \frac{mv_\perp}{qB} = ",
            f"{radius:.2f}",
            color=YELLOW
        ).to_corner(UL)
        self.add(formula)

        # ---------- 9. 动画循环 ----------
        num_points = 300
        t_values = np.linspace(0, 8, num_points)
        points = []

        # 预计算轨迹点
        for t in t_values:
            x = radius * np.cos(omega * t)
            z = radius * np.sin(omega * t)
            y = v_par * t
            points.append(np.array([x, y, z]))

        # 动画：粒子沿轨迹移动，同时绘制轨迹线
        for i in range(1, len(points)):
            # 更新粒子位置
            self.play(
                particle.animate.move_to(points[i]),
                run_time=0.02,
                rate_func=linear
            )
            # 更新轨迹
            trail.set_points_smoothly([points[:i+1]])
            # 显示速度箭头（每10帧更新一次）
            if i % 10 == 0 and i > 1:
                self.remove(*self.get_mobjects_from_last_arrow())
                self._add_velocity_arrows(points[i], v_perp, v_par, omega * t_values[i])

        # 保持最终画面
        self.wait(2)

    def _add_velocity_arrows(self, pos, v_perp, v_par, theta):
        """添加速度分解箭头"""
        # v⊥ 方向（水平径向）
        v_perp_dir = np.array([-np.sin(theta), 0, np.cos(theta)])
        v_perp_vec = v_perp_dir * v_perp * 0.5

        # v∥ 方向（竖直）
        v_par_vec = np.array([0, v_par * 0.5, 0])

        # 合速度
        v_total = v_perp_vec + v_par_vec

        # 创建箭头并添加到场景
        arrow_perp = Arrow3D(
            start=pos, end=pos + v_perp_vec,
            color=ORANGE, thickness=0.03
        )
        arrow_par = Arrow3D(
            start=pos, end=pos + v_par_vec,
            color=YELLOW, thickness=0.03
        )
        arrow_total = Arrow3D(
            start=pos, end=pos + v_total,
            color=GREEN, thickness=0.04
        )

        # 保存以便后续移除
        self._last_arrows = [arrow_perp, arrow_par, arrow_total]
        self.add(arrow_perp, arrow_par, arrow_total)