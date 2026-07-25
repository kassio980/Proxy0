import os, time, json, threading
BASE = os.path.dirname(os.path.abspath(__file__))

from flask import Flask, render_template_string, request, redirect, make_response, jsonify, session
from flask_socketio import SocketIO

app = Flask(__name__, static_folder="www", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY","okaida-proxy-2026-secret-mestra")
app.config['SESSION_COOKIE_NAME'] = 'okaida_session'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

MOD = {}
for nome in ["auth","perfis","geo_users","wifi_share","virus_mode"]:
    try: MOD[nome] = __import__(nome)
    except Exception as e: MOD[nome] = None

try: from extras_hacker import FLAGS, set_flag, IP
except: FLAGS={}; set_flag=lambda *a:FLAGS; IP=None

CFG = MOD["perfis"].carregar() if MOD["perfis"] else {}
INICIO = time.time()

def uptime():
    decorr = time.time() - INICIO
    max_s = 7*3600
    pct = min(100, round(decorr/max_s*100,1))
    h = int(decorr//3600); m=int((decorr%3600)//60); s=int(decorr%60)
    return {"texto":f"{h:02d}:{m:02d}:{s:02d}","porcento":pct,"decorrido_s":decorr}

def stats():
    return {
        "uptime": uptime(),
        "flags": FLAGS,
        "perfis": getattr(MOD.get("proxy_core"),"PERFIS",{}),
        "armas": getattr(MOD.get("proxy_core"),"ARMAS",["MP40","SCAR","AK47","M4A1","AWM","M1887","M1014","UMP","XM8","FAMAS","GROZA","SG12","AUG"]),
        "por_arma": CFG.get("CAPA",{}).get("POR_ARMA",{}),
        "usuarios": IP.resumo() if IP else {"online_agora":0,"ips_unicos_total":0,"paises_distintos":0,"top_paises":[],"ultimos_20":[]},
        "geo": MOD["geo_users"].USERS.resumo() if MOD.get("geo_users") else {"mapa":[]},
        "perfil_chave": CFG.get("CAPA",{}).get("PERFIL","SO_CAPA"),
        "perfil_atual": CFG.get("CAPA",{}).get("PERFIL","SO_CAPA"),
        "capa": CFG.get("ESTATISTICAS",{}).get("CAPAS",0),
        "peito": CFG.get("ESTATISTICAS",{}).get("PEITO_CABECA",0),
        "tcp": {"c":CFG.get("ESTATISTICAS",{}).get("CONEXOES_TCP",0)},
        "udp": {"p":CFG.get("ESTATISTICAS",{}).get("PACOTES_UDP",0),"c":CFG.get("ESTATISTICAS",{}).get("CONEXOES_UDP",0)},
    }

def broadcast():
    while True:
        try: socketio.emit("stats", stats())
        except: pass
        time.sleep(1.5)
threading.Thread(target=broadcast,daemon=True).start()

@app.route("/login", methods=["GET","POST"])
def login():
    if not MOD["auth"]: return render_template_string(open(f"{BASE}/templates/login.html").read(), erro=request.args.get("e"))
    if request.method=="POST":
        k = request.form.get("key","").strip()
        if MOD["auth"].chave_valida(k):
            r = make_response(redirect("/dash"))
            r.set_cookie("okaida_key", k, max_age=7*86400)
            session["key"] = k
            return r
        return redirect("/login?e=1")
    return render_template_string(open(f"{BASE}/templates/login.html").read(), erro=request.args.get("e"))

@app.route("/logout")
def logout():
    r = make_response(redirect("/login"))
    r.delete_cookie("okaida_key"); session.clear(); return r

@app.route("/")
def home():
    k = request.cookies.get("okaida_key") or request.args.get("key")
    if MOD.get("auth") and k and MOD["auth"].chave_valida(k):
        r = make_response(redirect("/dash"))
        r.set_cookie("okaida_key", k, max_age=7*86400); return r
    return redirect("/login")

@app.route("/overlay")
def overlay():
    return app.send_static_file("ff_overlay.html")

@app.route("/dash")
def dash():
    if MOD.get("auth"):
        k = request.cookies.get("okaida_key") or session.get("key")
        if not MOD["auth"].chave_valida(k): return redirect("/login")
    return render_template_string(open(f"{BASE}/templates/index.html").read(),
        user={"nivel":"ACESSO MESTRE"}, key=session.get("key",""), stats=stats())

@app.route("/api/st")
def api_st(): return jsonify(stats())

@app.route("/api/perfil/<nome>")
def api_perfil(nome):
    if not MOD["perfis"]: return jsonify({"ok":False})
    ok = MOD["perfis"].set_perfil(nome)
    return jsonify({"ok":ok,"perfil":nome})

@app.route("/api/arma/<arma>/<perfil>")
def api_arma(arma,perfil):
    if not MOD["perfis"]: return jsonify({"ok":False})
    ok = MOD["perfis"].set_por_arma(arma,perfil)
    return jsonify({"ok":ok,"arma":arma,"perfil":perfil})

@app.route("/api/flags/<nome>/<int:v>")
def api_flag(nome,v):
    return jsonify({"ok":True,"flags":set_flag(nome,bool(v))})

@app.route("/api/wifi/novo")
def api_wifi():
    if not MOD["wifi_share"]: return jsonify({"ok":False})
    d = MOD["wifi_share"].gerar_codigo_compartilhamento()
    qr = MOD["wifi_share"].gerar_qr_wifi(d)
    qp = MOD["wifi_share"].gerar_qr_proxy(d)
    return jsonify({"ok":True,"dados":d,"qr_wifi":qr,"qr_proxy_b64":qp})

@app.route("/api/virus/abrir_ff")
def api_ff():
    ok = MOD["virus_mode"].abrir_free_fire() if MOD["virus_mode"] else False
    return jsonify({"ok":bool(ok)})

@app.route("/api/codigo/<cod>")
def api_codigo(cod):
    from wifi_share import validar_codigo
    u = validar_codigo(cod)
    return jsonify({"ok":bool(u),"dados":u or {}})

@app.route("/api/fullvermelho/<int:n>")
def api_fv(n):
    from extras_hacker import set_fullvermelho, stats_fullvermelho
    return jsonify({"ok":True, **set_fullvermelho(n), "stats":stats_fullvermelho()})

@app.route("/health")
def health():
    return jsonify({"ok":True,"modo":"RENDER" if os.environ.get("RENDER") else "TERMUX","proxy_okaida":"v2.2","hora":time.strftime("%Y-%m-%d %H:%M:%S")})

if __name__=="__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT",8888)), allow_unsafe_werkzeug=True)
