import socket, time, json, os, random, string, threading, qrcode, io, base64
from datetime import datetime
from colorama import Fore, Style

BASE = os.path.dirname(os.path.abspath(__file__))
DB = f"{BASE}/db/keys.json"

def meu_ip_local():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80)); ip=s.getsockname()[0]; s.close()
        return ip
    except: return "127.0.0.1"

def gerar_codigo_compartilhamento(tipo="WIFI", horas=7):
    """Gera código de 6 dígitos + dados completos"""
    d = json.load(open(DB)) if os.path.exists(DB) else {"chaves_geradas":{}}
    while True:
        codigo = ''.join(random.choices(string.digits, k=6))
        if codigo not in d["chaves_geradas"]: break
    ip = meu_ip_local()
    dados = {
        "codigo": codigo,
        "tipo": tipo,
        "ip": ip,
        "porta_socks": 1080,
        "porta_udp": 1081,
        "porta_painel": 8888,
        "criado": time.time(),
        "expira": time.time() + horas*3600,
        "nome": f"PROXY OKAIDA · {ip}",
        "horas": horas
    }
    d["chaves_geradas"][codigo] = dados
    os.makedirs(os.path.dirname(DB),exist_ok=True)
    with open(DB,"w") as f: json.dump(d,f,indent=2,ensure_ascii=False)
    return dados

def gerar_qr_wifi(dados):
    """QR Code no formato Android: WIFI:T:WPA;S:ssid;P:senha;;"""
    ssid = f"PROXY-OKAIDA-{dados['codigo']}"
    senha = dados["codigo"] + dados["codigo"][::-1]
    texto = f"WIFI:T:WPA;S:{ssid};P:{senha};;"
    qr = qrcode.QRCode(box_size=2,border=1)
    qr.add_data(texto); qr.make(fit=True)
    img = qr.make_image(fill_color="black",back_color="white")
    buf = io.BytesIO(); img.save(buf,format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return {"ssid":ssid,"senha":senha,"qr_b64":b64,"texto":texto}

def gerar_qr_proxy(dados):
    """QR Code com config do proxy SOCKS5"""
    texto = f"socks5://{dados['ip']}:{dados['porta_socks']}#{dados['codigo']}"
    qr = qrcode.QRCode(box_size=3,border=1)
    qr.add_data(texto); qr.make(fit=True)
    img = qr.make_image(fill_color="#00ff00",back_color="#000000")
    buf = io.BytesIO(); img.save(buf,format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def validar_codigo(codigo):
    if not os.path.exists(DB): return False
    d = json.load(open(DB))
    u = d["chaves_geradas"].get(codigo.strip())
    if not u: return False
    if time.time() > u["expira"]: return False
    return u

def codigos_ativos():
    if not os.path.exists(DB): return []
    d = json.load(open(DB))
    agora = time.time()
    return [v for v in d["chaves_geradas"].values() if v.get("expira",0) > agora]

def servidor_http_simples(porta=8123):
    """Servidor mínimo pra quem escanear o QR baixar a config"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class H(BaseHTTPRequestHandler):
        def log_message(self,*a,**k): pass
        def do_GET(self):
            cod = self.path.strip("/").split("?")[0]
            u = validar_codigo(cod)
            if not u:
                self.send_response(404); self.end_headers()
                self.wfile.write(b"CODIGO INVALIDO OU EXPIRADO")
                return
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(json.dumps(u,indent=2).encode())
    try:
        HTTPServer(("0.0.0.0",porta),H).serve_forever()
    except: pass

def iniciar():
    t = threading.Thread(target=servidor_http_simples,daemon=True); t.start()
    dados = gerar_codigo_compartilhamento()
    qr_wifi = gerar_qr_wifi(dados)
    qr_proxy = gerar_qr_proxy(dados)
    print(f"\n{Fore.GREEN}{Style.BRIGHT}📶 COMPARTILHAMENTO WI-FI ATIVADO{Style.RESET_ALL}")
    print(f"   🔢 CÓDIGO:      {Fore.YELLOW}{Style.BRIGHT}{dados['codigo']}{Style.RESET_ALL}")
    print(f"   🌐 IP LOCAL:    {dados['ip']}:1080")
    print(f"   ⏰ VÁLIDO POR:  {dados['horas']} horas")
    print(f"   📶 REDE:        {qr_wifi['ssid']}")
    print(f"   🔑 SENHA WI-FI: {qr_wifi['senha']}")
    print(f"   🖥️  PAINEL:     http://{dados['ip']}:8888?key={dados['codigo']}")
    return {"dados":dados,"qr_wifi":qr_wifi,"qr_proxy_b64":qr_proxy}

if __name__=="__main__":
    print(iniciar())
