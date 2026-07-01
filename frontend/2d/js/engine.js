/**
 * 时间轴渲染引擎
 *
 * 读取 JSON 编排文件，按时间轴调用 components.js 中的组件进行绘制。
 * 帧率稳定、二分查找、动画参数解析、过渡处理、暂停/恢复/跳转。
 */

/* ─── 工具函数 ─── */

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function clamp(val, min, max) {
  if (val < min) return min;
  if (val > max) return max;
  return val;
}

function easeOut(t) {
  return 1 - Math.pow(1 - t, 3);
}

function easeInOut(t) {
  if (t < 0.5) {
    return 4 * t * t * t;
  }
  return 1 - Math.pow(-2 * t + 2, 3) / 2;
}

function easeOutBack(t) {
  var c1 = 1.70158;
  var c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
}

/**
 * 将十六进制颜色字符串解析为 { r, g, b }。
 * 支持 #RGB 和 #RRGGBB 格式。
 */
function parseHexColor(color) {
  if (typeof color !== 'string') return { r: 255, g: 255, b: 255 };
  var hex = color.replace('#', '');
  if (hex.length === 3) {
    hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
  }
  return {
    r: parseInt(hex.slice(0, 2), 16) || 0,
    g: parseInt(hex.slice(2, 4), 16) || 0,
    b: parseInt(hex.slice(4, 6), 16) || 0
  };
}

/**
 * 将 { r, g, b } 对象格式化为 #RRGGBB 字符串。
 */
function rgbToHex(r, g, b) {
  var rr = clamp(Math.round(r), 0, 255).toString(16);
  var gg = clamp(Math.round(g), 0, 255).toString(16);
  var bb = clamp(Math.round(b), 0, 255).toString(16);
  return '#' + (rr.length < 2 ? '0' : '') + rr +
              (gg.length < 2 ? '0' : '') + gg +
              (bb.length < 2 ? '0' : '') + bb;
}

/**
 * 在两个颜色之间线性插值。
 */
function lerpColor(c1, c2, t) {
  var a = parseHexColor(c1);
  var b = parseHexColor(c2);
  return rgbToHex(lerp(a.r, b.r, t), lerp(a.g, b.g, t), lerp(a.b, b.b, t));
}

/* ─── 动画参数解析 ─── */

/**
 * 解析单个动画参数。
 *
 * @param {*} param - 原始参数值
 * @param {number} frame - 当前绝对帧号
 * @param {number} segStart - 所属片段的起始帧
 * @param {number} segEnd - 所属片段的结束帧
 * @returns {*} 解析后的实际值
 */
function resolveAnimatedParam(param, frame, segStart, segEnd) {
  // 基础类型直接返回
  if (param === null || param === undefined) return param;
  if (typeof param === 'number') return param;
  if (typeof param === 'string') return param;
  if (typeof param === 'boolean') return param;

  // 处理 { animate: { from, to, easing, duration, delay } }
  if (typeof param === 'object' && param.animate !== undefined) {
    var anim = param.animate;
    var from = anim.from;
    var to = anim.to;
    var duration = anim.duration || 30;
    var delay = anim.delay || 0;
    var easing = anim.easing || 'easeOut';

    var relativeFrame = frame - segStart - delay;

    if (relativeFrame < 0) {
      // 支持 fromColor / toColor 颜色插值
      if (anim.fromColor !== undefined) return anim.fromColor;
      return from;
    }

    var progress = clamp(relativeFrame / duration, 0, 1);
    var eased;

    if (easing === 'easeOut') {
      eased = easeOut(progress);
    } else if (easing === 'easeInOut') {
      eased = easeInOut(progress);
    } else if (easing === 'easeOutBack') {
      eased = easeOutBack(progress);
    } else if (easing === 'linear') {
      eased = progress;
    } else {
      eased = easeOut(progress);
    }

    // 颜色插值
    if (anim.fromColor !== undefined || anim.toColor !== undefined) {
      var cFrom = anim.fromColor || '#000000';
      var cTo = anim.toColor || '#ffffff';
      return lerpColor(cFrom, cTo, eased);
    }

    // 数值插值
    if (typeof from === 'number' && typeof to === 'number') {
      return lerp(from, to, eased);
    }

    return from;
  }

  // 处理 { type: 'sin', amplitude, period }
  if (typeof param === 'object' && param.type === 'sin') {
    var amp = param.amplitude || 0;
    var period = param.period || 60;
    var center = param.center !== undefined ? param.center : 0;
    var offset = param.offset || 0;
    return center + amp * Math.sin((frame + offset) * 2 * Math.PI / period);
  }

  return param;
}

/* ─── 二分查找片段 ─── */

/**
 * 在有序的 timeline 数组中二分查找当前帧所属的片段。
 * timeline 按 startFrame 升序排列。
 *
 * @param {number} frame - 当前帧
 * @param {Array} timeline - 片段数组 [{ startFrame, endFrame, ... }]
 * @returns {object|null} 匹配的片段，或 null
 */
function findSegment(frame, timeline) {
  if (!timeline || timeline.length === 0) return null;

  var lo = 0;
  var hi = timeline.length - 1;

  while (lo <= hi) {
    var mid = Math.floor((lo + hi) / 2);
    var seg = timeline[mid];

    if (frame < seg.startFrame) {
      hi = mid - 1;
    } else if (frame > seg.endFrame) {
      lo = mid + 1;
    } else {
      return seg;
    }
  }

  // 没有精确匹配。检查是否落在任意片段的 startFrame <= frame <= endFrame 范围内。
  // 由于二分查找在边界情况可能 miss，做一次相邻检查。
  for (var i = Math.max(0, lo - 1); i <= Math.min(hi + 1, timeline.length - 1); i++) {
    var s = timeline[i];
    if (frame >= s.startFrame && frame <= s.endFrame) {
      return s;
    }
  }

  return null;
}

/* ─── 背景绘制 ─── */

/**
 * 绘制背景层（如果有 background 字段）。
 * background 可以是字符串（纯色）或对象。
 */
function drawBackground(ctx, background, frame) {
  if (!background) return;

  if (typeof background === 'string') {
    ctx.fillStyle = background;
    ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    return;
  }

  // 如果是对象，查找对应的背景绘制函数
  if (typeof background === 'object') {
    if (background.type === 'color') {
      ctx.fillStyle = background.color || '#000000';
      ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
      return;
    }

    // 支持通过 component 字段指定背景组件
    if (background.component) {
      var bgFunc = window.Components[background.component];
      if (bgFunc) {
        var bgParams = background.params || {};
        ctx.save();
        bgFunc(ctx, bgParams, frame);
        ctx.restore();
        return;
      }
    }
  }
}

/* ─── 引擎主函数 ─── */

/**
 * 校验 timeline 数据结构的完整性。
 * 校验失败时 console.error 输出具体错误，不会抛异常。
 *
 * @param {object} timelineData
 * @returns {boolean} 是否通过校验
 */
function validateTimeline(timelineData) {
  var errors = [];
  var warnings = [];

  if (!timelineData || typeof timelineData !== 'object') {
    errors.push('timelineData 不是有效对象');
    logErrors(errors);
    return false;
  }

  var meta = timelineData.meta || {};
  var totalFrames = meta.totalFrames;
  var timeline = timelineData.timeline || [];

  // 1. meta.totalFrames
  if (!totalFrames || typeof totalFrames !== 'number' || totalFrames <= 0 || !Number.isInteger(totalFrames)) {
    errors.push('meta.totalFrames 必须为正整数，当前值: ' + JSON.stringify(totalFrames));
  }

  // 2. timeline 是数组
  if (!Array.isArray(timeline)) {
    errors.push('timeline 必须是数组');
    logErrors(errors);
    return false;
  }
  if (timeline.length === 0) {
    warnings.push('timeline 为空数组，没有可播放内容');
  }

  var frameMap = {}; // 用于检测重叠

  for (var si = 0; si < timeline.length; si++) {
    var seg = timeline[si];
    var idx = 'timeline[' + si + ']';

    if (!seg || typeof seg !== 'object') {
      errors.push(idx + ' 不是有效对象');
      continue;
    }

    var sf = seg.startFrame;
    var ef = seg.endFrame;

    // 3. startFrame / endFrame
    if (typeof sf !== 'number' || !Number.isFinite(sf)) {
      errors.push(idx + '.startFrame 不是有效数字');
    }
    if (typeof ef !== 'number' || !Number.isFinite(ef)) {
      errors.push(idx + '.endFrame 不是有效数字');
    }
    if (typeof sf === 'number' && typeof ef === 'number') {
      if (ef <= sf) {
        errors.push(idx + '.endFrame (' + ef + ') 必须大于 startFrame (' + sf + ')');
      }
      // 检测重叠
      for (var f = sf; f <= ef; f++) {
        if (frameMap[f]) {
          errors.push(idx + ' 帧 ' + f + ' 与 ' + frameMap[f] + ' 重叠');
          break;
        }
        frameMap[f] = idx;
      }
    }

    // 4. mode 字段（可选，兼容 explain 和 simulate）
    var isSimMode = seg.mode === 'simulate';

    // 4a. physics 字段（simulate 模式必需）
    if (isSimMode) {
      var physics = seg.physics;
      if (!physics || typeof physics !== 'object') {
        errors.push(idx + '.physics 字段缺失或格式错误（simulate 模式下必需）');
      } else if (!Array.isArray(physics.frames)) {
        errors.push(idx + '.physics.frames 必须是数组');
      } else if (physics.frames.length === 0) {
        warnings.push(idx + '.physics.frames 为空数组');
      }
    }

    // 4b. layers 格式（simulate 模式可选，explain 模式必需）
    var layers = seg.layers;
    if (layers !== undefined) {
      if (!Array.isArray(layers)) {
        errors.push(idx + '.layers 必须是数组');
      } else {
        for (var li = 0; li < layers.length; li++) {
          var layer = layers[li];
          if (!layer || typeof layer !== 'object') {
            errors.push(idx + '.layers[' + li + '] 不是有效对象');
            continue;
          }
          if (!layer.component || typeof layer.component !== 'string') {
            errors.push(idx + '.layers[' + li + '] 缺少 component 字段');
          } else {
            // 检查组件是否存在
            var compExists = (typeof window !== 'undefined' && window.Components && window.Components[layer.component]);
            if (!compExists) {
              warnings.push(idx + '.layers[' + li + '] 组件 "' + layer.component + '" 未在 Components 中找到');
            }
          }
          if (!layer.params || typeof layer.params !== 'object') {
            warnings.push(idx + '.layers[' + li + '] 缺少 params 对象');
          }
        }
      }
    }

    // 5. background
    var bg = seg.background;
    if (bg !== undefined) {
      if (typeof bg === 'object' && bg !== null && !Array.isArray(bg)) {
        if (bg.component && typeof window !== 'undefined' && window.Components) {
          if (!window.Components[bg.component]) {
            warnings.push(idx + '.background.component "' + bg.component + '" 未找到');
          }
        }
      }
    }
  }

  if (errors.length > 0) {
    logErrors(errors, 'ERROR');
  }
  if (warnings.length > 0) {
    logErrors(warnings, 'WARN');
  }

  return errors.length === 0;
}

function logErrors(items, level) {
  level = level || 'ERROR';
  var prefix = level === 'ERROR' ? '❌ [Timeline校验]' : '⚠️ [Timeline校验]';
  for (var i = 0; i < items.length; i++) {
    if (level === 'ERROR') {
      console.error(prefix, items[i]);
    } else {
      console.warn(prefix, items[i]);
    }
  }
}

/**
 * 启动时间轴渲染引擎。
 *
 * @param {string} canvasId - canvas 元素的 id
 * @param {object} timelineData - 时间轴编排数据
 * @param {object} [callbacks] - 可选回调
 * @param {function} [callbacks.onFrameUpdate] - 每帧更新后调用 (frame, totalFrames)
 * @param {function} [callbacks.onComplete] - 播放完成时调用
 * @param {function} [callbacks.onSegmentChange] - 片段切换时调用 (newSegment, prevSegment)
 * @returns {object} 控制接口 { pause, resume, seek, getCurrentFrame, getState, destroy }
 */
function startEngine(canvasId, timelineData, callbacks) {
  var canvas = document.getElementById(canvasId);
  if (!canvas) {
    throw new Error('Canvas element not found: ' + canvasId);
  }

  // 校验 timeline 数据
  var isValid = validateTimeline(timelineData);
  if (!isValid) {
    console.warn('[Engine] timeline 校验发现错误，尝试继续播放，但可能出现异常');
  }

  var ctx = canvas.getContext('2d');
  if (!ctx) {
    throw new Error('Failed to get 2D context');
  }

  // meta 信息
  var meta = timelineData.meta || {};
  var totalFrames = meta.totalFrames || 300;
  var fps = meta.fps || 60;
  var timeline = timelineData.timeline || [];

  // 如果 meta 指定了 canvas 尺寸，应用它
  if (meta.width) canvas.width = meta.width;
  if (meta.height) canvas.height = meta.height;

  // 引擎内部状态
  var currentFrame = 0;
  var isPaused = true;
  var isComplete = false;
  var accumulator = 0;
  var lastTime = 0;
  var animId = null;
  var frameDuration = 1000 / fps;
  var prevSegment = null;

  // 回调
  var onFrameUpdate = (callbacks && callbacks.onFrameUpdate) || null;
  var onComplete = (callbacks && callbacks.onComplete) || null;
  var onSegmentChange = (callbacks && callbacks.onSegmentChange) || null;

  /* ─── 单帧渲染 ─── */

  function renderFrame(frame) {
    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 二分查找当前帧对应的片段
    var segment = findSegment(frame, timeline);
    if (!segment) {
      // 没有匹配的片段，仍然触发回调
      if (onFrameUpdate) {
        onFrameUpdate(frame, totalFrames);
      }
      return;
    }

    // 片段切换回调
    if (segment !== prevSegment) {
      if (onSegmentChange) {
        onSegmentChange(segment, prevSegment);
      }
      prevSegment = segment;
    }

    // 绘制背景
    if (segment.background) {
      drawBackground(ctx, segment.background, frame);
    }

    // 计算全局透明度（过渡处理）
    var globalAlpha = 1;

    // transition_in：片段切入过渡
    if (segment.transition_in) {
      var tin = segment.transition_in;
      var tinDuration = tin.duration || 15;
      var tinEasing = tin.easing || 'easeOut';
      var relFrame = frame - segment.startFrame;
      var tinProgress = clamp(relFrame / tinDuration, 0, 1);
      if (tinEasing === 'easeOut') {
        globalAlpha = easeOut(tinProgress);
      } else if (tinEasing === 'easeInOut') {
        globalAlpha = easeInOut(tinProgress);
      } else if (tinEasing === 'linear') {
        globalAlpha = tinProgress;
      } else {
        globalAlpha = easeOut(tinProgress);
      }
    }

    // transition：片段末尾淡出（覆盖 transition_in）
    if (segment.transition) {
      var trans = segment.transition;
      var transDuration = trans.duration || 15;
      var transEasing = trans.easing || 'easeOut';
      var framesLeft = segment.endFrame - frame;
      if (framesLeft < transDuration) {
        var transProgress = 1 - clamp(framesLeft / transDuration, 0, 1);
        var transAlpha;
        if (transEasing === 'easeOut') {
          transAlpha = 1 - easeOut(transProgress);
        } else if (transEasing === 'easeInOut') {
          transAlpha = 1 - easeInOut(transProgress);
        } else if (transEasing === 'linear') {
          transAlpha = 1 - transProgress;
        } else {
          transAlpha = 1 - easeOut(transProgress);
        }
        globalAlpha = Math.min(globalAlpha, transAlpha);
      }
    }

    ctx.globalAlpha = clamp(globalAlpha, 0, 1);

    // 绘制所有层
    var layers = segment.layers || [];
    var isSimMode = segment.mode === 'simulate';
    var localFrame = frame - segment.startFrame;

    for (var li = 0; li < layers.length; li++) {
      var layer = layers[li];
      var componentName = layer.component;
      var rawParams = layer.params || {};
      var resolvedParams = {};

      // 解析每个参数
      for (var key in rawParams) {
        if (rawParams.hasOwnProperty(key)) {
          resolvedParams[key] = resolveAnimatedParam(rawParams[key], frame, segment.startFrame, segment.endFrame);
        }
      }

      // 🔬 双模式：simulate 片段注入物理帧数据
      if (isSimMode && segment.physics && segment.physics.frames) {
        resolvedParams.frames = segment.physics.frames;
      }

      var drawFunc = null;
      if (typeof window !== 'undefined' && window.Components) {
        drawFunc = window.Components[componentName];
      }

      if (drawFunc) {
        ctx.save();
        // simulate 模式下用局部帧索引（物理组件用 frames[localFrame]）
        var componentFrame = isSimMode ? localFrame : frame;
        drawFunc(ctx, resolvedParams, componentFrame);
        ctx.restore();
      }
    }

    ctx.globalAlpha = 1;

    // 调用帧回调
    if (onFrameUpdate) {
      onFrameUpdate(frame, totalFrames);
    }
  }

  /* ─── 帧循环 ─── */

  function tick(now) {
    if (isPaused || isComplete) {
      animId = null;
      return;
    }

    if (lastTime === 0) {
      lastTime = now;
      animId = requestAnimationFrame(tick);
      return;
    }

    var delta = now - lastTime;
    lastTime = now;

    // 限制最大步长防止卡顿时跳帧过多
    if (delta > 100) {
      delta = frameDuration;
    }

    accumulator += delta;

    // 按固定时间步长推进
    var framesAdvanced = 0;
    while (accumulator >= frameDuration) {
      accumulator -= frameDuration;
      currentFrame++;
      framesAdvanced++;

      if (currentFrame > totalFrames) {
        currentFrame = totalFrames;
        isComplete = true;
        isPaused = true;
        renderFrame(currentFrame);
        if (onComplete) {
          onComplete();
        }
        animId = null;
        return;
      }
    }

    renderFrame(currentFrame);

    animId = requestAnimationFrame(tick);
  }

  /* ─── 控制接口 ─── */

  /**
   * 暂停播放。
   * 如果已经暂停，不做任何事。
   */
  function pause() {
    if (isPaused) return;
    isPaused = true;
    if (animId !== null) {
      cancelAnimationFrame(animId);
      animId = null;
    }
  }

  /**
   * 恢复播放。
   * 如果已经播放或播放完毕，不做任何事。
   */
  function resume() {
    if (!isPaused) return;
    if (isComplete) return;
    isPaused = false;
    lastTime = 0;
    accumulator = 0;
    animId = requestAnimationFrame(tick);
  }

  /**
   * 跳转到指定帧。
   * 跳转后自动暂停。
   *
   * @param {number} targetFrame - 目标帧号
   */
  function seek(targetFrame) {
    // 如果正在播放，先停止动画循环
    if (animId !== null) {
      cancelAnimationFrame(animId);
      animId = null;
    }

    currentFrame = clamp(Math.round(targetFrame), 0, totalFrames);
    isPaused = true;
    isComplete = (currentFrame >= totalFrames);
    lastTime = 0;
    accumulator = 0;

    // 重置片段缓存以触发 onSegmentChange
    prevSegment = null;

    // 渲染目标帧
    renderFrame(currentFrame);
  }

  /**
   * 获取当前帧号。
   */
  function getCurrentFrame() {
    return currentFrame;
  }

  /**
   * 获取引擎当前状态。
   */
  function getState() {
    return {
      currentFrame: currentFrame,
      totalFrames: totalFrames,
      isPaused: isPaused,
      isComplete: isComplete,
      fps: fps
    };
  }

  /**
   * 销毁引擎，释放资源。
   */
  function destroy() {
    if (animId !== null) {
      cancelAnimationFrame(animId);
      animId = null;
    }
    isPaused = true;
    currentFrame = 0;
    isComplete = false;
    accumulator = 0;
    lastTime = 0;
    prevSegment = null;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }

  // 返回控制接口
  return {
    pause: pause,
    resume: resume,
    seek: seek,
    getCurrentFrame: getCurrentFrame,
    getState: getState,
    destroy: destroy
  };
}

/* ─── 导出 ─── */
if (typeof window !== 'undefined') {
  window.startEngine = startEngine;
}
if (typeof module !== 'undefined') {
  module.exports = { startEngine: startEngine };
}
