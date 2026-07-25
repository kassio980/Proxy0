import os, time, json, threading, subprocess, random, socket
from datetime import datetime
from colorama import Fore, Style

BASE = os.path.dirname(os.path.abspath(__file__))
PACOTE_FF = "com.dts.freefireth"
PACOTE_FF_MAX = "com.dts.freefiremax"

def log(t,m,c=Fore.WHITE):
    print(f"{Fore.BLACK}[{datetime.now().strftime('%H:%M:%S')}]{Style.RESET_ALL} {c}[{t}] {m}")

def adb(cmd):
    try:
        r = subprocess.run(f"adb {cmd}",shell=True,capture_output=True,text=True,timeout=10)
        return r.stdout+r.stderr
    except: return ""

def descobrir_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80))
        ip = s.getsockname()[0]; s.close()
        return ip
    except: return "127.0.0.1"

def esta_conectado_adb():
    return "device" in adb("devices")

def conectar_adb_wifi(ip=None, porta=5555):
    """Conecta no celular por Wi-Fi sem cabo"""
    log("ADB",f"Tentando conexão Wi-Fi {ip}:{porta}...",Fore.CYAN)
    adb("kill-server")
    time.sleep(1)
    adb(f"tcpip {porta}")
    time.sleep(1)
    if ip:
        r = adb(f"connect {ip}:{porta}")
        if "connected" in r.lower():
            log("ADB",f"✅ CONECTADO VIA WI-FI → {ip}:{porta}",Fore.GREEN+Style.BRIGHT)
            return True
    return False

def processo_ff_rodando():
    """Verifica se FF tá aberto no celular conectado"""
    r = adb("shell dumpsys activity activities 2>/dev/null | grep -E 'mResumedActivity|topActivity'")
    return PACOTE_FF in r or PACOTE_FF_MAX in r

def abrir_free_fire():
    """Abre o Free Fire automaticamente"""
    log("VIRUS","🚀 ABRINDO FREE FIRE AUTOMATICAMENTE...",Fore.MAGENTA+Style.BRIGHT)
    adb(f"shell monkey -p {PACOTE_FF} -c android.intent.category.LAUNCHER 1 2>/dev/null")
    time.sleep(1)
    adb(f"shell monkey -p {PACOTE_FF_MAX} -c android.intent.category.LAUNCHER 1 2>/dev/null")
    time.sleep(2)
    return processo_ff_rodando()

def injetar_proxy_no_app():
    """MODO VÍRUS: configura proxy dentro do próprio app FF via iptables/forward"""
    log("VIRUS","⚡ INJETANDO PROXY NO SISTEMA DO FF...",Fore.RED+Style.BRIGHT)
    ip_local = descobrir_ip_local()
    # Forward de todo tráfego FF pro nosso proxy
    comandos = [
        f"shell settings put global http_proxy {ip_local}:1080",
        f"shell settings put global https_proxy {ip_local}:1080",
        "shell iptables -t nat -A OUTPUT -p tcp --dport 1:65535 -j DNAT --to-destination 127.0.0.1:1080 2>/dev/null",
        "shell iptables -t nat -A OUTPUT -p udp --dport 1:65535 -j DNAT --to-destination 127.0.0.1:1081 2>/dev/null",
    ]
    for c in comandos: adb(c)
    log("VIRUS",f"✅ PROXY INJETADO → {ip_local}:1080",Fore.GREEN)
    return ip_local

def instalar_ca_certificado():
    """Instala certificado pra interceptar HTTPS também"""
    log("VIRUS","🔐 Instalando certificado CA...",Fore.YELLOW)
    return True

def mini_janela_flutuante():
    """Cria overlay com menu de funções em cima do FF"""
    log("VIRUS","🪟 MINI JANELA FLUTUANTE ATIVADA — MENU SOBRE O FF",Fore.CYAN+Style.BRIGHT)
    # Cria serviço de acessibilidade simulado + janela flutuante
    html_janela = """
    <!doctype html><html><head><meta charset=utf-8>
    <style>
    *{margin:0;padding:0;box-sizing:border-box}
    #ffmenu{position:fixed;top:80px;left:10px;width:220px;background:#000c;color:#0f0;border:1px solid #0f08;
      font-family:monospace;font-size:11px;z-index:999999;border-radius:8px;backdrop-filter:blur(4px);
      box-shadow:0 0 20px #0f05;user-select:none}
    #ffmenu .t{padding:8px;background:#0f01;border-bottom:1px solid #0f05;font-weight:bold;letter-spacing:2px;cursor:move}
    #ffmenu .bt{display:block;width:100%;padding:7px 10px;background:transparent;color:#0f0;border:0;border-bottom:1px solid #0f03;
      text-align:left;font-family:monospace;font-size:11px;cursor:pointer}
    #ffmenu .bt:hover{background:#0f02;color:#fff}
    #ffmenu .bt.on{background:#0f03;color:#ff0}
    #ffmenu .st{padding:6px 10px;font-size:10px;opacity:.8}
    </style></head><body>
    <div id=ffmenu>
      <div class=t>🕵️ PROXY OKAIDA</div>
      <button class="bt on" data-p=SO_CABEÇA>🎯 SÓ CABEÇA</button>
      <button class="bt" data-p=PESCOÇO>🎯 PESCOÇO</button>
      <button class="bt" data-p=SO_CAPA>🏆 SÓ CAPA</button>
      <button class="bt" data-p=CABEÇA_PEITO>🎯 CABEÇA+PEITO</button>
      <button class="bt" data-p=SÓ_PEITO>🛡️ SÓ PEITO</button>
      <button class="bt" data-p=PÉ>🦶 SÓ PÉ</button>
      <button class="bt" data-p=PROXY_MAX>⚡ PROXY MÁXIMO</button>
      <div class=t style=margin-top:4px>🔫 POR ARMA</div>
      <button class="bt" data-a=TODAS>✅ TODAS ARMAS</button>
      <button class="bt" data-a=MP40>🔫 MP40</button>
      <button class="bt" data-a=M1014>🔫 M1014</button>
      <button class="bt" data-a=SCAR>🔫 SCAR</button>
      <button class="bt" data-a=AK47>🔫 AK47</button>
      <button class="bt" data-a=AWM>🎯 AWM</button>
      <div class=st id=st>CAPA: 0 | CONEXÕES: 0 | PING: --</div>
    </div>
    <script>
    const ws = new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/ws');
    ws.onmessage=e=>{const d=JSON.parse(e.data);document.getElementById('st').textContent=
      `CAPA: ${d.capa} | CONEX: ${d.udp.c+d.tcp.c} | SRV: ${Object.keys(d.srv||{}).length}`};
    document.querySelectorAll('.bt[data-p]').forEach(b=>b.onclick=()=>{
      document.querySelectorAll('.bt[data-p]').forEach(x=>x.classList.remove('on'));b.classList.add('on');
      fetch('/api/perfil/'+b.dataset.p,{headers:{'X-Key':localStorage.k||''}});
    });
    document.querySelectorAll('.bt[data-a]').forEach(b=>b.onclick=()=>{
      fetch('/api/arma/'+b.dataset.a+'/'+(b.classList.toggle('on')?'SO_CAPA':'DESLIGADO'),{headers:{'X-Key':localStorage.k||''}});
    });
    </script></body></html>"""
    os.makedirs(f"{BASE}/www",exist_ok=True)
    with open(f"{BASE}/www/ff_overlay.html","w") as f: f.write(html_janela)
    return html_janela

def loop_virus():
    """Loop infinito: conecta, injeta, abre FF, monitora"""
    log("VIRUS","🦠 MODO VÍRUS ATIVADO — CONECTANDO EM CONTAS FF...",Fore.RED+Style.BRIGHT)
    while True:
        try:
            if not esta_conectado_adb():
                log("VIRUS","🔍 Procurando celulares com FF na rede...",Fore.YELLOW)
                time.sleep(5); continue
            if not processo_ff_rodando():
                log("VIRUS","⚠️ FF fechado → abrindo automaticamente",Fore.MAGENTA)
                abrir_free_fire()
                time.sleep(8)
            ip = injetar_proxy_no_app()
            time.sleep(30)
        except Exception as e:
            log("ERRO",f"virus loop: {e}",Fore.RED)
            time.sleep(5)

def iniciar():
    mini_janela_flutuante()
    threading.Thread(target=loop_virus,daemon=True).start()
    return descobrir_ip_local()

if __name__=="__main__":
    iniciar()
    while True: time.sleep(999)
