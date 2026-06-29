// player-core.js v1 — 物理动画模板公共框架
// 注入到模板 IIFE 内部，不包装自己的 IIFE

// ================================================================
//  0. 全局错误捕获
// ================================================================
window.onerror = function(msg,url,l,c,e){
  console.error('[FATAL]',msg,'at',l+':'+c);
  var h=document.getElementById('emptyHint');
  if(h){h.style.display='flex';h.textContent='⚠ '+msg+' (line '+l+')';}
};

// ================================================================
//  1. 帧控制器 FC
// ================================================================
const FC={
  frame:0,total:10800,fps:60,isPlay:false,isComp:false,
  _animId:null,_lastT:0,_slow:null,
  _onFrame:null,_onDone:null,_onPause:null,
  _effSpd(){
    let s=this.speed||1;
    if(this._slow&&this.frame>=this._slow[0]&&this.frame<this._slow[1])s*=this._slow[2];
    return s;
  },
  _loop(ts){
    if(!this._lastT)this._lastT=ts;
    const dt=ts-this._lastT;this._lastT=ts;
    if(this.isPlay){
      this.frame=Math.min(this.frame+(dt/1000)*this.fps*this._effSpd(),this.total-1);
      try{if(this._onFrame)this._onFrame(Math.floor(this.frame));}catch(e){console.error('[loop] onFrame err',e);}
      if(this.frame>=this.total-1){this.isPlay=false;this.isComp=true;if(this._onDone)this._onDone();}
    }
    this._animId=requestAnimationFrame(t=>this._loop(t));
  },
  start(){this._lastT=0;this._animId=requestAnimationFrame(t=>this._loop(t));},
  play(){this.isPlay=true;this.isComp=false;this._lastT=0;},
  pause(){this.isPlay=false;if(this._onPause)this._onPause();},
  toggle(){
    if(this.isComp){this.seek(0);this.play();}
    else if(this.isPlay)this.pause();
    else this.play();
  },
  seek(f){this.frame=Math.max(0,Math.min(f,this.total-1));this.isComp=false;try{if(this._onFrame)this._onFrame(Math.floor(this.frame));}catch(e){console.error('[loop] onFrame err',e);}},
  setSlow(a,b,c){this._slow=[a,b,c||.3]},
  clrSlow(){this._slow=null}
};

// ================================================================
//  2. 场景调度 SD
// ================================================================
const SD={
  cur:null,prev:null,
  get(f){
    const p=f/(FC.total||10800);
    for(let s of SCENES)if(p>=s.s&&p<s.e)return s.id;
    return'ending';
  },
  prog(f,id){
    const s=SCENES.find(x=>x.id===id);if(!s)return 0;
    const r=s.e-s.s;if(r<=0)return 1;
    return Math.min(1,Math.max(0,(f/(FC.total||10800)-s.s)/r));
  },
  def(id){return SCENES.find(x=>x.id===id);},
  update(f){
    this.prev=this.cur;this.cur=this.get(f);
    return{id:this.cur,changed:this.cur!==this.prev};
  }
};

// ================================================================
//  3. 解题面板 Panel
// ================================================================
const Panel={el:null,cur:null,_manual:false,_step:0,
_evalAll(h){return h.replace(/\$\{([^}]+)\}/g,function(m,k){try{return eval(k);}catch(e){console.warn('[eval]',k,e.message);return '['+k+']';}});},
init(){
  this.el=document.getElementById('panel');
  if(this.el)this.el.onclick=function(e){
    if(Panel._manual)Panel._stepClick();
  };
},
_stepClick(){
  if(!this._manual)return;
  var cnt=0;
  if(typeof SCENES!=='undefined'&&SCENES){
    var sc=SCENES.find(function(s){return s.id===Panel.cur;});
    if(sc&&sc.steps)cnt=sc.steps.items.length;
  }
  if(cnt>0&&this._step<cnt+1){this._step++;this._applyStep(cnt);}
  if(this._step>cnt&&this._manual)this._manual=false;
},
_applyStep(cnt){
  if(!this.el)return;
  for(var i=0;i<cnt;i++){var e=document.getElementById('ps_'+i);if(e)e.classList.toggle('visible',i<this._step);}
  var ae=document.getElementById('psa_');if(ae)ae.classList.toggle('visible',this._step>cnt);
},
renderSteps(sc){
  if(!sc||!sc.steps){if(this.el)this.el.classList.remove('visible');this.cur=null;return;}
  var h='<div class="panel-title">'+sc.steps.title+'</div>';
  sc.steps.items.forEach(function(it,i){h+='<div class="step-row" id="ps_'+i+'"><span class="step-badge">'+(i+1)+'</span><span>'+it+'</span></div>';});
  h+='<div class="answer-box" id="psa_"><span class="answer-text">'+sc.steps.answer+'</span></div>';
  this.el.innerHTML=h;
},
update(sid,prog,sc){
  if(!sc||!sc.steps){if(this.cur){if(this.el)this.el.classList.remove('visible');this.cur=null;}return;}
  if(sid!==this.cur){
    this._manual=sid.indexOf('sol_')===0;
    this._step=0;
    this.cur=sid;this.renderSteps(sc);if(this.el)this.el.classList.add('visible');
    for(var i=0;i<sc.steps.items.length;i++){var e=document.getElementById('ps_'+i);if(e){var txt=this._evalAll(e.innerHTML);e.innerHTML=_convertMath(txt);}}
    var ae=document.getElementById('psa_');if(ae)ae.innerHTML=this._evalAll(ae.innerHTML);
    _renderMath(this.el);
    // 解题场景：添加点击翻步、初始隐藏步骤
    if(this._manual && this.el){
      for(var ri=0;ri<sc.steps.items.length;ri++){
        var re=document.getElementById('ps_'+ri);
        if(re)re.onclick=function(e){e.stopPropagation();Panel._stepClick();};
      }
      var ae2=document.getElementById('psa_');
      if(ae2)ae2.onclick=function(e){e.stopPropagation();Panel._stepClick();};
    }
    this._applyStep(sc.steps.items.length);
  }
  if(!this._manual){
    // 自动模式：随进度渐显
    var cnt=sc.steps.items.length,vis=Math.min(Math.floor(prog/.85*cnt),cnt);
    for(var i=0;i<cnt;i++){var e=document.getElementById('ps_'+i);if(e)e.classList.toggle('visible',i<vis);}
    var ae=document.getElementById('psa_');if(ae)ae.classList.toggle('visible',prog>.85);
  }
}};

// ================================================================
//  4. 答案汇总 End
// ================================================================
const End={el:null,_inited:false,
  init(){
    this.el=document.getElementById('endingBg');
    var c=document.getElementById('endingAnswers');if(!c||this._inited)return;
    var items=[];
    for(var i=0;i<SCENES.length;i++){var s=SCENES[i];
      if(s.answerItems){
        s.answerItems.forEach(function(ai){var val=ai.replace(/\$\{([^}]+)\}/g,function(m,k){try{return eval(k);}catch(e){console.warn('[eval]',k,e.message);return '['+k+']';}});items.push('<div class="ending-item"><span class="l">'+(s.title||'')+'</span><span class="r">'+val+'</span></div>');});
      }
    }
    c.innerHTML=items.length?items.join(''):'暂无答案';this._inited=true;
  },
  update(id,prog,sc){
    if(id!=='ending'){if(this.el)this.el.classList.remove('visible');return}
    if(!this._inited)this.init();
    var a=Math.min(1,(prog||0)/.6);if(this.el){this.el.style.opacity=a;this.el.classList.add('visible');}
  }
};

// ================================================================
//  5. 已知量面板 KP
// ================================================================
const KP={el:null,_inited:false,
  init(content){
    if(this._inited)return;
    this.el=document.getElementById('knownPanel');
    if(!this.el)return;
    this._inited=true;
    if(content)this.el.innerHTML='<div class="known-title">■ 已知量</div>'+content;
  },
  update(id){this.init();if(this.el)this.el.classList.toggle('visible',id==='intro');}
};

// ================================================================
//  6. 控制栏 UI
// ================================================================
const UI={_ready:false,_navDots:null,_solScenes:[],
  _initNav(){
    this._solScenes=SCENES?SCENES.filter(function(s){return s.id&&s.id.indexOf('sol_')===0;}):[];
    if(this._solScenes.length<2)return;
    var nav=document.createElement('div');nav.style.cssText='display:flex;gap:6px;align-items:center;margin:0 4px;flex-shrink:0';
    for(var i=0;i<this._solScenes.length;i++){
      var dot=document.createElement('button');
      dot.style.cssText='width:8px;height:8px;border-radius:50%;border:1px solid rgba(255,255,255,.3);background:transparent;cursor:pointer;padding:0;transition:all .2s';
      dot.title=(i+1)+'. '+this._solScenes[i].title;
      dot.onclick=function(idx){return function(){FC.seek(UI._solScenes[idx].sf);UI.sync();};}(i);
      nav.appendChild(dot);
    }
    this._navDots=nav.children;
    // Insert after play button
    this.pb.parentNode.insertBefore(nav,this.pb.nextSibling);
  },
  init(){
    this.pb=document.getElementById('playBtn');this.rw=document.getElementById('rewindBtn');
    this.pr=document.getElementById('progressBar');this.pf=document.getElementById('progressFill');
    this.tl=document.getElementById('timeLabel');this.sp=document.getElementById('speedBtn');
    if(!this.pb||!this.pr)return;this._ready=true;
    this._initNav();
    this.pb.onclick=()=>{FC.toggle();this.upd()};this.rw.onclick=()=>{FC.seek(0);this.sync()};
    this.pr.onclick=e=>{var r=this.pr.getBoundingClientRect(),p=Math.max(0,Math.min((e.clientX-r.left)/r.width,1));FC.seek(Math.floor(p*FC.total));this.sync()};
    this.sp.onclick=()=>{var ss=[.5,1,1.5,2,3,4],ci=ss.indexOf(FC.speed);FC.speed=ss[(ci+1)%ss.length];this.sp.textContent=FC.speed+'×'};
    document.addEventListener('keydown',e=>{switch(e.code){case'Space':e.preventDefault();FC.toggle();this.upd();break;case'ArrowRight':FC.seek(FC.frame+5*FC.fps);this.sync();break;case'ArrowLeft':FC.seek(FC.frame-5*FC.fps);this.sync();break;case'KeyR':FC.seek(0);this.sync();break}});
  },
  upd(){if(!this._ready||!this.pb)return;if(FC.isComp)this.pb.textContent='↺';else if(FC.isPlay)this.pb.textContent='⏸';else this.pb.textContent='▶'},
  sync(){this.upd();this.updProg(FC.frame,FC.total)},
  updProg(f,t){
    if(!this._ready)return;
    if(this.pf)this.pf.style.width=Math.min((f/t)*100,100)+'%';
    if(this.tl){var cs=Math.floor(f/FC.fps),ts=Math.floor(t/FC.fps);this.tl.textContent=String(Math.floor(cs/60))+':'+String(cs%60).padStart(2,'0')+' / '+String(Math.floor(ts/60))+':'+String(ts%60).padStart(2,'0');}
    // 更新导航点高亮
    if(this._navDots&&this._navDots.length>0){
      var sid=SD?SD.cur:null;
      for(var di=0;di<this._navDots.length;di++){
        var sc=this._solScenes[di];
        if(sc&&sc.id===sid)this._navDots[di].style.background='rgba(255,255,255,.7)';
        else this._navDots[di].style.background='transparent';
      }
    }
  }
};

// ================================================================
//  7. 数学渲染工具
// ================================================================
var _renderMath = function(el){
  try{if(window.renderMathInElement)renderMathInElement(el,{delimiters:[{left:'$',right:'$',display:false}]});}catch(e){}
};
var _convertMath=function(t){
  if(!t)return t;
  if(/[√²³×θΔπα½≥≤≈]/.test(t)){
    return '$'+t+'$';
  }
  return t;
};

// ================================================================
//  8. 星星生成
// ================================================================
(function(){var e=document.getElementById('stars');if(!e)return;for(var i=0;i<60;i++){var s=document.createElement('div');s.className='star';s.style.left=Math.random()*100+'%';s.style.top=Math.random()*100+'%';s.style.setProperty('--d',(2+Math.random()*4)+'s');var sz=1+Math.random()*2;s.style.width=sz+'px';s.style.height=sz+'px';e.appendChild(s);}})();

// ================================================================
//  9. onFrame 主循环
// ================================================================
function onFrame(frame){
  const ref=SD.update(frame);
  const sceneId=ref.id,changed=ref.changed;
  const prog=SD.prog(frame,sceneId);
  const scene=SCENES.find(s=>s.id===sceneId);
  if(!scene)return;
  const st=scene.physics?scene.physics(prog):{};

  if(changed){
    KP.update(sceneId);
    if(scene.steps)FC.setSlow(scene.sf,scene.ef,.35);
    else FC.clrSlow();
  }

  try{R.render(scene,st,frame);}catch(e){console.error('[render]',e);}
  try{Panel.update(sceneId,prog,scene);}catch(e){console.error('[panel]',e);}
  try{End.update(sceneId,prog,scene);}catch(e){console.error('[end]',e);}
  UI.updProg(frame,FC.total);
}

// ================================================================
//  10. 启动
// ================================================================
FC._onFrame=onFrame;
FC._onDone=()=>{UI.upd()};

if(!SCENES||SCENES.length===0){
  console.error('[core] 场景列表为空');
  var h=document.getElementById('emptyHint');
  if(h)h.style.display='block';
}else{
  Panel.init();
  R.init(document.getElementById('mainCanvas'));
  UI.init();
  FC.start();
  FC.seek(0);
  UI.upd();
}


