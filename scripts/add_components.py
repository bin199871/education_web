"""Add 8 new physics components to components.js."""
import re

COMPONENTS_JS_PATH = "D:/my_project/education_web/frontend/components.js"

NEW_COMPONENTS = r"""

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
"""

# Read current components.js
with open(COMPONENTS_JS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Insert before the export section
marker = '/* 导出方式：优先挂到 window，否则尝试 CommonJS */'
if marker in content:
    content = content.replace(marker, NEW_COMPONENTS + '\n' + marker, 1)
    with open(COMPONENTS_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print("8 new components added successfully")
else:
    print("ERROR: Marker not found")
