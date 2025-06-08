# Lab2 Notes

## Starting the Ryu Controller

```bash
clear; ryu-manager ./sp_routing.py --observe-links
```

```bash
clear; ryu-manager ./ft_routing.py --observe-links
```

## Starting Mininet

```bash
clear; sudo ./run.sh
```

## Dump Flows

```bash	
sudo ovs-ofctl dump-flows switch1
```

## Topology Discovery

Switches in the network will be discovered when they register with the controller. The controller will receive a `SwitchEnter` event for each switch that connects to it. The connected switches can be retireved using the `get_switch` method of the controller. Logging the returned switches will show their DPID (Datapath ID).

```
Switch<dpid=167903745, Port<dpid=167903745, port_no=4, LIVE> Port<dpid=167903745, port_no=1, LIVE> Port<dpid=167903745, port_no=2, LIVE> Port<dpid=167903745, port_no=3, LIVE> >
Switch<dpid=168034818, Port<dpid=168034818, port_no=4, LIVE> Port<dpid=168034818, port_no=1, LIVE> Port<dpid=168034818, port_no=2, LIVE> Port<dpid=168034818, port_no=3, LIVE> >
Switch<dpid=167772417, Port<dpid=167772417, port_no=4, LIVE> Port<dpid=167772417, port_no=1, LIVE> Port<dpid=167772417, port_no=2, LIVE> Port<dpid=167772417, port_no=3, LIVE> >
Switch<dpid=167838465, Port<dpid=167838465, port_no=1, LIVE> Port<dpid=167838465, port_no=4, LIVE> Port<dpid=167838465, port_no=2, LIVE> Port<dpid=167838465, port_no=3, LIVE> >
Switch<dpid=168034561, Port<dpid=168034561, port_no=4, LIVE> Port<dpid=168034561, port_no=1, LIVE> Port<dpid=168034561, port_no=2, LIVE> Port<dpid=168034561, port_no=3, LIVE> >
Switch<dpid=167969537, Port<dpid=167969537, port_no=4, LIVE> Port<dpid=167969537, port_no=1, LIVE> Port<dpid=167969537, port_no=2, LIVE> Port<dpid=167969537, port_no=3, LIVE> >
Switch<dpid=167837953, Port<dpid=167837953, port_no=1, LIVE> Port<dpid=167837953, port_no=4, LIVE> Port<dpid=167837953, port_no=2, LIVE> Port<dpid=167837953, port_no=3, LIVE> >
Switch<dpid=167837697, Port<dpid=167837697, port_no=1, LIVE> Port<dpid=167837697, port_no=4, LIVE> Port<dpid=167837697, port_no=2, LIVE> Port<dpid=167837697, port_no=3, LIVE> >
Switch<dpid=167772161, Port<dpid=167772161, port_no=1, LIVE> Port<dpid=167772161, port_no=4, LIVE> Port<dpid=167772161, port_no=2, LIVE> Port<dpid=167772161, port_no=3, LIVE> >
Switch<dpid=168034817, Port<dpid=168034817, port_no=4, LIVE> Port<dpid=168034817, port_no=1, LIVE> Port<dpid=168034817, port_no=2, LIVE> Port<dpid=168034817, port_no=3, LIVE> >
Switch<dpid=167904001, Port<dpid=167904001, port_no=4, LIVE> Port<dpid=167904001, port_no=1, LIVE> Port<dpid=167904001, port_no=2, LIVE> Port<dpid=167904001, port_no=3, LIVE> >
Switch<dpid=167969281, Port<dpid=167969281, port_no=1, LIVE> Port<dpid=167969281, port_no=4, LIVE> Port<dpid=167969281, port_no=2, LIVE> Port<dpid=167969281, port_no=3, LIVE> >
Switch<dpid=167903233, Port<dpid=167903233, port_no=1, LIVE> Port<dpid=167903233, port_no=4, LIVE> Port<dpid=167903233, port_no=2, LIVE> Port<dpid=167903233, port_no=3, LIVE> >
Switch<dpid=167968769, Port<dpid=167968769, port_no=1, LIVE> Port<dpid=167968769, port_no=4, LIVE> Port<dpid=167968769, port_no=2, LIVE> Port<dpid=167968769, port_no=3, LIVE> >
Switch<dpid=167772929, Port<dpid=167772929, port_no=4, LIVE> Port<dpid=167772929, port_no=1, LIVE> Port<dpid=167772929, port_no=2, LIVE> Port<dpid=167772929, port_no=3, LIVE> >
Switch<dpid=168034562, Port<dpid=168034562, port_no=4, LIVE> Port<dpid=168034562, port_no=1, LIVE> Port<dpid=168034562, port_no=2, LIVE> Port<dpid=168034562, port_no=3, LIVE> >
Switch<dpid=167838209, Port<dpid=167838209, port_no=4, LIVE> Port<dpid=167838209, port_no=1, LIVE> Port<dpid=167838209, port_no=2, LIVE> Port<dpid=167838209, port_no=3, LIVE> >
Switch<dpid=167903489, Port<dpid=167903489, port_no=4, LIVE> Port<dpid=167903489, port_no=1, LIVE> Port<dpid=167903489, port_no=2, LIVE> Port<dpid=167903489, port_no=3, LIVE> >
Switch<dpid=167969025, Port<dpid=167969025, port_no=4, LIVE> Port<dpid=167969025, port_no=1, LIVE> Port<dpid=167969025, port_no=2, LIVE> Port<dpid=167969025, port_no=3, LIVE> >
Switch<dpid=167772673, Port<dpid=167772673, port_no=4, LIVE> Port<dpid=167772673, port_no=1, LIVE> Port<dpid=167772673, port_no=2, LIVE> Port<dpid=167772673, port_no=3, LIVE> >
```

Links connecting the switches can be discovered using the `get_link` method of the controller. This will return a list of links, each represented by a `Link` object containing the source and destination switches and ports.

```
Link: Port<dpid=167838465, port_no=3, LIVE> to Port<dpid=168034818, port_no=4, LIVE>
Link: Port<dpid=168034818, port_no=3, LIVE> to Port<dpid=167969537, port_no=3, LIVE>
Link: Port<dpid=167968769, port_no=3, LIVE> to Port<dpid=167969537, port_no=4, LIVE>
Link: Port<dpid=168034818, port_no=1, LIVE> to Port<dpid=167904001, port_no=2, LIVE>
Link: Port<dpid=167903233, port_no=2, LIVE> to Port<dpid=167904001, port_no=4, LIVE>
Link: Port<dpid=167772417, port_no=2, LIVE> to Port<dpid=167772673, port_no=2, LIVE>
Link: Port<dpid=168034561, port_no=2, LIVE> to Port<dpid=167772673, port_no=1, LIVE>
Link: Port<dpid=167838465, port_no=4, LIVE> to Port<dpid=167837953, port_no=2, LIVE>
Link: Port<dpid=167772673, port_no=3, LIVE> to Port<dpid=168034562, port_no=3, LIVE>
Link: Port<dpid=167838465, port_no=2, LIVE> to Port<dpid=168034817, port_no=3, LIVE>
Link: Port<dpid=167772929, port_no=3, LIVE> to Port<dpid=168034817, port_no=4, LIVE>
Link: Port<dpid=167772417, port_no=3, LIVE> to Port<dpid=167772929, port_no=4, LIVE>
Link: Port<dpid=168034818, port_no=2, LIVE> to Port<dpid=167772929, port_no=2, LIVE>
Link: Port<dpid=167772929, port_no=1, LIVE> to Port<dpid=167772161, port_no=1, LIVE>
Link: Port<dpid=167772673, port_no=4, LIVE> to Port<dpid=167772161, port_no=4, LIVE>
Link: Port<dpid=168034561, port_no=1, LIVE> to Port<dpid=167838209, port_no=2, LIVE>
Link: Port<dpid=167837953, port_no=1, LIVE> to Port<dpid=167838209, port_no=1, LIVE>
Link: Port<dpid=168034562, port_no=1, LIVE> to Port<dpid=167838209, port_no=3, LIVE>
Link: Port<dpid=168034561, port_no=3, LIVE> to Port<dpid=167969281, port_no=3, LIVE>
Link: Port<dpid=167968769, port_no=2, LIVE> to Port<dpid=167969281, port_no=1, LIVE>
Link: Port<dpid=168034562, port_no=4, LIVE> to Port<dpid=167969281, port_no=4, LIVE>
Link: Port<dpid=167838209, port_no=1, LIVE> to Port<dpid=167837953, port_no=1, LIVE>
Link: Port<dpid=167772673, port_no=1, LIVE> to Port<dpid=168034561, port_no=2, LIVE>
Link: Port<dpid=167838209, port_no=2, LIVE> to Port<dpid=168034561, port_no=1, LIVE>
Link: Port<dpid=167969281, port_no=3, LIVE> to Port<dpid=168034561, port_no=3, LIVE>
Link: Port<dpid=167903745, port_no=3, LIVE> to Port<dpid=168034561, port_no=4, LIVE>
Link: Port<dpid=167969281, port_no=1, LIVE> to Port<dpid=167968769, port_no=2, LIVE>
Link: Port<dpid=167969537, port_no=4, LIVE> to Port<dpid=167968769, port_no=3, LIVE>
Link: Port<dpid=168034817, port_no=4, LIVE> to Port<dpid=167772929, port_no=3, LIVE>
Link: Port<dpid=167772161, port_no=1, LIVE> to Port<dpid=167772929, port_no=1, LIVE>
Link: Port<dpid=167969537, port_no=1, LIVE> to Port<dpid=167969025, port_no=1, LIVE>
Link: Port<dpid=167969281, port_no=2, LIVE> to Port<dpid=167969025, port_no=3, LIVE>
Link: Port<dpid=167904001, port_no=1, LIVE> to Port<dpid=168034817, port_no=1, LIVE>
Link: Port<dpid=167969537, port_no=2, LIVE> to Port<dpid=168034817, port_no=2, LIVE>
Link: Port<dpid=167772929, port_no=2, LIVE> to Port<dpid=168034818, port_no=2, LIVE>
Link: Port<dpid=167969537, port_no=3, LIVE> to Port<dpid=168034818, port_no=3, LIVE>
Link: Port<dpid=167904001, port_no=2, LIVE> to Port<dpid=168034818, port_no=1, LIVE>
Link: Port<dpid=167969281, port_no=4, LIVE> to Port<dpid=168034562, port_no=4, LIVE>
Link: Port<dpid=167838209, port_no=3, LIVE> to Port<dpid=168034562, port_no=1, LIVE>
Link: Port<dpid=167903745, port_no=2, LIVE> to Port<dpid=168034562, port_no=2, LIVE>
Link: Port<dpid=168034561, port_no=4, LIVE> to Port<dpid=167903745, port_no=3, LIVE>
Link: Port<dpid=167903233, port_no=4, LIVE> to Port<dpid=167903745, port_no=1, LIVE>
Link: Port<dpid=168034562, port_no=2, LIVE> to Port<dpid=167903745, port_no=2, LIVE>
Link: Port<dpid=167903489, port_no=4, LIVE> to Port<dpid=167903745, port_no=4, LIVE>
Link: Port<dpid=168034818, port_no=4, LIVE> to Port<dpid=167838465, port_no=3, LIVE>
Link: Port<dpid=167837953, port_no=2, LIVE> to Port<dpid=167838465, port_no=4, LIVE>
Link: Port<dpid=168034817, port_no=3, LIVE> to Port<dpid=167838465, port_no=2, LIVE>
Link: Port<dpid=167837697, port_no=1, LIVE> to Port<dpid=167838465, port_no=1, LIVE>
Link: Port<dpid=167837697, port_no=3, LIVE> to Port<dpid=167838209, port_no=4, LIVE>
Link: Port<dpid=168034817, port_no=1, LIVE> to Port<dpid=167904001, port_no=1, LIVE>
Link: Port<dpid=167903489, port_no=2, LIVE> to Port<dpid=167904001, port_no=3, LIVE>
Link: Port<dpid=167969025, port_no=3, LIVE> to Port<dpid=167969281, port_no=2, LIVE>
Link: Port<dpid=168034562, port_no=3, LIVE> to Port<dpid=167772673, port_no=3, LIVE>
Link: Port<dpid=167772161, port_no=4, LIVE> to Port<dpid=167772673, port_no=4, LIVE>
Link: Port<dpid=168034817, port_no=2, LIVE> to Port<dpid=167969537, port_no=2, LIVE>
Link: Port<dpid=167969025, port_no=1, LIVE> to Port<dpid=167969537, port_no=1, LIVE>
Link: Port<dpid=167838465, port_no=1, LIVE> to Port<dpid=167837697, port_no=1, LIVE>
Link: Port<dpid=167838209, port_no=4, LIVE> to Port<dpid=167837697, port_no=3, LIVE>
Link: Port<dpid=167772929, port_no=4, LIVE> to Port<dpid=167772417, port_no=3, LIVE>
Link: Port<dpid=167772673, port_no=2, LIVE> to Port<dpid=167772417, port_no=2, LIVE>
Link: Port<dpid=167904001, port_no=4, LIVE> to Port<dpid=167903233, port_no=2, LIVE>
Link: Port<dpid=167903745, port_no=1, LIVE> to Port<dpid=167903233, port_no=4, LIVE>
Link: Port<dpid=167904001, port_no=3, LIVE> to Port<dpid=167903489, port_no=2, LIVE>
Link: Port<dpid=167903745, port_no=4, LIVE> to Port<dpid=167903489, port_no=4, LIVE>
```