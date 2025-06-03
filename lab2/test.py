def dpid_to_mac(self, dpid):
        mac = hex(int(dpid))[2:].zfill(12)  # Convert DPID to hex and pad with zeros
        mac = ':'.join(mac[i:i + 2] for i in range(0, len(mac), 2))  # Format as MAC address
        return mac

print(dpid_to_mac(None, '167838465'))  # Example usage
