"""Enterprise AI Workspace —— Streamlit 前端（Lithos 风格 hero：双层图像 + 聚光灯揭示 → 隧道转场 → 登录/注册 → 聊天）

与后端 rag_system/rag_app.py 配合：
  注册 → 登录 → 带 token 提问（省略句自动改写）→ 查历史
所有 API 请求由前端组件（CCv2）直接调用后端；后端已开 CORS。
"""
import streamlit as st

import os

API = os.getenv("API", "http://localhost:8000")   # FastAPI 后端地址（容器里由环境变量注入）
# ===== hero 双层背景图（Lithos 提示词指定，可替换为金融主题图） =====
BG_IMAGE_1 = "https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260609_195923_b0ba8ace-1d1d-4f2c-9a28-1ab84b330680.png&w=1280&q=85"
BG_IMAGE_2 = "https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260609_201152_bba90a12-bf12-459f-91f0-51f237dbaf3b.png&w=1280&q=85"


st.set_page_config(
    page_title="金融顾问 AI 工作台",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ===== 隐藏 Streamlit 原生外壳，让科幻风组件全屏接管 =====
PAGE_CSS = """<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@1,400;1,500;1,600&display=swap');
  #MainMenu, footer {visibility: hidden;}
  header[data-testid="stHeader"] {display: none;}
  .stApp, [data-testid="stAppViewContainer"] {background: #05070f;}
  .block-container, [data-testid="stMainBlockContainer"] {
    padding: 0 !important;
    max-width: 100% !important;
  }
  [data-testid="stToolbar"] {display: none;}
</style>"""
st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ===== 科幻风前端组件（CCv2，内联 HTML/CSS/JS） =====
_COMPONENT_HTML = f"""<div id="app-root">
  <canvas id="street"></canvas>
  <div id="glow"></div>
  <div id="scanline"></div>

  <div id="tunnel">
    <div class="ring"></div>
    <div class="ring" style="animation-delay:.05s"></div>
    <div class="ring" style="animation-delay:.10s"></div>
    <div class="ring" style="animation-delay:.15s"></div>
    <div class="ring" style="animation-delay:.20s"></div>
    <div class="ring" style="animation-delay:.25s"></div>
    <div class="ring" style="animation-delay:.30s"></div>
    <div class="ring" style="animation-delay:.35s"></div>
    <div class="ring" style="animation-delay:.40s"></div>
  </div>

  <div class="scene active" id="scene-landing">
    <div class="hero-base hero-zoom" style="background-image:url('{BG_IMAGE_1}')"></div>
    <div class="hero-reveal" id="hero-reveal" style="background-image:url('{BG_IMAGE_2}')"></div>
    <canvas id="spot-canvas"></canvas>

    <nav class="hero-nav">
      <div class="hn-left">
        <svg width="26" height="26" viewBox="0 0 256 256" fill="#ffffff" aria-hidden="true"><path d="M 256 256 L 128 256 L 0 128 L 128 128 Z M 256 128 L 128 128 L 0 0 L 128 0 Z"/></svg>
        <span class="hn-word">Financial AI</span>
      </div>
      <div class="hn-pill">
        <button class="hn-item active" id="hn-home">首页</button>
        <button class="hn-item" id="hn-login">登录</button>
        <button class="hn-item" id="hn-register">注册</button>
      </div>
      <button class="hn-signup" id="hn-signup">Sign Up</button>
      <button class="hn-burger" id="hn-burger" aria-label="菜单">
        <span></span><span></span><span></span>
      </button>
      <div class="hn-mobile" id="hn-mobile">
        <button class="hn-m-item active" id="hn-m-home">首页</button>
        <button class="hn-m-item" id="hn-m-login">登录</button>
        <button class="hn-m-item" id="hn-m-register">注册</button>
        <button class="hn-m-item" id="hn-m-signup">Sign Up</button>
      </div>
    </nav>

    <div class="hero-head">
      <div class="hero-brand hero-anim hero-fade" style="animation-delay:.15s">// FINANCIAL AI WORKSPACE</div>
      <h1>
        <span class="hero-line hero-anim hero-reveal-anim" style="animation-delay:.25s">Layers hold</span>
        <span class="hero-line2 hero-anim hero-reveal-anim" style="animation-delay:.42s">tales of time</span>
      </h1>
      <div class="hero-sub hero-anim hero-fade" style="animation-delay:.6s">金融顾问 AI 工作台 · RAG 知识库 · 混合检索 + Rerank · 引用溯源</div>
    </div>

    <div class="hero-left hero-anim hero-fade" style="animation-delay:.7s">
      <p>每一份财报、每一篇研报，都是市场的时间沉积。RAG 知识库把这些沉积层折叠成可检索的洞察，让 AI 替你解读。</p>
    </div>

    <div class="hero-right hero-anim hero-fade" style="animation-delay:.85s">
      <p>上传财报与研报，检索、溯源、生成金融建议——从原始数据到投资洞察，一步到位。</p>
      <div class="hero-btns">
        <button class="btn-hero" id="btn-login">开始咨询</button>
        <button class="btn-hero ghost" id="btn-register">注 册</button>
      </div>
    </div>
  </div>

  <div class="scene" id="scene-login">
    <div class="card">
      <h3>身 份 认 证</h3>
      <div class="msg-line" id="login-msg"></div>
      <div class="field"><label>用户名</label><input id="login-user" placeholder="username" autocomplete="username"></div>
      <div class="field"><label>密码</label><input id="login-pass" type="password" placeholder="password" autocomplete="current-password"></div>
      <button class="btn wide" id="btn-login-submit">登 录</button>
      <div class="hint">还没有账号？<span class="link" id="lnk-to-register">去注册</span></div>
    </div>
  </div>

  <div class="scene" id="scene-register">
    <div class="card">
      <h3>注 册 账 号</h3>
      <div class="msg-line" id="reg-msg"></div>
      <div class="field"><label>用户名</label><input id="reg-user" placeholder="username" autocomplete="username"></div>
      <div class="field"><label>密码</label><input id="reg-pass" type="password" placeholder="password" autocomplete="new-password"></div>
      <div class="field"><label>确认密码</label><input id="reg-pass2" type="password" placeholder="confirm password" autocomplete="new-password"></div>
      <button class="btn wide" id="btn-register-submit">注 册</button>
      <div class="hint">已有账号？<span class="link" id="lnk-to-login">去登录</span></div>
    </div>
  </div>

  <div class="chat" id="scene-chat">
    <div class="finance" id="fin-layer">
      <svg viewBox="0 0 900 600" preserveAspectRatio="xMidYMid slice">
        <defs><linearGradient id="fagrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00e5ff" stop-opacity=".5"/><stop offset="1" stop-color="#7c4dff" stop-opacity=".5"/></linearGradient></defs>
        <g stroke="#122238" stroke-opacity=".55" stroke-width="1"><path d="M0 80 H900 M0 160 H900 M0 240 H900 M0 320 H900 M0 400 H900 M0 480 H900 M0 560 H900"/><path d="M120 0 V600 M240 0 V600 M360 0 V600 M480 0 V600 M600 0 V600 M720 0 V600 M840 0 V600"/></g>
        <g stroke="#2ad" stroke-width="1.4" opacity=".9"><path d="M120 140 h70 v-30 h60 v50 h70 v-20 h60" fill="none"/><path d="M440 320 h70 v-40 h60 v60 h70 v-30 h60" fill="none"/><path d="M700 480 h70 v-25 h60 v45 h70 v-15 h60" fill="none"/></g>
        <g fill="#0f8" stroke="#0f8" stroke-width="1" opacity=".9"><rect x="195" y="105" width="16" height="38"/><rect x="255" y="120" width="16" height="50" fill="#f55" stroke="#f55"/><rect x="320" y="95" width="16" height="42"/><rect x="505" y="275" width="16" height="45"/><rect x="565" y="290" width="16" height="52" fill="#f55" stroke="#f55"/><rect x="630" y="265" width="16" height="40"/><rect x="775" y="450" width="16" height="30"/><rect x="835" y="440" width="16" height="55" fill="#f55" stroke="#f55"/></g>
        <path d="M40 380 L120 350 L200 300 L280 310 L360 240 L440 260 L520 190 L600 200 L680 150 L760 170 L840 110 L900 90" fill="none" stroke="url(#fagrad)" stroke-width="3"/>
        <g font-family="Consolas,sans-serif" fill="#ffd166" opacity=".95"><text x="40" y="30" font-size="20">宁德时代 · CATL</text><text x="40" y="56" font-size="13" fill="#8fb">营收 423,701,834 千元 ▲ 17.04%</text><text x="700" y="30" font-size="13" fill="#8fb">净利润 72,201,282 千元 ▲ 42.28%</text></g>
        <g font-family="Consolas,sans-serif" fill="#7fd" opacity=".9"><text x="40" y="430" font-size="12">PG · pgvector · HNSW</text><text x="40" y="452" font-size="12">BM25 + Rerank · RRF</text><text x="40" y="474" font-size="12">SQLite · JWT · FastAPI</text></g>
      </svg>
    </div>
    <div class="topbar">
      <div class="avatar" id="chat-avatar">D</div>
      <div>
        <div class="who" id="chat-who">金融顾问 AI</div>
        <div class="role">会话已加密 · RAG 检索中</div>
      </div>
      <div class="top-actions">
        <button class="mini" id="btn-clear">清空</button>
        <button class="mini" id="btn-logout">退出</button>
      </div>
    </div>
    <div class="msgs" id="msg-list"></div>
    <div class="inputbar">
      <input id="chat-input" placeholder="输入你的金融问题…" autocomplete="off">
      <div class="send" id="btn-send">发 送</div>
    </div>
  </div>
</div>"""

_COMPONENT_CSS = """#app-root{
  --cy:#00e5ff;--tx:#d6f3ff;--txd:#5f7f9f;
  position:fixed;inset:0;z-index:1000000;overflow:hidden;
  background:#05070f;color:var(--tx);
  font-family:'Inter',"Segoe UI","Microsoft YaHei",system-ui,sans-serif;
  transform-origin:center center;
}
#app-root *{box-sizing:border-box;margin:0;padding:0;}
#street{position:absolute;inset:0;width:100%;height:100%;z-index:1;transition:opacity .6s ease;}
#app-root.chatmode #street{opacity:0;}
#glow{position:absolute;width:320px;height:320px;border-radius:50%;background:radial-gradient(circle,rgba(255,240,180,.14),rgba(0,229,255,.08) 40%,transparent 70%);pointer-events:none;mix-blend-mode:screen;transform:translate(-50%,-50%);left:50%;top:50%;transition:left .1s linear,top .1s linear,opacity .5s;z-index:2;}
#app-root.chatmode #glow{opacity:0;}
#scanline{position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(255,255,255,.015) 0 1px,transparent 1px 3px);z-index:1;}
.scene{position:absolute;inset:0;display:none;flex-direction:column;align-items:center;justify-content:center;z-index:3;}
.scene.active{display:flex;}
.brand{font-size:14px;letter-spacing:6px;color:var(--cy);opacity:.9;text-shadow:0 0 18px rgba(0,229,255,.7);}
.title{font-size:42px;font-weight:200;letter-spacing:8px;margin:14px 0 6px;text-shadow:0 0 30px rgba(0,229,255,.25);}
.title b{font-weight:600;color:var(--cy);}
.subtitle{font-size:12px;letter-spacing:4px;color:var(--txd);}
.btn-row{display:flex;gap:20px;margin-top:40px;}
.btn{cursor:pointer;position:relative;overflow:hidden;padding:13px 44px;font-size:14px;letter-spacing:5px;color:var(--cy);background:rgba(0,229,255,.06);border:1px solid rgba(0,229,255,.55);border-radius:999px;transition:box-shadow .3s,background .3s,transform .2s;font-family:inherit;}
.btn:hover{box-shadow:0 0 26px rgba(0,229,255,.5),inset 0 0 18px rgba(0,229,255,.15);background:rgba(0,229,255,.14);transform:translateY(-2px);}
.btn:disabled{opacity:.5;cursor:wait;transform:none;}
.btn.ghost{background:rgba(255,255,255,.03);color:#9fd8ff;border-color:rgba(159,216,255,.35);}
.btn.ghost:hover{box-shadow:0 0 26px rgba(159,216,255,.35);background:rgba(159,216,255,.1);}
.btn.wide{width:100%;margin-top:10px;}
.btn::after{content:"";position:absolute;top:0;left:-80%;width:60%;height:100%;background:linear-gradient(105deg,transparent,rgba(255,255,255,.28),transparent);animation:sweep 2.8s linear infinite;}
@keyframes sweep{0%{left:-80%;}55%{left:130%;}100%{left:130%;}}
.card{width:330px;padding:34px 30px;background:rgba(6,12,26,.8);border:1px solid rgba(0,229,255,.3);border-radius:14px;backdrop-filter:blur(8px);box-shadow:0 0 40px rgba(0,229,255,.1);}
.card h3{font-size:16px;letter-spacing:5px;font-weight:400;color:var(--cy);margin-bottom:18px;text-align:center;}
.field{margin-bottom:16px;}
.field label{display:block;font-size:11px;letter-spacing:2px;color:var(--txd);margin-bottom:6px;}
.field input{width:100%;padding:11px 12px;background:rgba(255,255,255,.04);border:1px solid rgba(0,229,255,.25);border-radius:8px;color:var(--tx);font-size:13px;outline:none;transition:border .2s,box-shadow .2s;font-family:inherit;}
.field input:focus{border-color:var(--cy);box-shadow:0 0 14px rgba(0,229,255,.25);}
.msg-line{min-height:18px;font-size:12px;letter-spacing:1px;text-align:center;margin-bottom:12px;color:var(--txd);}
.msg-line.err{color:#ff6b7a;}
.msg-line.ok{color:#3df5a0;}
.hint{margin-top:14px;font-size:11px;letter-spacing:1px;color:var(--txd);text-align:center;}
.link{cursor:pointer;color:var(--cy);text-decoration:underline;text-underline-offset:3px;}
.chat{position:absolute;inset:0;display:none;flex-direction:column;z-index:3;}
.chat.active{display:flex;}
.finance{position:absolute;inset:0;opacity:0;pointer-events:none;z-index:0;background:radial-gradient(1200px 800px at 75% 20%,rgba(124,77,255,.16),transparent 60%),radial-gradient(900px 700px at 20% 80%,rgba(0,229,255,.10),transparent 55%),linear-gradient(160deg,#070b18 0%,#0a0f22 55%,#060a14 100%);}
.finance svg{position:absolute;inset:0;width:100%;height:100%;opacity:.85;}
.chat.active .finance{animation:finReveal 1.8s cubic-bezier(.3,.6,.3,1) forwards;}
@keyframes finReveal{0%{opacity:0;filter:blur(10px);transform:scale(1.06);}60%{opacity:.75;filter:blur(3px);}100%{opacity:1;filter:blur(0);transform:scale(1);}}
.topbar{display:flex;align-items:center;gap:12px;padding:14px 22px;border-bottom:1px solid rgba(0,229,255,.16);background:rgba(4,8,18,.6);backdrop-filter:blur(6px);z-index:2;}
.avatar{width:34px;height:34px;border-radius:50%;border:1px solid var(--cy);display:flex;align-items:center;justify-content:center;font-size:13px;color:var(--cy);box-shadow:0 0 12px rgba(0,229,255,.4);}
.who{font-size:13px;letter-spacing:2px;}
.role{font-size:10px;color:var(--txd);letter-spacing:1px;}
.top-actions{margin-left:auto;display:flex;gap:10px;}
.mini{cursor:pointer;padding:6px 16px;font-size:11px;letter-spacing:2px;color:#9fd8ff;background:rgba(0,229,255,.06);border:1px solid rgba(0,229,255,.35);border-radius:999px;font-family:inherit;}
.mini:hover{box-shadow:0 0 14px rgba(0,229,255,.35);}
.msgs{flex:1;overflow-y:auto;padding:22px 24px;display:flex;flex-direction:column;gap:16px;z-index:2;scrollbar-width:thin;scrollbar-color:rgba(0,229,255,.3) transparent;}
.m{max-width:80%;padding:12px 15px;border-radius:12px;font-size:13px;line-height:1.7;white-space:pre-wrap;word-break:break-word;}
.m.user{align-self:flex-end;background:rgba(0,229,255,.13);border:1px solid rgba(0,229,255,.4);}
.m.ai{align-self:flex-start;background:rgba(124,77,255,.13);border:1px solid rgba(124,77,255,.4);}
.m.system{align-self:center;max-width:92%;font-size:11px;color:#8fd8c8;background:rgba(124,77,255,.12);border:1px solid rgba(124,77,255,.3);text-align:center;}
.m .t{margin-top:6px;font-size:10px;color:var(--txd);letter-spacing:.5px;}
.src{margin-top:10px;font-size:10.5px;color:var(--txd);letter-spacing:.5px;}
.src summary{cursor:pointer;color:var(--cy);margin-top:5px;font-weight:400;list-style:none;}
.src summary::before{content:"▸ ";color:var(--cy);}
.src details[open] summary::before{content:"▾ ";}
.excerpt{margin:6px 0 4px 14px;line-height:1.6;color:#9fb8d8;white-space:pre-wrap;word-break:break-word;}
.dots{display:inline-flex;align-items:center;gap:4px;margin-right:6px;}
.dots i{width:5px;height:5px;border-radius:50%;background:var(--cy);animation:blink 1s infinite;}
.dots i:nth-child(2){animation-delay:.2s;}
.dots i:nth-child(3){animation-delay:.4s;}
@keyframes blink{0%,80%,100%{opacity:.25;}40%{opacity:1;}}
.inputbar{display:flex;gap:10px;padding:14px 22px;border-top:1px solid rgba(0,229,255,.16);background:rgba(4,8,18,.6);backdrop-filter:blur(6px);z-index:2;}
.inputbar input{flex:1;padding:12px 16px;background:rgba(255,255,255,.04);border:1px solid rgba(0,229,255,.25);border-radius:999px;color:var(--tx);font-size:13px;outline:none;font-family:inherit;}
.inputbar input:focus{border-color:var(--cy);box-shadow:0 0 14px rgba(0,229,255,.2);}
.send{cursor:pointer;padding:0 24px;border-radius:999px;border:1px solid rgba(0,229,255,.55);color:var(--cy);background:rgba(0,229,255,.08);font-size:12px;letter-spacing:3px;display:flex;align-items:center;}
.send:hover{box-shadow:0 0 18px rgba(0,229,255,.45);}
#tunnel{position:absolute;inset:0;pointer-events:none;z-index:60;display:none;overflow:hidden;}
#tunnel.go{display:block;}
.ring{position:absolute;left:50%;top:50%;width:40px;height:40px;margin:-20px;border:2px solid rgba(0,229,255,.85);border-radius:50%;opacity:0;box-shadow:0 0 18px rgba(0,229,255,.4);}
#tunnel.go .ring{animation:ringfly .78s cubic-bezier(.2,.6,.3,1) forwards;}
@keyframes ringfly{0%{transform:scale(.2);opacity:1;}100%{transform:scale(46);opacity:0;}}
.zoom-in{animation:zoomIn .42s ease-in forwards;}
@keyframes zoomIn{to{transform:scale(9);filter:blur(7px);opacity:.25;}}
.zoom-out{animation:zoomOut .72s cubic-bezier(.2,.7,.2,1) forwards;}
@keyframes zoomOut{from{transform:scale(9);filter:blur(7px);opacity:.25;}to{transform:scale(1);filter:blur(0);opacity:1;}}
  /* ===== Lithos 风格 hero（落地页） ===== */
  #scene-landing{overflow:hidden;background:#05070f;}
  .hero-base{position:absolute;inset:0;z-index:1;background-size:cover;background-position:center;background-repeat:no-repeat;}
  .hero-reveal{position:absolute;inset:0;z-index:2;background-size:cover;background-position:center;background-repeat:no-repeat;pointer-events:none;-webkit-mask-size:100% 100%;mask-size:100% 100%;}
  #spot-canvas{position:absolute;inset:0;pointer-events:none;display:none;}
  .hero-nav{position:absolute;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:16px 20px;}
  .hn-left{display:flex;align-items:center;gap:10px;}
  .hn-word{font-family:'Playfair Display',serif;font-style:italic;font-size:24px;color:#fff;}
  .hn-pill{position:absolute;left:50%;transform:translateX(-50%);display:none;align-items:center;gap:2px;background:rgba(255,255,255,.12);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.3);border-radius:999px;padding:4px;}
  .hn-item{background:transparent;border:none;color:rgba(255,255,255,.8);font-size:13px;font-weight:500;padding:8px 16px;border-radius:999px;cursor:pointer;font-family:inherit;transition:background .2s,color .2s;}
  .hn-item:hover{background:rgba(255,255,255,.2);color:#fff;}
  .hn-item.active{color:#fff;}
  .hn-signup{display:none;background:#fff;color:#111;font-size:13px;font-weight:600;padding:10px 22px;border:none;border-radius:999px;cursor:pointer;font-family:inherit;transition:background .2s,transform .15s;}
  .hn-signup:hover{background:#e8e8e8;}
  .hn-burger{display:flex;flex-direction:column;align-items:center;gap:5px;background:transparent;border:none;cursor:pointer;padding:8px;z-index:110;}
  .hn-burger span{width:22px;height:2px;background:#fff;border-radius:2px;transition:transform .25s,opacity .25s;}
  .hn-burger.open span:nth-child(1){transform:translateY(7px) rotate(45deg);}
  .hn-burger.open span:nth-child(2){opacity:0;}
  .hn-burger.open span:nth-child(3){transform:translateY(-7px) rotate(-45deg);}
  .hn-mobile{position:absolute;top:62px;right:16px;display:none;flex-direction:column;gap:4px;min-width:160px;padding:10px;background:rgba(8,12,24,.94);backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.25);border-radius:14px;box-shadow:0 18px 44px rgba(0,0,0,.5);z-index:110;}
  .hn-mobile.open{display:flex;}
  .hn-m-item{background:transparent;border:none;color:rgba(255,255,255,.85);font-size:13px;font-weight:500;text-align:left;padding:10px 14px;border-radius:10px;cursor:pointer;font-family:inherit;transition:background .2s,color .2s;}
  .hn-m-item:hover{background:rgba(255,255,255,.12);color:#fff;}
  .hn-m-item.active{color:#fff;background:rgba(232,112,42,.18);}
  @media(min-width:768px){.hn-pill{display:flex;}.hn-signup{display:block;}.hn-burger{display:none;}.hn-mobile{display:none!important;}}
  .hero-head{position:absolute;top:14%;left:0;right:0;z-index:50;display:flex;flex-direction:column;align-items:center;text-align:center;padding:0 20px;pointer-events:none;}
  .hero-brand{font-size:12px;letter-spacing:6px;color:rgba(255,255,255,.75);}
  .hero-head h1{color:#fff;line-height:.95;margin-top:16px;}
  .hero-line{display:block;font-family:'Playfair Display',serif;font-style:italic;font-weight:400;font-size:48px;letter-spacing:-.05em;}
  .hero-line2{display:block;font-weight:400;font-size:48px;letter-spacing:-.08em;margin-top:-4px;}
  @media(min-width:640px){.hero-line,.hero-line2{font-size:72px;}}
  @media(min-width:768px){.hero-line,.hero-line2{font-size:96px;}}
  .hero-sub{margin-top:22px;font-size:12px;letter-spacing:3px;color:rgba(255,255,255,.6);}
  .hero-left{position:absolute;left:40px;bottom:56px;max-width:260px;z-index:50;display:none;}
  @media(min-width:640px){.hero-left{display:block;}}
  @media(min-width:768px){.hero-left{left:56px;}}
  .hero-left p{font-size:14px;line-height:1.75;color:rgba(255,255,255,.8);}
  .hero-right{position:absolute;left:20px;right:20px;bottom:40px;z-index:50;display:flex;flex-direction:column;align-items:flex-start;gap:16px;}
  @media(min-width:640px){.hero-right{left:auto;right:40px;bottom:96px;max-width:260px;gap:20px;}}
  @media(min-width:768px){.hero-right{right:56px;}}
  .hero-right p{font-size:12px;line-height:1.75;color:rgba(255,255,255,.8);}
  @media(min-width:640px){.hero-right p{font-size:14px;}}
  .hero-btns{display:flex;gap:12px;flex-wrap:wrap;}
  .btn-hero{cursor:pointer;background:#e8702a;color:#fff;font-size:14px;font-weight:500;padding:12px 28px;border:none;border-radius:999px;transition:all .2s;font-family:inherit;}
  .btn-hero:hover{background:#d2611f;transform:scale(1.03);box-shadow:0 10px 24px rgba(232,112,42,.3);}
  .btn-hero:active{transform:scale(.95);}
  .btn-hero.ghost{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.4);color:#fff;}
  .btn-hero.ghost:hover{background:rgba(255,255,255,.18);box-shadow:none;transform:scale(1.03);}
  @keyframes heroReveal{0%{opacity:0;transform:translateY(28px);filter:blur(12px);}100%{opacity:1;transform:translateY(0);filter:blur(0);}}
  @keyframes heroFadeUp{0%{opacity:0;transform:translateY(20px);}100%{opacity:1;transform:translateY(0);}}
  @keyframes heroZoom{0%{transform:scale(1.12);}100%{transform:scale(1);}}
  .hero-anim{opacity:0;animation-fill-mode:forwards;animation-timing-function:cubic-bezier(.16,1,.3,1);}
  .hero-reveal-anim{animation-name:heroReveal;animation-duration:1.1s;}
  .hero-fade{animation-name:heroFadeUp;animation-duration:1s;}
  .hero-zoom{animation:heroZoom 1.8s cubic-bezier(.16,1,.3,1) forwards;}
  @media(prefers-reduced-motion:reduce){.hero-anim,.hero-zoom{animation:none;opacity:1;}}"""

_COMPONENT_JS = """export default function (component) {
  const { data, parentElement } = component
  const root = parentElement.querySelector('#app-root')
  if (!root) return
  const API = (data && data.api_base) || 'http://localhost:8000'
  const $ = function (sel) { return root.querySelector(sel) }

  const sceneLanding = $('#scene-landing')
  const sceneLogin = $('#scene-login')
  const sceneRegister = $('#scene-register')
  const sceneChat = $('#scene-chat')
  const tunnel = $('#tunnel')
  const glow = $('#glow')
  const scenes = [sceneLanding, sceneLogin, sceneRegister, sceneChat]
  const burger = $('#hn-burger')
  const mobileMenu = $('#hn-mobile')

  let token = null
  let username = ''
  let messages = []
  let historyCount = 0
  let busy = false

  // ============ 霓虹街道（Canvas 鼠标点亮） ============
  const cv = $('#street')
  const ctx = cv.getContext('2d')
  let W = 0, H = 0, vpX = 0, vpY = 0
  let lights = []
  const mouse = { mx: -999, my: -999 }
  let rafId = null

  function buildLights () {
    lights = []
    for (let i = 0; i < 110; i++) {
      lights.push({
        x: W * (0.04 + 0.92 * Math.random()),
        y: H * (0.18 + 0.78 * Math.random()),
        r: 1.6 + Math.random() * 2.2,
        base: 0.04, bright: 0.04,
        color: ['#00e5ff', '#ff3df0', '#ffd166', '#7c4dff'][Math.floor(Math.random() * 4)]
      })
    }
  }
  function resize () {
    W = cv.width = window.innerWidth
    H = cv.height = window.innerHeight
    vpX = W / 2
    vpY = H * 0.40
    buildLights()
  }
  function step () {
    ctx.clearRect(0, 0, W, H)
    const sky = ctx.createLinearGradient(0, 0, 0, H)
    sky.addColorStop(0, '#04060f'); sky.addColorStop(0.55, '#0a0f22')
    ctx.fillStyle = sky; ctx.fillRect(0, 0, W, H)
    ctx.fillStyle = '#101b34'
    ctx.beginPath(); ctx.moveTo(0, H); ctx.lineTo(vpX - 6, vpY); ctx.lineTo(vpX + 6, vpY); ctx.lineTo(W, H); ctx.closePath(); ctx.fill()
    ctx.strokeStyle = 'rgba(255,214,90,.3)'; ctx.lineWidth = 2
    ctx.beginPath(); ctx.moveTo(vpX - 8, vpY); ctx.lineTo(vpX - 2, H); ctx.moveTo(vpX + 2, H); ctx.lineTo(vpX + 8, vpY); ctx.stroke()
    for (let i = 0; i < lights.length; i++) {
      const L = lights[i]
      const d = Math.hypot(L.x - mouse.mx, L.y - mouse.my)
      const tgt = L.base + Math.max(0, 1 - d / 150) * 0.9
      L.bright += (tgt - L.bright) * 0.12
      ctx.globalAlpha = L.bright
      ctx.fillStyle = L.color
      ctx.beginPath(); ctx.arc(L.x, L.y, L.r, 0, 6.283); ctx.fill()
      if (L.bright > 0.4) {
        const g = ctx.createRadialGradient(L.x, L.y, 0, L.x, L.y, L.r * 9)
        g.addColorStop(0, L.color); g.addColorStop(1, 'rgba(0,0,0,0)')
        ctx.globalAlpha = (L.bright - 0.4) * 0.45
        ctx.fillStyle = g
        ctx.beginPath(); ctx.arc(L.x, L.y, L.r * 9, 0, 6.283); ctx.fill()
      }
    }
    ctx.globalAlpha = 1
    rafId = requestAnimationFrame(step)
  }
  function onMouseMove (e) {
    const r = root.getBoundingClientRect()
    mouse.mx = e.clientX - r.left
    mouse.my = e.clientY - r.top
    glow.style.left = mouse.mx + 'px'
    glow.style.top = mouse.my + 'px'
  }
  function onResize () { resize() }
  resize()
  step()
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('resize', onResize)
  // ============ 聚光灯揭示（hero 核心交互：遮罩光斑） ============
  const SPOTLIGHT_R = 260
  const spotCanvas = $('#spot-canvas')
  const heroRevealEl = $('#hero-reveal')
  const spotCtx = spotCanvas.getContext('2d')
  const spotMouse = { x: -999, y: -999 }
  const spotSmooth = { x: -999, y: -999 }
  let spotRafId = null
  let spotW = 0
  let spotH = 0

  function spotResize () {
    spotW = spotCanvas.width = window.innerWidth
    spotH = spotCanvas.height = window.innerHeight
  }
  function spotStep () {
    spotSmooth.x += (spotMouse.x - spotSmooth.x) * 0.1
    spotSmooth.y += (spotMouse.y - spotSmooth.y) * 0.1
    spotCtx.clearRect(0, 0, spotW, spotH)
    const g = spotCtx.createRadialGradient(spotSmooth.x, spotSmooth.y, 0, spotSmooth.x, spotSmooth.y, SPOTLIGHT_R)
    g.addColorStop(0, 'rgba(255,255,255,1)')
    g.addColorStop(0.4, 'rgba(255,255,255,1)')
    g.addColorStop(0.6, 'rgba(255,255,255,0.75)')
    g.addColorStop(0.75, 'rgba(255,255,255,0.4)')
    g.addColorStop(0.88, 'rgba(255,255,255,0.12)')
    g.addColorStop(1, 'rgba(255,255,255,0)')
    spotCtx.fillStyle = g
    spotCtx.beginPath()
    spotCtx.arc(spotSmooth.x, spotSmooth.y, SPOTLIGHT_R, 0, Math.PI * 2)
    spotCtx.fill()
    const url = spotCanvas.toDataURL()
    heroRevealEl.style.maskImage = 'url(' + url + ')'
    heroRevealEl.style.webkitMaskImage = 'url(' + url + ')'
    spotRafId = requestAnimationFrame(spotStep)
  }
  function spotStart () {
    if (spotRafId) return
    spotSmooth.x = spotMouse.x
    spotSmooth.y = spotMouse.y
    spotResize()
    spotStep()
  }
  function spotStop () {
    if (spotRafId) { cancelAnimationFrame(spotRafId); spotRafId = null }
    heroRevealEl.style.maskImage = ''
    heroRevealEl.style.webkitMaskImage = ''
  }
  function onSpotMove (e) { spotMouse.x = e.clientX; spotMouse.y = e.clientY }
  function onSpotResize () { spotResize() }
  window.addEventListener('mousemove', onSpotMove)
  window.addEventListener('resize', onSpotResize)
  spotStart()

  // ============ 场景切换 + 隧道转场 ============
  function showScreen (name) {
    scenes.forEach(function (s) { s.classList.remove('active') })
    root.classList.remove('chatmode')
    root.querySelectorAll('.hn-item').forEach(function (it) { it.classList.remove('active') })
    root.querySelectorAll('.hn-m-item').forEach(function (it) { it.classList.remove('active') })
    const pillMap = { landing: 'hn-home', login: 'hn-login', register: 'hn-register' }
    const pillEl = pillMap[name] && $('#' + pillMap[name])
    if (pillEl) pillEl.classList.add('active')
    const mPillMap = { landing: 'hn-m-home', login: 'hn-m-login', register: 'hn-m-register' }
    const mPillEl = mPillMap[name] && $('#' + mPillMap[name])
    if (mPillEl) mPillEl.classList.add('active')
    closeMobileMenu()
    if (name === 'landing') { sceneLanding.classList.add('active'); spotStart() } else { spotStop() }
    if (name === 'login') sceneLogin.classList.add('active')
    if (name === 'register') sceneRegister.classList.add('active')
    if (name === 'chat') { sceneChat.classList.add('active'); root.classList.add('chatmode') }
  }
  function tunnelTo (name) {
    root.classList.remove('zoom-out')
    root.classList.add('zoom-in')
    tunnel.classList.add('go')
    setTimeout(function () {
      showScreen(name)
      root.classList.remove('zoom-in')
      root.classList.add('zoom-out')
      setTimeout(function () {
        root.classList.remove('zoom-out')
        tunnel.classList.remove('go')
      }, 740)
    }, 420)
  }

  // ============ 工具函数 ============
  function setMsg (el, text, kind) {
    el.textContent = text
    el.className = 'msg-line ' + (kind || '')
  }
  function clearMsg (el) { el.textContent = ''; el.className = 'msg-line' }
  function setBtnLoading (btn, on, label) {
    btn.disabled = on
    if (on) btn.textContent = label
  }
  function restoreBtn (btn, label) {
    btn.disabled = false
    btn.textContent = label
  }
  function nowText () {
    const d = new Date()
    function p (n) { return (n < 10 ? '0' : '') + n }
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds())
  }
  async function request (path, options) {
    const ctrl = new AbortController()
    const timer = setTimeout(function () { ctrl.abort() }, 90000)
    const opts = options || {}
    opts.signal = ctrl.signal
    try {
      const res = await fetch(API + path, opts)
      let body = null
      try { body = await res.json() } catch (e) { body = {} }
      return { ok: res.ok, status: res.status, body: body || {} }
    } catch (e) {
      return { ok: false, status: 0, body: {} }
    } finally {
      clearTimeout(timer)
    }
  }
  function showSystem (text) {
    messages.push({ role: 'system', content: text, time: '' })
    renderMessages()
  }

  // ============ 登录 ============
  const loginBtn = $('#btn-login-submit')
  const regBtn = $('#btn-register-submit')
  const LOGIN_LABEL = '登 录'
  const REG_LABEL = '注 册'
  const LOGIN_LOADING = '登录中…'
  const REG_LOADING = '注册中…'

  async function loadHistory () {
    if (!token) return
    const r = await request('/history', { headers: { Authorization: 'Bearer ' + token } })
    if (!r.ok) return
    const list = r.body.messages || []
    historyCount = list.length
    messages = []
    list.forEach(function (m) {
      messages.push({ role: 'user', content: m.question, time: m.created_at || '' })
      messages.push({ role: 'ai', content: m.answer, time: m.created_at || '', sources: null })
    })
    renderMessages()
  }

  async function doLogin () {
    if (loginBtn.disabled) return
    const userEl = $('#login-user')
    const passEl = $('#login-pass')
    const msgEl = $('#login-msg')
    const u = userEl.value.trim()
    const p = passEl.value
    if (!u || !p) { setMsg(msgEl, '请输入用户名和密码', 'err'); return }
    setBtnLoading(loginBtn, true, LOGIN_LOADING)
    clearMsg(msgEl)
    const r = await request('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: u, password: p })
    })
    restoreBtn(loginBtn, LOGIN_LABEL)
    if (r.status === 0) { setMsg(msgEl, '无法连接后端，请先启动 FastAPI', 'err'); return }
    if (!r.ok) { setMsg(msgEl, '登录失败：用户名或密码错误（新用户请先注册）', 'err'); return }
    token = r.body.token
    username = u
    historyCount = 0
    $('#chat-avatar').textContent = username[0].toUpperCase()
    $('#chat-who').textContent = username + ' · 金融顾问 AI'
    messages = []
    await loadHistory()
    showSystem('欢迎回来，' + username + '！已加载 ' + historyCount + ' 条历史对话。')
    tunnelTo('chat')
  }

  // ============ 注册 ============
  async function doRegister () {
    if (regBtn.disabled) return
    const userEl = $('#reg-user')
    const passEl = $('#reg-pass')
    const pass2El = $('#reg-pass2')
    const msgEl = $('#reg-msg')
    const u = userEl.value.trim()
    const p = passEl.value
    const p2 = pass2El.value
    if (!u || !p) { setMsg(msgEl, '用户名和密码不能为空', 'err'); return }
    if (p !== p2) { setMsg(msgEl, '两次密码不一致', 'err'); return }
    setBtnLoading(regBtn, true, REG_LOADING)
    clearMsg(msgEl)
    const r = await request('/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: u, password: p })
    })
    restoreBtn(regBtn, REG_LABEL)
    if (r.status === 0) { setMsg(msgEl, '无法连接后端，请先启动 FastAPI', 'err'); return }
    if (!r.ok) { setMsg(msgEl, r.body.detail || '注册失败', 'err'); return }
    $('#login-user').value = u
    $('#login-pass').value = ''
    setMsg($('#login-msg'), '注册成功，请登录', 'ok')
    tunnelTo('login')
  }

  // ============ 聊天 ============
  function renderMessages () {
    const list = $('#msg-list')
    list.innerHTML = ''
    messages.forEach(function (m) {
      const div = document.createElement('div')
      if (m.role === 'system') {
        div.className = 'm system'
        div.textContent = m.content
      } else if (m.role === 'user') {
        div.className = 'm user'
        div.textContent = m.content
        if (m.time) {
          const t = document.createElement('div')
          t.className = 't'
          t.textContent = m.time
          div.appendChild(t)
        }
      } else {
        div.className = 'm ai'
        if (m.loading) {
          const dots = document.createElement('span')
          dots.className = 'dots'
          dots.innerHTML = '<i></i><i></i><i></i>'
          div.appendChild(dots)
          div.appendChild(document.createTextNode(' 正在检索知识库…'))
        } else {
          div.textContent = m.content
          if (m.time) {
            const t = document.createElement('div')
            t.className = 't'
            t.textContent = m.time
            div.appendChild(t)
          }
          if (m.sources && m.sources.length) {
            const src = document.createElement('div')
            src.className = 'src'
            const lab = document.createElement('div')
            lab.textContent = '📚 引用来源（' + m.sources.length + '）'
            src.appendChild(lab)
            m.sources.forEach(function (s, i) {
              const det = document.createElement('details')
              const sum = document.createElement('summary')
              const name = (s && (s.filename || s.source)) || '未知来源'
              sum.textContent = '[' + (i + 1) + '] ' + name
              det.appendChild(sum)
              if (s && s.excerpt) {
                const ex = document.createElement('div')
                ex.className = 'excerpt'
                ex.textContent = s.excerpt
                det.appendChild(ex)
              }
              src.appendChild(det)
            })
            div.appendChild(src)
          }
        }
      }
      list.appendChild(div)
    })
    list.scrollTop = list.scrollHeight
  }

  async function sendQuestion () {
    const input = $('#chat-input')
    const q = input.value.trim()
    if (!q || !token || busy) return
    input.value = ''
    busy = true
    messages.push({ role: 'user', content: q, time: nowText() })
    const idx = messages.length
    messages.push({ role: 'ai', content: '', loading: true, time: '' })
    renderMessages()
    const r = await request('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
      body: JSON.stringify({ question: q })
    })
    busy = false
    if (r.status === 0) {
      messages[idx] = { role: 'ai', content: '无法连接后端，请先启动 FastAPI（uvicorn rag_app:app --port 8000）', time: '' }
    } else if (r.status === 401) {
      messages[idx] = { role: 'ai', content: '登录已过期，请重新登录', time: '' }
      renderMessages()
      token = null
      setTimeout(function () { tunnelTo('login') }, 1500)
      return
    } else if (!r.ok) {
      messages[idx] = { role: 'ai', content: '后端返回错误（' + r.status + '）：' + (r.body.detail || ''), time: '' }
    } else {
      messages[idx] = { role: 'ai', content: r.body.answer, time: nowText(), sources: r.body.sources || [] }
    }
    renderMessages()
  }

  // ============ 事件绑定 ============
  // ============ 移动端汉堡菜单 ============
  function closeMobileMenu () {
    if (burger) burger.classList.remove('open')
    if (mobileMenu) mobileMenu.classList.remove('open')
  }
  if (burger && mobileMenu) {
    burger.addEventListener('click', function () {
      const open = mobileMenu.classList.toggle('open')
      burger.classList.toggle('open', open)
    })
    parentElement.addEventListener('click', function (e) {
      if (mobileMenu.classList.contains('open') && !mobileMenu.contains(e.target) && !burger.contains(e.target)) closeMobileMenu()
    })
  }
  $('#hn-m-home').addEventListener('click', function () { closeMobileMenu(); tunnelTo('landing') })
  $('#hn-m-login').addEventListener('click', function () { clearMsg($('#login-msg')); closeMobileMenu(); tunnelTo('login') })
  $('#hn-m-register').addEventListener('click', function () { clearMsg($('#reg-msg')); closeMobileMenu(); tunnelTo('register') })
  $('#hn-m-signup').addEventListener('click', function () { clearMsg($('#reg-msg')); closeMobileMenu(); tunnelTo('register') })

  $('#btn-login').addEventListener('click', function () { clearMsg($('#login-msg')); tunnelTo('login') })
  $('#btn-register').addEventListener('click', function () { clearMsg($('#reg-msg')); tunnelTo('register') })
  $('#hn-home').addEventListener('click', function () { tunnelTo('landing') })
  $('#hn-login').addEventListener('click', function () { clearMsg($('#login-msg')); tunnelTo('login') })
  $('#hn-register').addEventListener('click', function () { clearMsg($('#reg-msg')); tunnelTo('register') })
  $('#hn-signup').addEventListener('click', function () { clearMsg($('#reg-msg')); tunnelTo('register') })
  $('#lnk-to-register').addEventListener('click', function () { tunnelTo('register') })
  $('#lnk-to-login').addEventListener('click', function () { tunnelTo('login') })
  loginBtn.addEventListener('click', doLogin)
  regBtn.addEventListener('click', doRegister)
  $('#login-pass').addEventListener('keydown', function (e) { if (e.key === 'Enter') doLogin() })
  $('#reg-pass2').addEventListener('keydown', function (e) { if (e.key === 'Enter') doRegister() })
  $('#btn-send').addEventListener('click', sendQuestion)
  $('#chat-input').addEventListener('keydown', function (e) { if (e.key === 'Enter') sendQuestion() })
  $('#btn-logout').addEventListener('click', function () {
    token = null
    username = ''
    messages = []
    historyCount = 0
    tunnelTo('landing')
  })
  $('#btn-clear').addEventListener('click', function () {
    messages = []
    historyCount = 0
    renderMessages()
  })

  return function cleanup () {
    cancelAnimationFrame(rafId)
    cancelAnimationFrame(spotRafId)
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mousemove', onSpotMove)
    window.removeEventListener('resize', onResize)
    window.removeEventListener('resize', onSpotResize)
  }
}"""

_FINANCIAL_APP = st.components.v2.component(
    "financial_ai_workspace",
    html=_COMPONENT_HTML,
    css=_COMPONENT_CSS,
    js=_COMPONENT_JS,
)

_FINANCIAL_APP(data={"api_base": API}, height="content")
