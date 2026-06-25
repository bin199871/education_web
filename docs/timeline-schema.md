# Timeline JSON 数据格式规范

> AI 生成物理教学动画的数据格式。遵循此规范即可确保被 `engine.js` 正确播放。
> 不需要写任何 HTML/CSS/JS，只需要填充 JSON 数据。

---

## 顶层结构

```json
{
  "meta": { ... },
  "timeline": [ ... ]
}
```

## meta — 全局配置

```json
{
  "meta": {
    "totalFrames": 4800,
    "fps": 60,
    "width": 1280,
    "height": 720
  }
}
```

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `totalFrames` | ✅ | number | 总帧数（时长秒数 × fps） |
| `fps` | ❌ | number | 默认 `60`，帧率 |
| `width` | ❌ | number | 画布宽，默认 `1280` |
| `height` | ❌ | number | 画布高，默认 `720` |

## timeline — 片段列表

按 `startFrame` **升序排列**的片段数组：

```json
{
  "timeline": [
    {
      "startFrame": 0,
      "endFrame": 600,
      "background": "#000000",
      "transition_in": { "type": "fade_in", "duration": 15 },
      "transition": { "type": "fade_out", "duration": 15 },
      "layers": [ ... ]
    }
  ]
}
```

### 片段字段

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `startFrame` | ✅ | number | 起始帧（含） |
| `endFrame` | ✅ | number | 结束帧（含），必须 > startFrame |
| `background` | ❌ | string/object | 背景色 `"#000"` 或背景组件配置 |
| `transition_in` | ❌ | object | 切入过渡 |
| `transition` | ❌ | object | 切出过渡（片尾淡出） |
| `layers` | ✅ | array | 渲染层列表，按顺序绘制（底→顶） |

### background 格式

**纯色字符串：**
```json
"background": "#0a0e1a"
```

**组件背景：**
```json
"background": {
  "component": "drawStarField",
  "params": { "stars": 80, "rotationSpeed": 0.001, "twinkleIntensity": 0.5 }
}
```

**纯色对象：**
```json
"background": { "type": "color", "color": "#1a1a2e" }
```

### transition 格式

```json
{
  "transition_in": {
    "type": "fade_in",
    "duration": 15,
    "easing": "easeOut"
  },
  "transition": {
    "type": "fade_out",
    "duration": 15,
    "easing": "easeOut"
  }
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `duration` | ❌ | 过渡持续帧数，默认 `15`（约0.25秒） |
| `easing` | ❌ | 缓动函数：`"easeOut"` / `"easeInOut"` / `"linear"` |

---

## layers — 渲染层

```json
{
  "layers": [
    { "component": "drawCube", "params": { "cx": 640, "cy": 300 } }
  ]
}
```

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `component` | ✅ | string | 组件名，必须是 Components 中注册的 |
| `params` | ✅ | object | 传给组件的参数，每个组件有不同参数 |

---

## 动画参数

组件的每个参数支持三种形式：

### 1. 静态值 — 直接填数字/字符串

```json
{ "cx": 640, "color": "#4CAF50", "label": "质量" }
```

### 2. 动画插值 — 从 A 到 B 过渡

```json
{
  "opacity": {
    "animate": { "from": 0, "to": 1, "duration": 30, "easing": "easeOut" }
  }
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `from` | ✅ | 起始值 |
| `to` | ✅ | 结束值 |
| `duration` | ❌ | 持续帧数，默认 `30` |
| `delay` | ❌ | 延迟帧数，默认 `0` |
| `easing` | ❌ | `"easeOut"` / `"easeInOut"` / `"easeOutBack"` / `"linear"` |

**颜色插值：**
```json
{
  "color": {
    "animate": { "fromColor": "#000000", "toColor": "#ffffff", "duration": 30 }
  }
}
```

### 3. 正弦波动 — 周期性变化

```json
{
  "rotY": {
    "type": "sin",
    "amplitude": 0.3,
    "period": 60,
    "center": 0.5
  }
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `amplitude` | ❌ | 振幅，默认 `0` |
| `period` | ❌ | 周期（帧数），默认 `60` |
| `center` | ❌ | 中心值，默认参数本身的默认值 |
| `offset` | ❌ | 相位偏移（帧数），默认 `0` |

---

## 组件参考

### drawPendulum — 单摆

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| cx/cy | ✅ | — | 悬挂点坐标 |
| length | ❌ | 120 | 摆长 |
| angle | ❌ | 0 | 摆角（弧度），支持sin动画 |
| bobSize | ❌ | 16 | 摆球大小 |
| bobColor | ❌ | #fbbf24 | 摆球颜色 |

### drawSpringOscillator — 弹簧振子

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| cx/cy | ✅ | — | 弹簧顶端坐标 |
| mass | ❌ | 20 | 振子大小 |
| displacement | ❌ | 0 | 位移（像素），支持sin动画 |
| restLength | ❌ | 80 | 弹簧原长 |

### drawInclinedPlane — 斜面

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| cx/cy | ✅ | — | 斜面底部坐标 |
| angle | ❌ | 30 | 斜面角度（度） |
| length | ❌ | 200 | 斜面长度 |
| objectPosition | ❌ | 0.5 | 物体在斜面上的位置 0-1 |
| showForces | ❌ | false | 显示受力箭头 |

### drawCircuitComponent — 电路元件

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| cx/cy | ✅ | — | 中心坐标 |
| type | ✅ | resistor | battery/resistor/bulb/switch/ammeter/voltmeter/wire |
| orientation | ❌ | horizontal | horizontal/vertical |
| state | ❌ | closed | 开关状态 open/closed |
| lit | ❌ | false | 灯泡发光 |

### drawGraph — 坐标系与数据曲线

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| cx/cy | ✅ | — | 原点坐标 |
| width/height | ❌ | 200/160 | 轴尺寸 |
| xLabel/yLabel | ❌ |  | 轴标签 |
| lines | ❌ | [] | [{points:[{x,y}], color, label}] |

### drawLever — 杠杆

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| cx/cy | ✅ | — | 支点坐标 |
| length | ❌ | 180 | 杠杆总长 |
| angle | ❌ | 0 | 倾斜角（弧度），支持sin动画 |
| leftLabel/rightLabel | ❌ |  | 左右标签 |

### drawContainer — 容器与液体

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| cx/cy | ✅ | — | 容器中心/底部 |
| width/height | ❌ | 100/120 | 容器尺寸 |
| liquidLevel | ❌ | 0.5 | 液面高度 0-1 |
| objectSize | ❌ | 0 | 浸入物体大小（0=无） |

### drawLightRay — 光线（反射/折射）

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| cx/cy | ✅ | — | 入射点坐标 |
| incidentAngle | ❌ | 45 | 入射角（度） |
| reflectAngle | ❌ | 45 | 反射角（度） |
| refractAngle | ❌ | 0 | 折射角（度，0=无折射） |



### drawCube — 3D 旋转立方体

```json
{
  "component": "drawCube",
  "params": {
    "cx": 640, "cy": 300,
    "size": 80,
    "color": "#88bbdd",
    "label": "1 kg",
    "rotX": 0.5,
    "rotY": 0.8,
    "opacity": 1
  }
}
```

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `cx` | ✅ | — | 锚点X |
| `cy` | ✅ | — | 锚点Y |
| `size` | ❌ | 80 | 边长 |
| `color` | ❌ | "#88bbdd" | 基准色 |
| `borderColor` | ❌ | "#334455" | 边框色 |
| `label` | ❌ | "" | 正面标签文字 |
| `labelColor` | ❌ | "#ffffff" | 标签颜色 |
| `rotX` | ❌ | 0.5 | X轴旋转（弧度），支持sin动画 |
| `rotY` | ❌ | 0.8 | Y轴旋转（弧度），支持sin动画 |
| `opacity` | ❌ | 1 | 透明度，支持动画 |

### drawBalance — 托盘天平

```json
{
  "component": "drawBalance",
  "params": {
    "cx": 320, "cy": 350,
    "scale": 1,
    "weight": 2.0,
    "label": "⚖️ 质量 = 1.0 kg",
    "pointerAngle": 0,
    "highlight": false
  }
}
```

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `cx` | ✅ | — | 锚点X |
| `cy` | ✅ | — | 锚点Y |
| `scale` | ❌ | 1 | 整体缩放 |
| `weight` | ❌ | 0 | 重量（影响物体大小），0-3 |
| `label` | ❌ | "" | 标签文字 |
| `pointerAngle` | ❌ | 0 | 指针偏角（弧度） |
| `highlight` | ❌ | false | 标签绿色高亮 |

### drawSpringScale — 弹簧秤

```json
{
  "component": "drawSpringScale",
  "params": {
    "cx": 960, "cy": 350,
    "scale": 1,
    "weight": 5.0,
    "label": "📏 重力 = 9.8 N",
    "highlight": false
  }
}
```

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `cx` | ✅ | — | 锚点X |
| `cy` | ✅ | — | 锚点Y |
| `scale` | ❌ | 1 | 整体缩放 |
| `weight` | ❌ | 0 | 重量 0-10，自动转指针角度 |
| `pointerAngle` | ❌ | — | 直接指定指针弧度（覆盖weight） |
| `label` | ❌ | "" | 标签文字 |
| `highlight` | ❌ | false | 标签橙色高亮 |

### drawTypewriterText — 打字机文字

```json
{
  "component": "drawTypewriterText",
  "params": {
    "cx": 640, "cy": 500,
    "text": "欢迎来到物理课堂",
    "startFrame": 0,
    "charsPerSecond": 10,
    "font": "24px sans-serif",
    "color": "#ffffff",
    "align": "center"
  }
}
```

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `cx` | ✅ | — | 锚点X |
| `cy` | ✅ | — | 锚点Y |
| `text` | ✅ | "" | 完整文本 |
| `startFrame` | ❌ | 0 | 开始打字的帧号 |
| `charsPerSecond` | ❌ | 10 | 打字速度 |
| `font` | ❌ | "24px sans-serif" | 字体 |
| `color` | ❌ | "#ffffff" | 文字颜色 |
| `align` | ❌ | "center" | 对齐：center/left/right |

### drawPopupLabel — 弹出标签框

```json
{
  "component": "drawPopupLabel",
  "params": {
    "cx": 640, "cy": 200,
    "width": 200, "height": 60,
    "text": "核心结论",
    "textColor": "#ffffff",
    "bgColor": "#333333",
    "borderColor": "#666666",
    "popStartFrame": 0,
    "popDuration": 30
  }
}
```

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `cx` | ✅ | — | 锚点X |
| `cy` | ✅ | — | 锚点Y |
| `width` | ❌ | 200 | 框宽度 |
| `height` | ❌ | 60 | 框高度 |
| `text` | ❌ | "" | 标签文字 |
| `textColor` | ❌ | "#ffffff" | 文字颜色 |
| `bgColor` | ❌ | "#333333" | 背景色 |
| `borderColor` | ❌ | "#666666" | 边框色 |
| `popStartFrame` | ❌ | 0 | 弹出动画起始帧 |
| `popDuration` | ❌ | 30 | 弹出动画持续帧 |

### drawStarField — 星空背景

```json
{
  "component": "drawStarField",
  "params": {
    "stars": 80,
    "rotationSpeed": 0.001,
    "twinkleIntensity": 0.5,
    "opacity": 1
  }
}
```

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `stars` | ❌ | [] | 如不传则自动生成 |
| `rotationSpeed` | ❌ | 0.001 | 旋转速度（弧度/帧） |
| `twinkleIntensity` | ❌ | 0.5 | 闪烁强度 0-1 |
| `opacity` | ❌ | 1 | 整体透明度，支持动画 |

### drawEarthBackground — 地球表面背景

```json
{
  "component": "drawEarthBackground",
  "params": {
    "grassColor": "#6B8E23",
    "clouds": [
      { "x": 100, "y": 60, "w": 80, "h": 25, "speed": 0.3 }
    ]
  }
}
```

### drawMoonBackground — 月球表面背景

```json
{
  "component": "drawMoonBackground",
  "params": {
    "craters": [
      { "x": 200, "y": 350, "rx": 30, "ry": 15, "depth": 0.5 }
    ],
    "earthPosition": { "x": 120, "y": 60 },
    "starOpacity": 0.8
  }
}
```

### drawSplitScreenDivider — 分屏分割线

```json
{
  "component": "drawSplitScreenDivider",
  "params": {
    "splitX": 640,
    "color": "#ffffff",
    "glowColor": "rgba(255,255,255,0.3)",
    "glowWidth": 60
  }
}
```

### drawMeteor — 流星

```json
{
  "component": "drawMeteor",
  "params": {
    "fromX": 200, "fromY": 0,
    "toX": 600, "toY": 300,
    "startFrame": 0,
    "duration": 30
  }
}
```

### drawForceArrow — 受力箭头（新增）

```json
{
  "component": "drawForceArrow",
  "params": {
    "cx": 640, "cy": 360,
    "angle": -90,
    "length": 80,
    "color": "#ef4444",
    "label": "F",
    "lineWidth": 3,
    "opacity": 1
  }
}
```

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `cx` | ✅ | — | 起点X |
| `cy` | ✅ | — | 起点Y |
| `angle` | ✅ | — | 方向角度（度），0=右 |
| `length` | ❌ | 60 | 箭头长度 |
| `color` | ❌ | "#ef4444" | 颜色 |
| `label` | ❌ | "" | 标签文字 |
| `lineWidth` | ❌ | 3 | 线宽 |
| `opacity` | ❌ | 1 | 透明度，支持动画 |

### drawFormulaBoard — 公式板（新增）

```json
{
  "component": "drawFormulaBoard",
  "params": {
    "cx": 640, "cy": 360,
    "formula": "G = mg",
    "variables": [
      { "symbol": "G", "name": "重力", "color": "#FF9800" }
    ],
    "bgColor": "rgba(0,0,0,0.5)",
    "opacity": 1
  }
}
```

### drawOptionCard — 选项卡片（新增）

```json
{
  "component": "drawOptionCard",
  "params": {
    "cx": 640, "cy": 300,
    "label": "A",
    "text": "选项内容",
    "correct": false,
    "showReason": false,
    "reason": "错误原因",
    "opacity": 1
  }
}
```

### drawTextBlock — 文字区块（新增）

```json
{
  "component": "drawTextBlock",
  "params": {
    "cx": 640, "cy": 400,
    "text": "一行文字",
    "font": "20px sans-serif",
    "color": "#ffffff",
    "align": "center",
    "opacity": 1
  }
}
```

---

## 完整示例

见 `docs/timeline-example.json`。

## 校验规则

engine.js 加载timeline.json时会自动校验：
1. `meta.totalFrames` 必须为正整数
2. `timeline` 必须是数组且非空
3. 每个片段 `endFrame` > `startFrame`
4. 片段按 `startFrame` 升序排列
5. 片段帧范围不重叠
6. 片段帧范围不超出 `totalFrames`
7. 每个 `layer.component` 必须在组件库中存在
8. 非必填参数自动补默认值

校验失败时控制台输出具体错误，不会白屏。
