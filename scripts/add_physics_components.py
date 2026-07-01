"""Add physics simulation components to components.js."""
import re

COMPONENTS_PATH = "D:/my_python_project/education_web/frontend/2d/js/components.js"

NEW_CODE = r"""

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
  var px = params.panelX || 730;
  var py = params.panelY || 60;
  var showEnergy = params.showEnergy || false;
  var opacity = resolveParam(params.opacity, frame, 1);
  ctx.globalAlpha = clamp(opacity, 0, 1);

  var idx = Math.min(frame, frames.length - 1);
  var d = frames[idx];
  if (!d) { ctx.restore(); return; }

  var panelH = showEnergy ? 220 : 160;
  ctx.fillStyle = 'rgba(15,25,35,0.85)';
  roundRectPath(ctx, px, py, 210, panelH, 8);
  ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 1;
  roundRectPath(ctx, px, py, 210, panelH, 8);
  ctx.stroke();

  ctx.fillStyle = '#94a3b8';
  ctx.font = '11px sans-serif';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'top';
  ctx.fillText('■ 实时数据 帧' + d.frame, px + 12, py + 8);

  // 阶段名
  var phaseNames = {'slope':'斜面加速','rough_surface':'粗糙面减速','horizontal_pull':'拉力加速'};
  var pn = phaseNames[d.phase] || d.phase;

  var items = [
    {label:'阶段', value:pn, color:'#f472b6'},
    {label:'位置', value:d.x.toFixed(2)+' m', color:'#fbbf24'},
    {label:'速度', value:d.v.toFixed(2)+' m/s', color:'#60a5fa'},
    {label:'加速度', value:d.a.toFixed(2)+' m/s²', color:'#a78bfa'},
  ];
  if (showEnergy) {
    items.push({label:'动能', value:d.Ek.toFixed(1)+' J', color:'#34d399'});
    items.push({label:'势能', value:d.Ep.toFixed(1)+' J', color:'#fbbf24'});
  }

  for (var ii = 0; ii < items.length; ii++) {
    var item = items[ii];
    var iy = py + 30 + ii * 24;
    ctx.fillStyle = '#64748b';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(item.label, px + 14, iy);
    ctx.fillStyle = item.color;
    ctx.textAlign = 'right';
    ctx.fillText(item.value, px + 198, iy);
  }

  if (showEnergy && (d.Ek > 0 || d.Ep > 0)) {
    var totalE = d.Ek + d.Ep;
    var barY = py + 170;
    var barW = 186;
    var barH = 12;
    ctx.fillStyle = 'rgba(50,60,80,0.5)';
    roundRectPath(ctx, px + 12, barY, barW, barH, 4);
    ctx.fill();
    if (totalE > 0) {
      var ekW = (d.Ek / totalE) * barW;
      ctx.fillStyle = '#34d399';
      roundRectPath(ctx, px + 12, barY, ekW, barH, 4);
      ctx.fill();
      ctx.fillStyle = '#fbbf24';
      roundRectPath(ctx, px + 12 + ekW, barY, (d.Ep/totalE)*barW, barH, 4);
      ctx.fill();
    }
    ctx.fillStyle = '#64748b';
    ctx.font = '9px sans-serif';
    ctx.textAlign = 'left'; ctx.textBaseline = 'bottom';
    ctx.fillText('动能', px + 14, barY - 2);
    ctx.textAlign = 'right';
    ctx.fillText('势能', px + 12 + barW, barY - 2);
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
"""

with open(COMPONENTS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

marker = '/* 导出方式：优先挂到 window，否则尝试 CommonJS */'
if marker in content:
    content = content.replace(marker, NEW_CODE + '\n' + marker, 1)
    with open(COMPONENTS_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Physics components added successfully")
else:
    print("ERROR: marker not found")
