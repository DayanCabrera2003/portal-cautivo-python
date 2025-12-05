import subprocess
import sys
import time
from firewall.network_manager import setup_captive_dns, cleanup_captive_dns

HOTSPOT_SSID = "PortalCautivo"
HOTSPOT_PASS = "password123"  # Cambiado: sin caracteres especiales
PORTAL_PORT = 8080
IPTABLES_BACKUP = "iptables-backup.txt"

def run_cmd(cmd, check=True):
    print(f"Ejecutando: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ Error ejecutando: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def backup_iptables():
    print("Haciendo backup de reglas iptables...")
    run_cmd(f"sudo iptables-save > {IPTABLES_BACKUP}")

def restore_iptables():
    print("Restaurando reglas iptables originales...")
    run_cmd(f"sudo iptables-restore < {IPTABLES_BACKUP}")

def get_wifi_interfaces():
    """Obtiene solo interfaces WiFi disponibles"""
    result = run_cmd(
        "nmcli device status | grep wifi | grep -v 'p2p' | awk '{print $1}'", 
        check=False
    )
    interfaces = result.stdout.strip().split('\n')
    return [iface for iface in interfaces if iface]

def create_hotspot(iface):
    print("Preparando interfaz para hotspot...")
    
    # Verificar si la interfaz está conectada a otra red
    result = run_cmd(f"nmcli device status | grep {iface} | awk '{{print $3}}'", check=False)
    status = result.stdout.strip()
    
    if "connected" in status:
        print(f"⚠️  Interfaz {iface} está conectada. Desconectando...")
        run_cmd(f"nmcli device disconnect {iface}", check=False)
        print("⏳ Esperando a que la interfaz esté lista...")
        time.sleep(3)
    
    # Verificar si ya existe un hotspot activo
    result = run_cmd("nmcli connection show | grep Hotspot", check=False)
    if result.stdout.strip():
        print("🔄 Hotspot existente detectado. Eliminando...")
        run_cmd("nmcli connection delete Hotspot", check=False)
        time.sleep(1)
    
    # Asegurarse de que la interfaz está habilitada
    print(f"🔌 Habilitando interfaz {iface}...")
    run_cmd(f"nmcli radio wifi on", check=False)
    run_cmd(f"nmcli device set {iface} managed yes", check=False)
    time.sleep(2)
    
    # Verificar que la interfaz está disponible
    for attempt in range(3):
        result = run_cmd(f"nmcli device status | grep {iface}", check=False)
        if "unavailable" not in result.stdout and "disconnected" in result.stdout:
            break
        print(f"⏳ Esperando a que {iface} esté disponible (intento {attempt + 1}/3)...")
        time.sleep(2)
    
    print(f"📡 Creando hotspot WiFi en {iface}...")
    print("📻 Configurando banda 2.4GHz (canal 6) para máxima compatibilidad...")
    
    # Eliminar cualquier hotspot previo
    run_cmd("nmcli connection delete Hotspot 2>/dev/null", check=False)
    
    # Crear conexión AP con configuración explícita
    print("⚙️  Creando perfil de conexión...")
    run_cmd(f"nmcli connection add type wifi ifname {iface} con-name Hotspot autoconnect yes ssid {HOTSPOT_SSID}", check=False)
    
    print("⚙️  Configurando modo Access Point...")
    run_cmd(f"nmcli connection modify Hotspot 802-11-wireless.mode ap", check=False)
    run_cmd(f"nmcli connection modify Hotspot 802-11-wireless.band bg", check=False)
    run_cmd(f"nmcli connection modify Hotspot 802-11-wireless.channel 6", check=False)
    
    # IMPORTANTE: Forzar que el SSID sea visible (no oculto)
    run_cmd(f"nmcli connection modify Hotspot 802-11-wireless.hidden no", check=False)
    
    print("⚙️  Configurando red y seguridad...")
    run_cmd(f"nmcli connection modify Hotspot ipv4.method shared", check=False)
    run_cmd(f"nmcli connection modify Hotspot ipv4.addresses 10.42.0.1/24", check=False)
    run_cmd(f"nmcli connection modify Hotspot ipv6.method ignore", check=False)
    
    # Forzar WPA2-PSK (mejor compatibilidad que WPA3)
    run_cmd(f"nmcli connection modify Hotspot wifi-sec.key-mgmt wpa-psk", check=False)
    run_cmd(f"nmcli connection modify Hotspot wifi-sec.psk '{HOTSPOT_PASS}'", check=False)
    run_cmd(f"nmcli connection modify Hotspot wifi-sec.proto rsn", check=False)  # WPA2
    run_cmd(f"nmcli connection modify Hotspot wifi-sec.pairwise ccmp", check=False)  # AES
    
    # Desactivar power management que puede causar problemas
    run_cmd(f"nmcli connection modify Hotspot 802-11-wireless.powersave 2", check=False)
    
    print("🚀 Activando hotspot...")
    result = run_cmd(f"nmcli connection up Hotspot", check=False)
    
    if result.returncode != 0:
        print(f"⚠️  Error activando: {result.stderr}")
    
    time.sleep(5)  # Esperar a que el hotspot se active y empiece a transmitir

def get_hotspot_ip(iface):
    """Obtener la IP asignada al hotspot"""
    for i in range(5):
        result = run_cmd(
            f"ip -4 addr show {iface} | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){{3}}'", 
            check=False
        )
        ip = result.stdout.strip()
        if ip:
            print(f"✓ IP del hotspot detectada: {ip}")
            return ip
        time.sleep(1)
    
    print("⚠ No se pudo detectar IP del hotspot, usando default 10.42.0.1")
    return "10.42.0.1"

def verify_hotspot():
    """Verificar que el hotspot esté activo"""
    print("\n🔍 Verificando hotspot...")
    result = run_cmd("nmcli connection show --active | grep Hotspot", check=False)
    if "Hotspot" in result.stdout:
        print("✓ Hotspot activo en NetworkManager")
        
        # Mostrar información del hotspot
        print("\n📋 Información del hotspot:")
        run_cmd("nmcli device wifi show-password", check=False)
        
        # Verificar que la interfaz está en modo AP
        result = run_cmd("iw dev | grep -A 5 'type AP'", check=False)
        if "type AP" in result.stdout:
            print("✓ Interfaz en modo Access Point")
        else:
            print("⚠️  Interfaz NO está en modo Access Point")
            return False
        
        # Verificar el canal y frecuencia actual
        print("\n📻 Configuración del canal:")
        result = run_cmd("iw dev wlo1 info | grep -E 'channel|freq'", check=False)
        print(result.stdout)
        
        # Verificar DHCP server (dnsmasq)
        print("\n🔍 Verificando servidor DHCP...")
        result = run_cmd("ps aux | grep dnsmasq | grep -v grep", check=False)
        if "dnsmasq" in result.stdout:
            print("✓ Servidor DHCP (dnsmasq) está corriendo")
        else:
            print("⚠️  Servidor DHCP NO está corriendo")
            print("   NetworkManager debería iniciarlo automáticamente")
            print("   Verifica los logs: journalctl -u NetworkManager -n 50")
        
        # Listar redes WiFi visibles para verificar que el hotspot está transmitiendo
        print("\n📡 Verificando que el hotspot sea visible...")
        result = run_cmd("nmcli device wifi list | grep PortalCautivo", check=False)
        if "PortalCautivo" in result.stdout:
            print("✓ ¡El hotspot 'PortalCautivo' ES VISIBLE!")
        else:
            print("⚠️  El hotspot NO aparece en el escaneo WiFi")
        
        return True
    else:
        print("❌ Hotspot NO está activo")
        return False

def main():
    if not sys.platform.startswith("linux"):
        print("Este script solo funciona en Linux.")
        sys.exit(1)
    if subprocess.getoutput("whoami") != "root":
        print("Debes ejecutar este script como root.")
        sys.exit(1)

    print("\n" + "="*50)
    print("🌐 CONFIGURANDO PORTAL CAUTIVO")
    print("="*50 + "\n")

    backup_iptables()
    
    # Configurar dnsmasq para interceptar DNS
    print("📝 Configurando DNS para detección de portal cautivo...")
    if not setup_captive_dns():
        print("⚠️  Advertencia: No se pudo configurar DNS automático")
        print("   El portal funcionará pero puede no detectarse automáticamente")
    
    interfaces = get_wifi_interfaces()
    if not interfaces:
        print("❌ No se encontró interfaz WiFi")
        sys.exit(1)
    
    hotspot_iface = interfaces[0] if len(interfaces) == 1 else interfaces[0]  # Usar wlo1 por defecto
    print(f"📡 Usando interfaz: {hotspot_iface}")
    
    # Verificar capacidades de la interfaz
    print(f"\n🔍 Verificando capacidades de {hotspot_iface}...")
    result = run_cmd(f"iw phy | grep -A 20 'Supported interface modes' | grep 'AP'", check=False)
    if "AP" in result.stdout:
        print("✓ La interfaz soporta modo Access Point (AP)")
    else:
        print("❌ La interfaz NO soporta modo Access Point")
        print("   Tu tarjeta WiFi no puede crear un hotspot.")
        sys.exit(1)

    create_hotspot(hotspot_iface)
    
    if not verify_hotspot():
        print("\n❌ Error: El hotspot no se pudo crear correctamente")
        print("\n🔧 Diagnóstico adicional:")
        print("1. Ejecuta: nmcli connection show")
        print("2. Ejecuta: nmcli device status")
        print("3. Ejecuta: iw dev")
        sys.exit(1)
    
    gateway_ip = get_hotspot_ip(hotspot_iface)

    print("\n" + "="*50)
    print("🌐 PORTAL CAUTIVO CONFIGURADO")
    print("="*50)
    print(f"📶 SSID: {HOTSPOT_SSID}")
    print(f"🔐 Password: {HOTSPOT_PASS}")
    print(f"🌍 IP Gateway: {gateway_ip}")
    print(f"🔌 Puerto: {PORTAL_PORT}")
    print("\n📱 INSTRUCCIONES:")
    print(f"1. En tu móvil, busca WiFi '{HOTSPOT_SSID}'")
    print(f"2. Conecta con password '{HOTSPOT_PASS}'")
    print(f"3. Abre navegador (cualquier página HTTP)")
    print(f"4. Serás redirigido al portal cautivo")
    print("\n🛑 Para detener: Ctrl+C luego ejecuta:")
    print("   sudo python3 setup_portal.py restore")
    print("="*50 + "\n")

    print("🚀 Lanzando servidor del portal cautivo...")
    
    # Ejecutar en primer plano para ver errores
    # main.py se encargará de configurar el firewall
    try:
        subprocess.run(["python3", "main.py"])
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo servidor...")
        restore_iptables()
        run_cmd("nmcli connection down Hotspot", check=False)
        print("✓ Portal cautivo detenido")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_iptables()
        run_cmd("nmcli connection down Hotspot", check=False)
        # Limpiar configuración DNS usando el módulo network_manager
        cleanup_captive_dns()
        print("✓ Portal cautivo detenido y reglas restauradas")
        sys.exit(0)
    
    main()