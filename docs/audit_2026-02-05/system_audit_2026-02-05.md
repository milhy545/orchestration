# System Audit Report

Generated: 2026-02-05T04:53:11.107234+00:00

## System
```
Linux home-automat-server 6.6.117-0-lts #1-Alpine SMP PREEMPT_DYNAMIC Tue, 25 Nov 2025 16:52:39 +0000 x86_64 GNU/Linux
```

## OS Release
```
NAME="Alpine Linux"
ID=alpine
VERSION_ID=3.19.9
PRETTY_NAME="Alpine Linux v3.19"
HOME_URL="https://alpinelinux.org/"
BUG_REPORT_URL="https://gitlab.alpinelinux.org/alpine/aports/-/issues"
```

## Uptime
```
04:53:11 up 2 days,  3:06,  0 users,  load average: 1.28, 2.18, 2.52
```

## Users
```
root:x:0:0:root:/root:/bin/zsh
bin:x:1:1:bin:/bin:/sbin/nologin
daemon:x:2:2:daemon:/sbin:/sbin/nologin
adm:x:3:4:adm:/var/adm:/sbin/nologin
lp:x:4:7:lp:/var/spool/lpd:/sbin/nologin
sync:x:5:0:sync:/sbin:/bin/sync
shutdown:x:6:0:shutdown:/sbin:/sbin/shutdown
halt:x:7:0:halt:/sbin:/sbin/halt
mail:x:8:12:mail:/var/mail:/sbin/nologin
news:x:9:13:news:/usr/lib/news:/sbin/nologin
uucp:x:10:14:uucp:/var/spool/uucppublic:/sbin/nologin
operator:x:11:0:operator:/root:x:0:0:root:/root:/bin/zsh
man:x:13:15:man:/usr/man:/sbin/nologin
postmaster:x:14:12:postmaster:/var/mail:/sbin/nologin
cron:x:16:16:cron:/var/spool/cron:/sbin/nologin
ftp:x:21:21::/var/lib/ftp:/sbin/nologin
sshd:x:22:22:sshd:/dev/null:/sbin/nologin
at:x:25:25:at:/var/spool/cron/atjobs:/sbin/nologin
squid:x:31:31:Squid:/var/cache/squid:/sbin/nologin
xfs:x:33:33:X Font Server:/etc/X11/fs:/sbin/nologin
games:x:35:35:games:/usr/games:/sbin/nologin
cyrus:x:85:12::/usr/cyrus:/sbin/nologin
vpopmail:x:89:89::/var/vpopmail:/sbin/nologin
ntp:x:123:123:NTP:/var/empty:/sbin/nologin
smmsp:x:209:209:smmsp:/var/spool/mqueue:/sbin/nologin
guest:x:405:100:guest:/dev/null:/sbin/nologin
nobody:x:65534:65534:nobody:/:/sbin/nologin
chrony:x:100:101:chrony:/var/log/chrony:/sbin/nologin
mcp:x:1000:1000:Linux User,,,:/home/mcp:/bin/ash
codeserver:x:1001:1001:Linux User,,,:/home/codeserver:/bin/sh
messagebus:x:101:103:messagebus:/dev/null:/sbin/nologin
milhy777:x:1002:1002:Linux User,,,:/home/milhy777:/bin/zsh
dnsmasq:x:102:104:dnsmasq:/dev/null:/sbin/nologin
mosquitto:x:103:105:mosquitto:/var/empty:/sbin/nologin
```

## Network Interfaces
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
11522: vethdfaa56c@if11521: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 52:4d:06:12:ff:9d brd ff:ff:ff:ff:ff:ff
    inet6 fe80::504d:6ff:fe12:ff9d/64 scope link 
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP qlen 1000
    link/ether b4:b5:2f:2f:9b:40 brd ff:ff:ff:ff:ff:ff
    inet 192.168.0.58/24 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fdaa:bbcc:ddee:0:b6b5:2fff:fe2f:9b40/64 scope global dynamic flags 100 
       valid_lft forever preferred_lft forever
    inet6 fe80::b6b5:2fff:fe2f:9b40/64 scope link 
       valid_lft forever preferred_lft forever
3: br-53a789ede06c: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP 
    link/ether 02:42:19:fd:a7:94 brd ff:ff:ff:ff:ff:ff
    inet 172.19.0.1/16 brd 172.19.255.255 scope global br-53a789ede06c
       valid_lft forever preferred_lft forever
    inet6 fe80::42:19ff:fefd:a794/64 scope link 
       valid_lft forever preferred_lft forever
4: docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP 
    link/ether 02:42:44:85:18:3a brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
       valid_lft forever preferred_lft forever
    inet6 fe80::42:44ff:fe85:183a/64 scope link 
       valid_lft forever preferred_lft forever
6: veth2cebf03@if5: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 72:39:4e:23:31:ac brd ff:ff:ff:ff:ff:ff
    inet6 fe80::7039:4eff:fe23:31ac/64 scope link 
       valid_lft forever preferred_lft forever
8: vethfe91d46@if7: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master docker0 state UP 
    link/ether 86:2a:df:b1:48:8b brd ff:ff:ff:ff:ff:ff
    inet6 fe80::842a:dfff:feb1:488b/64 scope link 
       valid_lft forever preferred_lft forever
12: veth17f5961@if11: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master docker0 state UP 
    link/ether da:99:09:51:1d:51 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d899:9ff:fe51:1d51/64 scope link 
       valid_lft forever preferred_lft forever
14: vethab5bb55@if13: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master docker0 state UP 
    link/ether 02:ad:d8:bb:1e:24 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::ad:d8ff:febb:1e24/64 scope link 
       valid_lft forever preferred_lft forever
16: veth6b2ef1c@if15: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 4e:8f:e0:8e:4e:75 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::4c8f:e0ff:fe8e:4e75/64 scope link 
       valid_lft forever preferred_lft forever
18: veth711ff63@if17: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master docker0 state UP 
    link/ether 8a:23:ed:0a:7b:fc brd ff:ff:ff:ff:ff:ff
    inet6 fe80::8823:edff:fe0a:7bfc/64 scope link 
       valid_lft forever preferred_lft forever
22: veth24acf37@if21: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 7a:44:3a:0b:6a:e6 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::7844:3aff:fe0b:6ae6/64 scope link 
       valid_lft forever preferred_lft forever
24: veth6fdf574@if23: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 36:38:f5:05:ca:3f brd ff:ff:ff:ff:ff:ff
    inet6 fe80::3438:f5ff:fe05:ca3f/64 scope link 
       valid_lft forever preferred_lft forever
28: veth141c301@if27: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 22:74:30:db:9f:35 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::2074:30ff:fedb:9f35/64 scope link 
       valid_lft forever preferred_lft forever
30: veth740fb1f@if29: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 0e:7f:02:7a:ae:01 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::c7f:2ff:fe7a:ae01/64 scope link 
       valid_lft forever preferred_lft forever
32: veth92331e3@if31: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 06:02:13:f6:9f:b6 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::402:13ff:fef6:9fb6/64 scope link 
       valid_lft forever preferred_lft forever
34: veth2f4e4ec@if33: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether ae:59:11:5a:2c:5c brd ff:ff:ff:ff:ff:ff
    inet6 fe80::ac59:11ff:fe5a:2c5c/64 scope link 
       valid_lft forever preferred_lft forever
40: veth7c434fc@if39: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 7e:bd:93:07:55:32 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::7cbd:93ff:fe07:5532/64 scope link 
       valid_lft forever preferred_lft forever
11562: vethd87d812@if11561: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 56:ad:a3:07:46:ec brd ff:ff:ff:ff:ff:ff
    inet6 fe80::54ad:a3ff:fe07:46ec/64 scope link 
       valid_lft forever preferred_lft forever
42: vethab157e0@if41: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 6e:9c:b2:b4:aa:c0 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::6c9c:b2ff:feb4:aac0/64 scope link 
       valid_lft forever preferred_lft forever
46: veth30f46de@if45: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 5e:65:ce:34:89:de brd ff:ff:ff:ff:ff:ff
    inet6 fe80::5c65:ceff:fe34:89de/64 scope link 
       valid_lft forever preferred_lft forever
48: vetha8a6c17@if47: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether f6:e0:c8:4b:02:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::f4e0:c8ff:fe4b:27a/64 scope link 
       valid_lft forever preferred_lft forever
50: veth5e9caa8@if49: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 96:3a:cc:bf:11:e0 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::943a:ccff:febf:11e0/64 scope link 
       valid_lft forever preferred_lft forever
52: veth448294a@if51: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 0e:d2:21:d1:5e:6c brd ff:ff:ff:ff:ff:ff
    inet6 fe80::cd2:21ff:fed1:5e6c/64 scope link 
       valid_lft forever preferred_lft forever
11574: vethc39e41e@if11573: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 5a:9a:49:da:54:6d brd ff:ff:ff:ff:ff:ff
    inet6 fe80::589a:49ff:feda:546d/64 scope link 
       valid_lft forever preferred_lft forever
11576: veth6a57072@if11575: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether d6:b8:a8:8c:9f:7f brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d4b8:a8ff:fe8c:9f7f/64 scope link 
       valid_lft forever preferred_lft forever
56: vethbaffd4a@if55: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether ce:24:07:f4:a2:a9 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::cc24:7ff:fef4:a2a9/64 scope link 
       valid_lft forever preferred_lft forever
11582: veth893375b@if11581: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether ca:29:44:5f:57:98 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::c829:44ff:fe5f:5798/64 scope link 
       valid_lft forever preferred_lft forever
11584: vethbc2d414@if11583: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 56:23:5c:f2:96:b2 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::5423:5cff:fef2:96b2/64 scope link 
       valid_lft forever preferred_lft forever
11588: veth42fb9d5@if11587: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether b2:36:4e:ac:e5:8a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::b036:4eff:feac:e58a/64 scope link 
       valid_lft forever preferred_lft forever
11516: vethb42cccb@if11515: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether a2:32:88:77:1f:92 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::a032:88ff:fe77:1f92/64 scope link 
       valid_lft forever preferred_lft forever
11518: vethefcef40@if11517: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue master br-53a789ede06c state UP 
    link/ether 1e:c7:bd:12:32:0b brd ff:ff:ff:ff:ff:ff
    inet6 fe80::1cc7:bdff:fe12:320b/64 scope link 
       valid_lft forever preferred_lft forever
```

## Routes
```
default via 192.168.0.1 dev eth0  metric 202 
172.17.0.0/16 dev docker0 scope link  src 172.17.0.1 
172.19.0.0/16 dev br-53a789ede06c scope link  src 172.19.0.1 
192.168.0.0/24 dev eth0 scope link  src 192.168.0.58
```

## Open Ports
```
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name    
tcp        0      0 0.0.0.0:5443            0.0.0.0:*               LISTEN      4716/docker-proxy
tcp        0      0 127.0.0.1:1883          0.0.0.0:*               LISTEN      2768/mosquitto
tcp        0      0 0.0.0.0:6060            0.0.0.0:*               LISTEN      4682/docker-proxy
tcp        0      0 0.0.0.0:8013            0.0.0.0:*               LISTEN      16457/docker-proxy
tcp        0      0 0.0.0.0:8025            0.0.0.0:*               LISTEN      27786/docker-proxy
tcp        0      0 0.0.0.0:8026            0.0.0.0:*               LISTEN      1880/docker-proxy
tcp        0      0 0.0.0.0:8027            0.0.0.0:*               LISTEN      27497/docker-proxy
tcp        0      0 0.0.0.0:8021            0.0.0.0:*               LISTEN      14163/docker-proxy
tcp        0      0 0.0.0.0:8022            0.0.0.0:*               LISTEN      27539/docker-proxy
tcp        0      0 0.0.0.0:8023            0.0.0.0:*               LISTEN      27519/docker-proxy
tcp        0      0 0.0.0.0:8018            0.0.0.0:*               LISTEN      10170/docker-proxy
tcp        0      0 0.0.0.0:8019            0.0.0.0:*               LISTEN      10337/docker-proxy
tcp        0      0 0.0.0.0:10001           0.0.0.0:*               LISTEN      4892/docker-proxy
tcp        0      0 0.0.0.0:10002           0.0.0.0:*               LISTEN      4547/docker-proxy
tcp        0      0 0.0.0.0:10003           0.0.0.0:*               LISTEN      4790/docker-proxy
tcp        0      0 0.0.0.0:7999            0.0.0.0:*               LISTEN      2897/python3
tcp        0      0 0.0.0.0:139             0.0.0.0:*               LISTEN      3139/smbd
tcp        0      0 0.0.0.0:2222            0.0.0.0:*               LISTEN      21325/sshd [listene
tcp        0      0 0.0.0.0:53              0.0.0.0:*               LISTEN      4909/docker-proxy
tcp        0      0 0.0.0.0:445             0.0.0.0:*               LISTEN      3139/smbd
tcp        0      0 0.0.0.0:443             0.0.0.0:*               LISTEN      4810/docker-proxy
tcp        0      0 0.0.0.0:7004            0.0.0.0:*               LISTEN      8415/docker-proxy
tcp        0      0 0.0.0.0:7005            0.0.0.0:*               LISTEN      7965/docker-proxy
tcp        0      0 0.0.0.0:7000            0.0.0.0:*               LISTEN      4476/docker-proxy
tcp        0      0 0.0.0.0:7001            0.0.0.0:*               LISTEN      5775/docker-proxy
tcp        0      0 0.0.0.0:7002            0.0.0.0:*               LISTEN      7636/docker-proxy
tcp        0      0 0.0.0.0:7003            0.0.0.0:*               LISTEN      6037/docker-proxy
tcp        0      0 0.0.0.0:853             0.0.0.0:*               LISTEN      4754/docker-proxy
tcp        0      0 0.0.0.0:7012            0.0.0.0:*               LISTEN      13850/docker-proxy
tcp        0      0 0.0.0.0:7014            0.0.0.0:*               LISTEN      8716/docker-proxy
tcp        0      0 0.0.0.0:7008            0.0.0.0:*               LISTEN      7884/docker-proxy
tcp        0      0 0.0.0.0:7009            0.0.0.0:*               LISTEN      5597/docker-proxy
tcp        0      0 0.0.0.0:7010            0.0.0.0:*               LISTEN      6884/docker-proxy
tcp        0      0 0.0.0.0:7011            0.0.0.0:*               LISTEN      5050/docker-proxy
tcp        0      0 0.0.0.0:7028            0.0.0.0:*               LISTEN      5309/docker-proxy
tcp        0      0 0.0.0.0:7029            0.0.0.0:*               LISTEN      8141/docker-proxy
tcp        0      0 0.0.0.0:7030            0.0.0.0:*               LISTEN      4699/docker-proxy
tcp        0      0 0.0.0.0:7024            0.0.0.0:*               LISTEN      5691/docker-proxy
tcp        0      0 0.0.0.0:9001            0.0.0.0:*               LISTEN      4496/docker-proxy
tcp        0      0 :::5443                 :::*                    LISTEN      4722/docker-proxy
tcp        0      0 :::6060                 :::*                    LISTEN      4690/docker-proxy
tcp        0      0 :::8013                 :::*                    LISTEN      16462/docker-proxy
tcp        0      0 :::8025                 :::*                    LISTEN      27793/docker-proxy
tcp        0      0 :::8026                 :::*                    LISTEN      1885/docker-proxy
tcp        0      0 :::8027                 :::*                    LISTEN      27504/docker-proxy
tcp        0      0 :::8021                 :::*                    LISTEN      14168/docker-proxy
tcp        0      0 :::8022                 :::*                    LISTEN      27546/docker-proxy
tcp        0      0 :::8023                 :::*                    LISTEN      27525/docker-proxy
tcp        0      0 :::8018                 :::*                    LISTEN      10176/docker-proxy
tcp        0      0 :::8019                 :::*                    LISTEN      10343/docker-proxy
tcp        0      0 :::10001                :::*                    LISTEN      4899/docker-proxy
tcp        0      0 :::10002                :::*                    LISTEN      4553/docker-proxy
tcp        0      0 :::10003                :::*                    LISTEN      4796/docker-proxy
tcp        0      0 :::139                  :::*                    LISTEN      3139/smbd
tcp        0      0 :::53                   :::*                    LISTEN      4915/docker-proxy
tcp        0      0 :::445                  :::*                    LISTEN      3139/smbd
tcp        0      0 :::443                  :::*                    LISTEN      4820/docker-proxy
tcp        0      0 ::1:1883                :::*                    LISTEN      2768/mosquitto
tcp        0      0 :::7004                 :::*                    LISTEN      8421/docker-proxy
tcp        0      0 :::7005                 :::*                    LISTEN      7972/docker-proxy
tcp        0      0 :::7000                 :::*                    LISTEN      4482/docker-proxy
tcp        0      0 :::7001                 :::*                    LISTEN      5780/docker-proxy
tcp        0      0 :::7002                 :::*                    LISTEN      7642/docker-proxy
tcp        0      0 :::7003                 :::*                    LISTEN      6043/docker-proxy
tcp        0      0 :::853                  :::*                    LISTEN      4760/docker-proxy
tcp        0      0 :::7012                 :::*                    LISTEN      13856/docker-proxy
tcp        0      0 :::7014                 :::*                    LISTEN      8722/docker-proxy
tcp        0      0 :::7008                 :::*                    LISTEN      7891/docker-proxy
tcp        0      0 :::7009                 :::*                    LISTEN      5604/docker-proxy
tcp        0      0 :::7010                 :::*                    LISTEN      6892/docker-proxy
tcp        0      0 :::7011                 :::*                    LISTEN      5059/docker-proxy
tcp        0      0 :::7028                 :::*                    LISTEN      5314/docker-proxy
tcp        0      0 :::7029                 :::*                    LISTEN      8148/docker-proxy
tcp        0      0 :::7030                 :::*                    LISTEN      4707/docker-proxy
tcp        0      0 :::7024                 :::*                    LISTEN      5721/docker-proxy
tcp        0      0 :::9001                 :::*                    LISTEN      4502/docker-proxy
udp        0      0 172.19.255.255:137      0.0.0.0:*                           3151/nmbd
udp        0      0 172.19.0.1:137          0.0.0.0:*                           3151/nmbd
udp        0      0 172.17.255.255:137      0.0.0.0:*                           3151/nmbd
udp        0      0 172.17.0.1:137          0.0.0.0:*                           3151/nmbd
udp        0      0 192.168.0.255:137       0.0.0.0:*                           3151/nmbd
udp        0      0 192.168.0.58:137        0.0.0.0:*                           3151/nmbd
udp        0      0 0.0.0.0:137             0.0.0.0:*                           3151/nmbd
udp        0      0 172.19.255.255:138      0.0.0.0:*                           3151/nmbd
udp        0      0 172.19.0.1:138          0.0.0.0:*                           3151/nmbd
udp        0      0 172.17.255.255:138      0.0.0.0:*                           3151/nmbd
udp        0      0 172.17.0.1:138          0.0.0.0:*                           3151/nmbd
udp        0      0 192.168.0.255:138       0.0.0.0:*                           3151/nmbd
udp        0      0 192.168.0.58:138        0.0.0.0:*                           3151/nmbd
udp        0      0 0.0.0.0:138             0.0.0.0:*                           3151/nmbd
udp        0      0 0.0.0.0:443             0.0.0.0:*                           4834/docker-proxy
udp        0      0 0.0.0.0:853             0.0.0.0:*                           4773/docker-proxy
udp        0      0 0.0.0.0:5443            0.0.0.0:*                           4735/docker-proxy
udp        0      0 0.0.0.0:53              0.0.0.0:*                           4928/docker-proxy
udp        0      0 0.0.0.0:67              0.0.0.0:*                           4872/docker-proxy
udp        0      0 0.0.0.0:68              0.0.0.0:*                           4853/docker-proxy
udp        0      0 :::443                  :::*                                4840/docker-proxy
udp        0      0 :::853                  :::*                                4779/docker-proxy
udp        0      0 :::5443                 :::*                                4741/docker-proxy
udp        0      0 :::53                   :::*                                4934/docker-proxy
udp        0      0 :::67                   :::*                                4880/docker-proxy
udp        0      0 :::68                   :::*                                4859/docker-proxy
```

## Firewall (iptables)
```
-P INPUT ACCEPT
-P FORWARD DROP
-P OUTPUT ACCEPT
-N DOCKER
-N DOCKER-ISOLATION-STAGE-1
-N DOCKER-ISOLATION-STAGE-2
-N DOCKER-USER
-A INPUT -p icmp -m icmp --icmp-type 8 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 10010 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 2222 -j ACCEPT
-A INPUT -s 192.168.0.0/24 -p tcp -m tcp --dport 8080 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 10001 -j DROP
-A INPUT -s 192.168.0.0/24 -p tcp -m tcp --dport 10001 -j ACCEPT
-A FORWARD -j DOCKER-USER
-A FORWARD -j DOCKER-ISOLATION-STAGE-1
-A FORWARD -o docker0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -o docker0 -j DOCKER
-A FORWARD -i docker0 ! -o docker0 -j ACCEPT
-A FORWARD -i docker0 -o docker0 -j ACCEPT
-A FORWARD -o br-53a789ede06c -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -o br-53a789ede06c -j DOCKER
-A FORWARD -i br-53a789ede06c ! -o br-53a789ede06c -j ACCEPT
-A FORWARD -i br-53a789ede06c -o br-53a789ede06c -j ACCEPT
-A FORWARD -o docker0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -o br-019b5730a02a -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -o br-019b5730a02a -j DOCKER
-A FORWARD -i br-019b5730a02a ! -o br-019b5730a02a -j ACCEPT
-A FORWARD -i br-019b5730a02a -o br-019b5730a02a -j ACCEPT
-A DOCKER -d 172.19.0.21/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.18/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 1883 -j ACCEPT
-A DOCKER -d 172.19.0.12/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.17/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 9090 -j ACCEPT
-A DOCKER -d 172.17.0.3/32 ! -i docker0 -o docker0 -p udp -m udp --dport 443 -j ACCEPT
-A DOCKER -d 172.17.0.3/32 ! -i docker0 -o docker0 -p udp -m udp --dport 68 -j ACCEPT
-A DOCKER -d 172.17.0.3/32 ! -i docker0 -o docker0 -p udp -m udp --dport 67 -j ACCEPT
-A DOCKER -d 172.17.0.3/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport 53 -j ACCEPT
-A DOCKER -d 172.17.0.3/32 ! -i docker0 -o docker0 -p udp -m udp --dport 53 -j ACCEPT
-A DOCKER -d 172.19.0.2/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8020 -j ACCEPT
-A DOCKER -d 172.17.0.2/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport 9001 -j ACCEPT
-A DOCKER -d 172.17.0.3/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport 8123 -j ACCEPT
-A DOCKER -d 172.17.0.4/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport 6060 -j ACCEPT
-A DOCKER -d 172.19.0.4/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 6379 -j ACCEPT
-A DOCKER -d 172.17.0.4/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport 5443 -j ACCEPT
-A DOCKER -d 172.17.0.4/32 ! -i docker0 -o docker0 -p udp -m udp --dport 5443 -j ACCEPT
-A DOCKER -d 172.17.0.4/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport 853 -j ACCEPT
-A DOCKER -d 172.17.0.4/32 ! -i docker0 -o docker0 -p udp -m udp --dport 853 -j ACCEPT
-A DOCKER -d 172.17.0.4/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport 80 -j ACCEPT
-A DOCKER -d 172.17.0.4/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport 443 -j ACCEPT
-A DOCKER -d 172.17.0.4/32 ! -i docker0 -o docker0 -p udp -m udp --dport 443 -j ACCEPT
-A DOCKER -d 172.17.0.4/32 ! -i docker0 -o docker0 -p udp -m udp --dport 68 -j ACCEPT
-A DOCKER -d 172.17.0.4/32 ! -i docker0 -o docker0 -p udp -m udp --dport 67 -j ACCEPT
-A DOCKER -d 172.17.0.5/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport 9443 -j ACCEPT
-A DOCKER -d 172.17.0.4/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport 53 -j ACCEPT
-A DOCKER -d 172.17.0.4/32 ! -i docker0 -o docker0 -p udp -m udp --dport 53 -j ACCEPT
-A DOCKER -d 172.19.0.6/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.7/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 9090 -j ACCEPT
-A DOCKER -d 172.19.0.9/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.10/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.11/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.15/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.16/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.18/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.19/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.20/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.23/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.3/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 6334 -j ACCEPT
-A DOCKER -d 172.19.0.3/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 6333 -j ACCEPT
-A DOCKER -d 172.19.0.22/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 6379 -j ACCEPT
-A DOCKER -d 172.19.0.25/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.24/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.5/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 1883 -j ACCEPT
-A DOCKER -d 172.19.0.8/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.13/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER -d 172.19.0.14/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 5432 -j ACCEPT
-A DOCKER -d 172.19.0.17/32 ! -i br-53a789ede06c -o br-53a789ede06c -p tcp -m tcp --dport 8000 -j ACCEPT
-A DOCKER-ISOLATION-STAGE-1 -i docker0 ! -o docker0 -j DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-1 -i br-53a789ede06c ! -o br-53a789ede06c -j DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-1 -j RETURN
-A DOCKER-ISOLATION-STAGE-2 -o docker0 -j DROP
-A DOCKER-ISOLATION-STAGE-2 -o br-53a789ede06c -j DROP
-A DOCKER-ISOLATION-STAGE-2 -j RETURN
-A DOCKER-USER -j RETURN
```

## Disk Usage
```
Filesystem      Size  Used Avail Use% Mounted on
devtmpfs         10M     0   10M   0% /dev
shm             1.8G     0  1.8G   0% /dev/shm
/dev/sda3       224G   61G  153G  29% /
tmpfs           705M  2.2M  703M   1% /run
/dev/sda1       272M   34M  219M  14% /boot
tmpfs           1.8G  8.0K  1.8G   1% /tmp
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/5497c3fb3e2ca68be37bb15bfc1b032a9ecb5b06d0b199ea7ac44ff10fe77a6a/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/cee0b85cfb5240a2843f83c3d0bcb96aa618a3e6993345975827dfce2e01706b/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/7d9093d2527c7369ff2f4895ca1d0c5b3beb4c0c949751823e212ce584a505cd/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/86b57b44c07f02aa1253090faf0c08dad496b9db47dae54f940d1533ee550aad/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/1424ecd998b0ac89b5d49b28d947e23d6207a004ba4e9bd18d27486bcb92fd93/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/023f1dc85198014c9ccb82fda9956a63e220503194186bb93b2c9c486af74fb1/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/325a1e49234b046e567f5ad0d3b2b3617c5653bdab911da831810bb2e5469844/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/fe602dd552ee41f7c0a033738027890991274127da353cbf36905ed1fb24f0ea/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/809b0753d4972b903f8b0e01b9c79e73075765af41556038955bee126d82a1b6/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/fe09fcd2e8eac6daedf1d5de436aac36d7966e37934a989c47584ef656c4f017/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/16c0ace8ed723fc68c28b27ca03570a490ab2e9c7b3b71c96456f4df9d1fe145/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/55bd1e692cc0bee1c5a01e904914354adc0b608cc78e0edeb5b449e66f58c7c8/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/be20660eda4fd70ae71b9d6d4b462dea3734719ab09c73477b936e67f7b4a0fe/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/51f9686800ffd1d3164032f40122d47a17a84814525ad3acf0a2a122384aba6b/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/44b43dfc73a1e7d7a298eb526b81df598139fb2dc375db3992ec651b0269d081/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/2b5f7ec6805fb1a86fe04a932df8916d04943c59eb089db16f7b26f1018df1f4/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/ecf99e02b11b789fc415b95bea0c428564ddf4baca9064a5f210578deb055160/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/946afe166997cb383e9f9b0f74ed2cb0add6716d944fc0177c1dbf4e7d0f2474/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/4b0c152ce1c3e0f5a457053a5ad29809a70d8fa17865b3165bff3e07f8c9e3fe/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/3ccb9d93cbe3c0e67b5305c512514a332440495c82f62ac2ad51a18a53df6a56/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/f2f423160ee1e2386a44ba50c0fb054971a2f835fbcbb4879b40ab6ba7749b22/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/d58449f01e77c25942e1f568bfd872589c7311a3a7e86fcdd6b3237aa64e0b7b/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/57dc93ad634441436aac186859717ff67bea1f734b80fbd75223b25fc13bdf3b/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/b3f8c8fbd121577c0a268fe5b9aa294288255030f1c0c391d527591da46ec713/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/a8af6954661209d914a6cffd63802ac35e21051be3a37d54d74009061eb58e39/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/05bfd9cc14546ea8ecbafa1b0b99b5917a94cf180f4022679c851e0ade0cb808/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/93fe7478840e943fc3db74e4122de40f1d78112fdf562542a65a0cbbd6cfeef0/merged
overlay         224G   61G  153G  29% /var/lib/docker/overlay2/e2d49f02e6684b56486a81346988c0872eaeeca3532f4880c7e3c86fc1b48c9d/merged
```

## Mounts (first 30 lines)
```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
devtmpfs on /dev type devtmpfs (rw,nosuid,noexec,relatime,size=10240k,nr_inodes=448557,mode=755,inode64)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000)
shm on /dev/shm type tmpfs (rw,nosuid,nodev,noexec,relatime,inode64)
/dev/sda3 on / type ext4 (rw,relatime)
tmpfs on /run type tmpfs (rw,nosuid,nodev,size=721852k,nr_inodes=819200,mode=755,inode64)
mqueue on /dev/mqueue type mqueue (rw,nosuid,nodev,noexec,relatime)
securityfs on /sys/kernel/security type securityfs (rw,nosuid,nodev,noexec,relatime)
debugfs on /sys/kernel/debug type debugfs (rw,nosuid,nodev,noexec,relatime)
pstore on /sys/fs/pstore type pstore (rw,nosuid,nodev,noexec,relatime)
tracefs on /sys/kernel/debug/tracing type tracefs (rw,nosuid,nodev,noexec,relatime)
/dev/sda1 on /boot type ext4 (rw,relatime)
tmpfs on /tmp type tmpfs (rw,nosuid,nodev,relatime,inode64)
none on /sys/fs/cgroup type cgroup2 (rw,nosuid,nodev,noexec,relatime,nsdelegate)
/dev/sda3 on /var/lib/docker type ext4 (rw,relatime)
overlay on /var/lib/docker/overlay2/5497c3fb3e2ca68be37bb15bfc1b032a9ecb5b06d0b199ea7ac44ff10fe77a6a/merged type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/MLPYKXSQR5IHGW3VWOGR4ZJGHP:/var/lib/docker/overlay2/l/N5QMUXQ6XBMLIJBQNYHIYALZIE:/var/lib/docker/overlay2/l/3KCXIVLJ3YKNMWMZAUCXODBNQH:/var/lib/docker/overlay2/l/67D7UMYYHQRUPWAXQLEHJYMO5K:/var/lib/docker/overlay2/l/LYW72M3QBY3DUFSD5F6SENSVL5:/var/lib/docker/overlay2/l/YNR3VO36HOJYPNQNJXFLEO3RQY:/var/lib/docker/overlay2/l/4KW6W7GTOCIJOGKTCUURRFZABH:/var/lib/docker/overlay2/l/FQS7ERSFIVW5DME4SXUWFHDL47:/var/lib/docker/overlay2/l/355OD2SJC6WEIWZNSS3HKGZCTR:/var/lib/docker/overlay2/l/Y4EPBEHDJPTS6Z3TBW4C6PBB2G,upperdir=/var/lib/docker/overlay2/5497c3fb3e2ca68be37bb15bfc1b032a9ecb5b06d0b199ea7ac44ff10fe77a6a/diff,workdir=/var/lib/docker/overlay2/5497c3fb3e2ca68be37bb15bfc1b032a9ecb5b06d0b199ea7ac44ff10fe77a6a/work)
overlay on /var/lib/docker/overlay2/cee0b85cfb5240a2843f83c3d0bcb96aa618a3e6993345975827dfce2e01706b/merged type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/352MUULK5TH645UNTS22XJOOIF:/var/lib/docker/overlay2/l/LRBZHVVCTKN3P3TKLICZZYZSMI:/var/lib/docker/overlay2/l/BGSEZ5JVD22YE3LOWFHG35P6UB:/var/lib/docker/overlay2/l/DP3W6Y5553CTD7QLJOAJHZ432M:/var/lib/docker/overlay2/l/D7B2CTIMPVHKMBIDNVU6RDA4GV:/var/lib/docker/overlay2/l/2DJ5X54HJJZDJCPAVTTEACSJMP:/var/lib/docker/overlay2/l/3AUKEU3CY5C7WLFXHOMGTCOP23:/var/lib/docker/overlay2/l/GE2PAWDYWEBSRY4SK4J5GEWMF3:/var/lib/docker/overlay2/l/SZXLIVSYLH6VAXGACBFITXDJIW,upperdir=/var/lib/docker/overlay2/cee0b85cfb5240a2843f83c3d0bcb96aa618a3e6993345975827dfce2e01706b/diff,workdir=/var/lib/docker/overlay2/cee0b85cfb5240a2843f83c3d0bcb96aa618a3e6993345975827dfce2e01706b/work)
overlay on /var/lib/docker/overlay2/7d9093d2527c7369ff2f4895ca1d0c5b3beb4c0c949751823e212ce584a505cd/merged type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/RUJA3733X6IO2HP33HOLHEZLOY:/var/lib/docker/overlay2/l/FA4VJJI57C5KIJMLVN3VFU3XQD:/var/lib/docker/overlay2/l/R3PA4XHIADGCQLCTCA625WQURX:/var/lib/docker/overlay2/l/X6YWBRA2F45TYLOI3FCZOODFGE:/var/lib/docker/overlay2/l/TR5XUEO5F3BTGTPO5E73UARWXJ:/var/lib/docker/overlay2/l/L4FPQ27FMC7GVHHWLQ4QDM2XXW:/var/lib/docker/overlay2/l/FI4PONQPMIYG3B2NLFUBR2PPBN:/var/lib/docker/overlay2/l/G2PGUOFESO37DIYF2XZTWZBRST:/var/lib/docker/overlay2/l/5UYI42OORMMUJFT6OSZEVNIU5D:/var/lib/docker/overlay2/l/QRUDJJZ26G4ZHSU4XCA2XD7CHG,upperdir=/var/lib/docker/overlay2/7d9093d2527c7369ff2f4895ca1d0c5b3beb4c0c949751823e212ce584a505cd/diff,workdir=/var/lib/docker/overlay2/7d9093d2527c7369ff2f4895ca1d0c5b3beb4c0c949751823e212ce584a505cd/work)
overlay on /var/lib/docker/overlay2/86b57b44c07f02aa1253090faf0c08dad496b9db47dae54f940d1533ee550aad/merged type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/AJ76LCAD32L6G5IPXIWXFAKJ2H:/var/lib/docker/overlay2/l/DYN546NVHZHPAMDNZ2M252UC64:/var/lib/docker/overlay2/l/3F2QI47T3PVLKYOAOF5MS4SILO:/var/lib/docker/overlay2/l/LJJ6SFJZUUC35SSTUUV5JRVDAY:/var/lib/docker/overlay2/l/N5Z5FZSTDLLA3B7SVBP5LS3XDM:/var/lib/docker/overlay2/l/TZLHA3L3K7DRASA7GT7CDLYFRV:/var/lib/docker/overlay2/l/ED4B7ZC37S5HYFWKO24KZEXHZR:/var/lib/docker/overlay2/l/7LQCFHPBA7455YWTIGPSKWEO4Z:/var/lib/docker/overlay2/l/GQA7QD3A6INKGXGC2Y6VEMWTLU:/var/lib/docker/overlay2/l/3CP6H5VL47ICN7YNJNR5XUT4UR:/var/lib/docker/overlay2/l/KXNLBV5KN4PAEPHJIS2ECYOKEP,upperdir=/var/lib/docker/overlay2/86b57b44c07f02aa1253090faf0c08dad496b9db47dae54f940d1533ee550aad/diff,workdir=/var/lib/docker/overlay2/86b57b44c07f02aa1253090faf0c08dad496b9db47dae54f940d1533ee550aad/work)
overlay on /var/lib/docker/overlay2/1424ecd998b0ac89b5d49b28d947e23d6207a004ba4e9bd18d27486bcb92fd93/merged type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/BRC42NKLH7YI2C2R4CDJOBSKJG:/var/lib/docker/overlay2/l/NIZI5VOI3W676NRVHBE6Y3U57O:/var/lib/docker/overlay2/l/K45OS4QPOG5MKSBWJ66QDN7B4F:/var/lib/docker/overlay2/l/GKA2VYGH26LDWYKWMKBSD3N5JP:/var/lib/docker/overlay2/l/WZFRB26SOU7JPV7O5NDJDJ2QQW:/var/lib/docker/overlay2/l/YNR3VO36HOJYPNQNJXFLEO3RQY:/var/lib/docker/overlay2/l/4KW6W7GTOCIJOGKTCUURRFZABH:/var/lib/docker/overlay2/l/FQS7ERSFIVW5DME4SXUWFHDL47:/var/lib/docker/overlay2/l/355OD2SJC6WEIWZNSS3HKGZCTR:/var/lib/docker/overlay2/l/Y4EPBEHDJPTS6Z3TBW4C6PBB2G,upperdir=/var/lib/docker/overlay2/1424ecd998b0ac89b5d49b28d947e23d6207a004ba4e9bd18d27486bcb92fd93/diff,workdir=/var/lib/docker/overlay2/1424ecd998b0ac89b5d49b28d947e23d6207a004ba4e9bd18d27486bcb92fd93/work)
overlay on /var/lib/docker/overlay2/023f1dc85198014c9ccb82fda9956a63e220503194186bb93b2c9c486af74fb1/merged type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/W6UF2Y5HIV2A6NEXVDHHQFTB5U:/var/lib/docker/overlay2/l/XPP5SNIR6EW5IZDCN57THAO6VU:/var/lib/docker/overlay2/l/V2ZPIKML6HPM6Q7KAQFVFBVTKR:/var/lib/docker/overlay2/l/4Y55LEBTQSXNJJATFE7OKHHQ7Y:/var/lib/docker/overlay2/l/TR5XUEO5F3BTGTPO5E73UARWXJ:/var/lib/docker/overlay2/l/L4FPQ27FMC7GVHHWLQ4QDM2XXW:/var/lib/docker/overlay2/l/FI4PONQPMIYG3B2NLFUBR2PPBN:/var/lib/docker/overlay2/l/G2PGUOFESO37DIYF2XZTWZBRST:/var/lib/docker/overlay2/l/5UYI42OORMMUJFT6OSZEVNIU5D:/var/lib/docker/overlay2/l/QRUDJJZ26G4ZHSU4XCA2XD7CHG,upperdir=/var/lib/docker/overlay2/023f1dc85198014c9ccb82fda9956a63e220503194186bb93b2c9c486af74fb1/diff,workdir=/var/lib/docker/overlay2/023f1dc85198014c9ccb82fda9956a63e220503194186bb93b2c9c486af74fb1/work)
overlay on /var/lib/docker/overlay2/325a1e49234b046e567f5ad0d3b2b3617c5653bdab911da831810bb2e5469844/merged type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/GOLYDILG3YFPNYARWTKD4JHWWS:/var/lib/docker/overlay2/l/QTAL2IK2LBWRHGAP4SVXODUG52:/var/lib/docker/overlay2/l/G5TGHIHIBJX52VYZ7D2SXTKMOD:/var/lib/docker/overlay2/l/QZHXYRZFRN3AHYEH666CUHIZUK:/var/lib/docker/overlay2/l/S6N54ZGZ3WWD5E2RYAZ3AMK4F3:/var/lib/docker/overlay2/l/VEIFTNKC6GN325DUXXNIKABEYY:/var/lib/docker/overlay2/l/O7IQMQAGQYGKX6ABCGLPXNYYFL:/var/lib/docker/overlay2/l/EGMMTDHA6F55WJBLLX4MN7AHD5:/var/lib/docker/overlay2/l/VZNHRFPNHK6FM6WKTWPBVULO6L:/var/lib/docker/overlay2/l/OF5WE5LBIE4PTJZUX2HIJ6CX7D,upperdir=/var/lib/docker/overlay2/325a1e49234b046e567f5ad0d3b2b3617c5653bdab911da831810bb2e5469844/diff,workdir=/var/lib/docker/overlay2/325a1e49234b046e567f5ad0d3b2b3617c5653bdab911da831810bb2e5469844/work)
overlay on /var/lib/docker/overlay2/fe602dd552ee41f7c0a033738027890991274127da353cbf36905ed1fb24f0ea/merged type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/SZ7SS46KPAEOCBSDG3XD2KEIVW:/var/lib/docker/overlay2/l/3NSHH2M5HF3RXPCK33PM5RMAHS:/var/lib/docker/overlay2/l/H6XF5OLFCIUM3BQ2H2HL5RLSB7:/var/lib/docker/overlay2/l/OD4TG5PGNN7BHPC5NT76DQ4C5H:/var/lib/docker/overlay2/l/VQUT5VXJKNMB4TTQMNKB2NKHXJ:/var/lib/docker/overlay2/l/LYW72M3QBY3DUFSD5F6SENSVL5:/var/lib/docker/overlay2/l/YNR3VO36HOJYPNQNJXFLEO3RQY:/var/lib/docker/overlay2/l/4KW6W7GTOCIJOGKTCUURRFZABH:/var/lib/docker/overlay2/l/FQS7ERSFIVW5DME4SXUWFHDL47:/var/lib/docker/overlay2/l/355OD2SJC6WEIWZNSS3HKGZCTR:/var/lib/docker/overlay2/l/Y4EPBEHDJPTS6Z3TBW4C6PBB2G,upperdir=/var/lib/docker/overlay2/fe602dd552ee41f7c0a033738027890991274127da353cbf36905ed1fb24f0ea/diff,workdir=/var/lib/docker/overlay2/fe602dd552ee41f7c0a033738027890991274127da353cbf36905ed1fb24f0ea/work)
overlay on /var/lib/docker/overlay2/809b0753d4972b903f8b0e01b9c79e73075765af41556038955bee126d82a1b6/merged type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/73BWPPVQTZPEDLE5DANAPKR4HN:/var/lib/docker/overlay2/l/ISA7WEAVTUZP5URFKEKVRLRM7C:/var/lib/docker/overlay2/l/ZGRRTZM2646FUCFEHFR6TEHIFO:/var/lib/docker/overlay2/l/6KIAWPE3OZDJHLRPR2EN47J2LL:/var/lib/docker/overlay2/l/QFDDEC5ZZKQAEPSPGCIKJNEIOP:/var/lib/docker/overlay2/l/YNR3VO36HOJYPNQNJXFLEO3RQY:/var/lib/docker/overlay2/l/4KW6W7GTOCIJOGKTCUURRFZABH:/var/lib/docker/overlay2/l/FQS7ERSFIVW5DME4SXUWFHDL47:/var/lib/docker/overlay2/l/355OD2SJC6WEIWZNSS3HKGZCTR:/var/lib/docker/overlay2/l/Y4EPBEHDJPTS6Z3TBW4C6PBB2G,upperdir=/var/lib/docker/overlay2/809b0753d4972b903f8b0e01b9c79e73075765af41556038955bee126d82a1b6/diff,workdir=/var/lib/docker/overlay2/809b0753d4972b903f8b0e01b9c79e73075765af41556038955bee126d82a1b6/work)
overlay on /var/lib/docker/overlay2/fe09fcd2e8eac6daedf1d5de436aac36d7966e37934a989c47584ef656c4f017/merged type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/TO4Y2ZUNJUW3FU4MH7NWSKLPH4:/var/lib/docker/overlay2/l/DU4ITIA5BWWUEDQ777JSTUARUV:/var/lib/docker/overlay2/l/V2ZPIKML6HPM6Q7KAQFVFBVTKR:/var/lib/docker/overlay2/l/4Y55LEBTQSXNJJATFE7OKHHQ7Y:/var/lib/docker/overlay2/l/TR5XUEO5F3BTGTPO5E73UARWXJ:/var/lib/docker/overlay2/l/L4FPQ27FMC7GVHHWLQ4QDM2XXW:/var/lib/docker/overlay2/l/FI4PONQPMIYG3B2NLFUBR2PPBN:/var/lib/docker/overlay2/l/G2PGUOFESO37DIYF2XZTWZBRST:/var/lib/docker/overlay2/l/5UYI42OORMMUJFT6OSZEVNIU5D:/var/lib/docker/overlay2/l/QRUDJJZ26G4ZHSU4XCA2XD7CHG,upperdir=/var/lib/docker/overlay2/fe09fcd2e8eac6daedf1d5de436aac36d7966e37934a989c47584ef656c4f017/diff,workdir=/var/lib/docker/overlay2/fe09fcd2e8eac6daedf1d5de436aac36d7966e37934a989c47584ef656c4f017/work)
overlay on /var/lib/docker/overlay2/16c0ace8ed723fc68c28b27ca03570a490ab2e9c7b3b71c96456f4df9d1fe145/merged type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/IURSELF7T2C37HBPHJRFQ5J3H7:/var/lib/docker/overlay2/l/I3L6D5FZZKLAG5NGXBD5QNWEKS:/var/lib/docker/overlay2/l/GY32HKOTZSG2VTUSL7JQFOELRX:/var/lib/docker/overlay2/l/ND3QIT5665YBOF7M6AARDZ5ES4:/var/lib/docker/overlay2/l/TR5XUEO5F3BTGTPO5E73UARWXJ:/var/lib/docker/overlay2/l/L4FPQ27FMC7GVHHWLQ4QDM2XXW:/var/lib/docker/overlay2/l/FI4PONQPMIYG3B2NLFUBR2PPBN:/var/lib/docker/overlay2/l/G2PGUOFESO37DIYF2XZTWZBRST:/var/lib/docker/overlay2/l/5UYI42OORMMUJFT6OSZEVNIU5D:/var/lib/docker/overlay2/l/QRUDJJZ26G4ZHSU4XCA2XD7CHG,upperdir=/var/lib/docker/overlay2/16c0ace8ed723fc68c28b27ca03570a490ab2e9c7b3b71c96456f4df9d1fe145/diff,workdir=/var/lib/docker/overlay2/16c0ace8ed723fc68c28b27ca03570a490ab2e9c7b3b71c96456f4df9d1fe145/work)
overlay on /var/lib/docker/overlay2/55bd1e692cc0bee1c5a01e904914354adc0b608cc78e0edeb5b449e66f58c7c8/merged type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/X4TA3O3532PTPEKWK22OQNIWHN:/var/lib/docker/overlay2/l/2V7TJINCA53SPJAZL22NUYEPNQ:/var/lib/docker/overlay2/l/HDJF6X6LD4LJXMX4HHTY2A7TGP:/var/lib/docker/overlay2/l/Y5T6CFSTA4HGCZGIIDMOAZHKAX:/var/lib/docker/overlay2/l/KRS3MH62PRYO2JT2Z7TH2H4FG4:/var/lib/docker/overlay2/l/SAVX2RHKTYYXSMMZCOI7B3VATA:/var/lib/docker/overlay2/l/MBMKXESICB3JR6HLVCNPXQZGFJ:/var/lib/docker/overlay2/l/FHR3EKXGPTWQNDQAJREU6UCTKV:/var/lib/docker/overlay2/l/JU3L7SZBWECR76QP76GCSOG2S3:/var/lib/docker/overlay2/l/VZNHRFPNHK6FM6WKTWPBVULO6L:/var/lib/docker/overlay2/l/OF5WE5LBIE4PTJZUX2HIJ6CX7D,upperdir=/var/lib/docker/overlay2/55bd1e692cc0bee1c5a01e904914354adc0b608cc78e0edeb5b449e66f58c7c8/diff,workdir=/var/lib/docker/overlay2/55bd1e692cc0bee1c5a01e904914354adc0b608cc78e0edeb5b449e66f58c7c8/work)
overlay on /var/lib/docker/overlay2/be20660eda4fd70ae71b9d6d4b462dea3734719ab09c73477b936e67f7b4a0fe/merged type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/XACHFDN6QSALZPKXJIXOTSIIYN:/var/lib/docker/overlay2/l/7MGH7JUUNWZLG47VQXXVWGONHE:/var/lib/docker/overlay2/l/GPBYZLJ67ZYHMEWZXKAZ36CPEQ:/var/lib/docker/overlay2/l/VK6XM3DJHPYYI6D7JACQ5NAT4G:/var/lib/docker/overlay2/l/LUM5C7FUTX54J7UJHZFOVK3XYA:/var/lib/docker/overlay2/l/TR5XUEO5F3BTGTPO5E73UARWXJ:/var/lib/docker/overlay2/l/L4FPQ27FMC7GVHHWLQ4QDM2XXW:/var/lib/docker/overlay2/l/FI4PONQPMIYG3B2NLFUBR2PPBN:/var/lib/docker/overlay2/l/G2PGUOFESO37DIYF2XZTWZBRST:/var/lib/docker/overlay2/l/5UYI42OORMMUJFT6OSZEVNIU5D:/var/lib/docker/overlay2/l/QRUDJJZ26G4ZHSU4XCA2XD7CHG,upperdir=/var/lib/docker/overlay2/be20660eda4fd70ae71b9d6d4b462dea3734719ab09c73477b936e67f7b4a0fe/diff,workdir=/var/lib/docker/overlay2/be20660eda4fd70ae71b9d6d4b462dea3734719ab09c73477b936e67f7b4a0fe/work)
overlay on /var/lib/docker/overlay2/51f9686800ffd1d3164032f40122d47a17a84814525ad3acf0a2a122384aba6b/merged type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/SRTAFILQTNMO3IBZ7HE2KTFRM3:/var/lib/docker/overlay2/l/ZVQZIMMDDC6OFGBOKY4SHD5TNK:/var/lib/docker/overlay2/l/2SJMI5Q45VJY6O7PLZWWEKV5WX:/var/lib/docker/overlay2/l/4LVYGM27GV2DK5SDGPTBKB6S7V:/var/lib/docker/overlay2/l/VGQIZUUXP72YR2OLJOEXSA7CV7:/var/lib/docker/overlay2/l/TR5XUEO5F3BTGTPO5E73UARWXJ:/var/lib/docker/overlay2/l/L4FPQ27FMC7GVHHWLQ4QDM2XXW:/var/lib/docker/overlay2/l/FI4PONQPMIYG3B2NLFUBR2PPBN:/var/lib/docker/overlay2/l/G2PGUOFESO37DIYF2XZTWZBRST:/var/lib/docker/overlay2/l/5UYI42OORMMUJFT6OSZEVNIU5D:/var/lib/docker/overlay2/l/QRUDJJZ26G4ZHSU4XCA2XD7CHG,upperdir=/var/lib/docker/overlay2/51f9686800ffd1d3164032f40122d47a17a84814525ad3acf0a2a122384aba6b/diff,workdir=/var/lib/docker/overlay2/51f9686800ffd1d3164032f40122d47a17a84814525ad3acf0a2a122384aba6b/work)
```

## Cron
```
@reboot sleep 30 && /root/tmux-autostart.sh
```

## SSHD Config (active settings)
```
5:Port 2222
6:AddressFamily inet
7:ListenAddress 0.0.0.0
10:PermitRootLogin no
11:PubkeyAuthentication yes
12:PasswordAuthentication no
14:ChallengeResponseAuthentication no
37:AllowUsers milhy777
39:AllowGroups wheel
52:LogLevel VERBOSE
```

## OpenRC Services
```
Runlevel: boot
 modules                                                           [  started  ]
 hwclock                                                           [  started  ]
 hostname                                                          [  started  ]
 swap                                                              [  started  ]
 sysctl                                                            [  started  ]
 bootmisc                                                          [  started  ]
 syslog                                                            [  started  ]
 loadkmap                                                          [  started  ]
 networking                                                        [  started  ]
 seedrng                                                           [  started  ]
Runlevel: default
 iptables                                                          [  started  ]
 mosquitto                                                         [  started  ]
 docker                                       [  started 2 day(s) 03:05:11 (0) ]
 claude-code                                                       [  started  ]
 acpid                                                             [  started  ]
 chronyd                                                           [  started  ]
 multi-llm-agent                                                   [  started  ]
 samba                                                             [  started  ]
 dbus                                                              [  started  ]
 backup-coordinator                                                [  started  ]
 sshd                                                              [  started  ]
Runlevel: nonetwork
Runlevel: shutdown
 savecache                                                         [  stopped  ]
 killprocs                                                         [  stopped  ]
 mount-ro                                                          [  stopped  ]
Runlevel: sysinit
 devfs                                                             [  started  ]
 dmesg                                                             [  started  ]
 mdev                                                              [  started  ]
 hwdrivers                                                         [  started  ]
Dynamic Runlevel: hotplugged
Dynamic Runlevel: needed/wanted
 sysfs                                                             [  started  ]
 cgroups                                                           [  started  ]
 fsck                                                              [  started  ]
 root                                                              [  started  ]
 localmount                                                        [  started  ]
Dynamic Runlevel: manual
```

## Docker Containers
```
CONTAINER ID   IMAGE                                          COMMAND                  CREATED          STATUS                        PORTS                                                                                                                                                                                                                                                                                                                                                                                                                                                                           NAMES
0747ecfaae63   orchestration-transcriber-mcp                  "uvicorn main:app --…"   2 minutes ago    Up About a minute (healthy)   0.0.0.0:8013->8000/tcp, :::8013->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-transcriber
03c11c3880de   postgres:15                                    "docker-entrypoint.s…"   4 minutes ago    Up 4 minutes (healthy)        0.0.0.0:8021->5432/tcp, :::8021->5432/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-postgresql
9ce3d2c1d74e   orchestration-mqtt-mcp                         "python main.py"         7 minutes ago    Up 7 minutes (healthy)        0.0.0.0:8019->8000/tcp, :::8019->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-mqtt
c7ea2a557a38   eclipse-mosquitto:2                            "/docker-entrypoint.…"   7 minutes ago    Up 7 minutes                  0.0.0.0:8018->1883/tcp, :::8018->1883/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mqtt-broker
4102149d1494   orchestration-qdrant-mcp-wrapper               "uvicorn main:app --…"   15 minutes ago   Up 14 minutes (healthy)       0.0.0.0:8026->8000/tcp, :::8026->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-qdrant-wrapper
de4ab8b4ee65   orchestration-redis-mcp-wrapper                "uvicorn main:app --…"   20 minutes ago   Up 20 minutes (healthy)       0.0.0.0:8025->8000/tcp, :::8025->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-redis-wrapper
55571451b021   qdrant/qdrant:latest                           "./entrypoint.sh"        20 minutes ago   Up 20 minutes                 0.0.0.0:8023->6333/tcp, :::8023->6333/tcp, 0.0.0.0:8027->6334/tcp, :::8027->6334/tcp                                                                                                                                                                                                                                                                                                                                                                                            mcp-qdrant
88e99e279083   redis:7-alpine                                 "docker-entrypoint.s…"   20 minutes ago   Up 20 minutes (healthy)       0.0.0.0:8022->6379/tcp, :::8022->6379/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-redis
0873808b4f81   node:18-alpine                                 "docker-entrypoint.s…"   4 months ago     Up 4 minutes                  0.0.0.0:7012->8000/tcp, :::7012->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-advanced-memory
7ddb9a22e24a   orchestration-filesystem-mcp                   "uvicorn main:app --…"   4 months ago     Up 2 days                     0.0.0.0:7001->8000/tcp, :::7001->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-filesystem
14578bc62e2c   orchestration-research-mcp                     "uvicorn main:app --…"   4 months ago     Up 2 days                     0.0.0.0:7011->8000/tcp, :::7011->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-research
2ff3aab4cf9a   orchestration-zen-coordinator                  "python zen_coordina…"   4 months ago     Up 2 days (healthy)           0.0.0.0:7000->8020/tcp, :::7000->8020/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       zen-coordinator
ec5b81ebd74a   orchestration-terminal-mcp                     "uvicorn main:app --…"   4 months ago     Up 2 days                     0.0.0.0:7003->8000/tcp, :::7003->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-terminal
b7fdf6a9ed37   orchestration-database-mcp                     "uvicorn main:app --…"   4 months ago     Up 2 days                     0.0.0.0:7004->8000/tcp, :::7004->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-database
434ba43dbe30   orchestration-memory-mcp                       "uvicorn main:app --…"   4 months ago     Up 2 days                     0.0.0.0:7005->8000/tcp, :::7005->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-memory
3a79e1002eea   orchestration-git-mcp                          "uvicorn main:app --…"   4 months ago     Up 2 days                     0.0.0.0:7002->8000/tcp, :::7002->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-git
08a5ddba4bc0   orchestration-postgresql-mcp-wrapper           "uvicorn main:app --…"   4 months ago     Up 2 days (healthy)           0.0.0.0:7024->8000/tcp, :::7024->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-postgresql-wrapper
f53fc78902ed   prom/prometheus:latest                         "/bin/prometheus --c…"   4 months ago     Up 2 days                     0.0.0.0:7028->9090/tcp, :::7028->9090/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-monitoring
00c933ce46c7   orchestration-config-mcp                       "uvicorn main:app --…"   4 months ago     Up 2 days (healthy)           0.0.0.0:7009->8000/tcp, :::7009->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-config
7429b10490fd   redis:7-alpine                                 "docker-entrypoint.s…"   4 months ago     Up 2 days                     0.0.0.0:7030->6379/tcp, :::7030->6379/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-message-queue
77211eef721a   orchestration-log-mcp                          "uvicorn main:app --…"   4 months ago     Up 2 days (healthy)           0.0.0.0:7010->8000/tcp, :::7010->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-log
d64d3b8b41f9   orchestration-backup-service                   "uvicorn main:app --…"   4 months ago     Up 2 days (healthy)           0.0.0.0:7029->8000/tcp, :::7029->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-backup
c29d41071778   orchestration-vision-mcp                       "uvicorn main:app --…"   4 months ago     Up 2 days (healthy)           0.0.0.0:7014->8000/tcp, :::7014->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-vision
e485a99342c0   orchestration-security-mcp                     "uvicorn main:app --…"   4 months ago     Up 2 days (healthy)           0.0.0.0:7008->8000/tcp, :::7008->8000/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       mcp-security
4b58b9671816   portainer/agent:2.27.9                         "./agent"                5 months ago     Up 2 days                     0.0.0.0:9001->9001/tcp, :::9001->9001/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                       portainer_agent
ba26628b2bb3   portainer/portainer-ce:latest                  "/portainer --ssl"       5 months ago     Up 2 days                     8000/tcp, 9000/tcp, 0.0.0.0:10001->9443/tcp, :::10001->9443/tcp                                                                                                                                                                                                                                                                                                                                                                                                                 portainer
392372ce2f29   adguard/adguardhome                            "/opt/adguardhome/Ad…"   6 months ago     Up 2 days                     0.0.0.0:53->53/udp, :::53->53/udp, 0.0.0.0:53->53/tcp, 0.0.0.0:67-68->67-68/udp, :::53->53/tcp, :::67-68->67-68/udp, 0.0.0.0:443->443/tcp, 0.0.0.0:443->443/udp, :::443->443/tcp, :::443->443/udp, 0.0.0.0:853->853/tcp, 0.0.0.0:853->853/udp, :::853->853/tcp, :::853->853/udp, 0.0.0.0:5443->5443/tcp, :::5443->5443/tcp, 0.0.0.0:6060->6060/tcp, 0.0.0.0:5443->5443/udp, :::6060->6060/tcp, :::5443->5443/udp, 3000/tcp, 3000/udp, 0.0.0.0:10003->80/tcp, :::10003->80/tcp   adguardhome
778c0779986e   ghcr.io/home-assistant/home-assistant:stable   "/init"                  7 months ago     Up 2 days                     0.0.0.0:10002->8123/tcp, :::10002->8123/tcp                                                                                                                                                                                                                                                                                                                                                                                                                                     homeassistant
```

## Docker Health Summary
```
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

## /home Summary
```
total 36376
drwxr-xr-x  9 root     root         4096 Aug 23 05:54 .
drwxr-xr-x 23 root     root         4096 Aug  6 20:48 ..
drwxr-xr-x  2 root     root         4096 Aug  7 14:04 .claude
drwxr-xr-x  3 root     root         4096 Aug 23 06:04 ZEN repo
drwxrwxr-x  8 milhy777 milhy777     4096 Jul 12  2025 claude-code-telegram
-rw-r--r--  1 root     root      1938948 Jul 12  2025 claude-telegram-patterns.tar.gz
-rw-r--r--  1 root     root         1574 Jul 21  2025 docker-compose-complete.yml.backup
-rw-r--r--  1 root     root         8211 Jul 23  2025 docker-mcp-backup-20250723.tar.gz
-rw-r--r--  1 root     root        28869 Aug  7 08:05 docker-mcp-stack-backup-20250807.tar.gz
-rw-r--r--  1 root     root       294998 Jul 12  2025 fei-patterns.tar.gz
-rw-r--r--  1 root     root      6932235 Jul 11  2025 has_backup_20250711_025338.tar.gz
drwxr-sr-x  7 milhy777 milhy777     4096 Dec 21 20:56 milhy777
drwxr-xr-x 21 root     root         4096 Feb  4 11:37 orchestration
-rw-r--r--  1 root     root     27271114 Aug 16 15:58 orchestration-backup-20250816-155751.tar.gz
-rw-r--r--  1 root     root       699593 Jul 27  2025 pre-reboot-backup-20250728_002045.tar.gz
-rw-r--r--  1 root     root         1457 Jul 27  2025 pre-reboot-services-20250728_002052.log
-rw-------  1 root     root         8963 Jul  3  2025 rules-save
drwxr-xr-x  2 root     root         4096 Jul  5  2025 webmin-backup-20250705-1734
drwxr-xr-x  3 root     root         4096 Jul  5  2025 webmin-backup-20250705-173522
```

## Claude/Anthropic Related Paths
```

```

## Git Status (repo: /home/orchestration)
```
## master...origin/master
 M .claude/agents/claude_code_agent.py
 M .claude/agents/multi_llm_agent.py
 M GEMINI.md
 M docker-compose.yml
 M mcp-servers/mqtt-broker/config/passwd
 M mcp-servers/mqtt-mcp/Dockerfile
 M mcp-servers/qdrant-mcp/requirements.txt
 M mcp-servers/webm-transcriber/Dockerfile
?? AGENTS.md
?? CLAUDE.md
?? docs/audit_2026-02-05/
```

## Git Diff Stat vs origin/master
```
.claude/agents/claude_code_agent.py     |  2 +-
 .claude/agents/multi_llm_agent.py       |  6 +--
 GEMINI.md                               | 94 +++++++++++++--------------------
 docker-compose.yml                      |  2 +-
 mcp-servers/mqtt-broker/config/passwd   |  2 +-
 mcp-servers/mqtt-mcp/Dockerfile         |  1 +
 mcp-servers/qdrant-mcp/requirements.txt |  1 +
 mcp-servers/webm-transcriber/Dockerfile |  7 ++-
 8 files changed, 51 insertions(+), 64 deletions(-)
```

## Git Diff Names vs origin/master
```
M	.claude/agents/claude_code_agent.py
M	.claude/agents/multi_llm_agent.py
M	GEMINI.md
M	docker-compose.yml
M	mcp-servers/mqtt-broker/config/passwd
M	mcp-servers/mqtt-mcp/Dockerfile
M	mcp-servers/qdrant-mcp/requirements.txt
M	mcp-servers/webm-transcriber/Dockerfile
```
