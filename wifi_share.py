import os, time, json, random, base64, io
BASE = os.path.dirname(os.path.abspath(__file__))
DB = f"{BASE}/db/wifi_codigos.json"
os.makedirs(os.path.dirname(DB), exist_ok=True)

# Carrega libs com fallback
try: import qrcode
except: qrcode = None
try: from PIL import Image
except: Image = None

CODIGOS = {}

def _carregar():
    global CODIGOS
    try:
        if os.path.exists(DB): CODIGOS = json.load(open(DB))
    except: CODIGOS = {}

def _salvar():
    try: json.dump(CODIGOS, open(DB,"w"), indent=2, ensure_ascii=False)
    except: pass

def gerar_codigo_6d():
    return "".join([str(random.randint(0,9)) for _ in range(6)])

def gerar_codigo_compartilhamento(tempo_horas=7, proxy_host="0.0.0.0", proxy_socks=1080, proxy_udp=1081):
    _carregar()
    cod = gerar_codigo_6d()
    agora = time.time()
    CODIGOS[cod] = {
        "codigo": cod,
        "criado": agora,
        "expira": agora + (tempo_horas * 3600),
        "valido": True,
        "proxy_host": proxy_host,
        "proxy_socks": proxy_socks,
        "proxy_udp": proxy_udp,
        "usos": 0,
        "tempo_horas": tempo_horas,
        "wifi_ssid": f"OKAIDA-{cod}",
        "wifi_senha": f"okaida{cod}"
    }
    _salvar()
    return CODIGOS[cod]

def validar_codigo(cod):
    _carregar()
    c = CODIGOS.get(str(cod).strip())
    if not c: return None
    if not c["valido"] or time.time() > c["expira"]: return None
    c["usos"] += 1; CODIGOS[cod] = c; _salvar()
    return c

def _qr_para_b64(texto):
    if not qrcode or not Image: return ""
    try:
        qr = qrcode.QRCode(border=2, box_size=8)
        qr.add_data(texto); qr.make(fit=True)
        img = qr.make_image(fill_color="#0d1338", back_color="white").convert("RGB")
        buf = io.BytesIO(); img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except: return ""

def gerar_qr_wifi(dados):
    """QR que conecta automaticamente no Wi-Fi do proxy"""
    ssid = dados.get("wifi_ssid","OKAIDA"); pwd = dados.get("wifi_senha","okaida")
    return _qr_para_b64(f"WIFI:T:WPA;S:{ssid};P:{pwd};;")

def gerar_qr_proxy(dados):
    """QR com todas configs do proxy para importar 1 toque"""
    txt = json.dumps({
        "h":dados.get("proxy_host",""),
        "s":dados.get("proxy_socks",1080),
        "u":dados.get("proxy_udp",1081),
        "c":dados.get("codigo",""),
        "t":dados.get("tempo_horas",7)
    }, separators=(",",":"))
    return _qr_para_b64(txt)

def listar_ativos():
    _carregar()
    return [c for c in CODIGOS.values() if c["valido"] and time.time()<c["expira"]]

def iniciar():
    _carregar()
    print(f"   📶 WI-FI SHARE OK · {len(listar_ativos())} códigos ativos")

if __name__=="__main__":
    d = gerar_codigo_compartilhamento()
    print("Código:", d["codigo"])
    print("Expira em:", d["tempo_horas"],"h")

def listar_todos():
    _carregar()
    return sorted(CODIGOS.values(), key=lambda c:-c["criado"])[:30]

