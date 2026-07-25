import os, time, json, threading
BASE = os.path.dirname(os.path.abspath(__file__))

from flask import Flask, render_template_string, request, redirect, make_response, jsonify, session
from flask_socketio import SocketIO

app = Flask(__name__, static_folder="www", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY","okaida-proxy-2026-secret-mestra")
app.config['SESSION_COOKIE_NAME'] = 'okaida_session'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Carrega módulos com try/except (NÃO QUEBRA SE FALTAR)
MOD = {}
for nome in ["auth","perfis","geo_users","wifi_share","virus_mode"]:
    try:
        m = __import__(nome)
        MOD[nome] = m
    except Exception as e:
        MOD[nome] = None
        print(f"   ⚠️  app_web: módulo {nome} não carregou: {e}")

try: from extras_hacker import FLAGS, set_flag, IP, AB
except: FLAGS={}; set_flag=lambda *a:FLAGS; IP=None; AB=None

CFG = MOD["perfis"].carregar() if MOD["perfis"] else {}

def stats():
    up = MOD["perfis"].status_tempo_restante(time.time()-3600*7, 7) if MOD["perfis"] else {"texto":"--:--:--","porcento":0}
    return {
        "uptime": up,
        "flags": FLAGS,
        "perfis": getattr(MOD.get("proxy_core"),"PERFIS",{}) if MOD.get("proxy_core") else {},
        "armas": getattr(MOD.get("proxy_core"),"ARMAS",[]) if MOD.get("proxy_core") else [],
        "por_arma": CFG.get("CAPA",{}).get("POR_ARMA",{}),
        "usuarios": IP.resumo() if IP else {"online_agora":0,"ips_unicos_total":0},
        "geo": MOD["geo_users"].USERS.resumo() if MOD.get("geo_users") else {"mapa":[]},
    }

def broadcast():
    while True:
        try: socketio.emit("stats", stats())
        except: pass
        time.sleep(1.5)
threading.Thread(target=broadcast,daemon=True).start()

# ===== ROTAS =====
@app.route("/login", methods=["GET","POST"])
def login():
    if not MOD["auth"]: return "auth.py faltando", 500
    if request.method=="POST":
        k = request.form.get("key","").strip()
        if MOD["auth"].chave_valida(k):
            r = make_response(redirect("/dash"))
            r.set_cookie("okaida_key", k, max_age=7*86400)
            session["key"] = k
            return r
        return redirect("/login?e=1")
    return MOD["auth"].pagina_login()

@app.route("/logout")
def logout():
    r = make_response(redirect("/login"))
    r.delete_cookie("okaida_key"); session.clear(); return r

@app.route("/overlay")
def overlay():
    try: return app.send_static_file("ff_overlay.html")
    except: return "overlay não encontrado", 404

# ===== API =====
@app.route("/api/st")
def api_st(): return jsonify(stats())

@app.route("/api/perfil/<nome>")
@MOD["auth"].requer_login
def api_perfil(nome):
    if not MOD["perfis"]: return jsonify({"ok":False})
    ok = MOD["perfis"].set_perfil(nome)
    return jsonify({"ok":ok,"perfil":nome})

@app.route("/api/arma/<arma>/<perfil>")
@MOD["auth"].requer_login
def api_arma(arma,perfil):
    if not MOD["perfis"]: return jsonify({"ok":False})
    ok = MOD["perfis"].set_por_arma(arma,perfil)
    return jsonify({"ok":ok,"arma":arma,"perfil":perfil})

@app.route("/api/flags/<nome>/<int:v>")
@MOD["auth"].requer_login
def api_flag(nome,v):
    return jsonify({"ok":True,"flags":set_flag(nome,bool(v))})

@app.route("/api/wifi/novo")
@MOD["auth"].requer_login
def api_wifi():
    if not MOD["wifi_share"]: return jsonify({"ok":False})
    d = MOD["wifi_share"].gerar_codigo_compartilhamento()
    qr = MOD["wifi_share"].gerar_qr_wifi(d)
    qp = MOD["wifi_share"].gerar_qr_proxy(d)
    return jsonify({"dados":d,"qr_wifi":qr,"qr_proxy_b64":qp})

@app.route("/api/virus/abrir_ff")
@MOD["auth"].requer_login
def api_ff():
    ok = MOD["virus_mode"].abrir_free_fire() if MOD["virus_mode"] else False
    return jsonify({"ok":bool(ok)})

@app.route("/api/codigo/<cod>")
def api_cod(cod):
    u = MOD["wifi_share"].validar_codigo(cod) if MOD["wifi_share"] else None
    return jsonify({"ok":bool(u),"dados":u or {}})

def index():
    tpl_path = f"{BASE}/templates/index.html"
    if not os.path.exists(tpl_path): return "Painel OK — crie templates/index.html", 200
    try:
        return render_template_string(open(tpl_path).read(),
            user={"nivel":"USER"}, key=session.get("key",""), stats=stats())
    except Exception as e:
        return f"Erro template: {e}", 500

app.add_url_rule("/app_index","app_index", index)

@socketio.on("comando")
def cmd(d):
    try:
        if d.get("a")=="perfil" and MOD["perfis"]: MOD["perfis"].set_perfil(d["v"])
        if d.get("a")=="flag": set_flag(d["n"], bool(d.get("v",1)))
    except: pass

if __name__=="__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT",8888)), allow_unsafe_werkzeug=True)
