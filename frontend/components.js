/**
 * Canvas 2D 物理教学动画组件库
 *
 * 每个组件是一个纯函数，签名统一为 drawXxx(ctx, params, frame)
 * - ctx: CanvasRenderingContext2D
 * - params: 配置参数对象
 * - frame: 整数帧号，从0递增用于驱动动画
 *
 * 所有坐标相对锚点 (cx, cy)，组件内部不感知画布绝对位置。
 */

/* ─── 公共工具函数 ─── */

/** 线性插值 */
function lerp(a, b, t) {
  return a + (b - a) * t;
}

/** 限制值在 [min, max] 范围内 */
function clamp(val, min, max) {
  if (val < min) return min;
  if (val > max) return max;
  return val;
}

/** 缓出 (easeOutCubic) */
function easeOut(t) {
  return 1 - Math.pow(1 - t, 3);
}

/** 缓入缓出 (easeInOutCubic) */
function easeInOut(t) {
  if (t < 0.5) {
    return 4 * t * t * t;
  }
  return 1 - Math.pow(-2 * t + 2, 3) / 2;
}

/** 带回弹效果的缓出 (easeOutBack) */
function easeOutBack(t) {
  var c1 = 1.70158;
  var c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
}

/**
 * 解析参数。如果值是 { type: 'sin', amplitude, period } 则按正弦计算动画值，
 * 否则直接返回值本身。
 */
function resolveParam(value, frame, defaultValue) {
  if (value === undefined || value === null) return defaultValue;
  if (typeof value === 'number') return value;
  if (typeof value === 'object' && value.type === 'sin') {
    var amp = value.amplitude !== undefined ? value.amplitude : 0;
    var period = value.period !== undefined ? value.period : 60;
    var offset = value.offset || 0;
    var center = value.center !== undefined ? value.center : defaultValue;
    return center + amp * Math.sin((frame + offset) * 2 * Math.PI / period);
  }
  return defaultValue;
}

/**
 * 在 canvas 上下文中绘制圆角矩形路径。
 * 避免依赖 CanvasRenderingContext2D.roundRect（非标准 API 兼容性差）。
 */
function roundRectPath(ctx, x, y, w, h, r) {
  if (r > w / 2) r = w / 2;
  if (r > h / 2) r = h / 2;
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.arcTo(x + w, y, x + w, y + r, r);
  ctx.lineTo(x + w, y + h - r);
  ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
  ctx.lineTo(x + r, y + h);
  ctx.arcTo(x, y + h, x, y + h - r, r);
  ctx.lineTo(x, y + r);
  ctx.arcTo(x, y, x + r, y, r);
  ctx.closePath();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawCube — 绘制一个带3D旋转效果的立方体。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 锚点X
 * @param {number} params.cy - 锚点Y
 * @param {number|object} [params.size=80] - 边长，或 { type:'sin', amplitude, period }
 * @param {number|object} [params.rotX=0.5] - X轴旋转（弧度），或正弦动画对象
 * @param {number|object} [params.rotY=0.8] - Y轴旋转（弧度），或正弦动画对象
 * @param {string} [params.color='#88bbdd'] - 基准色
 * @param {string} [params.borderColor='#334455'] - 边框色
 * @param {string} [params.label=''] - 正面标签文字
 * @param {string} [params.labelColor='#ffffff'] - 标签颜色
 * @param {number|object} [params.opacity=1] - 整体透明度，或正弦动画对象
 * @param {number} frame - 当前帧号
 */
function drawCube(ctx, params, frame) {
  ctx.save();

  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var color = params.color || '#88bbdd';
  var borderColor = params.borderColor || '#334455';
  var label = params.label || '';
  var labelColor = params.labelColor || '#ffffff';

  var size = resolveParam(params.size, frame, 80);
  var rotX = resolveParam(params.rotX, frame, 0.5);
  var rotY = resolveParam(params.rotY, frame, 0.8);
  var opacity = resolveParam(params.opacity, frame, 1);

  ctx.globalAlpha = clamp(opacity, 0, 1);
  ctx.translate(cx, cy);

  var s = size / 2;

  // 8 个顶点（相对于中心）
  var vertices = [
    [-s, -s, -s], [ s, -s, -s], [ s,  s, -s], [-s,  s, -s],
    [-s, -s,  s], [ s, -s,  s], [ s,  s,  s], [-s,  s,  s]
  ];

  // 旋转矩阵
  var cosX = Math.cos(rotX), sinX = Math.sin(rotX);
  var cosY = Math.cos(rotY), sinY = Math.sin(rotY);

  var rotated = vertices.map(function(v) {
    var x = v[0], y = v[1], z = v[2];
    var x1 = x * cosY + z * sinY;
    var z1 = -x * sinY + z * cosY;
    var y1 = y * cosX - z1 * sinX;
    var z2 = y * sinX + z1 * cosX;
    var perspective = 600 / (600 + z2);
    return { x: x1 * perspective, y: y1 * perspective, z: z2 };
  });

  // 6 个面（顶点索引）
  var faces = [
    { indices: [0, 1, 2, 3], depthAvg: 0, shade: 0.55 },
    { indices: [4, 5, 6, 7], depthAvg: 0, shade: 1.0  },
    { indices: [1, 5, 6, 2], depthAvg: 0, shade: 0.75 },
    { indices: [0, 4, 7, 3], depthAvg: 0, shade: 0.60 },
    { indices: [3, 2, 6, 7], depthAvg: 0, shade: 0.85 },
    { indices: [0, 1, 5, 4], depthAvg: 0, shade: 0.65 }
  ];

  // 计算每个面的平均z深度
  for (var fi = 0; fi < faces.length; fi++) {
    var f = faces[fi];
    var sumZ = 0;
    for (var vi = 0; vi < f.indices.length; vi++) {
      sumZ += rotated[f.indices[vi]].z;
    }
    f.depthAvg = sumZ / f.indices.length;
  }

  // 按深度排序（远到近）
  faces.sort(function(a, b) {
    return a.depthAvg - b.depthAvg;
  });

  // 解析基准色为RGB
  var baseR = parseInt(color.slice(1, 3), 16);
  var baseG = parseInt(color.slice(3, 5), 16);
  var baseB = parseInt(color.slice(5, 7), 16);

  for (fi = 0; fi < faces.length; fi++) {
    f = faces[fi];
    var pts = [];
    for (vi = 0; vi < f.indices.length; vi++) {
      pts.push(rotated[f.indices[vi]]);
    }
    var shade = clamp(f.shade, 0.3, 1.0);

    var rr = Math.round(baseR * shade);
    var gg = Math.round(baseG * shade);
    var bb = Math.round(baseB * shade);
    var fillColor = 'rgb(' + rr + ',' + gg + ',' + bb + ')';

    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (var pi = 1; pi < pts.length; pi++) {
      ctx.lineTo(pts[pi].x, pts[pi].y);
    }
    ctx.closePath();
    ctx.fillStyle = fillColor;
    ctx.fill();
    ctx.strokeStyle = borderColor;
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }

  // 正面标签
  if (label) {
    var frontFace = faces[faces.length - 1];
    var ci = frontFace.indices;
    var cx3d = (rotated[ci[0]].x + rotated[ci[1]].x + rotated[ci[2]].x + rotated[ci[3]].x) / 4;
    var cy3d = (rotated[ci[0]].y + rotated[ci[1]].y + rotated[ci[2]].y + rotated[ci[3]].y) / 4;

    ctx.fillStyle = labelColor;
    ctx.font = 'bold ' + Math.round(size * 0.22) + 'px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, cx3d, cy3d);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawBalance — 绘制一个托盘天平。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 锚点X
 * @param {number} params.cy - 锚点Y
 * @param {number} [params.scale=1] - 整体缩放
 * @param {number} [params.weight=0] - 重量（影响左托盘物体大小，范围0-3）
 * @param {string} [params.label=''] - 标签
 * @param {number} [params.pointerAngle=0] - 指针偏角（弧度），0=垂直
 * @param {boolean} [params.highlight=false] - 标签绿色高亮
 * @param {number} frame - 当前帧号
 */
function drawBalance(ctx, params, frame) {
  ctx.save();
  frame = frame || 0;

  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var scale = params.scale !== undefined ? params.scale : 1;
  var weight = params.weight !== undefined ? params.weight : 0;
  var label = params.label || '';
  var pointerAngle = params.pointerAngle !== undefined ? params.pointerAngle : 0;
  var highlight = params.highlight || false;

  var s = scale;
  ctx.translate(cx, cy);
  ctx.scale(s, s);

  // 底座
  var baseW = 140, baseH = 16;
  ctx.fillStyle = '#8B7355';
  ctx.strokeStyle = '#5C4033';
  ctx.lineWidth = 2;
  roundRectPath(ctx, -baseW / 2, 60, baseW, baseH, 4);
  ctx.fill();
  ctx.stroke();

  // 立柱
  ctx.fillStyle = '#A0896C';
  ctx.strokeStyle = '#5C4033';
  ctx.lineWidth = 1.5;
  roundRectPath(ctx, -6, -50, 12, 112, 3);
  ctx.fill();
  ctx.stroke();

  // 柱顶装饰
  ctx.fillStyle = '#C4A97D';
  ctx.beginPath();
  ctx.arc(0, -52, 8, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = '#5C4033';
  ctx.lineWidth = 1;
  ctx.stroke();

  // 横梁
  var beamLen = 130;
  var beamY = -40;
  var beamAngle = pointerAngle * 0.8;

  ctx.save();
  ctx.translate(0, beamY);
  ctx.rotate(beamAngle);

  ctx.fillStyle = '#C4A97D';
  ctx.strokeStyle = '#8B7355';
  ctx.lineWidth = 2;
  roundRectPath(ctx, -beamLen, -5, beamLen * 2, 10, 3);
  ctx.fill();
  ctx.stroke();

  // 横梁端点装饰
  ctx.fillStyle = '#D4B98D';
  ctx.beginPath();
  ctx.arc(-beamLen, 0, 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(beamLen, 0, 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // 托盘绳
  var panY = 40;
  var ropeLen = panY;

  ctx.strokeStyle = '#666';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(-beamLen, 0);
  ctx.lineTo(-beamLen - 8, ropeLen);
  ctx.moveTo(-beamLen, 0);
  ctx.lineTo(-beamLen + 8, ropeLen);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(beamLen, 0);
  ctx.lineTo(beamLen - 8, ropeLen);
  ctx.moveTo(beamLen, 0);
  ctx.lineTo(beamLen + 8, ropeLen);
  ctx.stroke();

  ctx.restore();

  // 左托盘（含物体）
  var panW = 44, panH = 6;
  var leftPanX = -beamLen;
  var rightPanX = beamLen;

  ctx.save();
  ctx.translate(leftPanX, panY);
  ctx.rotate(beamAngle);

  ctx.fillStyle = '#9E9E9E';
  ctx.strokeStyle = '#666';
  ctx.lineWidth = 1.5;
  roundRectPath(ctx, -panW / 2, -panH, panW, panH, 2);
  ctx.fill();
  ctx.stroke();

  var objSize = 6 + clamp(weight, 0, 3) * 8;
  ctx.fillStyle = '#E57373';
  ctx.strokeStyle = '#C62828';
  ctx.lineWidth = 1;
  var objY = -panH - objSize;
  roundRectPath(ctx, -objSize / 2 + 2, objY, objSize, objSize, 1);
  ctx.fill();
  ctx.stroke();

  ctx.restore();

  // 右托盘
  ctx.save();
  ctx.translate(rightPanX, panY);
  ctx.rotate(beamAngle);

  ctx.fillStyle = '#9E9E9E';
  ctx.strokeStyle = '#666';
  ctx.lineWidth = 1.5;
  roundRectPath(ctx, -panW / 2, -panH, panW, panH, 2);
  ctx.fill();
  ctx.stroke();

  ctx.restore();

  // 指针
  ctx.save();
  ctx.translate(0, -52);
  ctx.rotate(pointerAngle);

  ctx.strokeStyle = '#D32F2F';
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(0, 36);
  ctx.stroke();

  ctx.fillStyle = '#D32F2F';
  ctx.beginPath();
  ctx.arc(0, 36, 3, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();

  // 刻度盘
  ctx.save();
  ctx.translate(0, -14);

  ctx.fillStyle = '#FFF8E1';
  ctx.strokeStyle = '#8B7355';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(0, 0, 20, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.strokeStyle = '#5C4033';
  ctx.lineWidth = 1.5;
  ctx.font = '9px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  for (var i = -3; i <= 3; i++) {
    var a = i * 0.15 - 0.01;
    var inner = 15;
    var outer = (i === 0) ? 19 : 18;
    var x1 = inner * Math.sin(a);
    var y1 = -inner * Math.cos(a);
    var x2 = outer * Math.sin(a);
    var y2 = -outer * Math.cos(a);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();

    if (i !== 0) {
      var tx = (outer + 5) * Math.sin(a);
      var ty = -(outer + 5) * Math.cos(a);
      ctx.fillText(String(i), tx, ty);
    }
  }

  ctx.fillStyle = '#5C4033';
  ctx.font = '8px sans-serif';
  ctx.fillText('0', 0, 0);

  ctx.restore();

  // 标签
  if (label) {
    ctx.fillStyle = highlight ? '#4CAF50' : '#333';
    ctx.font = 'bold 16px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillText(label, 0, -85);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawSpringScale — 绘制一个圆形弹簧秤。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 锚点X
 * @param {number} params.cy - 锚点Y
 * @param {number} [params.scale=1] - 整体缩放
 * @param {number} [params.weight=0] - 重量（0-10，对应指针位置）
 * @param {string} [params.label=''] - 标签文字
 * @param {number} [params.pointerAngle=undefined] - 指针角度（弧度），未设置则由weight计算
 * @param {boolean} [params.highlight=false] - 标签橙色高亮
 * @param {number} frame - 当前帧号
 */
function drawSpringScale(ctx, params, frame) {
  ctx.save();
  frame = frame || 0;

  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var scale = params.scale !== undefined ? params.scale : 1;
  var weight = params.weight !== undefined ? params.weight : 0;
  var label = params.label || '';
  var highlight = params.highlight || false;

  var s = scale;
  ctx.translate(cx, cy);
  ctx.scale(s, s);

  var radius = 70;

  // 表盘外框
  var grad = ctx.createRadialGradient(0, 0, radius - 10, 0, 0, radius + 5);
  grad.addColorStop(0, '#F5F5F5');
  grad.addColorStop(0.7, '#E0E0E0');
  grad.addColorStop(1, '#BDBDBD');
  ctx.fillStyle = grad;
  ctx.strokeStyle = '#757575';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.arc(0, 0, radius, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // 内边框
  ctx.strokeStyle = '#9E9E9E';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(0, 0, radius - 6, 0, Math.PI * 2);
  ctx.stroke();

  // 刻度
  var angleMin = -0.8;
  var angleMax = 0.8;
  var numTicks = 10;

  ctx.strokeStyle = '#424242';
  ctx.lineWidth = 2;
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  for (var i = 0; i <= numTicks; i++) {
    var t = i / numTicks;
    var angle = lerp(angleMin, angleMax, t);
    var innerR = radius - 16;
    var outerR = (i % 2 === 0) ? radius - 8 : radius - 12;

    var ix1 = innerR * Math.sin(angle);
    var iy1 = -innerR * Math.cos(angle);
    var ix2 = outerR * Math.sin(angle);
    var iy2 = -outerR * Math.cos(angle);

    ctx.beginPath();
    ctx.moveTo(ix1, iy1);
    ctx.lineTo(ix2, iy2);
    ctx.stroke();

    if (i % 2 === 0) {
      var tr = radius - 22;
      var tx = tr * Math.sin(angle);
      var ty = -tr * Math.cos(angle);
      ctx.fillStyle = '#333';
      ctx.fillText(String(i), tx, ty);
    }
  }

  // 指针
  var pointerAngle;
  if (params.pointerAngle !== undefined) {
    pointerAngle = params.pointerAngle;
  } else {
    var w = clamp(weight, 0, 10);
    pointerAngle = lerp(angleMin, angleMax, w / 10);
  }

  ctx.save();
  ctx.rotate(pointerAngle);

  ctx.fillStyle = '#757575';
  ctx.beginPath();
  ctx.arc(0, 0, 5, 0, Math.PI * 2);
  ctx.fill();

  ctx.strokeStyle = '#D32F2F';
  ctx.lineWidth = 2.5;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(6, 0);
  ctx.lineTo(radius - 18, 0);
  ctx.stroke();

  ctx.restore();

  // 中心装饰
  ctx.fillStyle = '#D32F2F';
  ctx.beginPath();
  ctx.arc(0, 0, 3, 0, Math.PI * 2);
  ctx.fill();

  // 底部挂钩
  var hookY = radius + 6;
  ctx.strokeStyle = '#757575';
  ctx.lineWidth = 2.5;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(0, hookY);
  ctx.lineTo(0, hookY + 18);
  ctx.stroke();

  ctx.beginPath();
  ctx.arc(0, hookY + 22, 6, 0, Math.PI, false);
  ctx.stroke();

  // 悬挂物体
  var weightSize = 6 + clamp(weight, 0, 10) * 1.5;
  var objY = hookY + 28 + weightSize / 2;

  ctx.strokeStyle = '#999';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, hookY + 24);
  ctx.lineTo(0, objY - weightSize / 2);
  ctx.stroke();

  ctx.fillStyle = '#E57373';
  ctx.strokeStyle = '#C62828';
  ctx.lineWidth = 1.5;
  ctx.fillRect(-weightSize / 2, objY - weightSize / 2, weightSize, weightSize);
  ctx.strokeRect(-weightSize / 2, objY - weightSize / 2, weightSize, weightSize);

  // 标签
  if (label) {
    ctx.fillStyle = highlight ? '#FF9800' : '#333';
    ctx.font = 'bold 16px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(label, 0, -radius - 22);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawTypewriterText — 绘制打字机效果的文字。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 锚点X
 * @param {number} params.cy - 锚点Y
 * @param {string} [params.text=''] - 要显示的完整文本
 * @param {number} [params.startFrame=0] - 开始打字的帧号
 * @param {number} [params.charsPerSecond=10] - 每秒打印字符数
 * @param {string} [params.font='24px sans-serif'] - 字体
 * @param {string} [params.color='#ffffff'] - 文字颜色
 * @param {string} [params.align='center'] - 水平对齐
 * @param {number} frame - 当前帧号
 */
function drawTypewriterText(ctx, params, frame) {
  ctx.save();

  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var text = params.text || '';
  var startFrame = params.startFrame || 0;
  var charsPerSecond = params.charsPerSecond !== undefined ? params.charsPerSecond : 10;
  var font = params.font || '24px sans-serif';
  var color = params.color || '#ffffff';
  var align = params.align || 'center';

  ctx.translate(cx, cy);
  ctx.font = font;
  ctx.fillStyle = color;
  ctx.textAlign = align;
  ctx.textBaseline = 'middle';

  var fps = 60;
  var framesPerChar = fps / Math.max(charsPerSecond, 0.1);
  var elapsed = Math.max(0, frame - startFrame);
  var charCount = Math.min(text.length, Math.floor(elapsed / framesPerChar));

  var displayText = text.slice(0, charCount);

  if (displayText.length > 0) {
    ctx.fillText(displayText, 0, 0);
  }

  // 闪烁光标
  if (charCount < text.length) {
    var cursorVisible = Math.floor(frame / 20) % 2 === 0;
    if (cursorVisible) {
      var metrics = ctx.measureText(displayText);
      var cursorX = 0;
      if (align === 'left') {
        cursorX = metrics.width + 2;
      } else if (align === 'right') {
        cursorX = -metrics.width - 2;
      } else {
        cursorX = metrics.width / 2 + 2;
      }
      ctx.fillStyle = color;
      ctx.globalAlpha = 0.8;
      ctx.font = font;
      ctx.fillText('|', cursorX, 0);
    }
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawPopupLabel — 绘制一个带弹性缩放效果的标签框。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 锚点X
 * @param {number} params.cy - 锚点Y
 * @param {number} [params.width=200] - 框宽度
 * @param {number} [params.height=60] - 框高度
 * @param {string} [params.text=''] - 标签文字
 * @param {string} [params.textColor='#ffffff'] - 文字颜色
 * @param {string} [params.bgColor='#333333'] - 背景色
 * @param {string} [params.borderColor='#666666'] - 边框色
 * @param {number} [params.popStartFrame=0] - 弹出动画起始帧
 * @param {number} [params.popDuration=30] - 弹出动画持续帧数
 * @param {number} frame - 当前帧号
 */
function drawPopupLabel(ctx, params, frame) {
  ctx.save();

  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var width = params.width || 200;
  var height = params.height || 60;
  var text = params.text || '';
  var textColor = params.textColor || '#ffffff';
  var bgColor = params.bgColor || '#333333';
  var borderColor = params.borderColor || '#666666';
  var popStartFrame = params.popStartFrame || 0;
  var popDuration = params.popDuration || 30;

  if (frame < popStartFrame) {
    ctx.restore();
    return;
  }

  ctx.translate(cx, cy);

  var elapsed = frame - popStartFrame;
  var duration = Math.max(popDuration, 1);
  var progress = clamp(elapsed / duration, 0, 1);

  var scaleVal = easeOutBack(clamp(progress, 0, 1));
  ctx.scale(scaleVal, scaleVal);

  var hw = width / 2;
  var hh = height / 2;

  ctx.shadowColor = 'rgba(0,0,0,0.3)';
  ctx.shadowBlur = 8;
  ctx.shadowOffsetY = 3;

  ctx.fillStyle = bgColor;
  roundRectPath(ctx, -hw, -hh, width, height, 10);
  ctx.fill();

  ctx.shadowColor = 'transparent';

  ctx.strokeStyle = borderColor;
  ctx.lineWidth = 2;
  roundRectPath(ctx, -hw, -hh, width, height, 10);
  ctx.stroke();

  if (text) {
    ctx.fillStyle = textColor;
    ctx.font = 'bold 18px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, 0, 0);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawStarField — 绘制星空背景。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {Array} [params.stars=[]] - 星星数组，每个元素 { x, y, r, baseAlpha, twinkleSpeed, twinklePhase }
 * @param {number} [params.rotationSpeed=0.001] - 每帧旋转速度（弧度）
 * @param {number} [params.twinkleIntensity=0.5] - 闪烁强度 0-1
 * @param {number} [params.opacity=1] - 整体透明度
 * @param {number} frame - 当前帧号
 */
function drawStarField(ctx, params, frame) {
  ctx.save();

  var stars = params.stars || [];
  var rotationSpeed = params.rotationSpeed !== undefined ? params.rotationSpeed : 0.001;
  var twinkleIntensity = params.twinkleIntensity !== undefined ? params.twinkleIntensity : 0.5;
  var opacity = params.opacity !== undefined ? params.opacity : 1;

  ctx.globalAlpha = clamp(opacity, 0, 1);

  var canvasW = ctx.canvas ? ctx.canvas.width : 800;
  var canvasH = ctx.canvas ? ctx.canvas.height : 600;
  var centerX = canvasW / 2;
  var centerY = canvasH / 2;

  ctx.translate(centerX, centerY);
  ctx.rotate(frame * rotationSpeed);
  ctx.translate(-centerX, -centerY);

  for (var si = 0; si < stars.length; si++) {
    var star = stars[si];
    var sx = star.x || 0;
    var sy = star.y || 0;
    var sr = star.r || 1;
    var baseAlpha = star.baseAlpha !== undefined ? star.baseAlpha : 0.5;
    var twinkleSpeed = star.twinkleSpeed !== undefined ? star.twinkleSpeed : 0.05;
    var twinklePhase = star.twinklePhase || 0;

    var twinkle = Math.sin(frame * twinkleSpeed + twinklePhase) * twinkleIntensity;
    var alpha = clamp(baseAlpha + twinkle, 0, 1);

    ctx.globalAlpha = alpha * opacity;
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(sx, sy, sr, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawEarthBackground — 绘制地球表面场景背景。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {Array} [params.clouds=[]] - 云朵数组 [{ x, y, w, h, speed }]
 * @param {string} [params.grassColor='#6B8E23'] - 草地颜色
 * @param {Array} [params.skyGradient] - 天空渐变颜色数组 [{ pos, color }]
 * @param {number} frame - 当前帧号
 */
function drawEarthBackground(ctx, params, frame) {
  ctx.save();

  var clouds = params.clouds || [];
  var grassColor = params.grassColor || '#6B8E23';

  var canvasW = ctx.canvas ? ctx.canvas.width : 800;
  var canvasH = ctx.canvas ? ctx.canvas.height : 600;

  // 天空渐变
  var skyColors = params.skyGradient || [
    { pos: 0, color: '#0D47A1' },
    { pos: 0.3, color: '#42A5F5' },
    { pos: 0.55, color: '#81C784' },
    { pos: 0.65, color: '#388E3C' }
  ];

  var skyGrad = ctx.createLinearGradient(0, 0, 0, canvasH * 0.65);
  for (var si = 0; si < skyColors.length; si++) {
    skyGrad.addColorStop(skyColors[si].pos, skyColors[si].color);
  }

  ctx.fillStyle = skyGrad;
  ctx.fillRect(0, 0, canvasW, canvasH * 0.65);

  // 地面
  var groundY = canvasH * 0.6;
  var earthGrad = ctx.createLinearGradient(0, groundY, 0, canvasH);
  earthGrad.addColorStop(0, grassColor);
  earthGrad.addColorStop(1, '#4A6E28');
  ctx.fillStyle = earthGrad;
  ctx.fillRect(0, groundY, canvasW, canvasH - groundY);

  // 草地（竖线模拟，带微风效果）
  var windOffset = frame * 0.5;
  ctx.strokeStyle = '#7CB342';
  ctx.lineWidth = 1.5;
  ctx.globalAlpha = 0.6;

  for (var gi = 0; gi < 120; gi++) {
    var gx = (gi * 12 + Math.sin(gi * 1.3 + windOffset) * 3);
    if (gx > canvasW) gx = gx % canvasW;
    var gy = groundY + 4 + Math.sin(gi * 2.1) * 15;
    var gh = 6 + Math.sin(gi * 0.7 + frame * 0.02) * 4;
    var sway = Math.sin(gi * 0.5 + windOffset * 0.08) * 2;
    ctx.beginPath();
    ctx.moveTo(gx, gy);
    ctx.lineTo(gx + sway, gy - gh);
    ctx.stroke();
  }

  ctx.globalAlpha = 1;

  // 云朵
  for (var ci = 0; ci < clouds.length; ci++) {
    var cloud = clouds[ci];
    var cx2 = ((cloud.x + frame * (cloud.speed || 0.2)) % (canvasW + 200)) - 100;
    var cy2 = cloud.y;
    var cw = cloud.w || 60;
    var ch = cloud.h || 20;

    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
    ctx.beginPath();
    ctx.ellipse(cx2, cy2, cw / 2, ch / 2, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.ellipse(cx2 - cw * 0.25, cy2 - ch * 0.2, cw * 0.3, ch * 0.35, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.ellipse(cx2 + cw * 0.25, cy2 - ch * 0.15, cw * 0.28, ch * 0.32, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.ellipse(cx2 + cw * 0.45, cy2 + ch * 0.05, cw * 0.2, ch * 0.25, 0, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawMoonBackground — 绘制月球表面场景背景。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {Array} [params.craters=[]] - 陨石坑数组 [{ x, y, rx, ry, depth }]
 * @param {object} [params.earthPosition] - 地球位置 { x, y }
 * @param {number} [params.starOpacity=0.8] - 星星透明度
 * @param {number} frame - 当前帧号
 */
function drawMoonBackground(ctx, params, frame) {
  ctx.save();
  frame = frame || 0;

  var craters = params.craters || [];
  var earthPosition = params.earthPosition;
  var starOpacity = params.starOpacity !== undefined ? params.starOpacity : 0.8;

  var canvasW = ctx.canvas ? ctx.canvas.width : 800;
  var canvasH = ctx.canvas ? ctx.canvas.height : 600;

  // 深空背景（径向渐变）
  var bgGrad = ctx.createRadialGradient(canvasW / 2, canvasH / 2, 0, canvasW / 2, canvasH / 2, canvasW * 0.8);
  bgGrad.addColorStop(0, '#1A1A2E');
  bgGrad.addColorStop(0.5, '#0F0F1A');
  bgGrad.addColorStop(1, '#05050A');
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, canvasW, canvasH);

  // 星星
  ctx.fillStyle = '#ffffff';
  var starSeed = [3, 7, 13, 21, 29, 37, 43, 53, 59, 67, 73, 79, 83, 97, 101, 107, 113, 127, 131, 137];
  for (var si = 0; si < 80; si++) {
    var sx = (si * 137.5 + starSeed[si % starSeed.length]) % canvasW;
    var sy = (si * 97.3 + starSeed[(si + 3) % starSeed.length]) % canvasH;
    var sr = 0.5 + (si % 3) * 0.4;
    ctx.globalAlpha = starOpacity * (0.3 + (si % 5) * 0.15);
    ctx.beginPath();
    ctx.arc(sx, sy, sr, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;

  // 月面
  var moonCY = canvasH * 0.82;
  var moonRX = canvasW * 0.55;
  var moonRY = canvasH * 0.35;

  var moonGrad = ctx.createRadialGradient(canvasW / 2, moonCY - moonRY * 0.3, 0, canvasW / 2, moonCY, moonRX);
  moonGrad.addColorStop(0, '#E8E0D4');
  moonGrad.addColorStop(0.4, '#C8BFB0');
  moonGrad.addColorStop(0.7, '#A89F8E');
  moonGrad.addColorStop(1, '#7A7265');
  ctx.fillStyle = moonGrad;
  ctx.beginPath();
  ctx.ellipse(canvasW / 2, moonCY, moonRX, moonRY, 0, 0, Math.PI * 2);
  ctx.fill();

  // 陨石坑
  for (var cri = 0; cri < craters.length; cri++) {
    var crater = craters[cri];
    var cx2 = crater.x || 0;
    var cy2 = crater.y || 0;
    var rx = crater.rx || 10;
    var ry = crater.ry || 6;
    var depth = crater.depth !== undefined ? crater.depth : 0.3;

    ctx.fillStyle = 'rgba(60, 55, 45, ' + (0.2 + depth * 0.4) + ')';
    ctx.beginPath();
    ctx.ellipse(cx2, cy2, rx, ry * 0.8, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = 'rgba(220, 210, 190, ' + (0.15 + depth * 0.25) + ')';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.ellipse(cx2 - 1, cy2 - 1, rx * 0.85, ry * 0.7, 0, 0, Math.PI * 2);
    ctx.stroke();
  }

  // 远处的蓝色地球
  if (earthPosition) {
    var ex = earthPosition.x !== undefined ? earthPosition.x : canvasW * 0.2;
    var ey = earthPosition.y !== undefined ? earthPosition.y : canvasH * 0.12;
    var earthR = 20;

    var glowGrad = ctx.createRadialGradient(ex, ey, earthR * 0.5, ex, ey, earthR * 2.5);
    glowGrad.addColorStop(0, 'rgba(100, 180, 255, 0.15)');
    glowGrad.addColorStop(1, 'rgba(100, 180, 255, 0)');
    ctx.fillStyle = glowGrad;
    ctx.beginPath();
    ctx.arc(ex, ey, earthR * 2.5, 0, Math.PI * 2);
    ctx.fill();

    var earthGrad = ctx.createRadialGradient(ex - earthR * 0.3, ey - earthR * 0.3, 1, ex, ey, earthR);
    earthGrad.addColorStop(0, '#4FC3F7');
    earthGrad.addColorStop(0.6, '#1E88E5');
    earthGrad.addColorStop(1, '#0D47A1');
    ctx.fillStyle = earthGrad;
    ctx.beginPath();
    ctx.arc(ex, ey, earthR, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = 'rgba(76, 175, 80, 0.5)';
    ctx.beginPath();
    ctx.ellipse(ex - earthR * 0.25, ey + earthR * 0.1, earthR * 0.22, earthR * 0.18, 0.2, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.ellipse(ex + earthR * 0.2, ey - earthR * 0.15, earthR * 0.15, earthR * 0.2, -0.1, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.ellipse(ex + earthR * 0.05, ey + earthR * 0.3, earthR * 0.12, earthR * 0.1, 0.3, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = 'rgba(255,255,255,0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(ex - earthR * 0.2, ey - earthR * 0.25, earthR * 0.8, -Math.PI * 0.8, Math.PI * 0.1);
    ctx.stroke();
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawSplitScreenDivider — 绘制分屏对比的中分线。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.splitX - 分割线X位置（画布绝对坐标）
 * @param {string} [params.color='#ffffff'] - 分割线颜色
 * @param {string} [params.glowColor='rgba(255,255,255,0.3)'] - 光晕颜色
 * @param {number} [params.glowWidth=60] - 光晕宽度
 * @param {number} frame - 当前帧号
 */
function drawSplitScreenDivider(ctx, params, frame) {
  ctx.save();
  frame = frame || 0;

  var splitX = params.splitX || 400;
  var color = params.color || '#ffffff';
  var glowColor = params.glowColor || 'rgba(255,255,255,0.3)';
  var glowWidth = params.glowWidth || 60;

  var canvasH = ctx.canvas ? ctx.canvas.height : 600;

  // 左侧光晕
  var leftGrad = ctx.createLinearGradient(splitX - glowWidth, 0, splitX, 0);
  leftGrad.addColorStop(0, 'transparent');
  leftGrad.addColorStop(1, glowColor);
  ctx.fillStyle = leftGrad;
  ctx.fillRect(splitX - glowWidth, 0, glowWidth, canvasH);

  // 右侧光晕
  var rightGrad = ctx.createLinearGradient(splitX, 0, splitX + glowWidth, 0);
  rightGrad.addColorStop(0, glowColor);
  rightGrad.addColorStop(1, 'transparent');
  ctx.fillStyle = rightGrad;
  ctx.fillRect(splitX, 0, glowWidth, canvasH);

  // 中心虚线
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  var dashLen = 6;
  var gapLen = 4;
  ctx.beginPath();
  for (var y = 0; y < canvasH; y += dashLen + gapLen) {
    ctx.moveTo(splitX, y);
    ctx.lineTo(splitX, Math.min(y + dashLen, canvasH));
  }
  ctx.stroke();

  // 中心发光点
  ctx.shadowColor = color;
  ctx.shadowBlur = 8;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(splitX, canvasH / 2, 3, 0, Math.PI * 2);
  ctx.fill();
  ctx.shadowBlur = 0;

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawMeteor — 绘制一颗流星。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.fromX - 起点X（画布绝对坐标）
 * @param {number} params.fromY - 起点Y（画布绝对坐标）
 * @param {number} params.toX - 终点X（画布绝对坐标）
 * @param {number} params.toY - 终点Y（画布绝对坐标）
 * @param {number} [params.startFrame=0] - 流星开始帧
 * @param {number} [params.duration=30] - 飞行持续帧数
 * @param {number} frame - 当前帧号
 */
function drawMeteor(ctx, params, frame) {
  ctx.save();

  var fromX = params.fromX || 0;
  var fromY = params.fromY || 0;
  var toX = params.toX || 100;
  var toY = params.toY || 100;
  var startFrame = params.startFrame || 0;
  var duration = params.duration || 30;

  var elapsed = frame - startFrame;

  if (elapsed < 0 || elapsed > duration) {
    ctx.restore();
    return;
  }

  var progress = clamp(elapsed / duration, 0, 1);
  var easeProgress = easeInOut(progress);

  var curX = lerp(fromX, toX, easeProgress);
  var curY = lerp(fromY, toY, easeProgress);

  var dx = toX - fromX;
  var dy = toY - fromY;
  var angle = Math.atan2(dy, dx);

  ctx.translate(curX, curY);
  ctx.rotate(angle);

  // 拖尾（多点渐隐）
  var trailLength = 12;
  for (var ti = 0; ti < trailLength; ti++) {
    var tt = ti / trailLength;
    var alpha = (1 - tt) * 0.6;
    var radius = 1.5 + (1 - tt) * 2.5;
    var dist = -tt * 50;

    ctx.globalAlpha = alpha;
    ctx.fillStyle = (ti < 3) ? '#FFFFFF' : '#FFD54F';
    ctx.beginPath();
    ctx.arc(dist, 0, radius, 0, Math.PI * 2);
    ctx.fill();
  }

  // 流星头
  ctx.globalAlpha = 1;
  ctx.shadowColor = '#FFD54F';
  ctx.shadowBlur = 20;
  ctx.fillStyle = '#FFFFFF';
  ctx.beginPath();
  ctx.arc(0, 0, 3, 0, Math.PI * 2);
  ctx.fill();

  ctx.shadowBlur = 0;
  ctx.fillStyle = '#FFF9C4';
  ctx.beginPath();
  ctx.arc(0, 0, 1.5, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * sceneLabel — 绘制场景标识文字（带半透明背景条）。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 锚点X
 * @param {number} params.cy - 锚点Y
 * @param {string} [params.text=''] - 标识文字
 * @param {string} [params.color='#ffffff'] - 文字颜色
 * @param {string} [params.bgColor='rgba(0,0,0,0.5)'] - 背景色
 * @param {number} [params.padding=8] - 内边距
 * @param {number} [params.fontSize=16] - 字号
 * @param {number} frame - 当前帧号
 */
function sceneLabel(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var text = params.text || '';
  var color = params.color || '#ffffff';
  var bgColor = params.bgColor || 'rgba(0,0,0,0.5)';
  var padding = params.padding !== undefined ? params.padding : 8;
  var fontSize = params.fontSize || 16;

  ctx.font = fontSize + 'px sans-serif';
  var metrics = ctx.measureText(text);
  var tw = metrics.width;
  var th = fontSize * 1.4;

  ctx.fillStyle = bgColor;
  roundRectPath(ctx, cx - tw/2 - padding, cy - th/2, tw + padding*2, th, 4);
  ctx.fill();

  ctx.fillStyle = color;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, cx, cy + 1);
  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * floatUpText — 绘制从底部上浮的文字。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 锚点X
 * @param {number} params.cy - 锚点Y（上浮起始位置）
 * @param {number} [params.targetY] - 上浮目标Y（默认 cy - 30）
 * @param {string} [params.text=''] - 文字
 * @param {string} [params.color='#ffffff'] - 文字颜色
 * @param {string} [params.font='20px sans-serif'] - 字体
 * @param {number} [params.startFrame=0] - 起始帧
 * @param {number} [params.floatDuration=30] - 上浮持续帧数
 * @param {number} [params.stayDuration=60] - 停留持续帧数
 * @param {number} frame - 当前帧号
 */
function floatUpText(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var targetY = params.targetY !== undefined ? params.targetY : cy - 30;
  var text = params.text || '';
  var color = params.color || '#ffffff';
  var font = params.font || '20px sans-serif';
  var startFrame = params.startFrame || 0;
  var floatDuration = params.floatDuration || 30;
  var stayDuration = params.stayDuration || 60;
  var align = params.align || 'center';

  var elapsed = frame - startFrame;
  if (elapsed < 0) { ctx.restore(); return; }

  ctx.font = font;
  ctx.fillStyle = color;
  ctx.textAlign = align;
  ctx.textBaseline = 'middle';

  if (elapsed < floatDuration) {
    var progress = clamp(elapsed / floatDuration, 0, 1);
    var eased = easeOut(progress);
    var curY = cy + (targetY - cy) * eased;
    ctx.globalAlpha = progress;
    ctx.fillText(text, cx, curY);
  } else if (elapsed < floatDuration + stayDuration) {
    ctx.globalAlpha = 1;
    ctx.fillText(text, cx, targetY);
  } else {
    ctx.globalAlpha = 0;
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * flashLabel — 绘制闪烁标注文字。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 锚点X
 * @param {number} params.cy - 锚点Y
 * @param {string} [params.text=''] - 文字
 * @param {string} [params.color='#FF9800'] - 文字颜色
 * @param {string} [params.font='bold 20px sans-serif'] - 字体
 * @param {number} [params.startFrame=0] - 起始帧
 * @param {number} [params.flashSpeed=0.1] - 闪烁速度
 * @param {number} frame - 当前帧号
 */
function flashLabel(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var text = params.text || '';
  var color = params.color || '#FF9800';
  var font = params.font || 'bold 20px sans-serif';
  var startFrame = params.startFrame || 0;
  var flashSpeed = params.flashSpeed || 0.1;

  var elapsed = frame - startFrame;
  if (elapsed < 0) { ctx.restore(); return; }

  var alpha = 0.4 + 0.6 * (0.5 + 0.5 * Math.sin(elapsed * flashSpeed * 2 * Math.PI));

  ctx.font = font;
  ctx.fillStyle = color;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.globalAlpha = alpha;
  ctx.fillText(text, cx, cy);

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * distantEarth — 绘制远处的地球图标（简笔风格）。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 锚点X
 * @param {number} params.cy - 锚点Y
 * @param {number} [params.radius=20] - 地球半径
 * @param {number} [params.opacity=0.8] - 透明度
 * @param {number} frame - 当前帧号
 */
function distantEarth(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var radius = params.radius || 20;
  var opacity = params.opacity !== undefined ? params.opacity : 0.8;

  ctx.globalAlpha = clamp(opacity, 0, 1);

  // 发光光晕
  var glowGrad = ctx.createRadialGradient(cx, cy, radius * 0.3, cx, cy, radius * 2.5);
  glowGrad.addColorStop(0, 'rgba(100, 180, 255, 0.12)');
  glowGrad.addColorStop(1, 'rgba(100, 180, 255, 0)');
  ctx.fillStyle = glowGrad;
  ctx.beginPath();
  ctx.arc(cx, cy, radius * 2.5, 0, Math.PI * 2);
  ctx.fill();

  // 地球本体（径向渐变）
  var earthGrad = ctx.createRadialGradient(cx - radius * 0.3, cy - radius * 0.3, 1, cx, cy, radius);
  earthGrad.addColorStop(0, '#4FC3F7');
  earthGrad.addColorStop(0.6, '#1E88E5');
  earthGrad.addColorStop(1, '#0D47A1');
  ctx.fillStyle = earthGrad;
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fill();

  // 大陆块（简化绿色斑块）
  ctx.fillStyle = 'rgba(76, 175, 80, 0.5)';
  ctx.beginPath();
  ctx.ellipse(cx - radius * 0.25, cy + radius * 0.1, radius * 0.22, radius * 0.18, 0.2, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.ellipse(cx + radius * 0.2, cy - radius * 0.15, radius * 0.15, radius * 0.2, -0.1, 0, Math.PI * 2);
  ctx.fill();

  // 高光
  ctx.strokeStyle = 'rgba(255,255,255,0.25)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(cx - radius * 0.2, cy - radius * 0.25, radius * 0.7, -Math.PI * 0.8, Math.PI * 0.1);
  ctx.stroke();

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * staticLabel — 绘制静态标签框（无弹出动画）。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 锚点X
 * @param {number} params.cy - 锚点Y
 * @param {number} [params.width=180] - 框宽度
 * @param {number} [params.height=44] - 框高度
 * @param {string} [params.text=''] - 标签文字
 * @param {string} [params.textColor='#ffffff'] - 文字颜色
 * @param {string} [params.bgColor='rgba(51,51,51,0.85)'] - 背景色
 * @param {string} [params.borderColor='#666'] - 边框色
 * @param {number} [params.borderRadius=8] - 圆角
 * @param {number} [params.opacity=1] - 透明度
 * @param {number} frame - 当前帧号
 */
function staticLabel(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var width = params.width || 180;
  var height = params.height || 44;
  var text = params.text || '';
  var textColor = params.textColor || '#ffffff';
  var bgColor = params.bgColor || 'rgba(51,51,51,0.85)';
  var borderColor = params.borderColor || '#666';
  var borderRadius = params.borderRadius || 8;
  var opacity = params.opacity !== undefined ? params.opacity : 1;

  ctx.globalAlpha = clamp(opacity, 0, 1);

  // 阴影
  ctx.shadowColor = 'rgba(0,0,0,0.25)';
  ctx.shadowBlur = 6;
  ctx.shadowOffsetY = 2;

  ctx.fillStyle = bgColor;
  roundRectPath(ctx, cx - width/2, cy - height/2, width, height, borderRadius);
  ctx.fill();

  ctx.shadowColor = 'transparent';
  ctx.shadowBlur = 0;

  ctx.strokeStyle = borderColor;
  ctx.lineWidth = 1.5;
  roundRectPath(ctx, cx - width/2, cy - height/2, width, height, borderRadius);
  ctx.stroke();

  if (text) {
    ctx.fillStyle = textColor;
    ctx.font = '15px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, cx, cy + 1);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawForceArrow — 绘制受力箭头。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 起点X
 * @param {number} params.cy - 起点Y
 * @param {number} params.angle - 方向角度（度），0=向右，-90=向上
 * @param {number} [params.length=60] - 箭头长度
 * @param {string} [params.color='#ef4444'] - 颜色
 * @param {string} [params.label=''] - 标签文字
 * @param {number} [params.lineWidth=3] - 线宽
 * @param {number} [params.opacity=1] - 透明度，支持动画
 * @param {number} frame
 */
function drawForceArrow(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var angle = (params.angle || 0) * Math.PI / 180;
  var length = params.length !== undefined ? params.length : 60;
  var color = params.color || '#ef4444';
  var label = params.label || '';
  var lineWidth = params.lineWidth !== undefined ? params.lineWidth : 3;
  var opacity = resolveParam(params.opacity, frame, 1);

  ctx.globalAlpha = clamp(opacity, 0, 1);
  ctx.translate(cx, cy);
  ctx.rotate(angle);

  // 箭杆
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(length, 0);
  ctx.stroke();

  // 箭头（三角形）
  var headLen = 12 + lineWidth * 2;
  var headWid = 6 + lineWidth;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(length, 0);
  ctx.lineTo(length - headLen, -headWid);
  ctx.lineTo(length - headLen, headWid);
  ctx.closePath();
  ctx.fill();

  // 标签
  if (label) {
    ctx.fillStyle = color;
    ctx.font = 'bold 16px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillText(label, length / 2, -8);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawFormulaBoard — 绘制公式板。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 锚点X
 * @param {number} params.cy - 锚点Y
 * @param {string} params.formula - 公式文本
 * @param {Array} [params.variables] - 变量说明 [{ symbol, name, color }]
 * @param {string} [params.bgColor='rgba(0,0,0,0.5)'] - 背景色
 * @param {number} [params.opacity=1] - 透明度，支持动画
 * @param {number} frame
 */
function drawFormulaBoard(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var formula = params.formula || '';
  var variables = params.variables || [];
  var bgColor = params.bgColor || 'rgba(0,0,0,0.5)';
  var opacity = resolveParam(params.opacity, frame, 1);

  ctx.globalAlpha = clamp(opacity, 0, 1);

  // 公式大字
  ctx.font = 'bold 36px serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  var formulaWidth = ctx.measureText(formula).width;

  // 背景框
  var boxW = Math.max(formulaWidth + 60, 200);
  var boxH = 60 + (variables.length > 0 ? variables.length * 24 + 16 : 0);
  var boxX = cx - boxW / 2;
  var boxY = cy - boxH / 2;

  ctx.fillStyle = bgColor;
  roundRectPath(ctx, boxX, boxY, boxW, boxH, 12);
  ctx.fill();

  ctx.strokeStyle = 'rgba(255,215,0,0.4)';
  ctx.lineWidth = 1.5;
  roundRectPath(ctx, boxX, boxY, boxW, boxH, 12);
  ctx.stroke();

  // 公式
  ctx.fillStyle = '#fbbf24';
  ctx.font = 'bold 36px serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(formula, cx, boxY + 32);

  // 变量说明
  if (variables.length > 0) {
    ctx.font = '15px sans-serif';
    ctx.textAlign = 'left';
    for (var vi = 0; vi < variables.length; vi++) {
      var v = variables[vi];
      var vy = boxY + 60 + vi * 24;
      ctx.fillStyle = v.color || '#ffffff';
      ctx.fillText(v.symbol + ' = ' + (v.name || ''), boxX + 20, vy);
    }
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawOptionCard — 绘制选项卡片。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 锚点X
 * @param {number} params.cy - 锚点Y
 * @param {string} params.label - 选项标签 A/B/C/D
 * @param {string} params.text - 选项文本
 * @param {boolean} [params.correct=false] - 是否正确
 * @param {boolean} [params.showReason=false] - 是否显示解析
 * @param {string} [params.reason=''] - 解析文本
 * @param {number} [params.opacity=1] - 透明度，支持动画
 * @param {number} frame
 */
function drawOptionCard(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var label = params.label || '?';
  var text = params.text || '';
  var correct = params.correct || false;
  var showReason = params.showReason || false;
  var reason = params.reason || '';
  var opacity = resolveParam(params.opacity, frame, 1);

  ctx.globalAlpha = clamp(opacity, 0, 1);

  var isCorrect = !!correct;
  var borderColor = isCorrect ? '#22c55e' : '#475569';
  var bgColor = isCorrect ? 'rgba(34,197,94,0.1)' : 'rgba(30,41,59,0.8)';
  var markColor = isCorrect ? '#22c55e' : '#ef4444';
  var mark = isCorrect ? '✓' : '✗';

  // 背景卡片
  ctx.fillStyle = bgColor;
  roundRectPath(ctx, cx - 280, cy - 20, 560, 40, 8);
  ctx.fill();
  ctx.strokeStyle = borderColor;
  ctx.lineWidth = 1.5;
  roundRectPath(ctx, cx - 280, cy - 20, 560, 40, 8);
  ctx.stroke();

  // 标签圆圈
  ctx.fillStyle = isCorrect ? '#22c55e' : '#334155';
  ctx.beginPath();
  ctx.arc(cx - 250, cy, 14, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 13px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(label, cx - 250, cy);

  // 对错标记
  ctx.fillStyle = markColor;
  ctx.font = 'bold 16px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(mark, cx - 216, cy);

  // 选项文本
  ctx.fillStyle = isCorrect ? '#86efac' : '#cbd5e1';
  ctx.font = '15px sans-serif';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, cx - 200, cy);

  // 解析文字
  if (showReason && reason) {
    ctx.fillStyle = '#94a3b8';
    ctx.font = '13px sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText(reason, cx - 200, cy + 22);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawTextBlock — 绘制文字区块。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 锚点X
 * @param {number} params.cy - 锚点Y
 * @param {string} params.text - 文字内容
 * @param {string} [params.font='20px sans-serif'] - 字体
 * @param {string} [params.color='#ffffff'] - 颜色
 * @param {string} [params.align='center'] - 对齐方式
 * @param {number} [params.opacity=1] - 透明度，支持动画
 * @param {number} frame
 */
function drawTextBlock(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var text = params.text || '';
  var font = params.font || '20px sans-serif';
  var color = params.color || '#ffffff';
  var align = params.align || 'center';
  var opacity = resolveParam(params.opacity, frame, 1);

  ctx.globalAlpha = clamp(opacity, 0, 1);
  ctx.font = font;
  ctx.fillStyle = color;
  ctx.textAlign = align;
  ctx.textBaseline = 'middle';

  // 换行支持
  var lines = text.split('\n');
  var lineH = parseInt(font) * 1.4 || 28;
  var startY = cy - (lines.length - 1) * lineH / 2;
  for (var li = 0; li < lines.length; li++) {
    ctx.fillText(lines[li], cx, startY + li * lineH);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */



/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawPendulum — 绘制单摆。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 悬挂点X
 * @param {number} params.cy - 悬挂点Y
 * @param {number} [params.length=120] - 摆长
 * @param {number} [params.angle=0] - 摆角（弧度），支持sin动画
 * @param {number} [params.bobSize=16] - 摆球大小
 * @param {string} [params.bobColor='#fbbf24'] - 摆球颜色
 * @param {string} [params.stringColor='#94a3b8'] - 摆线颜色
 * @param {string} [params.label=''] - 标签
 * @param {number} [params.opacity=1] - 透明度
 * @param {number} frame
 */
function drawPendulum(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var length = params.length !== undefined ? params.length : 120;
  var angle = resolveParam(params.angle, frame, 0);
  var bobSize = params.bobSize !== undefined ? params.bobSize : 16;
  var bobColor = params.bobColor || '#fbbf24';
  var stringColor = params.stringColor || '#94a3b8';
  var label = params.label || '';
  var opacity = resolveParam(params.opacity, frame, 1);

  ctx.globalAlpha = clamp(opacity, 0, 1);
  ctx.translate(cx, cy);

  // 悬挂点
  ctx.fillStyle = '#94a3b8';
  ctx.beginPath();
  ctx.arc(0, 0, 4, 0, Math.PI * 2);
  ctx.fill();

  // 摆线
  var bobX = Math.sin(angle) * length;
  var bobY = Math.cos(angle) * length;
  ctx.strokeStyle = stringColor;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(bobX, bobY);
  ctx.stroke();

  // 摆球
  ctx.fillStyle = bobColor;
  ctx.strokeStyle = 'rgba(0,0,0,0.2)';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(bobX, bobY, bobSize, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // 高光
  ctx.fillStyle = 'rgba(255,255,255,0.3)';
  ctx.beginPath();
  ctx.arc(bobX - bobSize * 0.25, bobY - bobSize * 0.25, bobSize * 0.35, 0, Math.PI * 2);
  ctx.fill();

  if (label) {
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(label, bobX, bobY + bobSize + 6);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawSpringOscillator — 绘制弹簧振子。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 弹簧顶端X
 * @param {number} params.cy - 弹簧顶端Y
 * @param {number} [params.mass=20] - 振子大小
 * @param {string} [params.massColor='#60a5fa'] - 振子颜色
 * @param {string} [params.springColor='#94a3b8'] - 弹簧颜色
 * @param {number} [params.displacement=0] - 位移（像素），支持sin动画
 * @param {number} [params.restLength=80] - 弹簧原长
 * @param {number} [params.coils=8] - 弹簧圈数
 * @param {string} [params.label=''] - 标签
 * @param {number} [params.opacity=1] - 透明度
 * @param {number} frame
 */
function drawSpringOscillator(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var mass = params.mass !== undefined ? params.mass : 20;
  var massColor = params.massColor || '#60a5fa';
  var springColor = params.springColor || '#94a3b8';
  var displacement = resolveParam(params.displacement, frame, 0);
  var restLength = params.restLength !== undefined ? params.restLength : 80;
  var coils = params.coils !== undefined ? params.coils : 8;
  var label = params.label || '';
  var opacity = resolveParam(params.opacity, frame, 1);

  ctx.globalAlpha = clamp(opacity, 0, 1);
  ctx.translate(cx, cy);

  var totalLen = restLength + displacement;
  var massTop = totalLen;
  var massBottom = totalLen + mass;

  // 悬挂架
  ctx.fillStyle = '#94a3b8';
  ctx.fillRect(-6, -2, 12, 4);
  ctx.fillRect(-2, -6, 4, 12);

  // 弹簧（之字形折线）
  ctx.strokeStyle = springColor;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, 0);
  var segs = coils * 2;
  var segH = restLength / segs;
  for (var ci = 0; ci <= segs; ci++) {
    var sx = (ci % 2 === 0) ? 0 : ((ci % 4 === 1) ? 10 : -10);
    ctx.lineTo(sx, segH * ci);
  }
  ctx.stroke();

  // 振子
  var my = massTop;
  ctx.fillStyle = massColor;
  ctx.strokeStyle = 'rgba(0,0,0,0.2)';
  ctx.lineWidth = 1.5;
  ctx.fillRect(-mass/2, my, mass, mass);
  ctx.strokeRect(-mass/2, my, mass, mass);

  if (label) {
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(label, 0, massBottom + 6);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawInclinedPlane — 绘制斜面与物体。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 斜面底部X
 * @param {number} params.cy - 斜面底部Y
 * @param {number} [params.angle=30] - 斜面角度（度）
 * @param {number} [params.length=200] - 斜面长度
 * @param {number} [params.objectSize=24] - 物体大小
 * @param {string} [params.objectColor='#60a5fa'] - 物体颜色
 * @param {number} [params.objectPosition=0.5] - 物体在斜面上的位置 0-1
 * @param {string} [params.label=''] - 物体标签
 * @param {boolean} [params.showForces=false] - 显示受力
 * @param {number} [params.opacity=1]
 * @param {number} frame
 */
function drawInclinedPlane(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var angle = (params.angle || 30) * Math.PI / 180;
  var length = params.length !== undefined ? params.length : 200;
  var objSize = params.objectSize !== undefined ? params.objectSize : 24;
  var objectColor = params.objectColor || '#60a5fa';
  var objPos = params.objectPosition !== undefined ? params.objectPosition : 0.5;
  var label = params.label || '';
  var showForces = params.showForces || false;
  var opacity = resolveParam(params.opacity, frame, 1);

  ctx.globalAlpha = clamp(opacity, 0, 1);
  ctx.translate(cx, cy);

  var topX = -Math.cos(angle) * length;
  var topY = -Math.sin(angle) * length;

  // 斜面
  ctx.fillStyle = '#334155';
  ctx.strokeStyle = '#64748b';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(topX, topY);
  ctx.lineTo(topX, 0);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // 物体
  var objDist = objPos * length;
  var objX = -Math.cos(angle) * objDist;
  var objY = -Math.sin(angle) * objDist;
  var halfSize = objSize / 2;

  ctx.save();
  ctx.translate(objX, objY);
  ctx.rotate(-angle);
  ctx.fillStyle = objectColor;
  ctx.strokeStyle = 'rgba(0,0,0,0.2)';
  ctx.lineWidth = 1.5;
  ctx.fillRect(-halfSize, -halfSize, objSize, objSize);
  ctx.strokeRect(-halfSize, -halfSize, objSize, objSize);
  if (label) {
    ctx.fillStyle = '#e2e8f0';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillText(label, 0, -halfSize - 4);
  }
  ctx.restore();

  // 受力箭头
  if (showForces) {
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(objX, objY);
    ctx.lineTo(objX, objY + 50);
    ctx.stroke();
    ctx.fillStyle = '#ef4444';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('G', objX, objY + 56);

    ctx.strokeStyle = '#22c55e';
    ctx.lineWidth = 2;
    var nAngle = -angle + Math.PI / 2;
    ctx.beginPath();
    ctx.moveTo(objX, objY);
    ctx.lineTo(objX + Math.cos(nAngle) * 35, objY + Math.sin(nAngle) * 35);
    ctx.stroke();
    ctx.fillStyle = '#22c55e';
    ctx.fillText('N', objX + Math.cos(nAngle) * 40, objY + Math.sin(nAngle) * 40);
  }

  ctx.fillStyle = '#94a3b8';
  ctx.font = '12px sans-serif';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'top';
  ctx.fillText('θ=' + (params.angle || 30) + '°', 4, 4);

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawCircuitComponent — 电路元件（电池、电阻、灯泡、开关、电表）。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 中心X
 * @param {number} params.cy - 中心Y
 * @param {string} params.type - battery|resistor|bulb|switch|ammeter|voltmeter|wire
 * @param {string} [params.orientation='horizontal'] - horizontal|vertical
 * @param {string} [params.state='closed'] - 开关状态: open|closed
 * @param {boolean} [params.lit=false] - 灯泡发光
 * @param {string} [params.label=''] - 标签
 * @param {number} [params.scale=1] - 缩放
 * @param {number} [params.opacity=1]
 * @param {number} frame
 */
function drawCircuitComponent(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var type = params.type || 'resistor';
  var orientation = params.orientation || 'horizontal';
  var state = params.state || 'closed';
  var lit = params.lit || false;
  var label = params.label || '';
  var scale = params.scale !== undefined ? params.scale : 1;
  var opacity = resolveParam(params.opacity, frame, 1);

  ctx.globalAlpha = clamp(opacity, 0, 1);
  ctx.translate(cx, cy);
  ctx.scale(scale, scale);

  var isH = orientation === 'horizontal';

  if (type === 'wire') {
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(isH ? -30 : 0, isH ? 0 : -30);
    ctx.lineTo(isH ? 30 : 0, isH ? 0 : 30);
    ctx.stroke();
  }
  else if (type === 'battery') {
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    if (isH) {
      ctx.moveTo(-25, 0); ctx.lineTo(-3, 0);
      ctx.moveTo(3, 0); ctx.lineTo(25, 0);
      ctx.moveTo(0, -12); ctx.lineTo(0, 12);
      ctx.fillStyle = '#ef4444'; ctx.font = 'bold 13px sans-serif';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText('+', -32, 0);
    } else {
      ctx.moveTo(0, -25); ctx.lineTo(0, -3);
      ctx.moveTo(0, 3); ctx.lineTo(0, 25);
      ctx.moveTo(-12, 0); ctx.lineTo(12, 0);
      ctx.fillStyle = '#ef4444'; ctx.font = 'bold 13px sans-serif';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText('+', 0, -32);
    }
    ctx.stroke();
  }
  else if (type === 'resistor') {
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 2;
    // 矩形电阻
    ctx.strokeRect(isH ? -15 : -8, isH ? -8 : -15, isH ? 30 : 16, isH ? 16 : 30);
    ctx.beginPath();
    if (isH) {
      ctx.moveTo(-28, 0); ctx.lineTo(-15, 0);
      ctx.moveTo(15, 0); ctx.lineTo(28, 0);
    } else {
      ctx.moveTo(0, -28); ctx.lineTo(0, -15);
      ctx.moveTo(0, 15); ctx.lineTo(0, 28);
    }
    ctx.stroke();
  }
  else if (type === 'bulb') {
    ctx.strokeStyle = lit ? '#fbbf24' : '#64748b';
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(0, 0, 14, 0, Math.PI * 2); ctx.stroke();
    if (lit) {
      ctx.fillStyle = 'rgba(251,191,36,0.15)';
      ctx.beginPath(); ctx.arc(0, 0, 18, 0, Math.PI * 2); ctx.fill();
    }
    ctx.beginPath();
    ctx.moveTo(-8, -8); ctx.lineTo(8, 8);
    ctx.moveTo(8, -8); ctx.lineTo(-8, 8);
    ctx.stroke();
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    if (isH) { ctx.moveTo(-28, 0); ctx.lineTo(-14, 0); ctx.moveTo(14, 0); ctx.lineTo(28, 0); }
    else { ctx.moveTo(0, -28); ctx.lineTo(0, -14); ctx.moveTo(0, 14); ctx.lineTo(0, 28); }
    ctx.stroke();
  }
  else if (type === 'switch') {
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 2;
    if (isH) {
      ctx.beginPath(); ctx.moveTo(-25, 0); ctx.lineTo(-10, 0);
      if (state === 'closed') ctx.lineTo(25, 0);
      else ctx.lineTo(25, -18);
      ctx.stroke();
      ctx.fillStyle = '#64748b';
      ctx.beginPath(); ctx.arc(25, 0, 3, 0, Math.PI * 2); ctx.fill();
    } else {
      ctx.beginPath(); ctx.moveTo(0, -25); ctx.lineTo(0, -10);
      if (state === 'closed') ctx.lineTo(0, 25);
      else ctx.lineTo(18, 25);
      ctx.stroke();
      ctx.fillStyle = '#64748b';
      ctx.beginPath(); ctx.arc(0, 25, 3, 0, Math.PI * 2); ctx.fill();
    }
  }
  else if (type === 'ammeter' || type === 'voltmeter') {
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(0, 0, 14, 0, Math.PI * 2); ctx.stroke();
    ctx.fillStyle = '#e2e8f0';
    ctx.font = 'bold 15px sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(type === 'ammeter' ? 'A' : 'V', 0, 1);
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    if (isH) { ctx.moveTo(-28, 0); ctx.lineTo(-14, 0); ctx.moveTo(14, 0); ctx.lineTo(28, 0); }
    else { ctx.moveTo(0, -28); ctx.lineTo(0, -14); ctx.moveTo(0, 14); ctx.lineTo(0, 28); }
    ctx.stroke();
  }

  if (label) {
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(label, 0, isH ? 24 : -34);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawGraph — 绘制坐标系与数据曲线。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 原点X
 * @param {number} params.cy - 原点Y
 * @param {number} [params.width=200] - 轴宽度
 * @param {number} [params.height=160] - 轴高度
 * @param {string} [params.xLabel=''] - X轴标签
 * @param {string} [params.yLabel=''] - Y轴标签
 * @param {boolean} [params.showGrid=false] - 网格
 * @param {Array} [params.lines=[]] - 数据线 [{points:[{x,y}], color, label}]
 * @param {number} [params.opacity=1]
 * @param {number} frame
 */
function drawGraph(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var w = params.width !== undefined ? params.width : 200;
  var h = params.height !== undefined ? params.height : 160;
  var xLabel = params.xLabel || '';
  var yLabel = params.yLabel || '';
  var showGrid = params.showGrid || false;
  var lines = params.lines || [];
  var opacity = resolveParam(params.opacity, frame, 1);

  ctx.globalAlpha = clamp(opacity, 0, 1);
  ctx.translate(cx, cy);

  // 坐标轴
  ctx.strokeStyle = '#94a3b8';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(-8, 0); ctx.lineTo(w + 8, 0);
  ctx.moveTo(0, h + 8); ctx.lineTo(0, -8);
  ctx.stroke();

  // 箭头
  ctx.fillStyle = '#94a3b8';
  ctx.beginPath(); ctx.moveTo(w + 8, 0); ctx.lineTo(w, -4); ctx.lineTo(w, 4); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(0, -8); ctx.lineTo(-4, 0); ctx.lineTo(4, 0); ctx.closePath(); ctx.fill();

  if (showGrid) {
    ctx.strokeStyle = 'rgba(148,163,184,0.15)';
    ctx.lineWidth = 0.5;
    for (var gi = 1; gi < 5; gi++) {
      var gx = gi * w / 5, gy = gi * h / 5;
      ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, h);
      ctx.moveTo(0, gy); ctx.lineTo(w, gy); ctx.stroke();
    }
  }

  ctx.fillStyle = '#94a3b8';
  ctx.font = '13px sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'top';
  if (xLabel) ctx.fillText(xLabel, w / 2, h + 10);
  ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
  if (yLabel) ctx.fillText(yLabel, -14, -h / 2);

  for (var li = 0; li < lines.length; li++) {
    var line = lines[li];
    var pts = line.points || [];
    if (pts.length < 2) continue;
    ctx.strokeStyle = line.color || '#60a5fa';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(pts[0].x, -pts[0].y);
    for (var pi = 1; pi < pts.length; pi++) ctx.lineTo(pts[pi].x, -pts[pi].y);
    ctx.stroke();
    for (var pi = 0; pi < pts.length; pi++) {
      ctx.fillStyle = line.color || '#60a5fa';
      ctx.beginPath(); ctx.arc(pts[pi].x, -pts[pi].y, 4, 0, Math.PI * 2); ctx.fill();
    }
    if (line.label && pts.length > 0) {
      ctx.fillStyle = line.color || '#60a5fa';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'left'; ctx.textBaseline = 'bottom';
      ctx.fillText(line.label, pts[pts.length-1].x + 6, -pts[pts.length-1].y);
    }
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawLever — 绘制杠杆。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 支点X
 * @param {number} params.cy - 支点Y
 * @param {number} [params.length=180] - 杠杆总长
 * @param {number} [params.angle=0] - 倾斜角（弧度），支持sin
 * @param {number} [params.leftMass=20] - 左侧物体大小
 * @param {number} [params.rightMass=20] - 右侧物体大小
 * @param {string} [params.leftColor='#60a5fa']
 * @param {string} [params.rightColor='#f472b6']
 * @param {string} [params.leftLabel='']
 * @param {string} [params.rightLabel='']
 * @param {number} [params.opacity=1]
 * @param {number} frame
 */
function drawLever(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var length = params.length !== undefined ? params.length : 180;
  var angle = resolveParam(params.angle, frame, 0);
  var leftMass = params.leftMass !== undefined ? params.leftMass : 20;
  var rightMass = params.rightMass !== undefined ? params.rightMass : 20;
  var leftColor = params.leftColor || '#60a5fa';
  var rightColor = params.rightColor || '#f472b6';
  var leftLabel = params.leftLabel || '';
  var rightLabel = params.rightLabel || '';
  var opacity = resolveParam(params.opacity, frame, 1);

  ctx.globalAlpha = clamp(opacity, 0, 1);
  ctx.translate(cx, cy);

  // 支点
  ctx.fillStyle = '#94a3b8';
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-10, 16); ctx.lineTo(10, 16); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = '#94a3b8';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(0, 16); ctx.lineTo(0, 28); ctx.stroke();

  // 杠杆臂
  var halfLen = length / 2;
  var cosA = Math.cos(angle), sinA = Math.sin(angle);
  ctx.strokeStyle = '#cbd5e1';
  ctx.lineWidth = 6;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(-halfLen * cosA, -halfLen * sinA);
  ctx.lineTo(halfLen * cosA, halfLen * sinA);
  ctx.stroke();

  // 左侧物体
  var lx = -halfLen * cosA, ly = -halfLen * sinA;
  ctx.fillStyle = leftColor;
  ctx.strokeStyle = 'rgba(0,0,0,0.2)';
  ctx.lineWidth = 1.5;
  ctx.fillRect(lx - leftMass/2, ly + 8, leftMass, leftMass);
  ctx.strokeRect(lx - leftMass/2, ly + 8, leftMass, leftMass);
  if (leftLabel) {
    ctx.fillStyle = '#e2e8f0'; ctx.font = '12px sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    ctx.fillText(leftLabel, lx, ly + leftMass + 12);
  }

  // 右侧物体
  var rx = halfLen * cosA, ry = halfLen * sinA;
  ctx.fillStyle = rightColor;
  ctx.strokeStyle = 'rgba(0,0,0,0.2)';
  ctx.lineWidth = 1.5;
  ctx.fillRect(rx - rightMass/2, ry + 8, rightMass, rightMass);
  ctx.strokeRect(rx - rightMass/2, ry + 8, rightMass, rightMass);
  if (rightLabel) {
    ctx.fillStyle = '#e2e8f0'; ctx.font = '12px sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    ctx.fillText(rightLabel, rx, ry + rightMass + 12);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawContainer — 绘制容器与液体。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 容器中心X
 * @param {number} params.cy - 容器底部Y
 * @param {number} [params.width=100] - 容器宽度
 * @param {number} [params.height=120] - 容器高度
 * @param {number} [params.liquidLevel=0.5] - 液面 0-1
 * @param {string} [params.liquidColor='rgba(66,165,245,0.3)']
 * @param {number} [params.objectSize=0] - 浸没物体大小（0=无）
 * @param {string} [params.objectColor='#fbbf24']
 * @param {string} [params.label=''] - 标签
 * @param {number} [params.opacity=1]
 * @param {number} frame
 */
function drawContainer(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var w = params.width !== undefined ? params.width : 100;
  var h = params.height !== undefined ? params.height : 120;
  var liquidLevel = params.liquidLevel !== undefined ? params.liquidLevel : 0.5;
  var liquidColor = params.liquidColor || 'rgba(66,165,245,0.3)';
  var objSize = params.objectSize !== undefined ? params.objectSize : 0;
  var objectColor = params.objectColor || '#fbbf24';
  var label = params.label || '';
  var opacity = resolveParam(params.opacity, frame, 1);

  ctx.globalAlpha = clamp(opacity, 0, 1);
  ctx.translate(cx, cy);

  // 容器壁
  ctx.strokeStyle = '#64748b';
  ctx.lineWidth = 3;
  ctx.strokeRect(-w/2, -h, w, h);

  // 液体
  var liquidH = h * liquidLevel;
  ctx.fillStyle = liquidColor;
  ctx.fillRect(-w/2 + 3, -liquidH, w - 6, liquidH);

  // 液面线
  ctx.strokeStyle = 'rgba(66,165,245,0.5)';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(-w/2 + 3, -liquidH);
  ctx.lineTo(w/2 - 3, -liquidH);
  ctx.stroke();

  // 浸没物体
  if (objSize > 0) {
    var objY = params.objectY !== undefined ? params.objectY : -liquidH + objSize/2;
    ctx.fillStyle = objectColor;
    ctx.strokeStyle = 'rgba(0,0,0,0.2)';
    ctx.lineWidth = 1.5;
    ctx.fillRect(-objSize/2, objY - objSize/2, objSize, objSize);
    ctx.strokeRect(-objSize/2, objY - objSize/2, objSize, objSize);
  }

  if (label) {
    ctx.fillStyle = '#e2e8f0'; ctx.font = '13px sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    ctx.fillText(label, 0, 6);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawLightRay — 绘制光线（反射/折射）。
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} params
 * @param {number} params.cx - 入射点X
 * @param {number} params.cy - 入射点Y
 * @param {number} [params.incidentAngle=45] - 入射角（度）
 * @param {number} [params.reflectAngle=45] - 反射角（度）
 * @param {number} [params.refractAngle=0] - 折射角（度，0=无）
 * @param {number} [params.rayLength=80] - 光线长度
 * @param {string} [params.incidentColor='#fbbf24']
 * @param {string} [params.reflectColor='#34d399']
 * @param {string} [params.refractColor='#60a5fa']
 * @param {boolean} [params.showNormal=true] - 法线
 * @param {string} [params.surfaceLabel=''] - 介面标签
 * @param {number} [params.opacity=1]
 * @param {number} frame
 */
function drawLightRay(ctx, params, frame) {
  ctx.save();
  var cx = params.cx || 0;
  var cy = params.cy || 0;
  var iAngle = params.incidentAngle || 45;
  var rAngle = params.reflectAngle !== undefined ? params.reflectAngle : 45;
  var refrAngle = params.refractAngle !== undefined ? params.refractAngle : 0;
  var rayLen = params.rayLength !== undefined ? params.rayLength : 80;
  var incColor = params.incidentColor || '#fbbf24';
  var refColor = params.reflectColor || '#34d399';
  var refrColor = params.refractColor || '#60a5fa';
  var showNormal = params.showNormal !== false;
  var surfaceLabel = params.surfaceLabel || '';
  var opacity = resolveParam(params.opacity, frame, 1);

  ctx.globalAlpha = clamp(opacity, 0, 1);
  ctx.translate(cx, cy);

  // 法线
  if (showNormal) {
    ctx.strokeStyle = 'rgba(148,163,184,0.4)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(0, -rayLen); ctx.lineTo(0, rayLen); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = 'rgba(148,163,184,0.5)';
    ctx.font = '11px sans-serif'; ctx.textAlign = 'left'; ctx.textBaseline = 'bottom';
    ctx.fillText('N', 4, -4);
  }

  // 介面
  ctx.strokeStyle = '#64748b';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(-rayLen, 0); ctx.lineTo(rayLen, 0); ctx.stroke();
  if (surfaceLabel) {
    ctx.fillStyle = '#94a3b8'; ctx.font = '11px sans-serif';
    ctx.textAlign = 'right'; ctx.textBaseline = 'top';
    ctx.fillText(surfaceLabel, rayLen, 4);
  }

  // 绘制光线和箭头（简化版，不含复杂箭头）
  var iRad = iAngle * Math.PI / 180;
  ctx.strokeStyle = incColor;
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(-Math.sin(iRad) * rayLen, -Math.cos(iRad) * rayLen);
  ctx.stroke();

  var refRad = rAngle * Math.PI / 180;
  ctx.strokeStyle = refColor;
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(Math.sin(refRad) * rayLen, -Math.cos(refRad) * rayLen);
  ctx.stroke();

  if (refrAngle > 0) {
    var refrRad = refrAngle * Math.PI / 180;
    ctx.strokeStyle = refrColor;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(Math.sin(refrRad) * rayLen * 0.8, Math.cos(refrRad) * rayLen * 0.8);
    ctx.stroke();
  }

  // 角度标注
  ctx.fillStyle = '#94a3b8';
  ctx.font = '12px sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
  ctx.fillText(iAngle + '°', -30, -16);

  ctx.restore();
}



/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawPhysicsStage — 绘制物理场景（斜面、水平面、轨道等）。
 */
function drawPhysicsStage(ctx, params, frame) {
  ctx.save();
  var type = params.type || 'slope+surface';
  var angle = params.angle || 37;
  var slopeLen = params.slopeLength || 3;
  var s = params.scale || 100;
  var ox = params.originX || 80;
  var oy = params.originY || 500;
  var showLabels = params.showLabels !== false;
  var opacity = resolveParam(params.opacity, frame, 1);
  ctx.globalAlpha = clamp(opacity, 0, 1);

  var aRad = angle * Math.PI / 180;
  var slopeEndX = ox + slopeLen * s * Math.cos(aRad);
  var slopeEndY = oy - slopeLen * s * Math.sin(aRad);
  var mu = params.mu || 0.4;

  if (type === 'slope+surface' || type === 'slope') {
    ctx.fillStyle = '#1e293b';
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(ox, oy);
    ctx.lineTo(slopeEndX, slopeEndY);
    ctx.lineTo(slopeEndX, oy);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  }

  if (type === 'slope+surface' || type === 'surface') {
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(slopeEndX, oy);
    ctx.lineTo(slopeEndX + 400, oy);
    ctx.stroke();
    ctx.fillStyle = '#334155';
    for (var ri = 0; ri < 20; ri++) {
      ctx.fillRect(slopeEndX + 15 + ri * 18, oy + 2, 6, 4);
    }
  }

  if (showLabels && (type === 'slope+surface' || type === 'slope')) {
    ctx.strokeStyle = 'rgba(148,163,184,0.4)';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    var arcR = 40;
    ctx.beginPath();
    ctx.arc(ox, oy, arcR, -aRad, 0);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '13px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText('θ=' + angle + '°', ox + arcR * 0.6, oy + 4);
    ctx.fillStyle = '#64748b';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillText('L=' + slopeLen + 'm', (ox + slopeEndX) / 2, slopeEndY - 6);
  }

  if (type === 'slope+surface') {
    ctx.fillStyle = '#64748b';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText('μ=' + mu.toFixed(1), slopeEndX + 10, oy + 10);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawPhysicsObject — 绘制并移动物理对象。
 */
function drawPhysicsObject(ctx, params, frame) {
  ctx.save();
  var frames = params.frames || [];
  if (frames.length === 0) { ctx.restore(); return; }
  var scale = params.scale || 100;
  var ox = params.originX || 80;
  var oy = params.originY || 500;
  var angle = params.angle || 37;
  var slopeLen = params.slopeLength || 3;
  var size = params.objectSize || 24;
  var color = params.objectColor || '#60a5fa';
  var label = params.label || '';
  var showVel = params.showVelocity || false;
  var mass = params.mass || 2;
  var opacity = resolveParam(params.opacity, frame, 1);
  ctx.globalAlpha = clamp(opacity, 0, 1);

  var idx = Math.min(frame, frames.length - 1);
  var data = frames[idx];
  if (!data) { ctx.restore(); return; }

  var aRad = angle * Math.PI / 180;
  var slopeEndX = ox + slopeLen * scale * Math.cos(aRad);
  var screenX, screenY;
  if (data.phase === 'slope') {
    screenX = ox + data.x * scale * Math.cos(aRad);
    screenY = oy - data.x * scale * Math.sin(aRad);
  } else {
    screenX = slopeEndX + (data.x - slopeLen) * scale;
    screenY = oy;
  }

  ctx.fillStyle = 'rgba(0,0,0,0.2)';
  ctx.fillRect(screenX - size/2 + 3, screenY - size/2 + 3, size, size);
  ctx.fillStyle = color;
  ctx.shadowColor = color + '44';
  ctx.shadowBlur = 12;
  ctx.fillRect(screenX - size/2, screenY - size/2, size, size);
  ctx.shadowBlur = 0;
  ctx.strokeStyle = 'rgba(255,255,255,0.2)';
  ctx.lineWidth = 1;
  ctx.strokeRect(screenX - size/2, screenY - size/2, size, size);

  var lbl = label || ('m=' + mass + 'kg');
  ctx.fillStyle = '#e2e8f0';
  ctx.font = '11px sans-serif';
  ctx.textAlign = 'center';
  if (data.phase === 'slope') {
    ctx.textBaseline = 'bottom';
    ctx.fillText(lbl, screenX, screenY - size/2 - 4);
  } else {
    ctx.textBaseline = 'top';
    ctx.fillText(lbl, screenX, screenY + size/2 + 4);
  }

  if (showVel && data.v > 0.05) {
    var arrowLen = Math.min(data.v * 12, 80);
    var startX = screenX + size/2;
    var startY = screenY;
    ctx.strokeStyle = '#60a5fa';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(startX + arrowLen, startY);
    ctx.stroke();
    ctx.fillStyle = '#60a5fa';
    ctx.beginPath();
    ctx.moveTo(startX + arrowLen, startY);
    ctx.lineTo(startX + arrowLen - 8, startY - 4);
    ctx.lineTo(startX + arrowLen - 8, startY + 4);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = '#60a5fa';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillText('v=' + data.v.toFixed(1) + 'm/s', startX + arrowLen/2, startY - 6);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawPhysicsHUD — 显示物理量数据面板。
 */
function drawPhysicsHUD(ctx, params, frame) {
  ctx.save();
  var frames = params.frames || [];
  if (frames.length === 0) { ctx.restore(); return; }
  var px = params.panelX || 20;
  var py = params.panelY || 20;
  var showEnergy = params.showEnergy || false;
  var mode = params.mode || 'electric_pendulum';
  var opacity = resolveParam(params.opacity, frame, 1);
  ctx.globalAlpha = clamp(opacity, 0, 1);

  var idx = Math.min(frame, frames.length - 1);
  var d = frames[idx];
  if (!d) { ctx.restore(); return; }

  var panelH = showEnergy ? 210 : 150;
  ctx.fillStyle = 'rgba(10,15,25,0.82)';
  roundRectPath(ctx, px, py, 200, panelH, 8);
  ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 1;
  roundRectPath(ctx, px, py, 200, panelH, 8);
  ctx.stroke();

  ctx.fillStyle = '#94a3b8';
  ctx.font = '11px sans-serif';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'top';
  ctx.fillText('■ 实时数据', px + 12, py + 8);

  var items = [];
  if (mode === 'electric_pendulum') {
    items = [
      {label:'角度 θ', value:(d.theta_deg || Math.abs(d.theta || 0) * 180 / Math.PI).toFixed(1) + '°', color:'#fbbf24'},
      {label:'速度 v', value:(d.v || 0).toFixed(2) + ' m/s', color:'#60a5fa'},
      {label:'高度 h', value:(d.y || 0).toFixed(3) + ' m', color:'#34d399'},
      {label:'F电', value:((params.q || 5e-4) * (params.E || 2000)).toFixed(2) + ' N', color:'#ef4444'},
      {label:'G', value:((params.mass || 0.1) * (params.g || 10)).toFixed(2) + ' N', color:'#3b82f6'},
    ];
  } else {
    items = [
      {label:'阶段', value:d.phase || 'unknown', color:'#f472b6'},
      {label:'位置', value:(d.x||0).toFixed(2) + ' m', color:'#fbbf24'},
      {label:'速度', value:(d.v||0).toFixed(2) + ' m/s', color:'#60a5fa'},
      {label:'加速度', value:(d.a||0).toFixed(2) + ' m/s²', color:'#a78bfa'},
    ];
    if (showEnergy) {
      items.push({label:'动能', value:(d.Ek||0).toFixed(1)+' J', color:'#34d399'});
      items.push({label:'势能', value:(d.Ep||0).toFixed(1)+' J', color:'#fbbf24'});
    }
  }

  for (var ii = 0; ii < items.length; ii++) {
    var item = items[ii];
    var iy = py + 30 + ii * 22;
    ctx.fillStyle = '#64748b';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(item.label, px + 14, iy);
    ctx.fillStyle = item.color;
    ctx.textAlign = 'right';
    ctx.fillText(item.value, px + 188, iy);
  }

  // 能量条（三色：动能/重力势能/电势能）
  if (showEnergy && mode === 'electric_pendulum') {
    var Ek = d.Ek || 0;
    var Ep_grav = d.Ep_grav || d.Ep || 0;
    var Ep_elec = d.Ep_elec || d.Ep_electric || 0;
    var totalE = Ek + Ep_grav + Ep_elec;
    if (totalE > 0) {
      var barY = py + panelH - 50;
      var barW = 176;
      var barH = 14;
      ctx.fillStyle = 'rgba(50,60,80,0.4)';
      roundRectPath(ctx, px + 12, barY, barW, barH, 5);
      ctx.fill();
      var eW = Math.max(2, (Ep_elec / totalE) * barW);
      ctx.fillStyle = '#3b82f6';
      roundRectPath(ctx, px + 12, barY, eW, barH, 5);
      ctx.fill();
      var kW = Math.max(2, (Ek / totalE) * barW);
      ctx.fillStyle = '#34d399';
      roundRectPath(ctx, px + 12 + eW, barY, kW, barH, 0);
      ctx.fill();
      if (eW + kW >= barW - 2) { roundRectPath(ctx, px + 12 + eW, barY, kW, barH, 5); ctx.fill(); }
      var gW = Math.max(2, (Ep_grav / totalE) * barW);
      ctx.fillStyle = '#f97316';
      roundRectPath(ctx, px + 12 + eW + kW, barY, gW, barH, 0);
      ctx.fill();
      roundRectPath(ctx, px + 12 + eW + kW, barY, gW, barH, gW > 4 ? 5 : 0);
      ctx.fill();
      // 标签
      ctx.fillStyle = '#64748b';
      ctx.font = '9px sans-serif';
      ctx.textAlign = 'left'; ctx.textBaseline = 'bottom';
      ctx.fillText('⚡电势', px + 14, barY - 2);
      ctx.textAlign = 'center';
      ctx.fillText('动能', px + 12 + eW + kW/2, barY - 2);
      ctx.textAlign = 'right';
      ctx.fillText('重力势', px + 12 + barW, barY - 2);
      // 总能量值
      ctx.fillStyle = 'rgba(255,255,255,0.3)';
      ctx.font = '9px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('E总 = ' + totalE.toFixed(2) + ' J（守恒）', px + 12 + barW/2, barY + barH + 12);
    }
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawPhaseLabel — 显示当前阶段标签。
 */
function drawPhaseLabel(ctx, params, frame) {
  ctx.save();
  var frames = params.frames || [];
  if (frames.length === 0) { ctx.restore(); return; }
  var x = params.x || 16;
  var y = params.y || 16;
  var opacity = resolveParam(params.opacity, frame, 1);
  ctx.globalAlpha = clamp(opacity, 0, 1);
  var idx = Math.min(frame, frames.length - 1);
  var d = frames[idx];
  if (!d || !d.phase) { ctx.restore(); return; }
  var phaseNames = {'slope':'斜面加速下滑','rough_surface':'粗糙面减速','horizontal_pull':'水平拉力加速'};
  var pn = phaseNames[d.phase] || d.phase;
  ctx.fillStyle = 'rgba(0,0,0,0.6)';
  roundRectPath(ctx, x, y, 200, 32, 6);
  ctx.fill();
  ctx.fillStyle = '#f6d365';
  ctx.font = 'bold 14px sans-serif';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText('▶ ' + pn, x + 14, y + 16);
  ctx.fillStyle = '#64748b';
  ctx.font = '11px sans-serif';
  ctx.textAlign = 'right';
  ctx.fillText('帧' + d.frame, x + 188, y + 16);
  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
/**
 * drawElectricFieldBg — 绘制水平匀强电场背景（箭头指示线）。
 */
function drawElectricFieldBg(ctx, params, frame) {
  ctx.save();
  var opacity = resolveParam(params.opacity, frame, 1);
  ctx.globalAlpha = clamp(opacity, 0, 1);
  var fieldColor = params.fieldColor || 'rgba(59,130,246,0.05)';
  var arrowColor = params.arrowColor || 'rgba(59,130,246,0.20)';
  var cx = params.cx || 480;
  var cy = params.cy || 320;
  var w = params.width || 800;
  var h = params.height || 500;
  var spacing = params.spacing || 70;
  var direction = params.direction || 'right';
  var grad = ctx.createLinearGradient(cx - w/2, cy, cx + w/2, cy);
  grad.addColorStop(0, 'rgba(59,130,246,0.02)');
  grad.addColorStop(0.5, 'rgba(59,130,246,0.06)');
  grad.addColorStop(1, 'rgba(59,130,246,0.02)');
  ctx.fillStyle = grad;
  ctx.fillRect(cx - w/2, cy - h/2, w, h);
  var dir = direction === 'right' ? 1 : -1;
  var startX = cx - w/2 + 20;
  var endX = cx + w/2 - 20;
  var arrowLen = 12;
  for (var yy = cy - h/2 + 30; yy < cy + h/2 - 20; yy += spacing) {
    ctx.strokeStyle = arrowColor;
    ctx.lineWidth = 1.5;
    ctx.setLineDash([8, 12]);
    ctx.lineDashOffset = -frame * 1.5;
    ctx.beginPath();
    ctx.moveTo(startX, yy);
    ctx.lineTo(endX, yy);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.lineDashOffset = 0;
    for (var ax = startX + 30; ax < endX - 20; ax += 80) {
      ctx.fillStyle = arrowColor;
      ctx.beginPath();
      ctx.moveTo(ax + arrowLen * dir, yy);
      ctx.lineTo(ax + arrowLen * dir - 8 * dir, yy - 4);
      ctx.lineTo(ax + arrowLen * dir - 8 * dir, yy + 4);
      ctx.closePath();
      ctx.fill();
    }
  }
  ctx.fillStyle = 'rgba(59,130,246,0.35)';
  ctx.font = 'bold 13px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  ctx.fillText('E', endX + 20, cy - h/2 + 4);
  ctx.fillStyle = 'rgba(59,130,246,0.15)';
  ctx.font = '11px sans-serif';
  ctx.fillText('匀强电场 → → → → →', cx, cy - h/2 + 22);
  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
/**
 * drawElectricPendulum — 绘制电场中的带电单摆。
 * 从 params.frames[frame] 中获取 theta、v、Ek 等物理量。
 */
function drawElectricPendulum(ctx, params, frame) {
  ctx.save();
  var frames = params.frames || [];
  if (frames.length === 0) { ctx.restore(); return; }
  var idx = Math.min(frame, frames.length - 1);
  var d = frames[idx];
  if (!d) { ctx.restore(); return; }

  var theta = d.theta || 0;
  var cx = params.cx || 480;
  var cy = params.cy || 80;
  var L = params.length || 120;
  var bobR = params.bobSize || 16;
  var bobColor = params.bobColor || '#fbbf24';
  var showAngle = params.showAngle !== false;
  var showForce = params.showForce || false;
  var showVelocity = params.showVelocity || false;
  var mass = params.mass || 0.1;
  var q = params.q || 5e-4;
  var E = params.E || 2000;
  var g = params.g || 10;
  var scale = params.scale || 1;

  // ---- 布局 ----
  var bobX = cx + L * scale * Math.sin(theta);
  var bobY = cy + L * scale * Math.cos(theta);

  // ---- 虚线圆弧轨迹 ----
  ctx.strokeStyle = 'rgba(148,163,184,0.15)';
  ctx.lineWidth = 1;
  ctx.setLineDash([4, 6]);
  ctx.beginPath();
  ctx.arc(cx, cy, L * scale, 0, Math.PI, false);
  ctx.stroke();
  ctx.setLineDash([]);

  // ---- 悬挂点 ----
  ctx.fillStyle = '#94a3b8';
  ctx.beginPath();
  ctx.arc(cx, cy, 5, 0, Math.PI * 2);
  ctx.fill();

  // ---- 天花板 ----
  ctx.strokeStyle = '#475569';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx - 100, cy);
  ctx.lineTo(cx + 100, cy);
  ctx.stroke();
  // 天花板小斜线
  for (var ti = -80; ti <= 80; ti += 20) {
    ctx.beginPath();
    ctx.moveTo(cx + ti, cy);
    ctx.lineTo(cx + ti - 4, cy + 6);
    ctx.stroke();
  }

  // ---- 摆线 ----
  ctx.strokeStyle = '#94a3b8';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(bobX, bobY);
  ctx.stroke();

  // 摆长标注
  ctx.fillStyle = 'rgba(148,163,184,0.3)';
  ctx.font = '11px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillText('L=' + (params._realLength || '1.0') + 'm', (cx + bobX) / 2, (cy + bobY) / 2 - 4);

  // ---- 角度弧 ----
  if (showAngle && Math.abs(theta) > 0.01) {
    var arcR = 50;
    var arcEnd = theta < 0 ? -Math.abs(theta) : Math.abs(theta);
    // 弧线（实线 + 半透明）
    ctx.strokeStyle = 'rgba(255,255,255,0.3)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(cx, cy, arcR, -0.08, arcEnd > 0 ? arcEnd : -arcEnd);
    ctx.stroke();
    // θ 标签
    ctx.fillStyle = 'rgba(255,255,255,0.5)';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    var labelX = cx + arcR * 0.6 * (theta > 0 ? 1 : -1);
    var labelY = cy + arcR * 0.6 + 4;
    ctx.fillText('θ', labelX, labelY);
    // θ 数值（靠近球的位置）
    var degLabel = (Math.abs(theta) * 180 / Math.PI).toFixed(1) + '°';
    ctx.fillStyle = 'rgba(255,255,255,0.25)';
    ctx.font = '11px sans-serif';
    ctx.fillText(degLabel, bobX - 30, bobY - 20);
  }

  // ---- 摆球 ----
  ctx.shadowColor = bobColor + '66';
  ctx.shadowBlur = 20;
  ctx.fillStyle = bobColor;
  ctx.beginPath();
  ctx.arc(bobX, bobY, bobR, 0, Math.PI * 2);
  ctx.fill();
  ctx.shadowBlur = 0;
  // 边框
  ctx.strokeStyle = 'rgba(0,0,0,0.12)';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(bobX, bobY, bobR, 0, Math.PI * 2);
  ctx.stroke();
  // 高光
  ctx.fillStyle = 'rgba(255,255,255,0.3)';
  ctx.beginPath();
  ctx.arc(bobX - bobR*0.25, bobY - bobR*0.25, bobR*0.35, 0, Math.PI*2);
  ctx.fill();
  // "+" 正电标记
  ctx.fillStyle = '#fff';
  ctx.font = 'bold 12px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('+', bobX, bobY);

  // ---- 速度箭头（切线方向） ----
  if (showVelocity && d.v != null && d.v > 0.05) {
    var vScale = 6;
    var vx = -Math.sin(theta) * d.v * vScale;
    var vy = Math.cos(theta) * d.v * vScale;
    var tipX = bobX + vx;
    var tipY = bobY + vy;
    // 箭头线
    ctx.strokeStyle = '#60a5fa';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(bobX, bobY);
    ctx.lineTo(tipX, tipY);
    ctx.stroke();
    // 箭头头部
    var aLen = 8;
    var aAngle = Math.atan2(vy, vx);
    ctx.fillStyle = '#60a5fa';
    ctx.beginPath();
    ctx.moveTo(tipX, tipY);
    ctx.lineTo(tipX - aLen * Math.cos(aAngle - 0.4), tipY - aLen * Math.sin(aAngle - 0.4));
    ctx.lineTo(tipX - aLen * Math.cos(aAngle + 0.4), tipY - aLen * Math.sin(aAngle + 0.4));
    ctx.closePath();
    ctx.fill();
    // v 标签
    ctx.fillStyle = '#60a5fa';
    ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'bottom';
    var vLabelX = tipX + 8;
    var vLabelY = tipY - 4;
    ctx.fillText('v', vLabelX, vLabelY);
    // 速度值
    ctx.fillStyle = 'rgba(96,165,250,0.5)';
    ctx.font = '10px sans-serif';
    ctx.fillText(d.v.toFixed(2) + 'm/s', vLabelX + 16, vLabelY);
  }

  // ---- 受力分析箭头（实线精美箭头） ----
  if (showForce) {
    var arrowLenBase = 50;  // 基础箭头像素长度
    var fArrowColor = '#ef4444';  // 红色：重力
    var eArrowColor = '#3b82f6';  // 蓝色：电场力
    var rArrowColor = '#f97316';  // 橙色：合力

    // 计算各力的大小比例
    var mg_val = mass * g;
    var qE_val = q * E;
    var fMax = Math.max(mg_val, qE_val, 0.01);
    var gLen = (mg_val / fMax) * arrowLenBase * 0.9 + 10;
    var eLen = (qE_val / fMax) * arrowLenBase * 0.9 + 10;
    var rLen = Math.sqrt(mg_val*mg_val + qE_val*qE_val) / fMax * arrowLenBase * 0.9 + 10;

    // 辅助函数：画箭头
    function drawForceArrow(ctx2, fromX, fromY, toX, toY, color, label, labelColor) {
      var dx = toX - fromX, dy = toY - fromY;
      var angle = Math.atan2(dy, dx);
      var len = Math.sqrt(dx*dx + dy*dy);
      if (len < 1) return;
      // 箭头主体（粗实线）
      ctx2.strokeStyle = color;
      ctx2.lineWidth = 2.5;
      ctx2.globalAlpha = 0.85;
      ctx2.beginPath();
      ctx2.moveTo(fromX, fromY);
      ctx2.lineTo(toX, toY);
      ctx2.stroke();
      ctx2.globalAlpha = 1;
      // 箭头头部（实心三角）
      var headLen = 10, headAngle = 0.5;
      ctx2.fillStyle = color;
      ctx2.beginPath();
      ctx2.moveTo(toX, toY);
      ctx2.lineTo(toX - headLen * Math.cos(angle - headAngle), toY - headLen * Math.sin(angle - headAngle));
      ctx2.lineTo(toX - headLen * Math.cos(angle + headAngle), toY - headLen * Math.sin(angle + headAngle));
      ctx2.closePath();
      ctx2.fill();
      // 发光光晕
      ctx2.shadowColor = color;
      ctx2.shadowBlur = 6;
      ctx2.beginPath();
      ctx2.arc(toX, toY, 3, 0, Math.PI * 2);
      ctx2.fill();
      ctx2.shadowBlur = 0;
      // 标签
      ctx2.fillStyle = labelColor || color;
      ctx2.font = 'bold 12px sans-serif';
      ctx2.textAlign = 'center';
      ctx2.textBaseline = 'bottom';
      var lx = (fromX + toX) / 2;
      var ly = (fromY + toY) / 2;
      ctx2.fillText(label, lx, ly - 4);
    }

    // ---- 重力 G（蓝色，竖直向下） ----
    drawForceArrow(ctx, bobX, bobY, bobX, bobY + gLen, '#3b82f6', 'G', '#60a5fa');
    // ---- 电场力 F电（红色，水平向右，因为正电荷） ----
    drawForceArrow(ctx, bobX, bobY, bobX + eLen, bobY, '#ef4444', 'F电', '#f87171');
    // ---- 合力 F合（橙色，斜向） ----
    var rDx = eLen, rDy = gLen;
    var rLen_actual = Math.sqrt(rDx*rDx + rDy*rDy);
    var rNormX = rDx / rLen_actual, rNormY = rDy / rLen_actual;
    var rEndX = bobX + rNormX * rLen * 0.9;
    var rEndY = bobY + rNormY * rLen * 0.9;
    drawForceArrow(ctx, bobX, bobY, rEndX, rEndY, '#f97316', 'F合', '#fb923c');

    // ---- 力的合成关系（虚线辅助框，仅在小角度时显示） ----
    if (Math.abs(theta) < 0.5) {
      ctx.strokeStyle = 'rgba(255,255,255,0.08)';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 4]);
      // 从 G 箭头末端到 F合 末端（水平连线）
      ctx.beginPath();
      ctx.moveTo(bobX, bobY + gLen);
      ctx.lineTo(rEndX, bobY + gLen);
      ctx.stroke();
      // 从 F电 箭头末端到 F合 末端（竖直连线）
      ctx.beginPath();
      ctx.moveTo(bobX + eLen, bobY);
      ctx.lineTo(bobX + eLen, rEndY);
      ctx.stroke();
      ctx.setLineDash([]);
      // 平行四边形标注
      ctx.fillStyle = 'rgba(255,255,255,0.08)';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('平行四边形法则', rEndX + 40, rEndY);
    }

    // ---- 受力数值标签（在球附近汇总） ----
    ctx.fillStyle = 'rgba(15,25,35,0.7)';
    roundRectPath(ctx, bobX + bobR + 6, bobY - 48, 110, 46, 4);
    ctx.fill();

    ctx.font = '10px sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#ef4444'; ctx.fillText('F电 = ' + qE_val.toFixed(1) + 'N', bobX + bobR + 12, bobY - 36);
    ctx.fillStyle = '#3b82f6'; ctx.fillText('G  = ' + mg_val.toFixed(1) + 'N', bobX + bobR + 12, bobY - 20);
    ctx.fillStyle = '#f97316'; ctx.fillText('F合 = ' + Math.sqrt(mg_val*mg_val+qE_val*qE_val).toFixed(2) + 'N', bobX + bobR + 12, bobY - 4);
  }

  ctx.restore();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/**
 * drawCinematicElectricPendulum — 精良版电场中带电单摆动画。
 */
function drawCinematicElectricPendulum(ctx, params, frame) {
  var frames = params.frames || [];
  var totalFrames = params.totalFrames || 4800;
  var mass = params.mass || 0.1, q = params.q || 5e-4, E = params.E || 2000;
  var g = params.g || 10, L = params.L || 1.0;
  var Fq = params.Fq || 1.0, Fg = params.Fg || 1.0, Fr = params.Fr || 1.414;
  var captions = params.captions || {};
  var W = ctx.canvas.width, H = ctx.canvas.height;

  var total = totalFrames;
  var I0 = Math.floor(total*0.02), I1 = Math.floor(total*0.17), I2 = Math.floor(total*0.55);
  var I3 = Math.floor(total*0.85), I4 = Math.floor(total*0.97);
  var scene = frame < I0 ? 'INTRO' : frame < I1 ? 'FORCES' : frame < I2 ? 'SWING' : frame < I3 ? 'ENERGY' : frame < I4 ? 'SOLUTION' : 'ENDING';

  var CX = W/2, CY = 130, Lp = 130, BR = 18;

  function lerp(a,b,t){return a+(b-a)*t;}
  function clamp(v,l,h){return Math.max(l,Math.min(h,v));}
  function eo(t){return 1-Math.pow(1-t,3);}
  function rc(c,x,y,w,h,r){
    if(r>w/2)r=w/2;if(r>h/2)r=h/2;
    c.beginPath();c.moveTo(x+r,y);c.lineTo(x+w-r,y);
    c.arcTo(x+w,y,x+w,y+r,r);c.lineTo(x+w,y+h-r);
    c.arcTo(x+w,y+h,x+w-r,y+h,r);c.lineTo(x+r,y+h);
    c.arcTo(x,y+h,x,y+h-r,r);c.lineTo(x,y+r);
    c.arcTo(x,y,x+r,y,r);c.closePath();
  }
  function da(c,x1,y1,x2,y2,cl){
    var a=Math.atan2(y2-y1,x2-x1);
    c.strokeStyle=cl;c.lineWidth=2.5;
    c.beginPath();c.moveTo(x1,y1);c.lineTo(x2,y2);c.stroke();
    c.fillStyle=cl;
    c.beginPath();c.moveTo(x2,y2);
    c.lineTo(x2-10*Math.cos(a-0.5),y2-10*Math.sin(a-0.5));
    c.lineTo(x2-10*Math.cos(a+0.5),y2-10*Math.sin(a+0.5));
    c.closePath();c.fill();
  }

  // 物理状态
  var theta=0,v=0,Ek=0,Ep_g=0,Ep_e=0,Etot=0;
  if(frames&&frames.length>0){
    var fi=Math.min(Math.floor(frame/total*frames.length),frames.length-1);
    var d=frames[fi]||{};
    theta=d.theta||0;v=d.v||0;Ek=d.Ek||0;Ep_g=d.Ep_gravity||d.Ep||0;Ep_e=d.Ep_electric||0;Etot=d.E_total||0;
  }
  var bX=CX+Lp*Math.sin(theta),bY=CY+Lp*Math.cos(theta);

  // 背景
  var bg=ctx.createRadialGradient(W/2,H/2,0,W/2,H/2,W);
  bg.addColorStop(0,'#0f172a');bg.addColorStop(0.6,'#0a0e17');bg.addColorStop(1,'#060a0f');
  ctx.fillStyle=bg;ctx.fillRect(0,0,W,H);

  if(scene==='INTRO'||scene==='ENDING'){
    ctx.fillStyle='rgba(255,255,255,0.1)';
    for(var i=0;i<50;i++){
      var tw=Math.sin(frame*0.02+i*1.3)*0.5+0.5;
      ctx.globalAlpha=tw*0.25;
      ctx.beginPath();ctx.arc((i*137.5+i*7)%W,(i*97.3+i*13)%(H*0.35),0.5+(i%3)*0.3,0,Math.PI*2);ctx.fill();
    }
    ctx.globalAlpha=1;
  }

  // 电场箭头
  if(scene!=='ENDING'){
    var fo=(frame*1.5)%30;
    for(var y=40;y<bY+30&&y<H-40;y+=50){
      ctx.strokeStyle='rgba(59,130,246,0.09)';ctx.lineWidth=1.2;
      ctx.setLineDash([6,10]);ctx.lineDashOffset=-frame*1.2;
      ctx.beginPath();ctx.moveTo(60,y);ctx.lineTo(W-60,y);ctx.stroke();
      ctx.setLineDash([]);ctx.lineDashOffset=0;
      for(var x=100;x<W-80;x+=70){
        var fx=x+((fo<15)?fo*1.5:(fo-30)*1.5);
        if(fx<60||fx>W-60)continue;
        ctx.fillStyle='rgba(59,130,246,0.1)';
        ctx.beginPath();ctx.moveTo(fx+10,y);ctx.lineTo(fx+2,y-4);ctx.lineTo(fx+2,y+4);ctx.closePath();ctx.fill();
      }
    }
    ctx.fillStyle='rgba(59,130,246,0.18)';ctx.font='bold 12px sans-serif';
    ctx.textAlign='right';ctx.textBaseline='top';ctx.fillText('E →',W-60,42);
  }

  // 圆弧轨迹
  ctx.save();ctx.globalAlpha=0.08;
  ctx.strokeStyle='#94a3b8';ctx.lineWidth=1;ctx.setLineDash([4,6]);
  ctx.beginPath();ctx.arc(CX,CY,Lp,0.15,Math.PI-0.15,false);ctx.stroke();
  ctx.setLineDash([]);ctx.restore();

  // 天花板+悬点
  var gd=ctx.createLinearGradient(CX-120,CY,CX+120,CY);
  gd.addColorStop(0,'rgba(71,85,105,0)');gd.addColorStop(0.3,'rgba(71,85,105,0.5)');
  gd.addColorStop(0.7,'rgba(71,85,105,0.5)');gd.addColorStop(1,'rgba(71,85,105,0)');
  ctx.strokeStyle=gd;ctx.lineWidth=3;
  ctx.beginPath();ctx.moveTo(CX-100,CY);ctx.lineTo(CX+100,CY);ctx.stroke();
  ctx.strokeStyle='rgba(71,85,105,0.2)';ctx.lineWidth=1;
  for(var ti=-90;ti<=90;ti+=15){ctx.beginPath();ctx.moveTo(CX+ti,CY);ctx.lineTo(CX+ti-5,CY+6);ctx.stroke();}
  ctx.fillStyle='#94a3b8';ctx.beginPath();ctx.arc(CX,CY,5,0,Math.PI*2);ctx.fill();

  // 摆线
  ctx.strokeStyle='rgba(148,163,184,0.5)';ctx.lineWidth=2;
  ctx.beginPath();ctx.moveTo(CX,CY);ctx.lineTo(bX,bY);ctx.stroke();
  if(scene==='INTRO'||scene==='FORCES'){
    ctx.fillStyle='rgba(148,163,184,0.2)';ctx.font='11px sans-serif';ctx.textAlign='center';
    ctx.fillText('L = 1.0m',(CX+bX)/2-10,(CY+bY)/2-6);
  }

  // 角度
  if(Math.abs(theta)>0.02&&(scene==='SWING'||scene==='ENERGY')){
    ctx.strokeStyle='rgba(255,255,255,0.18)';ctx.lineWidth=1.5;
    ctx.beginPath();ctx.arc(CX,CY,45,-0.05,theta>0?theta:-theta);ctx.stroke();
    ctx.fillStyle='rgba(255,255,255,0.3)';ctx.font='bold 14px sans-serif';ctx.textAlign='center';
    ctx.fillText('θ='+(Math.abs(theta)*180/Math.PI).toFixed(1)+'°',CX+45*0.6*(theta>0?1:-1),CY+45*0.6+6);
  }

  // 摆球
  var gl=ctx.createRadialGradient(bX,bY,2,bX,bY,BR*2);
  gl.addColorStop(0,'rgba(251,191,36,0.15)');gl.addColorStop(1,'rgba(251,191,36,0)');
  ctx.fillStyle=gl;ctx.beginPath();ctx.arc(bX,bY,BR*2,0,Math.PI*2);ctx.fill();
  var bg2=ctx.createRadialGradient(bX-BR*0.3,bY-BR*0.3,2,bX,bY,BR);
  bg2.addColorStop(0,'#fcd34d');bg2.addColorStop(0.6,'#fbbf24');bg2.addColorStop(1,'#d97706');
  ctx.shadowColor='rgba(251,191,36,0.25)';ctx.shadowBlur=20;
  ctx.fillStyle=bg2;ctx.beginPath();ctx.arc(bX,bY,BR,0,Math.PI*2);ctx.fill();
  ctx.shadowBlur=0;
  ctx.strokeStyle='rgba(0,0,0,0.1)';ctx.lineWidth=1;
  ctx.beginPath();ctx.arc(bX,bY,BR,0,Math.PI*2);ctx.stroke();
  ctx.fillStyle='rgba(255,255,255,0.3)';
  ctx.beginPath();ctx.arc(bX-BR*0.25,bY-BR*0.25,BR*0.3,0,Math.PI*2);ctx.fill();
  ctx.fillStyle='#fff';ctx.font='bold 13px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.fillText('+',bX,bY);

  // 受力箭头
  if(scene==='FORCES'||scene==='SWING'||scene==='ENERGY'){
    var al=50,fqX=bX+al,fqY=bY,fgX=bX,fgY=bY+al;
    var frL=Math.sqrt(al*al+al*al),frX=bX+(al/frL)*frL*0.9,frY=bY+(al/frL)*frL*0.9;
    ctx.save();
    ctx.shadowColor='rgba(59,130,246,0.3)';ctx.shadowBlur=8;
    da(ctx,bX,bY,fgX,fgY,'rgba(59,130,246,0.85)');ctx.shadowBlur=0;
    ctx.fillStyle='#60a5fa';ctx.font='bold 13px sans-serif';ctx.textAlign='center';ctx.fillText('G',bX-16,bY+al*0.5-4);
    ctx.shadowColor='rgba(239,68,68,0.3)';ctx.shadowBlur=8;
    da(ctx,bX,bY,fqX,fqY,'rgba(239,68,68,0.85)');ctx.shadowBlur=0;
    ctx.fillStyle='#ef4444';ctx.fillText('F电',bX+al*0.5,bY-14);
    ctx.shadowColor='rgba(249,115,22,0.3)';ctx.shadowBlur=8;
    da(ctx,bX,bY,frX,frY,'rgba(249,115,22,0.85)');ctx.shadowBlur=0;
    ctx.fillStyle='#fb923c';ctx.textAlign='left';ctx.fillText('F合',(bX+frX)/2+12,(bY+frY)/2-4);
    if(scene==='FORCES'){
      ctx.strokeStyle='rgba(255,255,255,0.06)';ctx.lineWidth=1;ctx.setLineDash([3,4]);
      ctx.beginPath();ctx.moveTo(bX,bY+al);ctx.lineTo(frX,bY+al);ctx.stroke();
      ctx.beginPath();ctx.moveTo(bX+al,bY);ctx.lineTo(bX+al,frY);ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle='rgba(255,255,255,0.05)';ctx.font='11px sans-serif';ctx.fillText('平行四边形法则',frX+16,frY+4);
    }
    ctx.fillStyle='rgba(10,15,25,0.7)';
    rc(ctx,bX+BR+8,bY-52,115,48,6);ctx.fill();
    ctx.font='11px sans-serif';ctx.textAlign='left';ctx.textBaseline='middle';
    ctx.fillStyle='#ef4444';ctx.fillText('F电 = '+Fq.toFixed(1)+' N',bX+BR+16,bY-38);
    ctx.fillStyle='#60a5fa';ctx.fillText('G   = '+Fg.toFixed(1)+' N',bX+BR+16,bY-22);
    ctx.fillStyle='#fb923c';ctx.fillText('F合 = '+Fr.toFixed(2)+' N',bX+BR+16,bY-6);
    ctx.restore();
  }

  // 速度箭头
  if((scene==='SWING'||scene==='ENERGY')&&v>0.05){
    var va=theta+Math.PI/2,vx=bX+v*5*Math.cos(va),vy=bY+v*5*Math.sin(va);
    da(ctx,bX,bY,vx,vy,'rgba(96,165,250,0.7)');
    ctx.fillStyle='#60a5fa';ctx.font='bold 12px sans-serif';ctx.textAlign='left';
    ctx.fillText('v',vx+8,vy-4);
    ctx.fillStyle='rgba(96,165,250,0.4)';ctx.font='10px sans-serif';
    ctx.fillText(v.toFixed(2)+'m/s',vx+20,vy-4);
  }

  // 数据面板
  if(scene==='SWING'||scene==='ENERGY'){
    var px=20,py=20,pw=185,ph=140;
    ctx.fillStyle='rgba(10,15,25,0.78)';
    rc(ctx,px,py,pw,ph,8);ctx.fill();
    ctx.fillStyle='#94a3b8';ctx.font='11px sans-serif';ctx.textAlign='left';ctx.textBaseline='top';
    ctx.fillText('■ 实时物理量',px+12,py+8);
    var its=[{l:'角度 θ',v:(Math.abs(theta)*180/Math.PI).toFixed(1)+'°',c:'#fbbf24'},{l:'速度 v',v:v.toFixed(2)+' m/s',c:'#60a5fa'},{l:'动能 Ek',v:Ek.toFixed(3)+' J',c:'#34d399'},{l:'重力势能',v:Ep_g.toFixed(3)+' J',c:'#f97316'},{l:'电势能',v:Ep_e.toFixed(3)+' J',c:'#3b82f6'},{l:'总能量',v:Etot.toFixed(3)+' J',c:'#a78bfa'}];
    for(var ii=0;ii<its.length;ii++){
      var y2=py+30+ii*18;
      ctx.fillStyle='#64748b';ctx.font='11px sans-serif';ctx.textAlign='left';ctx.textBaseline='middle';
      ctx.fillText(its[ii].l,px+14,y2);
      ctx.fillStyle=its[ii].c;ctx.textAlign='right';
      ctx.fillText(its[ii].v,px+pw-10,y2);
    }
  }

  // 能量条
  if(scene==='ENERGY'){
    var K=Math.max(0.001,Ek),Pg=Math.max(0.001,Ep_g),Pe2=Math.max(0.001,Math.abs(Ep_e));
    var ttl=K+Pg+Pe2;
    var bx2=30,by2=H-60,bw2=W-60,bh2=14;
    ctx.fillStyle='rgba(50,60,80,0.3)';
    rc(ctx,bx2,by2,bw2,bh2,7);ctx.fill();
    if(ttl>0){
      var eW=(Pe2/ttl)*bw2,kW=(K/ttl)*bw2,gW=(Pg/ttl)*bw2;
      ctx.fillStyle='#3b82f6';rc(ctx,bx2,by2,Math.max(eW,3),bh2,7);ctx.fill();
      ctx.fillStyle='#34d399';ctx.fillRect(bx2+eW,by2,Math.max(kW,3),bh2);
      ctx.fillStyle='#f97316';rc(ctx,bx2+eW+kW,by2,Math.max(gW,3),bh2,7);ctx.fill();
      ctx.fillStyle='rgba(255,255,255,0.35)';ctx.font='10px sans-serif';ctx.textAlign='left';ctx.textBaseline='bottom';
      ctx.fillText('⚡电势',bx2+6,by2-4);ctx.textAlign='center';ctx.fillText('动能',bx2+eW+kW/2,by2-4);
      ctx.textAlign='right';ctx.fillText('重力势',bx2+bw2-6,by2-4);
      ctx.fillStyle='rgba(255,255,255,0.15)';ctx.font='10px sans-serif';ctx.textAlign='center';ctx.textBaseline='top';
      ctx.fillText('E总 = '+Etot.toFixed(3)+' J（守恒）',bx2+bw2/2,by2+bh2+6);
    }
  }

    // 解题过程（简化版）
  if(scene==='SOLUTION'){
    var SF=frame-(I4-Math.floor(total*0.10));
    var steps=['已知：m=0.1kg, q=5×10⁻⁴C, E=2×10³N/C, L=1.0m, g=10m/s²','电场力：F电 = qE = 1.0 N','重力：G = mg = 1.0 N','动能定理：W电+W重=½mv²','代入 θ=37°：v²=2×(0.6+0.2)/0.1=16'];
    var px2=80,py2=100,pw2=W-160;
    ctx.fillStyle='rgba(0,0,0,0.3)';ctx.fillRect(0,0,W,H);
    ctx.fillStyle='rgba(10,15,25,0.88)';rc(ctx,px2,py2,pw2,380,12);ctx.fill();
    ctx.fillStyle='#e2e8f0';ctx.font='bold 20px sans-serif';ctx.textAlign='center';ctx.textBaseline='top';
    ctx.fillText('解题过程',px2+pw2/2,py2+18);
    var vs=Math.min(Math.floor(SF/20)+1,steps.length);
    for(var si=0;si<vs;si++){
      var sy2=py2+56+si*38,op2=clamp((SF-si*20)/15,0,1);
      ctx.globalAlpha=op2;
      ctx.fillStyle='#64748b';ctx.font='bold 13px sans-serif';ctx.textAlign='left';ctx.textBaseline='top';
      ctx.fillText(String(si+1)+'.',px2+30,sy2);
      ctx.fillStyle='#cbd5e1';ctx.font='15px sans-serif';
      ctx.fillText(steps[si],px2+56,sy2);
    }
    var ans=clamp((SF-steps.length*20)/20,0,1);
    if(ans>0){
      ctx.globalAlpha=ans;
      ctx.fillStyle='#052e16';rc(ctx,px2+40,py2+270,pw2-80,60,10);ctx.fill();
      ctx.strokeStyle='#22c55e';ctx.lineWidth=2;rc(ctx,px2+40,py2+270,pw2-80,60,10);ctx.stroke();
      ctx.fillStyle='#22c55e';ctx.font='bold 22px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';
      ctx.fillText('答案：v = 4 m/s（当 θ=37° 时）',px2+pw2/2,py2+300);
    }
  }

  // 标题（快速淡入）
  if(scene==='INTRO'){
    var pr=clamp(frame/Math.floor(total*0.02),0,1);
    ctx.globalAlpha=Math.max(0,1-pr*2);
    ctx.fillStyle='#fff';ctx.font='bold 26px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText('电场中的带电单摆',CX,230);
    ctx.globalAlpha=1;
  }

  // 字幕// 字幕
  var ct='';
  if(scene==='INTRO'&&frame>total*0.03&&frame<total*0.12) ct=captions.intro||'';
  else if(scene==='FORCES'&&frame>total*0.17&&frame<total*0.27) ct=captions.forces||'';
  else if(scene==='SWING'&&frame>total*0.33&&frame<total*0.38) ct=captions.swing||'';
  else if(scene==='ENERGY'&&frame>total*0.68&&frame<total*0.73) ct=captions.energy||'';
  else if(scene==='SOLUTION') ct=captions.solution||'';
  else if(scene==='ENDING') ct=captions.ending||'';
  if(ct){
    var ta=scene==='SOLUTION'||scene==='ENDING'?1:0.9;
    ctx.globalAlpha=ta;
    ctx.fillStyle='rgba(0,0,0,0.5)';rc(ctx,W/2-300,H-50,600,36,8);ctx.fill();
    ctx.fillStyle='#fff';ctx.font='14px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(ct,W/2,H-32);
  }
}
/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/* 导出方式：优先挂到 window，否则尝试 CommonJS */
if (typeof window !== 'undefined') {
  window.Components = {
    drawCube: drawCube,
    drawBalance: drawBalance,
    drawSpringScale: drawSpringScale,
    drawTypewriterText: drawTypewriterText,
    drawPopupLabel: drawPopupLabel,
    drawStarField: drawStarField,
    drawEarthBackground: drawEarthBackground,
    drawMoonBackground: drawMoonBackground,
    drawSplitScreenDivider: drawSplitScreenDivider,
    drawMeteor: drawMeteor,
    drawForceArrow: drawForceArrow,
    drawFormulaBoard: drawFormulaBoard,
    drawOptionCard: drawOptionCard,
    drawTextBlock: drawTextBlock,
    drawPhysicsStage: drawPhysicsStage,
    drawPhysicsObject: drawPhysicsObject,
    drawPhysicsHUD: drawPhysicsHUD,
    drawPhaseLabel: drawPhaseLabel,
    drawPendulum: drawPendulum,
    drawElectricFieldBg: drawElectricFieldBg,
    drawElectricPendulum: drawElectricPendulum,
    drawSpringOscillator: drawSpringOscillator,
    drawInclinedPlane: drawInclinedPlane,
    drawCircuitComponent: drawCircuitComponent,
    drawGraph: drawGraph,
    drawLever: drawLever,
    drawContainer: drawContainer,
    drawLightRay: drawLightRay,
    drawCinematicElectricPendulum: drawCinematicElectricPendulum,
    sceneLabel: sceneLabel,
    floatUpText: floatUpText,
    flashLabel: flashLabel,
    distantEarth: distantEarth,
    staticLabel: staticLabel
  };
} else if (typeof module !== 'undefined') {
  module.exports = {
    drawCube: drawCube,
    drawBalance: drawBalance,
    drawSpringScale: drawSpringScale,
    drawTypewriterText: drawTypewriterText,
    drawPopupLabel: drawPopupLabel,
    drawStarField: drawStarField,
    drawEarthBackground: drawEarthBackground,
    drawMoonBackground: drawMoonBackground,
    drawSplitScreenDivider: drawSplitScreenDivider,
    drawMeteor: drawMeteor,
    sceneLabel: sceneLabel,
    floatUpText: floatUpText,
    flashLabel: flashLabel,
    distantEarth: distantEarth,
    staticLabel: staticLabel
  };
}
