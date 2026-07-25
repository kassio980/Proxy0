import json, time, hashlib, random, string
from functools import wraps
from flask import request, jsonify, render_template_string, redirect, session

BASE = __import__('os').path.dirname(__file__)
DB = f"{BASE}/db/keys.json"

def carregar():
    with open(DB,'r',encoding='utf-8') as f: return json.load(f)
def salvar(d):
    with open(DB,'w',encoding='utf-8') as f: json.dump(d,f,indent=2,ensure_ascii=False)

def chave_valida(chave):
    d = carregar()
    if chave == d['chave_mestra']: return {'nivel':'MESTRE','expira':time.time()+86400*365}
    if chave in d['chaves_geradas']:
        u = d['chaves_geradas'][chave]
        if time.time() < u['expira']: return u
    return False

def gerar_chave_usuario(nome, horas=7):
    d = carregar()
    while True:
        k = 'OKD-'+''.join(random.choices(string.ascii_uppercase+string.digits,k=8))
        if k not in d['chaves_geradas']: break
    d['chaves_geradas'][k] = {
        'nome':nome,'nivel':'USUARIO','criada':time.time(),
        'expira':time.time()+horas*3600,'chave':k
    }
    salvar(d); return k

def requer_login(f):
    @wraps(f)
    def wrapper(*a,**k):
        chave = request.headers.get('X-Key') or request.args.get('key') or request.cookies.get('okaida_key') or session.get('key')
        u = chave_valida(chave) if chave else False
        if not u: return redirect('/login')
        request.user = u; request.chave = chave; return f(*a,**k)
    return wrapper

def pagina_login():
    return render_template_string("""<!doctype html><html><head><meta charset=utf-8>
    <title>🔐 PROXY OKAIDA — LOGIN</title>
    <style>
    *{box-sizing:border-box}body{margin:0;background:#000;color:#0f0;font-family:monospace;min-height:100vh;
      display:flex;align-items:center;justify-content:center;
      background-image:radial-gradient(#0f02 1px,transparent 1px),linear-gradient(#0f01 1px,transparent 1px);
      background-size:3px 3px,100% 24px}
    .l{border:1px solid #0f0;padding:30px 40px;background:#000c;box-shadow:0 0 30px #0f05;max-width:400px;width:90%}
    h1{margin:0 0 20px;letter-spacing:4px;font-size:20px;text-shadow:0 0 8px #0f0}
    input{width:100%;padding:12px;background:#000;color:#0f0;border:1px solid #0f05;font-family:monospace;font-size:16px;letter-spacing:2px;margin:10px 0}
    input:focus{outline:none;border-color:#0f0;box-shadow:0 0 10px #0f05}
    button{width:100%;padding:14px;background:#0f0;color:#000;border:0;font-family:monospace;font-weight:bold;font-size:16px;cursor:pointer;letter-spacing:3px;margin-top:10px}
    button:hover{background:#0c0;box-shadow:0 0 20px #0f08}.e{color:#f00;margin-top:10px;min-height:18px}
    .blink{animation:b 1s steps(2) infinite}@keyframes b{50%{opacity:0}}
    </style></head><body>
    <form method=post class=l>
      <h1>🕵️ PROXY OKAIDA <span class=blink>_</span></h1>
      <div style=opacity:.7;font-size:12px;letter-spacing:2px>INSIRA SUA CHAVE DE ACESSO</div>
      <input name=key type=password placeholder="DIGITE A CHAVE..." autocomplete=off autofocus>
      <button type=submit>▶ ENTRAR NO SISTEMA</button>
      <div class=e id=e>{% if erro %}{{ erro }}{% endif %}</div>
    </form>
    <script>
    if(new URLSearchParams(location.search).has('e'))document.getElementById('e').textContent='❌ CHAVE INVÁLIDA';
    </script></body></html>""", erro=request.args.get('e'))
