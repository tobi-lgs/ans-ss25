# Lab1 Notes

## First test with the ryu 'simple_switch' app and single switch topology

Start the Ryu controller with the `simple_switch` application. This application is a basic switch that forwards packets based on MAC addresses.

```bash
ryu-manager ryu.app.simple_switch
```

Start the Mininet single switch topology with three hosts and with the `--controller` option to specify the Ryu controller.

```bash
sudo mn --topo single,3 --mac --controller remote --switch ovsk --test pingall
```

Don't forget to clean up the Mininet environment after testing.

```bash
sudo mn -c
```

## Second test with the ryu 'simple_switch' app and custom topology

Network topology and configuration for this lab.

![Network topology and configuration for this lab.](topology.png)

Launch the python script with the custom topology, expecting a remote controller.
    
```bash
sudo python3 run_network.py
```

Again, use the ryu controller with the `simple_switch` application and test it with the pingall command.

```bash
mininet> pingall
*** Ping: testing ping reachability
ext -> X X X
h1 -> X h2 ser
h2 -> X h1 ser
ser -> X h1 h2
*** Results: 50% dropped (6/12 received)
```

This indicates a successful topology setup. Additionally to the pingall command, you can also use the `iperf` command to test bandwidth between hosts.

```bash
mininet> iperf h1 h2
*** Iperf: testing TCP bandwidth between h1 and h2
*** Results: ['12.1 Mbits/sec', '14.8 Mbits/sec']
```

Finally, every host should be able to ping its own gateway, but not the gateways of others.

```bash
mininet> h1 ping 10.0.1.1 -c1
PING 10.0.1.1 (10.0.1.1) 56(84) bytes of data.
From 10.0.1.2 icmp_seq=1 Destination Host Unreachable

--- 10.0.1.1 ping statistics ---
1 packets transmitted, 0 received, +1 errors, 100% packet loss, time 0ms
```

It seems that this is not working with the `simple_swithch` application.

Check the fowarding table entries.


```bash
 sudo ovs-ofctl dump-flows s1
 cookie=0x0, duration=102.800s, table=0, n_packets=3, n_bytes=238, in_port="s1-eth2",dl_src=26:dc:3b:41:cd:a0,dl_dst=e6:15:16:c0:ec:90 actions=output:"s1-eth1"
 cookie=0x0, duration=102.771s, table=0, n_packets=2, n_bytes=140, in_port="s1-eth1",dl_src=e6:15:16:c0:ec:90,dl_dst=26:dc:3b:41:cd:a0 actions=output:"s1-eth2"
 cookie=0x0, duration=102.612s, table=0, n_packets=3, n_bytes=238, in_port="s1-eth3",dl_src=52:da:c1:61:8a:86,dl_dst=e6:15:16:c0:ec:90 actions=output:"s1-eth1"
 cookie=0x0, duration=102.590s, table=0, n_packets=2, n_bytes=140, in_port="s1-eth1",dl_src=e6:15:16:c0:ec:90,dl_dst=52:da:c1:61:8a:86 actions=output:"s1-eth3"
 cookie=0x0, duration=102.296s, table=0, n_packets=3, n_bytes=238, in_port="s1-eth3",dl_src=52:da:c1:61:8a:86,dl_dst=26:dc:3b:41:cd:a0 actions=output:"s1-eth2"
 cookie=0x0, duration=102.275s, table=0, n_packets=2, n_bytes=140, in_port="s1-eth2",dl_src=26:dc:3b:41:cd:a0,dl_dst=52:da:c1:61:8a:86 actions=output:"s1-eth3"
```

Explanation of the output:

- `cookie=0x0`: An identifier used by the controller to track flows (not typically important for simple switches).

- `duration=102.800s`: How long this flow has been in the switch's table.

- `table=0`: Refers to OpenFlow table 0 (the default).

- `n_packets=3`: Number of packets matched by this flow so far.

- `n_bytes=238`: Total bytes matched.

- `in_port="s1-eth2"`: The incoming interface.

- `dl_src=26:dc:3b:41:cd:a0`: Source MAC address.

- `dl_dst=e6:15:16:c0:ec:90`: Destination MAC address.

- `actions=output:"s1-eth1"`: Packets matching this flow should be forwarded out s1-eth1.

s1:

| **Cookie** | **Duration (s)** | **Table** | **Packets** | **Bytes** | **In Port**  | **Source MAC**           | **Destination MAC**      | **Action (Output Port)** |
|------------|------------------|-----------|-------------|-----------|--------------|---------------------------|---------------------------|---------------------------|
| 0x0        | 102.800          | 0         | 3           | 238       | s1-eth2      | 26:dc:3b:41:cd:a0         | e6:15:16:c0:ec:90         | s1-eth1                   |
| 0x0        | 102.771          | 0         | 2           | 140       | s1-eth1      | e6:15:16:c0:ec:90         | 26:dc:3b:41:cd:a0         | s1-eth2                   |
| 0x0        | 102.612          | 0         | 3           | 238       | s1-eth3      | 52:da:c1:61:8a:86         | e6:15:16:c0:ec:90         | s1-eth1                   |
| 0x0        | 102.590          | 0         | 2           | 140       | s1-eth1      | e6:15:16:c0:ec:90         | 52:da:c1:61:8a:86         | s1-eth3                   |
| 0x0        | 102.296          | 0         | 3           | 238       | s1-eth3      | 52:da:c1:61:8a:86         | 26:dc:3b:41:cd:a0         | s1-eth2                   |
| 0x0        | 102.275          | 0         | 2           | 140       | s1-eth2      | 26:dc:3b:41:cd:a0         | 52:da:c1:61:8a:86         | s1-eth3                   |

s2:

| **Cookie** | **Duration (s)** | **Table** | **Packets** | **Bytes** | **In Port**  | **Source MAC**           | **Destination MAC**      | **Action (Output Port)** |
|------------|------------------|-----------|-------------|-----------|--------------|---------------------------|---------------------------|---------------------------|
| 0x0        | 1431.181         | 0         | 3           | 238       | s2-eth1      | 8a:f1:d9:63:d5:8e         | 0e:20:33:fc:8f:3b         | s2-eth2                   |
| 0x0        | 1431.052         | 0         | 2           | 140       | s2-eth2      | 0e:20:33:fc:8f:3b         | 8a:f1:d9:63:d5:8e         | s2-eth1                   |
| 0x0        | 1430.838         | 0         | 3           | 238       | s2-eth1      | 8a:f1:d9:63:d5:8e         | e6:37:ec:5a:d6:61         | s2-eth2                   |
| 0x0        | 1430.724         | 0         | 2           | 140       | s2-eth2      | e6:37:ec:5a:d6:61         | 8a:f1:d9:63:d5:8e         | s2-eth1                   |

s3:

| **Cookie** | **Duration (s)** | **Table** | **Packets** | **Bytes** | **In Port**  | **Source MAC**           | **Destination MAC**      | **Action (Output Port)** |
|------------|------------------|-----------|-------------|-----------|--------------|---------------------------|---------------------------|---------------------------|
| 0x0        | 1487.098         | 0         | 3           | 238       | s3-eth3      | 8a:f1:d9:63:d5:8e         | 0e:20:33:fc:8f:3b         | s3-eth2                   |
| 0x0        | 1487.022         | 0         | 2           | 140       | s3-eth2      | 0e:20:33:fc:8f:3b         | 8a:f1:d9:63:d5:8e         | s3-eth3                   |
| 0x0        | 1486.764         | 0         | 3           | 238       | s3-eth3      | 8a:f1:d9:63:d5:8e         | e6:37:ec:5a:d6:61         | s3-eth2                   |
| 0x0        | 1486.694         | 0         | 2           | 140       | s3-eth2      | e6:37:ec:5a:d6:61         | 8a:f1:d9:63:d5:8e         | s3-eth3                   |

## Task 1: Everyone Is Learning, Including Switches

Run mininet with the topology defined in the python script.

```bash
sudo python3 run_network.py
```

Start the custom controller.

```bash
ryu-manager ans_controller.py
```

Test the network by pinging `h2` from `h1`.

```bash
mininet> h1 ping -c1 h2
PING 10.0.1.3 (10.0.1.3) 56(84) bytes of data.
64 bytes from 10.0.1.3: icmp_seq=1 ttl=64 time=42.9 ms

--- 10.0.1.3 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 42.925/42.925/42.925/0.000 ms
```

Then try to ping other connections with the `pingall` command.

```bash
mininet> pingall
*** Ping: testing ping reachability
ext -> X X X
h1 -> X h2 X
h2 -> X h1 X
ser -> X X X
*** Results: 83% dropped (2/12 received)
```

As expected, the ping between `h1` and `h2` works, but the ping to the external network does not work. Also iperf between `h1` and `h2` doesn't work yet.

See what the switch `s1` has learned:

```bash
vagrant@ans-vm:/vagrant/lab1$ sudo ovs-ofctl dump-flows s1
  cookie=0x0, duration=874.499s, table=0, n_packets=2247, n_bytes=148310, priority=1,in_port="s1-eth2",dl_dst=fa:b2:cd:84:28:f0 actions=output:"s1-eth1"
  cookie=0x0, duration=874.477s, table=0, n_packets=2328, n_bytes=6707224, priority=1,in_port="s1-eth1",dl_dst=4a:24:67:15:93:45 actions=output:"s1-eth2"
  cookie=0x0, duration=876.864s, table=0, n_packets=74, n_bytes=5592, priority=0 actions=CONTROLLER:65535
```

Formatted output:

| **Cookie** | **Duration (s)** | **Table** | **Packets** | **Bytes** | **In Port**  | **Destination MAC**      | **Action (Output Port)** | **Priority** |
|------------|------------------|-----------|-------------|-----------|--------------|---------------------------|---------------------------|--------------|
| 0x0        | 874.499          | 0         | 2247        | 148310    | s1-eth2      | fa:b2:cd:84:28:f0         | s1-eth1                   | 1            |
| 0x0        | 874.477          | 0         | 2328        | 6707224   | s1-eth1      | 4a:24:67:15:93:45         | s1-eth2                   | 1            |
| 0x0        | 876.864          | 0         | 74          | 5592      |              |                           | CONTROLLER:65535          | 0            |
