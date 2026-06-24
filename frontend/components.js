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
