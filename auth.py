import os, json, time, hashlib
BASE = os.path.dirname(os.path.abspath(__file__))
DB = f"{BASE}/db/chaves.json"
os.makedirs(os.path.dirname(DB), exist_ok=True)

# 🔐 CHAVE MESTRA OFICIAL — NÃO MUDA
CHAVE_MESTRA = os.environ.get("CHAVE_MESTRA", "okaida2026").strip()

NIVEIS = {
    CHAVE_MESTRA: {"nivel":"ACESSO MESTRE","dono":"Mestre Okaida","expira":9999999999,"ativo":True,"tudo":True},
}

def _carregar():
    try:
        if os.path.exists(DB):
            d = json.load(open(DB))
            for k,v in d.items(): NIVEIS[k] = v
    except: pass

def _salvar():
    try:
        d = {k:v for k,v in NIVEIS.items() if k != CHAVE_MESTRA}
        json.dump(d, open(DB,"w"), indent=2, ensure_ascii=False)
    except: pass

_carregar()

def chave_valida(chave):
    """✅ Retorna True SE E SOMENTE SE a chave for válida"""
    if not chave: return False
    chave = str(chave).strip()
    if not chave: return False
    # Chave mestra SEMPRE funciona
    if chave == CHAVE_MESTRA: return True
    # Outras chaves
    c = NIVEIS.get(chave)
    if not c or not c.get("ativo"): return False
    if c.get("expira",0) < time.time(): return False
    return True

def info_chave(chave):
    if not chave: return {"nivel":"CONVIDADO","valido":False}
    chave = str(chave).strip()
    if chave == CHAVE_MESTRA:
        return {"nivel":"ACESSO MESTRE","valido":True,"dono":"Mestre Okaida","tudo":True,"mestra":True}
    c = NIVEIS.get(chave)
    if not c: return {"nivel":"INVÁLIDO","valido":False}
    return {**c,"valido":c.get("ativo") and c.get("expira",0)>time.time(),"mestra":False}

def requer_login(funcao):
    """Decorator: BLOQUEIA a rota se não estiver logado"""
    from functools import wraps
    from flask import request, redirect, make_response, session
    @wraps(funcao)
    def wrapper(*args, **kwargs):
        k = request.cookies.get("okaida_key") or session.get("key") or request.args.get("key")
        if not chave_valida(k):
            r = make_response(redirect("/login?e=2"))
            r.delete_cookie("okaida_key")
            session.clear()
            return r
        return funcao(*args, **kwargs)
    return wrapper

def pagina_login(erro=None):
    """Retorna a tela de login (renderiza o arquivo templates/login.html)"""
    try:
        html = open(f"{BASE}/templates/login.html").read()
        if erro == "1": html = html.replace('<!--ERRO-->', '<div class="erro">❌ Chave incorreta</div>')
        if erro == "2": html = html.replace('<!--ERRO-->', '<div class="erro">🔒 Faça login para continuar</div>')
        return html
    except Exception as e:
        return f"""<html><body style=background:#050816;color:#fff;font-family:system-ui>
        <div style=max-width:400px;margin:100px auto>
        <h1>🔐 PROXY OKAIDA</h1>
        <form method=post><input name=key placeholder=CHAVE style=width:100%;padding:12px;margin:10px 0>
        <button style=width:100%;padding:12px;background:#7c3aed;color:#fff;border:0;border-radius:8px>ENTRAR</button></form>
        </div></body></html>"""

# Adiciona rota no app_web automaticamente
def injetar_rotas(app):
    from flask import request, redirect, make_response, session, render_template_string
    @app.route("/login", methods=["GET","POST"])
    def rota_login():
        if request.method == "POST":
            k = request.form.get("key","").strip()
            if chave_valida(k):
                r = make_response(redirect("/dash"))
                r.set_cookie("okaida_key", k, max_age=7*86400, httponly=True)
                session["key"] = k
                session["nivel"] = info_chave(k)["nivel"]
                return r
            return redirect("/login?e=1")
        return pagina_login(erro=request.args.get("e"))

    @app.route("/logout")
    def rota_logout():
        r = make_response(redirect("/login"))
        r.delete_cookie("okaida_key")
        session.clear()
        return r

    @app.route("/")
    def rota_home():
        k = request.cookies.get("okaida_key") or session.get("key")
        if chave_valida(k): return redirect("/dash")
        return redirect("/login")

print(f"   🔐 AUTH CARREGADO · CHAVE MESTRA = {CHAVE_MESTRA[:3]}***{CHAVE_MESTRA[-3:]}")
