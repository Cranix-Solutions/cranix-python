import netifaces
from ipaddress import IPv4Interface
from typing import List, Any
from .common import *

def network_to_netifaces():
    """Ermittelt die Netzwerke, zu denen jede Netzwerkschnittstelle gehört, mit netifaces."""

    results = {}

    # 1. Liste aller Schnittstellennamen abrufen
    interfaces = netifaces.interfaces()

    logger.debug(f"Interfaces: {interfaces}")
    logger.error(f"No interfaces found") if len(interfaces) == 0 else ...

    for iface in interfaces:
        # 2. Adressen für die aktuelle Schnittstelle abrufen
        adressen = netifaces.ifaddresses(iface)
        logger.debug(f"Adressen: {adressen}")
        # 3. Nur die Adressen der Familie AF_INET (IPv4) betrachten
        if iface.find(":") == -1 and netifaces.AF_INET in adressen:

            # Eine Schnittstelle kann mehrere IPv4-Adressen haben.
            for adr_info in adressen[netifaces.AF_INET]:
                # Wir benötigen 'addr' (IP) und 'netmask' (Subnetzmaske)
                ip_adresse = adr_info.get('addr')
                subnet_maske = adr_info.get('netmask')

                # Sicherstellen, dass beide Werte vorhanden sind
                if ip_adresse and subnet_maske:
                    try:
                        # IP und Maske im CIDR-Format zusammenfügen
                        cidr_notation = f"{ip_adresse}/{subnet_maske}"

                        # IPv4Interface-Objekt erstellen, das die Netzwerkadresse berechnet
                        interface_obj = IPv4Interface(cidr_notation)

                        # Netzwerkadresse im CIDR-Format extrahieren
                        network = str(interface_obj.network)

                        logger.debug(f"Network adress: {network}")

                        # Ergebnis speichern (ggf. mit Index, falls mehrere IPs pro NIC)
                        results[network] = {}
                        results[network]['dev'] = f"{iface}"
                        results[network]['ip'] = f"{ip_adresse}"

                    except Exception as e:
                        # Fehlerbehandlung für ungültige IP/Masken
                        results[f"{iface}"] = f"Fehler bei IPv4-Berechnung: {e}"

    return results

def get_default_gateway_interface():
    """
    Returns the name of the network interface used for the default route.
    Returns None if no default gateway is found.
    """
    # Get all default gateways
    gateways = netifaces.gateways()

    # 'default' returns a dict mapping Address Family to (gateway, interface)
    # AF_INET is the constant for IPv4
    default_route = gateways.get('default', {}).get(netifaces.AF_INET)

    if default_route:
        logger.debug(f"Default route: {default_route}")
        # default_route is a tuple: (gateway_ip, interface_name)
        return default_route[1]

    return None

def get_default_interface_ip():
    """
    Finds the default network interface and returns its IPv4 address.
    """
    interface_name = get_default_gateway_interface()
    logger.error("No default route found") if not interface_name else ...


    # Get addresses associated with the interface
    addresses = netifaces.ifaddresses(interface_name)

    # Extract the IPv4 info
    ipv4_info = addresses.get(netifaces.AF_INET)

    if ipv4_info:
        # ipv4_info is a list of dicts; usually the first one is the primary IP
        logger.debug(f"IPv4: {ipv4_info}")
        return ipv4_info[0].get('addr')

    return None

def get_rooms() -> List[Any]:
    """
    Returns the list of the rooms on the server
    """

    rooms = []
    cmd = f'/usr/sbin/crx_api.sh GET rooms/all'
    try:
        rooms = json.load(os.popen(cmd))
        logger.debug(f"Rooms: {rooms}")
    except:
        pass
        logger.error(f"Unable to get rooms")
    return rooms

# Usage
if __name__ == "__main__":
    ip_address = get_default_interface_ip()
    print(f"IP Address of default device: {ip_address}")
    print(f"There are {len(get_rooms())} rooms in the school")
