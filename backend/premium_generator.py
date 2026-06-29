"""Premium HTML Generator - style-demo quality physics animation HTML"""
import math, json


def gen_ep_html(params):
    """Generate premium HTML for electric pendulum problems."""
    m = float(params.get("mass", 0.1))
    q = float(params.get("charge", 5e-4))
    Ef = float(params.get("electric_field", 2000))
    L = float(params.get("length", 1.0))
    g = float(params.get("g", 10))
    th0_deg = float(params.get("initial_angle_deg", 0))
    th0 = math.radians(th0_deg)

    Fe = q * Ef
    Fg = m * g
    Fr = math.sqrt(Fe*Fe + Fg*Fg)
    eq_deg = math.degrees(math.atan2(Fe, Fg))
    Wg = Fg * L * (1 - math.cos(th0))
    We = Fe * L * math.sin(th0)
    vA = math.sqrt(2 * (Wg + We) / m)
    Tmax = Fg + m * vA*vA / L
    dEp_e = -We
    dEp_g = -Wg

    def fmt(v):
        return f"{v:.4f}".rstrip('0').rstrip('.')

    V = {
        "Fe": fmt(Fe), "Fg": fmt(Fg), "Fr": fmt(Fr),
        "eq": f"{eq_deg:.1f}", "vA": fmt(vA),
        "dEp_e": fmt(dEp_e), "dEp_g": fmt(dEp_g),
        "Tmax": fmt(Tmax), "m": fmt(m),
        "q": fmt(q), "E": fmt(Ef), "L": fmt(L), "g": fmt(g),
        "th0": f"{th0_deg:.0f}",
    }

    # Generate physics frames
    frames = []
    dt = 1.0/60; ss = 8; th = th0; om = 0.0
    for _ in range(300):
        for _ in range(ss):
            a = -(g/L)*math.sin(th) + (Fe/(m*L))*math.cos(th)
            om += a * dt/ss
            th += om * dt/ss
        v = L*abs(om)
        Ek = 0.5*m*v*v
        Eg = Fg*L*(1-math.cos(th))
        Ee = -Fe*L*math.sin(th)
        frames.append({
            "theta": round(th, 5), "v": round(v, 4),
            "Ek": round(Ek, 4), "Ep_g": round(Eg, 4),
            "Ep_e": round(Ee, 4), "E_total": round(Ek+Eg+Ee, 4),
        })

    # Scene durations (seconds): F, S1, T1, W, S2, T2, E2(energy), S3, T3(tension), S4, END
    D = [7, 14, 2, 14, 14, 2, 10, 10, 10, 14, 8]
    tot = sum(D) * 60
    I = []; c = 0
    for d in D:
        c += d * 60
        I.append(c)

    def js(s):
        return json.dumps(s, ensure_ascii=False)

    sq1 = js([
        "Step 1: Electric force",
        f"Fe = qE = {V['q']} x {V['E']} = {V['Fe']} N", "",
        "Step 2: Gravity",
        f"G = mg = {V['m']} x {V['g']} = {V['Fg']} N", "",
        "Step 3: Resultant force",
        f"Fr = sqrt({V['Fe']}² + {V['Fg']}²) = {V['Fr']} N",
        f"Direction: alpha = {V['eq']} deg from vertical",
    ])
    sq2 = js([
        "Step 1: Initial to final position",
        f"From theta0 = {V['th0']} deg to bottom A (theta = 0)", "",
        "Step 2: Work by gravity",
        f"h = L(1-cos{V['th0']}) = {L*(1-math.cos(th0)):.3f} m",
        f"Wg = mgh = {Wg:.3f} J", "",
        "Step 3: Work by electric field",
        f"x = L sin{V['th0']} = {L*math.sin(th0):.3f} m",
        f"We = Fe x = {We:.3f} J", "",
        "Step 4: Kinetic energy theorem",
        f"W_total = {Wg+We:.3f} J",
        f"vA = sqrt(2*{Wg+We:.3f}/{m}) = {vA:.3f} m/s",
    ])
    sq3 = js([
        "第一步：电势能的变化",
        "电场力做正功 → 电势能减少",
        "ΔEp电 = −We = −qE·Δx",
        f"= −({Fe})×({L*math.sin(th0):.3f})",
        f"= {dEp_e:.3f} J（减少）", "",
        "第二步：重力势能的变化",
        "重力做正功 → 重力势能减少",
        "ΔEp重 = −Wg = −mg·Δh",
        f"= −({Fg})×({L*(1-math.cos(th0)):.3f})",
        f"= {dEp_g:.3f} J（减少）",
    ])
    sq4 = js([
        "第一步：确定拉力最大位置",
        "最低点 A 处速度大，且",
        "拉力需同时提供向心力和平衡重力",
        "→ 拉力在 A 点最大", "",
        "第二步：在最低点 A 受力分析",
        "沿细线方向：T − G = mv²/L",
        "（电场力水平，不贡献径向分量）", "",
        "第三步：代入数据",
        f"Tmax = G + mvA²/L",
        f"= {Fg:.1f} + {m}×{vA*vA:.3f}/{L}",
        f"= {Fg:.1f} + {m*vA*vA/L:.3f}",
        f"= {Tmax:.3f} N",
    ])

    phys = json.dumps({k: str(v) for k, v in V.items()}, ensure_ascii=False)
    time_str = f"{tot//3600:02d}:{tot//60%60:02d}"
    fr_json = json.dumps(frames)

    html = TEMPLATE
    for k, v_rep in [
        ("__F__", "60"), ("__T__", str(tot)),
        ("__TIME__", time_str), ("__FR__", fr_json),
        ("__SQ1__", sq1), ("__SQ2__", sq2),
        ("__SQ3__", sq3), ("__SQ4__", sq4),
        ("__PH__", phys),
    ]:
        for i, iv in enumerate(I):
            html = html.replace(f"__I{i}__", str(iv))
        html = html.replace(k, v_rep)
    return html


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Electric Pendulum Solution</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0e17;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:"Microsoft YaHei","PingFang SC",sans-serif}
canvas{display:block;border-radius:12px}
#app{position:relative}
#controls{position:absolute;bottom:0;left:0;right:0;display:flex;align-items:center;gap:12px;padding:10px 20px;background:linear-gradient(transparent,rgba(0,0,0,0.8));opacity:0;transition:opacity .3s}
#app:hover #controls{opacity:1}
#controls button{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);color:#fff;width:34px;height:34px;border-radius:50%;cursor:pointer;font-size:14px}
#controls input[type=range]{flex:1;height:4px;-webkit-appearance:none;appearance:none;background:rgba(255,255,255,0.15);border-radius:2px;outline:none}
#controls input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;border-radius:50%;background:#f6d365;cursor:pointer}
#time-display{color:rgba(255,255,255,0.5);font-size:12px;min-width:80px;text-align:right;font-variant-numeric:tabular-nums}
</style>
</head>
<body>
<div id="app">
<canvas id="c" width="960" height="640"></canvas>
<div id="controls">
<button id="playBtn">&#9654;</button>
<input type="range" id="seekBar" min="0" max="100" value="0">
<span id="time-display">00:00 / __TIME__</span>
</div>
</div>
<script>
var c=document.getElementById('c'),ctx=c.getContext('2d');
var W=960,H=640,CX=480,CY=130,LP=130,BR=18;
var F=__F__,T=__T__;
var P=__PH__;
var I0=__I0__,I1=__I1__,I2=__I2__,I3=__I3__,I4=__I4__,I5=__I5__,I6=__I6__,I7=__I7__,I8=__I8__,I9=__I9__,I10=__I10__;
function gs(f){if(f<I0)return'F';if(f<I1)return'S1';if(f<I2)return'T1';if(f<I3)return'W';if(f<I4)return'S2';if(f<I5)return'T2';if(f<I6)return'E2';if(f<I7)return'S3';if(f<I8)return'T3';if(f<I9)return'S4';if(f<I10)return'E5';return'E'}
var FR=__FR__;
function gp(f){if(f>=I2&&f<I3){var p=(f-I2)/(I3-I2);if(p<0)p=0;if(p>1)p=1;var fi=Math.min(Math.floor(p*FR.length),FR.length-1)}else if(f>=I6&&f<I7){var p=(f-I6)/(I7-I6);if(p<0)p=0;if(p>1)p=1;var fi=Math.min(Math.floor(p*FR.length),FR.length-1)}else if(f>=I8&&f<I9){var p=(f-I8)/(I9-I8);if(p<0)p=0;if(p>1)p=1;var fi=Math.min(Math.floor(p*FR.length),FR.length-1)}else var fi=0;return FR[fi]||{}}
var SQ1=__SQ1__,SQ2=__SQ2__,SQ3=__SQ3__,SQ4=__SQ4__;
function cv(v,l,h){return Math.max(l,Math.min(h,v))}
function rc(x,y,w,h,r){if(r>w/2)r=w/2;if(r>h/2)r=h/2;ctx.beginPath();ctx.moveTo(x+r,y);ctx.lineTo(x+w-r,y);ctx.arcTo(x+w,y,x+w,y+r,r);ctx.lineTo(x+w,y+h-r);ctx.arcTo(x+w,y+h,x+w-r,y+h,r);ctx.lineTo(x+r,y+h);ctx.arcTo(x,y+h,x,y+h-r,r);ctx.lineTo(x,y+r);ctx.arcTo(x,y,x+r,y,r);ctx.closePath()}
function da(x1,y1,x2,y2,cl){var a=Math.atan2(y2-y1,x2-x1);ctx.strokeStyle=cl;ctx.lineWidth=2.5;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();ctx.fillStyle=cl;ctx.beginPath();ctx.moveTo(x2,y2);ctx.lineTo(x2-10*Math.cos(a-0.5),y2-10*Math.sin(a-0.5));ctx.lineTo(x2-10*Math.cos(a+0.5),y2+10*Math.sin(a+0.5));ctx.closePath();ctx.fill()}
var fm=0,pl=false;
function rd(){
  ctx.clearRect(0,0,W,H);
  var sc=gs(fm),ph=gp(fm);
  var th=animScenes?(ph.theta||0):0,bx=CX+LP*Math.sin(th),by=CY+LP*Math.cos(th);
  var sp=(sc==='F'||sc==='W'||sc==='E2'||sc==='T3');
  var animScenes=(sc==='W'||sc==='E2'||sc==='T3');
  var gd=ctx.createRadialGradient(W/2,H/2,0,W/2,H/2,W);gd.addColorStop(0,'#0f172a');gd.addColorStop(0.6,'#0a0e17');gd.addColorStop(1,'#060a0f');ctx.fillStyle=gd;ctx.fillRect(0,0,W,H);
  if(sc!=='E'){for(var y=40;y<by+30&&y<H-40;y+=50){ctx.strokeStyle='rgba(59,130,246,0.09)';ctx.lineWidth=1.2;ctx.setLineDash([6,10]);ctx.lineDashOffset=-fm*1.2;ctx.beginPath();ctx.moveTo(60,y);ctx.lineTo(W-60,y);ctx.stroke();ctx.setLineDash([]);ctx.lineDashOffset=0;for(var x=100;x<W-80;x+=70){var fx=x+((fm*1.5%30)<15?fm*1.5%30*1.5:(fm*1.5%30-30)*1.5);if(fx<60||fx>W-60)continue;ctx.fillStyle='rgba(59,130,246,0.1)';ctx.beginPath();ctx.moveTo(fx+10,y);ctx.lineTo(fx+2,y-4);ctx.lineTo(fx+2,y+4);ctx.closePath();ctx.fill()}}ctx.fillStyle='rgba(59,130,246,0.18)';ctx.font='bold 12px sans-serif';ctx.textAlign='right';ctx.textBaseline='top';ctx.fillText('E ->',W-60,42)}
  ctx.save();ctx.globalAlpha=0.08;ctx.strokeStyle='#94a3b8';ctx.lineWidth=1;ctx.setLineDash([4,6]);ctx.beginPath();ctx.arc(CX,CY,LP,0.15,Math.PI-0.15,false);ctx.stroke();ctx.setLineDash([]);ctx.restore();
  ctx.strokeStyle='rgba(71,85,105,0.5)';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(CX-100,CY);ctx.lineTo(CX+100,CY);ctx.stroke();ctx.fillStyle='#94a3b8';ctx.beginPath();ctx.arc(CX,CY,5,0,Math.PI*2);ctx.fill();
  ctx.strokeStyle='rgba(148,163,184,0.5)';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(CX,CY);ctx.lineTo(bx,by);ctx.stroke();
  if(Math.abs(th)>0.02&&sp){ctx.strokeStyle='rgba(255,255,255,0.2)';ctx.lineWidth=1;ctx.beginPath();ctx.arc(CX,CY,45,Math.PI/2,Math.PI/2-th,true);ctx.stroke();ctx.fillStyle='rgba(255,255,255,0.3)';ctx.font='bold 14px sans-serif';ctx.textAlign='center';ctx.fillText((Math.abs(th)*180/Math.PI).toFixed(1)+String.fromCharCode(176),CX+50*Math.cos(Math.PI/2-th/2),CY+50*Math.sin(Math.PI/2-th/2)+6)}
  var gl=ctx.createRadialGradient(bx,by,2,bx,by,BR*2);gl.addColorStop(0,'rgba(251,191,36,0.15)');gl.addColorStop(1,'rgba(251,191,36,0)');ctx.fillStyle=gl;ctx.beginPath();ctx.arc(bx,by,BR*2,0,Math.PI*2);ctx.fill();
  var bg2=ctx.createRadialGradient(bx-BR*0.3,by-BR*0.3,2,bx,by,BR);bg2.addColorStop(0,'#fcd34d');bg2.addColorStop(0.6,'#fbbf24');bg2.addColorStop(1,'#d97706');ctx.shadowColor='rgba(251,191,36,0.25)';ctx.shadowBlur=20;ctx.fillStyle=bg2;ctx.beginPath();ctx.arc(bx,by,BR,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
  ctx.fillStyle='rgba(255,255,255,0.3)';ctx.beginPath();ctx.arc(bx-BR*0.25,by-BR*0.25,BR*0.3,0,Math.PI*2);ctx.fill();ctx.fillStyle='#fff';ctx.font='bold 13px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('+',bx,by);
  if(sp){var al=50;da(bx,by,bx,by+al,'rgba(59,130,246,0.85)');ctx.fillStyle='#60a5fa';ctx.font='bold 13px sans-serif';ctx.textAlign='center';ctx.fillText('G',bx-16,by+al*0.5-4);da(bx,by,bx+al,by,'rgba(239,68,68,0.85)');ctx.fillStyle='#ef4444';ctx.fillText('Fe',bx+al*0.5,by-14);da(bx,by,bx+al*0.9,by+al*0.9,'rgba(249,115,22,0.85)');ctx.fillStyle='#fb923c';ctx.textAlign='left';ctx.fillText('Fr',bx+al*0.5+12,by+al*0.5-4)}
  if(sc==='W'&&ph.v>0.05){var va=th+Math.PI/2;da(bx,by,bx+ph.v*8*Math.cos(va),by+ph.v*8*Math.sin(va),'rgba(96,165,250,0.7)');ctx.fillStyle='#60a5fa';ctx.font='bold 12px sans-serif';ctx.textAlign='left';ctx.fillText('v='+ph.v.toFixed(2)+'m/s',bx+ph.v*8*Math.cos(va)+8,by+ph.v*8*Math.sin(va)-4)}
  if(sc==='W'){ctx.fillStyle='rgba(10,15,25,0.78)';rc(20,20,210,158,8);ctx.fill();ctx.fillStyle='#94a3b8';ctx.font='11px sans-serif';ctx.textAlign='left';ctx.textBaseline='top';ctx.fillText('\\u5b9e\\u65f6\\u6570\\u636e',32,28);var its=[['th',(Math.abs(th)*180/Math.PI).toFixed(1)+'\\u00b0','#fbbf24'],['v',(ph.v||0).toFixed(2)+'m/s','#60a5fa'],['Ek',(ph.Ek||0).toFixed(3)+'J','#34d399'],['Ep\\u91cd',(ph.Ep_g||0).toFixed(3)+'J','#f97316'],['Ep\\u7535',(ph.Ep_e||0).toFixed(3)+'J','#3b82f6'],['E\\u603b',(ph.E_total||0).toFixed(3)+'J','#a78bfa']];for(var ii=0;ii<its.length;ii++){var y2=50+ii*18;ctx.fillStyle='#64748b';ctx.font='11px sans-serif';ctx.textBaseline='middle';ctx.fillText(its[ii][0],34,y2);ctx.fillStyle=its[ii][2];ctx.textAlign='right';ctx.fillText(its[ii][1],220,y2)}}
  function dsp(st,sf,lb,cl){var df=fm-sf;ctx.fillStyle='rgba(0,0,0,0.3)';ctx.fillRect(0,0,W,H);ctx.fillStyle='rgba(10,15,25,0.88)';rc(50,50,W-100,550,12);ctx.fill();ctx.fillStyle=cl;ctx.font='bold 16px sans-serif';ctx.textAlign='center';ctx.textBaseline='top';ctx.fillText(lb,W/2,68);var fl=[];for(var si=0;si<st.length;si++){if(st[si]!=='')fl.push(st[si])}var v=Math.min(Math.floor(df/18)+1,fl.length);for(var si=0;si<v;si++){var sy=95+si*26,o2=cv((df-si*18)/14,0,1);ctx.globalAlpha=o2;if(si==0){ctx.fillStyle=cl;ctx.font='bold 13px sans-serif'}else{ctx.fillStyle='#cbd5e1';ctx.font='13px sans-serif'}ctx.textAlign='left';ctx.textBaseline='top';ctx.fillText(fl[si],70,sy)}ctx.globalAlpha=1}
  function dab(tx,cl,y){ctx.fillStyle='#052e16';rc(120,y,W-240,40,8);ctx.fill();ctx.strokeStyle='#22c55e';ctx.lineWidth=2;rc(120,y,W-240,40,8);ctx.stroke();ctx.fillStyle='#22c55e';ctx.font='bold 16px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(tx,W/2,y+20)}
  if(sc==='S1'){dsp(SQ1,I0,'Q1: \\u6c42\\u7535\\u573a\\u529b\\u548c\\u5408\\u529b','#93c5fd');var a1=cv((fm-I0-14*18)/18,0,1);if(a1>0){ctx.globalAlpha=a1;dab('Fe='+P.Fe+'N  Fr='+P.Fr+'N  \\u65b9\\u5411='+P.eq+String.fromCharCode(176),'#22c55e',520);ctx.globalAlpha=1}}
  if(sc==='S2'){dsp(SQ2,I3,'Q2: \\u6700\\u4f4e\\u70b9\\u901f\\u5ea6 vA','#86efac');var a2=cv((fm-I3-14*18)/18,0,1);if(a2>0){ctx.globalAlpha=a2;dab('vA = '+P.vA+' m/s','#22c55e',520);ctx.globalAlpha=1}}
  // E2: Energy visualization before Q3 solution
  if(sc==='E2'){if(sp){var al=50;da(bx,by,bx,by+al,'rgba(59,130,246,0.85)');ctx.fillStyle='#60a5fa';ctx.font='bold 13px sans-serif';ctx.textAlign='center';ctx.fillText('G',bx-16,by+al*0.5-4);da(bx,by,bx+al,by,'rgba(239,68,68,0.85)');ctx.fillStyle='#ef4444';ctx.fillText('Fe',bx+al*0.5,by-14)}ctx.fillStyle='rgba(10,15,25,0.78)';rc(20,20,230,176,8);ctx.fill();ctx.fillStyle='#94a3b8';ctx.font='11px sans-serif';ctx.textAlign='left';ctx.textBaseline='top';ctx.fillText('\\u80fd\\u91cf\\u6570\\u636e',32,28);var its=[['th',(Math.abs(th)*180/Math.PI).toFixed(1)+'d','#fbbf24'],['v',(ph.v||0).toFixed(2),'#60a5fa'],['Ek',(ph.Ek||0).toFixed(3)+'J','#34d399'],['Ep\\u91cd',(ph.Ep_g||0).toFixed(3)+'J','#f97316'],['Ep\\u7535',(ph.Ep_e||0).toFixed(3)+'J','#3b82f6'],['E\\u603b',(ph.E_total||0).toFixed(3)+'J','#a78bfa']];for(var ii=0;ii<its.length;ii++){var y2=50+ii*18;ctx.fillStyle='#64748b';ctx.font='11px sans-serif';ctx.textBaseline='middle';ctx.fillText(its[ii][0],34,y2);ctx.fillStyle=its[ii][2];ctx.textAlign='right';ctx.fillText(its[ii][1],220,y2)}
  ctx.fillStyle='rgba(249,115,22,0.12)';rc(30,30,280,36,8);ctx.fill();ctx.fillStyle='#f97316';ctx.font='bold 14px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('\\u89c2\\u5bdf\\uff1a\\u80fd\\u91cf\\u8f6c\\u5316\\u8fc7\\u7a0b',170,48);}
  // T3: Tension visualization before Q4 solution
  if(sc==='T3'){da(bx,by-70,bx,by,'rgba(168,85,247,0.85)');ctx.fillStyle='#d8b4fe';ctx.font='bold 14px sans-serif';ctx.textAlign='center';ctx.fillText('T',bx-14,by-35);ctx.fillStyle='#ea580c';ctx.font='bold 13px sans-serif';if(th<0.2){ctx.fillStyle='rgba(168,85,247,0.15)';rc(20,20,240,52,8);ctx.fill();ctx.fillStyle='#d8b4fe';ctx.font='bold 14px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('\\u6700\\u4f4e\\u70b9\\uff1aT - G = mv\\u00b2/L',140,46);}else{ctx.fillStyle='rgba(10,15,25,0.78)';rc(20,20,185,140,8);ctx.fill();ctx.fillStyle='#94a3b8';ctx.font='11px sans-serif';ctx.textAlign='left';ctx.textBaseline='top';ctx.fillText('\\u6446\\u52a8\\u8fc7\\u7a0b',32,28);var its2=[['th',(Math.abs(th)*180/Math.PI).toFixed(1)+'d','#fbbf24'],['v',(ph.v||0).toFixed(2),'#60a5fa'],['Ek',(ph.Ek||0).toFixed(3)+'J','#34d399']];for(var ii=0;ii<its2.length;ii++){var y2=50+ii*18;ctx.fillStyle='#64748b';ctx.font='11px sans-serif';ctx.textBaseline='middle';ctx.fillText(its2[ii][0],34,y2);ctx.fillStyle=its2[ii][2];ctx.textAlign='right';ctx.fillText(its2[ii][1],195,y2)}}
  ctx.fillStyle='rgba(168,85,247,0.12)';rc(W-310,30,280,36,8);ctx.fill();ctx.fillStyle='#d8b4fe';ctx.font='bold 14px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('\\u7b2c(4)\\u95ee\\uff1a\\u6c42\\u7ec6\\u7ebf\\u62c9\\u529b T',W-170,48);}
  // S3: Q3 solution
  if(sc==='S3'){dsp(SQ3,I7,'Q3: \\u7535\\u52bf\\u80fd\\u548c\\u91cd\\u529b\\u52bf\\u80fd\\u53d8\\u5316','#f97316');var a3=cv((fm-I7-12*18)/18,0,1);if(a3>0){ctx.globalAlpha=a3;dab('\\u0394Ep\\u7535='+P.dEp_e+'J  \\u0394Ep\\u91cd='+P.dEp_g+'J','#22c55e',520);ctx.globalAlpha=1}}
  // S4: Q4 solution
  if(sc==='S4'){dsp(SQ4,I9,'Q4: \\u7ec6\\u7ebf\\u6700\\u5927\\u62c9\\u529b Tmax','#d8b4fe');var a4=cv((fm-I9-14*18)/18,0,1);if(a4>0){ctx.globalAlpha=a4;dab('Tmax = '+P.Tmax+' N','#22c55e',520);ctx.globalAlpha=1}}
  if(sc==='T1'){var tr=cv((fm-I2)/40,0,1);ctx.globalAlpha=tr<0.5?tr*2:(1-(tr-0.5)*2);ctx.fillStyle='rgba(0,0,0,0.4)';ctx.fillRect(0,0,W,H);ctx.fillStyle='#e2e8f0';ctx.font='bold 22px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('\\u7b2c(2)\\u95ee\\uff1a\\u6c42\\u6700\\u4f4e\\u70b9\\u901f\\u5ea6 vA',W/2,320);ctx.fillStyle='#94a3b8';ctx.font='15px sans-serif';ctx.fillText('\\u89c2\\u5bdf\\u6446\\u7403\\u4ece 60\\u00b0 \\u6446\\u52a8\\u5230\\u6700\\u4f4e\\u70b9\\u7684\\u8fc7\\u7a0b',W/2,360);ctx.globalAlpha=1}
  if(sc==='T2'){var tr=cv((fm-I5)/40,0,1);ctx.globalAlpha=tr<0.5?tr*2:(1-(tr-0.5)*2);ctx.fillStyle='rgba(0,0,0,0.4)';ctx.fillRect(0,0,W,H);ctx.fillStyle='#e2e8f0';ctx.font='bold 22px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('\\u7b2c(3)\\u95ee\\uff1a\\u80fd\\u91cf\\u53d8\\u5316',W/2,320);ctx.fillStyle='#94a3b8';ctx.font='15px sans-serif';ctx.fillText('\\u89c2\\u5bdf\\u80fd\\u91cf\\u6570\\u636e\\u7684\\u53d8\\u5316',W/2,360);ctx.globalAlpha=1}
  if(sc==='E'){ctx.fillStyle='rgba(0,0,0,0.35)';ctx.fillRect(0,0,W,H);ctx.fillStyle='rgba(10,15,25,0.9)';rc(120,100,W-240,440,16);ctx.fill();ctx.fillStyle='#e2e8f0';ctx.font='bold 22px sans-serif';ctx.textAlign='center';ctx.textBaseline='top';ctx.fillText('\\u7b54\\u6848\\u6c47\\u603b',W/2,120);var sd=[['(1) \\u7535\\u573a\\u529b','Fe='+P.Fe+'N'],['(1) \\u5408\\u529b','Fr='+P.Fr+'N \\u65b9\\u5411='+P.eq+String.fromCharCode(176)],['(2) \\u6700\\u4f4e\\u70b9\\u901f\\u5ea6','vA='+P.vA+'m/s'],['(3) \\u7535\\u52bf\\u80fd\\u53d8','\\u0394Ep\\u7535='+P.dEp_e+'J'],['(3) \\u91cd\\u529b\\u52bf\\u80fd\\u53d8','\\u0394Ep\\u91cd='+P.dEp_g+'J'],['(4) \\u6700\\u5927\\u62c9\\u529b','Tmax='+P.Tmax+'N']];for(var si=0;si<sd.length;si++){var sy=170+si*54;ctx.fillStyle='#94a3b8';ctx.font='15px sans-serif';ctx.textAlign='left';ctx.textBaseline='top';ctx.fillText(sd[si][0],W/2-180,sy);ctx.fillStyle='#22c55e';ctx.font='bold 18px sans-serif';ctx.textAlign='right';ctx.textBaseline='top';ctx.fillText(sd[si][1],W/2+180,sy)}}
  ctx.fillStyle='rgba(255,255,255,0.04)';ctx.font='12px sans-serif';ctx.textAlign='right';ctx.textBaseline='bottom';ctx.fillText('education_web',W-16,H-12);
}
var pb=document.getElementById('playBtn'),sb=document.getElementById('seekBar');
function tk(){if(pl){rd();fm++;if(fm>=T){fm=T;pl=false;pb.textContent='\\u21ba'}sb.value=(fm/T)*100;var cu=Math.floor(fm/F),tl=Math.floor(T/F);var f2=function(s){return(s<10?'0':'')+s};document.getElementById('time-display').textContent=f2(Math.floor(cu/60))+':'+f2(cu%60)+' / '+f2(Math.floor(tl/60))+':'+f2(tl%60)}requestAnimationFrame(tk)}
pb.addEventListener('click',function(){if(fm>=T){fm=0;pl=true;pb.textContent='\\u23f8';return}pl=!pl;pb.textContent=pl?'\\u23f8':'\\u25b6'});
sb.addEventListener('mousedown',function(){pl=false;pb.textContent='\\u25b6'});
sb.addEventListener('input',function(){fm=Math.round((this.value/100)*T);rd()});
document.addEventListener('keydown',function(e){if(e.code==='Space'){e.preventDefault();pb.click()}});
sb.value=0;tk();
</script>
</body>
</html>"""


def generate_premium_html(problem_type: str, params: dict) -> str:
    if problem_type == "electric_pendulum":
        return gen_ep_html(params)
    raise ValueError(f"Unsupported premium type: {problem_type}")
