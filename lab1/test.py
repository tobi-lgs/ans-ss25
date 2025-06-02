import ipaddress

dst_ip = "10.2.1.3"
dst_network = ipaddress.ip_network(f"{dst_ip}/{24}", strict=False)
dst_switch_ip = dst_network.network_address + 1
print(f"Target switch IP for host {dst_ip} is: {dst_switch_ip}")