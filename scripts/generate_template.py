#!/usr/bin/env python3
"""物理讲解动画模板生成器

用法:
    python scripts/generate_template.py <template_id> <title> [选项]

示例:
    python scripts/generate_template.py spring_oscillator "弹簧振子" \\
      --params m,k,A,g
"""

import argparse
import os


def make_html(tid, title, params, defaults, units, goals):
    p = params
    d = defaults
    u = units
    n = len(p)

    defaults_js = ", ".join(f"{p[i]}:{d[i]}" for i in range(n))
    in_lines = "\n".join(f"      {p[i]}: _IN.{p[i]} ?? _DEFAULTS.{p[i]}," for i in range(n))
    known_rows = "".join(f'<div class="known-row">{p[i]} = ${{{p[i]}}} {u[i] if i < len(u) else ""}</div>' for i in range(n))
    goals_js = ", ".join(f"'{g}'" for g in goals)

    JS = r"""
const _DEFAULTS = { """ + defaults_js + r""" };
const _IN = (typeof __INJECTED_PARAMS__ !== 'undefined') ? __INJECTED_PARAMS__ : {};
const P = {
""" + in_lines + r"""
};
// TODO: 添加衍生计算 P.xxx = ...
const TOTAL = 10800, FPS = 60;
const _GOALS = _IN._goals || [""" + goals_js + r"""];
const _HAS = (g) => _GOALS.includes(g);

// ---- BRICKS 积木定义 ----
// TODO: 定义场景积木
const _BRICKS = {
  // intro:  { title:""" + repr(title) + r""", dur:.06, goals:[], layers:['bg','title','known'], physics:()=>({}) },
  // ending: { title:'答案总结', dur:.06, goals:[], layers:['bg','ending'] }
};

// ---- 编排引擎 ----
function composeScenes(goals) { return ['intro', 'ending']; }
function allocateTime(brickIds) {
  var td=0,i,b; for(i=0;i<brickIds.length;i++){b=_BRICKS[brickIds[i]];if(b)td+=b.dur;}
  var c=0,ss=[]; for(i=0;i<brickIds.length;i++){
    b=_BRICKS[brickIds[i]]; if(!b) continue;
    var w=b.dur/td; ss.push({id:brickIds[i], title:b.title, s:c, e:c+w,
      layers:b.layers, physics:b.physics, steps:b.steps, transIn:b.transIn, answerItems:b.answerItems});
    c+=w;
  } return ss;
}
var SCENES = allocateTime(composeScenes(_GOALS));
SCENES.forEach(function(s){s.sf=Math.floor(s.s*TOTAL); s.ef=Math.floor(s.e*TOTAL); s.dur=s.ef-s.sf});

// ---- Canvas 渲染器 ----
const R = { ctx:null,
  init(c){this.ctx=c.getContext('2d');},
  rc(x,y,w,h,r){var ctx=this.ctx; if(r>w/2)r=w/2; if(r>h/2)r=h/2;
    ctx.beginPath(); ctx.moveTo(x+r,y); ctx.lineTo(x+w-r,y); ctx.arcTo(x+w,y,x+w,y+r,r);
    ctx.lineTo(x+w,y+h-r); ctx.arcTo(x+w,y+h,x+w-r,y+h,r); ctx.lineTo(x+r,y+h);
    ctx.arcTo(x,y+h,x,y+h-r,r); ctx.lineTo(x,y+r); ctx.arcTo(x,y,x+r,y,r); ctx.closePath();},
  render(scene, st, frame){
    var ctx=this.ctx, layers=scene.layers||['bg'];
    ctx.clearRect(0,0,960,640);
    if(layers.includes('bg')){var g=ctx.createRadialGradient(480,320,0,480,320,500);
      g.addColorStop(0,'#0f172a'); g.addColorStop(.6,'#0a0e17'); g.addColorStop(1,'#060a0f');
      ctx.fillStyle=g; ctx.fillRect(0,0,960,640);}
    // TODO: 按 layers 绘制场景元素
    if(layers.includes('title')){var t=scene.title; if(t){ctx.save();
      ctx.font='bold 14px sans-serif'; ctx.fillStyle='rgba(10,15,25,.5)';
      this.rc(30,24,ctx.measureText(t).width+40,34,8); ctx.fill();
      ctx.fillStyle='#e2e8f0'; ctx.font='bold 14px sans-serif'; ctx.textAlign='center';
      ctx.textBaseline='middle'; ctx.fillText(t,480,41); ctx.restore();}}
    if(scene.transIn){var sp=(frame/TOTAL-scene.s)/(scene.e-scene.s);
      if(sp<.15){var a=sp<.075?sp*13.3:(1-(sp-.075)*13.3); ctx.save();
        ctx.globalAlpha=Math.min(a,1)*.4; ctx.fillStyle='#000'; ctx.fillRect(0,0,960,640);
        ctx.globalAlpha=1; ctx.fillStyle='#e2e8f0'; ctx.font='bold 20px sans-serif';
        ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText(scene.transIn,480,320);
        ctx.restore();}}}
  }
};

// ---- 帧控制器 ----
const FC={frame:0,total:TOTAL,fps:FPS,isPlay:false,speed:1,isComp:false,_animId:null,_lastT:0,_slow:null,
  _effSpd(){let s=this.speed; if(this._slow&&this.frame>=this._slow[0]&&this.frame<this._slow[1])s*=this._slow[2]; return s;},
  _loop(ts){if(!this._lastT)this._lastT=ts; var dt=ts-this._lastT; this._lastT=ts;
    if(this.isPlay){this.frame=Math.min(this.frame+(dt/1000)*this.fps*this._effSpd(),this.total-1);
      if(this._onFrame)this._onFrame(Math.floor(this.frame));
      if(this.frame>=this.total-1){this.isPlay=false; this.isComp=true; if(this._onDone)this._onDone();}}
    this._animId=requestAnimationFrame(t=>this._loop(t));},
  start(){this._lastT=0; this._animId=requestAnimationFrame(t=>this._loop(t));},
  play(){this.isPlay=true; this.isComp=false; this._lastT=0;},
  pause(){this.isPlay=false;},
  toggle(){if(this.isComp){this.seek(0); this.play();}else if(this.isPlay)this.pause();else this.play();},
  seek(f){this.frame=Math.max(0,Math.min(f,this.total-1)); this.isComp=false; if(this._onFrame)this._onFrame(Math.floor(this.frame));}
};
const SD={cur:null, get(f){var p=f/TOTAL; for(var s of SCENES)if(p>=s.s&&p<s.e)return s.id; return'ending';},
  prog(f,id){var s=SCENES.find(x=>x.id===id); if(!s)return 0; var r=s.e-s.s; return r<=0?1:Math.min(1,Math.max(0,(f/TOTAL-s.s)/r));},
  update(f){this.prev=this.cur; this.cur=this.get(f); return{id:this.cur, changed:this.cur!==this.prev};}
};

// ---- 解题面板 + KaTeX ----
var _convertMath=function(t){if(!t)return t;
  if(/[√²³×θΔπα½≥≤≈]/.test(t)){
    return '$'+t+'$';}return t;};
var _renderMath=function(el){if(window.renderMathInElement){
    try{renderMathInElement(el,{delimiters:[{left:'$',right:'$',display:false}]});}catch(e){}}};
const Panel={el:document.getElementById('panel'),cur:null,
  _evalAll(h){return h.replace(/\$\{([^}]+)\}/g,function(m,k){try{return eval(k);}catch(e){return '?';}});},
  renderSteps(sc){if(!sc.steps){this.el.classList.remove('visible');this.cur=null;return;}
    var h='<div class="panel-title">'+sc.steps.title+'</div>';
    sc.steps.items.forEach(function(it,i){h+='<div class="step-row" id="gs_'+i+'"><span class="step-badge">'+(i+1)+'</span><span>'+it+'</span></div>';});
    h+='<div class="answer-box" id="ga_"><span class="answer-text">'+sc.steps.answer+'</span></div>';
    this.el.innerHTML=h; _renderMath(this.el);},
  update(sid,prog,sc){if(!sc||!sc.steps){if(this.cur){this.el.classList.remove('visible');this.cur=null;}return;}
    if(sid!==this.cur){this.cur=sid; this.renderSteps(sc); this.el.classList.add('visible');
      for(var i=0;i<sc.steps.items.length;i++){var e=document.getElementById('gs_'+i); if(e)e.innerHTML=this._evalAll(e.innerHTML);}
      var ae=document.getElementById('ga_'); if(ae)ae.innerHTML=this._evalAll(ae.innerHTML);
      _renderMath(this.el);}
    var cnt=sc.steps.items.length, vis=Math.min(Math.floor(prog/.85*cnt),cnt);
    for(var i=0;i<cnt;i++){var e=document.getElementById('gs_'+i); if(e)e.classList.toggle('visible',i<vis);}
    var ae=document.getElementById('ga_'); if(ae)ae.classList.toggle('visible',prog>.85);}
};
const End={el:document.getElementById('endingBg'),_inited:false,
  init(){var c=document.getElementById('endingAnswers'); if(!c)return; var items=[];
    for(var i=0;i<SCENES.length;i++){var s=SCENES[i]; if(s.answerItems){s.answerItems.forEach(function(ai){items.push('<div class="ending-item"><span class="l">'+(s.title||'')+'</span><span class="r">'+ai+'</span></div>');});}}
    c.innerHTML=items.length?items.join(''):'No results';this._inited=true;},
  update(id,prog,sc){if(id!=='ending'){this.el.classList.remove('visible');return} if(!this._inited)this.init(sc);
    var a=Math.min(1,prog/.6); this.el.style.opacity=a; this.el.classList.add('visible');}
};
const KP={el:document.getElementById('knownPanel'),_inited:false,
  init(){if(this._inited)return; this._inited=true;
    this.el.innerHTML='<div class="known-title">Known</div>"""+known_rows+r"""';},
  update(id){this.init(); this.el.classList.toggle('visible',id==='intro');}
};
const UI={_ready:false,
  init(){this.pb=document.getElementById('playBtn');this.rw=document.getElementById('rewindBtn');
    this.pr=document.getElementById('progressBar');this.pf=document.getElementById('progressFill');
    this.tl=document.getElementById('timeLabel');this.sp=document.getElementById('speedBtn');
    if(!this.pb||!this.pr)return; this._ready=true;
    this.pb.onclick=()=>{FC.toggle();this.upd()}; this.rw.onclick=()=>{FC.seek(0);this.sync()};
    this.pr.onclick=e=>{var r=this.pr.getBoundingClientRect(),p=Math.max(0,Math.min((e.clientX-r.left)/r.width,1));FC.seek(Math.floor(p*TOTAL));this.sync()};
    this.sp.onclick=()=>{var ss=[.5,1,1.5,2],ci=ss.indexOf(FC.speed); FC.speed=ss[(ci+1)%ss.length];this.sp.textContent=FC.speed+'x'};
    document.addEventListener('keydown',e=>{switch(e.code){case'Space':e.preventDefault();FC.toggle();this.upd();break;
      case'ArrowRight':FC.seek(FC.frame+5*FPS);this.sync();break; case'ArrowLeft':FC.seek(FC.frame-5*FPS);this.sync();break;
      case'KeyR':FC.seek(0);this.sync();break}}});},
  upd(){if(!this._ready||!this.pb)return; if(FC.isComp)this.pb.textContent='R';else if(FC.isPlay)this.pb.textContent='||';else this.pb.textContent='>'},
  sync(){this.upd();this.updProg(FC.frame,TOTAL)},
  updProg(f,t){if(!this._ready)return; if(this.pf)this.pf.style.width=Math.min((f/t)*100,100)+'%';
    if(this.tl){var cs=Math.floor(f/FPS),ts=Math.floor(t/FPS); this.tl.textContent=String(Math.floor(cs/60))+':'+String(cs%60).padStart(2,'0')+'/'+String(Math.floor(ts/60))+':'+String(ts%60).padStart(2,'0');}}};
(function(){var e=document.getElementById('stars'); for(var i=0;i<60;i++){var s=document.createElement('div'); s.className='star';
  s.style.left=Math.random()*100+'%'; s.style.top=Math.random()*100+'%'; s.style.setProperty('--d',(2+Math.random()*4)+'s');
  var sz=1+Math.random()*2; s.style.width=sz+'px'; s.style.height=sz+'px'; e.appendChild(s);}})();
function onFrame(frame){var ref=SD.update(frame),sid=ref.id,chg=ref.changed,prog=SD.prog(frame,sid);
  var sc=SCENES.find(function(s){return s.id===sid;}); if(!sc)return;
  var st=sc.physics?sc.physics(prog):{};
  if(chg)KP.update(sid);
  R.render(sc,st,frame); Panel.update(sid,prog,sc); End.update(sid,prog,sc); UI.updProg(frame,TOTAL);}
FC._onFrame=onFrame; FC._onDone=()=>{UI.upd()};
R.init(document.getElementById('mainCanvas')); UI.init(); FC.start(); FC.seek(0); UI.upd();
})();"""

    return """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8">
<title>""" + title + """ - Physics</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0b0e1a;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Microsoft YaHei','PingFang SC',sans-serif}
.app{position:relative;width:960px;height:640px;border-radius:12px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.8)}
.stars{position:absolute;inset:0;pointer-events:none;z-index:0;overflow:hidden}
.star{position:absolute;border-radius:50%;background:#fff;animation:twinkle var(--d,3s) infinite alternate}
@keyframes twinkle{0%{opacity:.1}100%{opacity:.8}}
#mainCanvas{position:absolute;inset:0;z-index:1;width:100%;height:100%;display:block}
.known-panel{position:absolute;top:60px;left:20px;z-index:2;pointer-events:none;background:rgba(10,15,25,.75);border-radius:10px;padding:14px 16px;opacity:0;transition:opacity .6s ease;color:#cbd5e1;font-size:12px;line-height:1.8}
.known-panel.visible{opacity:1}.known-title{color:#94a3b8;font-size:11px;font-weight:700;margin-bottom:6px}
.solution-panel{position:absolute;right:0;top:50%;transform:translate(100%,-50%);z-index:4;width:270px;max-height:78%;padding:22px 18px;background:rgba(8,12,22,.92);backdrop-filter:blur(16px);border-left:1px solid rgba(255,255,255,.06);border-radius:14px 0 0 14px;overflow-y:auto;transition:transform .55s cubic-bezier(.23,1,.32,1)}
.solution-panel.visible{transform:translate(0,-50%)}.panel-title{font-size:14px;font-weight:700;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,.06);color:#93c5fd}
.step-row{opacity:0;transform:translateX(18px);transition:opacity .4s ease,transform .4s ease;margin-bottom:7px;font-size:13px;line-height:1.6;color:#cbd5e1;display:flex;align-items:flex-start;gap:6px}
.step-row.visible{opacity:1;transform:translateX(0)}
.step-badge{display:inline-flex;width:18px;height:18px;border-radius:50%;background:rgba(255,255,255,.07);align-items:center;justify-content:center;font-size:10px;color:#94a3b8;flex-shrink:0;margin-top:2px}
.answer-box{margin-top:12px;padding:10px 14px;border:1px solid rgba(34,197,94,.25);border-radius:8px;opacity:0;transition:opacity .5s ease,transform .5s cubic-bezier(.34,1.56,.64,1);transform:scale(.9);text-align:center}
.answer-box.visible{opacity:1;transform:scale(1);background:rgba(34,197,94,.08)}.answer-text{color:#22c55e;font-size:15px;font-weight:700}
.scene-overlay{position:absolute;top:20px;left:50%;transform:translateX(-50%);z-index:3;text-align:center;pointer-events:none}
.ending-bg{position:absolute;inset:0;z-index:5;display:flex;justify-content:center;align-items:center;background:rgba(0,0,0,.5);backdrop-filter:blur(8px);opacity:0;transition:opacity .8s ease;pointer-events:none}
.ending-bg.visible{opacity:1;pointer-events:auto}
.ending-card{background:rgba(10,15,25,.94);border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:30px 40px;width:460px;text-align:center;transform:scale(.92);transition:transform .6s cubic-bezier(.34,1.56,.64,1)}
.ending-bg.visible .ending-card{transform:scale(1)}.ending-card h2{color:#22c55e;font-size:22px;margin-bottom:22px}
.ending-item{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05)}
.ending-item:last-child{border-bottom:none}.ending-item .l{color:#94a3b8;font-size:15px}.ending-item .r{color:#22c55e;font-size:16px;font-weight:700}
.controls{position:absolute;bottom:16px;left:16px;right:16px;z-index:10;display:flex;align-items:center;gap:12px;padding:7px 16px;background:rgba(0,0,0,.6);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.04);border-radius:28px;opacity:0;transition:opacity .3s}
.app:hover .controls{opacity:1}
.controls button{background:none;border:none;color:#d0dfff;font-size:20px;width:34px;height:34px;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .2s;flex-shrink:0}
.controls button:hover{background:rgba(255,255,255,.07)}
.controls .spd{font-size:13px;font-weight:700;width:44px;color:#9aa9c9}
.progress-bar{flex:1;height:4px;background:#2a3a5a;border-radius:4px;cursor:pointer;position:relative;min-width:60px}
.progress-fill{height:100%;width:0%;background:linear-gradient(90deg,#f6d365,#fda085);border-radius:4px;transition:width .05s linear}
.time-label{color:#9aa9c9;font-size:12px;min-width:80px;text-align:center;font-variant-numeric:tabular-nums;flex-shrink:0}
</style>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
</head>
<body><div class="app" id="app">
<div class="stars" id="stars"></div>
<canvas id="mainCanvas" width="960" height="640"></canvas>
<div class="known-panel" id="knownPanel"><div class="known-title">Known</div></div>
<div class="solution-panel" id="panel"></div>
<div class="ending-bg" id="endingBg"><div class="ending-card"><h2>Answers</h2><div id="endingAnswers"></div></div></div>
<div class="controls" id="controls">
<button id="playBtn">></button><button id="rewindBtn">|</button>
<div class="progress-bar" id="progressBar"><div class="progress-fill" id="progressFill"></div></div>
<span class="time-label" id="timeLabel">0:00/0:00</span><button class="spd" id="speedBtn">1x</button>
</div></div>
<script>
(function(){
'use strict';""" + JS + r"""
</script></body></html>"""


def main():
    parser = argparse.ArgumentParser(description="Physics template generator")
    parser.add_argument("template_id", help="Template ID")
    parser.add_argument("title", help="Template title")
    parser.add_argument("--params", default="m,g", help="Parameters")
    parser.add_argument("--defaults", default="1,10", help="Defaults")
    parser.add_argument("--units", default="kg,m/s2", help="Units")
    parser.add_argument("--goals", default="", help="Goal types")
    parser.add_argument("--output", default=None, help="Output path")
    parser.add_argument("--no-write", action="store_true", help="Print only")
    args = parser.parse_args()

    params = [p.strip() for p in args.params.split(",")]
    defaults = [d.strip() for d in args.defaults.split(",")]
    units = [u.strip() for u in args.units.split(",")] if args.units else []
    goals = [g.strip() for g in args.goals.split(",")] if args.goals else []
    while len(defaults) < len(params): defaults.append("1")
    while len(units) < len(params): units.append("")

    html = make_html(args.template_id, args.title, params, defaults, units, goals)

    if args.no_write:
        print(html)
        return

    tdir = os.path.join(os.path.dirname(__file__), "..", "backend", "templates")
    out = args.output or os.path.join(tdir, f"{args.template_id}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK: {out} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
