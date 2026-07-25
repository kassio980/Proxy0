import os, time, json, threading
from flask import Flask, render_template_string, request, redirect, make_response, jsonify, session
from flask_socketio import SocketIO, emit
from auth import requer_login, chave_valida, pagina_login, gerar_chave_usuario, carregar as auth_db

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder="www", template_folder="www")
app.secret_key = "okaida-proxy-2026-secret-key-mestra"
app.config['SESSION_COOKIE_NAME'] = 'okaida_session'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Carregar módulos do proxy
import proxy_core, perfis, wifi_share, virus_mode
CFG = perfis.carregar()

def stats_publicas():
    up = perfis.status_tempo_restante(proxy_core.ST["inicio"], CFG["TEMPO_MAX_HORAS"])
    return {
        "inicio": proxy_core.ST["inicio"],
        "uptime": up,
        "tcp": proxy_core.ST["tcp"],
        "udp": proxy_core.ST["udp"],
        "capa": proxy_core.ST["capa"],
        "peito": proxy_core.ST["peito"],
        "servidores": dict(sorted(proxy_core.ST["servidores"].items(),key=lambda x:-x[1])[:30]),
        "usuarios": list(proxy_core.ST["usuarios"].values())[-50:],
        "perfil_atual": proxy_core.PERF["nome"],
        "perfil_chave": proxy_core.C["PERFIL"],
        "perfis": proxy_core.PERFIS,
        "armas": proxy_core.ARMAS,
        "por_arma": proxy_core.C["POR_ARMA"],
        "todas_armas": proxy_core.C["TODAS_ARMAS"],
        "antiban": proxy_core.AB,
        "codigos": wifi_share.codigos_ativos(),
        "ip_local": wifi_share.meu_ip_local(),
    }

# Thread que envia stats ao vivo via WebSocket
def broadcast():
    while True:
        try: socketio.emit("stats", stats_publicas())
        except: pass
        time.sleep(1)
threading.Thread(target=broadcast,daemon=True).start()

# ============ ROTAS ============
@app.route("/")
@requer_login
def index():
    return render_template_string(open(f"{BASE}/templates/index.html").read(),
        user=request.user, key=request.chave, stats=stats_publicas())

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        k = request.form.get("key","").strip()
        if chave_valida(k):
            resp = make_response(redirect("/"))
            resp.set_cookie("okaida_key", k, max_age=CFG["TEMPO_MAX_HORAS"]*3600)
            session["key"] = k
            return resp
        return redirect("/login?e=1")
    return pagina_login()

@app.route("/logout")
def logout():
    r = make_response(redirect("/login"))
    r.delete_cookie("okaida_key"); session.clear(); return r

@app.route("/overlay")
def overlay():
    return app.send_static_file("ff_overlay.html")

# ============ API ============
@app.route("/api/st")
def api_st(): return jsonify(stats_publicas())

@app.route("/api/perfil/<nome>")
@requer_login
def api_perfil(nome):
    ok = perfis.set_perfil(nome)
    if ok:
        proxy_core.C["PERFIL"] = nome
        proxy_core.PERF = proxy_core.PERFIS[nome]
        proxy_core.salvar_cfg()
    return jsonify({"ok":ok,"perfil":nome})

@app.route("/api/arma/<arma>/<perfil>")
@requer_login
def api_arma(arma,perfil):
    ok = perfis.set_por_arma(arma,perfil)
    if ok:
        proxy_core.C["POR_ARMA"] = perfis.carregar()["CAPA"]["POR_ARMA"]
        proxy_core.C["TODAS_ARMAS"] = perfis.carregar()["CAPA"]["TODAS_ARMAS"]
        proxy_core.salvar_cfg()
    return jsonify({"ok":ok,"arma":arma,"perfil":perfil})

@app.route("/api/capa/toggle")
@requer_login
def api_toggle():
    proxy_core.C["ATIVO"] = not proxy_core.C["ATIVO"]
    proxy_core.salvar_cfg()
    return jsonify({"ok":True,"ativo":proxy_core.C["ATIVO"]})

@app.route("/api/antiban/toggle")
@requer_login
def api_ab():
    proxy_core.AB["ATIVO"] = not proxy_core.AB["ATIVO"]
    proxy_core.salvar_cfg()
    return jsonify({"ok":True,"ativo":proxy_core.AB["ATIVO"]})

@app.route("/api/wifi/novo")
@requer_login
def api_wifi():
    d = wifi_share.gerar_codigo_compartilhamento()
    qr = wifi_share.gerar_qr_wifi(d)
    qp = wifi_share.gerar_qr_proxy(d)
    return jsonify({"dados":d,"qr_wifi":qr,"qr_proxy_b64":qp})

@app.route("/api/virus/abrir_ff")
@requer_login
def api_abrir_ff():
    ok = virus_mode.abrir_free_fire()
    return jsonify({"ok":ok})

@app.route("/api/virus/injetar")
@requer_login
def api_injetar():
    ip = virus_mode.injetar_proxy_no_app()
    return jsonify({"ok":True,"ip":ip})

@app.route("/api/chave/gerar/<nome>/<int:horas>")
@requer_login
def api_chave(nome,horas):
    if request.user.get("nivel") != "MESTRE": return jsonify({"ok":False,"erro":"apenas mestre"}),403
    return jsonify({"ok":True,"chave":gerar_chave_usuario(nome,max(1,min(horas,72)))})

@app.route("/api/codigo/<cod>")
def api_codigo(cod):
    u = wifi_share.validar_codigo(cod)
    return jsonify({"ok":bool(u),"dados":u or {}})

@socketio.on("comando")
def cmd(d):
    try:
        if d.get("a")=="perfil": api_perfil(d["v"])
        if d.get("a")=="arma":
            p=d["p"]; a=d["a"]
            perfis.set_por_arma(a,p)
            proxy_core.C["POR_ARMA"] = perfis.carregar()["CAPA"]["POR_ARMA"]
    except: pass

if __name__=="__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", CFG["PROXY"]["PAINEL"])), allow_unsafe_werkzeug=True)
