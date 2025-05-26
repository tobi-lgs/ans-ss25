# Lab0 Notes

### Startup

```bash
vagrant@ans-vm:~$ sudo -E mn --custom /vagrant/lab0/network_topo.py --topo bridge --link tc
*** No default OpenFlow controller found for default switch!
*** Falling back to OVS Bridge
*** Creating network
*** Adding controller
*** Adding hosts:
h1 h2 h3 h4
*** Adding switches:
s1 s2
*** Adding links:
(15.00Mbit 10ms delay) (15.00Mbit 10ms delay) (h1, s1) (15.00Mbit 10ms delay) (15.00Mbit 10ms delay) (h2, s1) (15.00Mbit 10ms delay) (15.00Mbit 10ms delay) (h3, s2) (15.00Mbit 10ms delay) (15.00Mbit 10ms delay) (h4, s2) (20.00Mbit 45ms dela                                                                                                                                                                                                                                             y) (20.00Mbit 45ms delay) (s1, s2)
*** Configuring hosts
h1 h2 h3 h4
*** Starting controller

*** Starting 2 switches
s1 s2 ...(15.00Mbit 10ms delay) (15.00Mbit 10ms delay) (20.00Mbit 45ms delay) (1                                                                                                                                                                                                                                             5.00Mbit 10ms delay) (15.00Mbit 10ms delay) (20.00Mbit 45ms delay)
*** Starting CLI:
```

## 4.3 Measure the Performance of the Network

### Logs from h1 to h2:

Ping h2 and iperf to test the delay between h1 and h2.
    
```bash
ping -c10 10.0.0.2
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=54.8 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=43.1 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=64 time=47.6 ms
64 bytes from 10.0.0.2: icmp_seq=4 ttl=64 time=48.6 ms
64 bytes from 10.0.0.2: icmp_seq=5 ttl=64 time=110 ms
64 bytes from 10.0.0.2: icmp_seq=6 ttl=64 time=68.6 ms
64 bytes from 10.0.0.2: icmp_seq=7 ttl=64 time=42.3 ms
64 bytes from 10.0.0.2: icmp_seq=8 ttl=64 time=49.5 ms
64 bytes from 10.0.0.2: icmp_seq=9 ttl=64 time=51.5 ms
64 bytes from 10.0.0.2: icmp_seq=10 ttl=64 time=41.1 ms

--- 10.0.0.2 ping statistics ---
10 packets transmitted, 10 received, 0% packet loss, time 9109ms
rtt min/avg/max/mdev = 41.144/55.673/109.575/19.476 ms
```

iperf test with h1 in client mode and h2 in server mode to test the bandwidth between h1 and h2.

```bash
root@ans-vm:~# iperf -c 10.0.0.2 -t 20
------------------------------------------------------------
Client connecting to 10.0.0.2, TCP port 5001
TCP window size: 85.3 KByte (default)
------------------------------------------------------------
[  5] local 10.0.0.1 port 44176 connected with 10.0.0.2 port 5001
[ ID] Interval       Transfer     Bandwidth
[  5]  0.0-21.0 sec  32.2 MBytes  12.9 Mbits/sec
```

```bash
root@ans-vm:~# iperf -s
------------------------------------------------------------
Server listening on TCP port 5001
TCP window size: 85.3 KByte (default)
------------------------------------------------------------
[  6] local 10.0.0.2 port 5001 connected with 10.0.0.1 port 44176
[ ID] Interval       Transfer     Bandwidth
[  6]  0.0-32.5 sec  32.2 MBytes  8.33 Mbits/sec
```

### Logs from h1 to h3:

```bash
root@ans-vm:~# ping -c10 10.0.0.3
PING 10.0.0.3 (10.0.0.3) 56(84) bytes of data.
64 bytes from 10.0.0.3: icmp_seq=1 ttl=64 time=335 ms
64 bytes from 10.0.0.3: icmp_seq=2 ttl=64 time=159 ms
64 bytes from 10.0.0.3: icmp_seq=3 ttl=64 time=144 ms
64 bytes from 10.0.0.3: icmp_seq=4 ttl=64 time=147 ms
64 bytes from 10.0.0.3: icmp_seq=5 ttl=64 time=156 ms
64 bytes from 10.0.0.3: icmp_seq=6 ttl=64 time=147 ms
64 bytes from 10.0.0.3: icmp_seq=7 ttl=64 time=146 ms
64 bytes from 10.0.0.3: icmp_seq=8 ttl=64 time=146 ms
64 bytes from 10.0.0.3: icmp_seq=9 ttl=64 time=152 ms
64 bytes from 10.0.0.3: icmp_seq=10 ttl=64 time=149 ms

--- 10.0.0.3 ping statistics ---
10 packets transmitted, 10 received, 0% packet loss, time 9031ms
rtt min/avg/max/mdev = 143.705/167.966/334.956/55.855 ms
```

iperf test with h1 in client mode and h3 in server mode to test the bandwidth between h1 and h3.

```bash
root@ans-vm:~# iperf -c 10.0.0.3 -t 20
------------------------------------------------------------
Client connecting to 10.0.0.3, TCP port 5001
TCP window size: 85.3 KByte (default)
------------------------------------------------------------
[  5] local 10.0.0.1 port 33304 connected with 10.0.0.3 port 5001
[ ID] Interval       Transfer     Bandwidth
[  5]  0.0-21.1 sec  29.6 MBytes  11.8 Mbits/sec
```


```bash
root@ans-vm:~# iperf -s
------------------------------------------------------------
Server listening on TCP port 5001
TCP window size: 85.3 KByte (default)
------------------------------------------------------------
[  6] local 10.0.0.3 port 5001 connected with 10.0.0.1 port 33304
[ ID] Interval       Transfer     Bandwidth
[  6]  0.0-31.9 sec  29.6 MBytes  7.78 Mbits/sec
```

## 4.4 Effect of Multiplexing

### h1 to h3 and h2 to h4 at the same time

Test: ping h1 to h3 while h2 sends iperf data to h4.

```bash
--- 10.0.0.2 ping statistics ---
20 packets transmitted, 20 received, 0% packet loss, time 19080ms
rtt min/avg/max/mdev = 50.723/847.118/2454.435/819.410 ms, pipe 3
```
Result: The average delay is 847.118 ms, which is much higher than the previous test (55.673 ms).

Test: iperf h1 to h3 while h2 sends iperf data to h4.

```bash
root@ans-vm:~# iperf -c 10.0.0.3 -t 30
------------------------------------------------------------
Client connecting to 10.0.0.3, TCP port 5001
TCP window size: 85.3 KByte (default)
------------------------------------------------------------
[  5] local 10.0.0.1 port 54032 connected with 10.0.0.3 port 5001
[ ID] Interval       Transfer     Bandwidth
[  5]  0.0-31.7 sec  22.1 MBytes  5.85 Mbits/sec
```

```bash
root@ans-vm:~# iperf -s
------------------------------------------------------------
Server listening on TCP port 5001
TCP window size: 85.3 KByte (default)
------------------------------------------------------------
[  6] local 10.0.0.3 port 5001 connected with 10.0.0.1 port 54032
[ ID] Interval       Transfer     Bandwidth
[  6]  0.0-41.4 sec  22.1 MBytes  4.49 Mbits/sec
```

Result: The bandwidth is 5.85 Mbits/sec, which is much lower than the previous test (12.9 Mbits/sec).

### h1 and h2 to h4 at the same time

Test: iperf h1 and h2 to h4 at the same time.

```bash
root@ans-vm:~# iperf -c 10.0.0.4 -t 30
------------------------------------------------------------
Client connecting to 10.0.0.4, TCP port 5001
TCP window size: 85.3 KByte (default)
------------------------------------------------------------
[  5] local 10.0.0.1 port 37712 connected with 10.0.0.4 port 5001
[ ID] Interval       Transfer     Bandwidth
[  5]  0.0-33.3 sec  13.6 MBytes  3.44 Mbits/sec
```

```bash
root@ans-vm:~# iperf -c 10.0.0.4 -t 30
------------------------------------------------------------
Client connecting to 10.0.0.4, TCP port 5001
TCP window size: 85.3 KByte (default)
------------------------------------------------------------
[  5] local 10.0.0.2 port 41870 connected with 10.0.0.4 port 5001
[ ID] Interval       Transfer     Bandwidth
[  5]  0.0-34.0 sec  30.9 MBytes  7.62 Mbits/sec
```

```bash
[  6] local 10.0.0.4 port 5001 connected with 10.0.0.2 port 41870
[  7] local 10.0.0.4 port 5001 connected with 10.0.0.1 port 37712
[  6]  0.0-60.3 sec  30.9 MBytes  4.29 Mbits/sec
[  7]  0.0-57.7 sec  13.6 MBytes  1.98 Mbits/sec
```

Result: The bandwidth is 3.44 Mbits/sec for h1 and 7.62 Mbits/sec for h2, which is much lower than the previous test (12.9 Mbits/sec).