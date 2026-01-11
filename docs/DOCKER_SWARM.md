# Docker Swarm Deployment Guide (IPvlan)

> [!NOTE]
> This is community-contributed. Due to environment, setup, or networking differences, results may vary. Please open a PR to improve it instead of creating an issue, as the maintainer is not actively maintaining it.


This guide describes how to deploy **NetAlertX** in a **Docker Swarm** environment using an `ipvlan` network. This enables the container to receive a LAN IP address directly, which is ideal for network monitoring.

---

## ⚙️ Step 1: Create an IPvlan Config-Only Network on All Nodes

> Run this command on **each node** in the Swarm.

```bash
docker network create -d ipvlan \
  --subnet=192.168.1.0/24 \              # 🔧 Replace with your LAN subnet
  --gateway=192.168.1.1 \                # 🔧 Replace with your LAN gateway
  -o ipvlan_mode=l2 \
  -o parent=eno1 \                       # 🔧 Replace with your network interface (e.g., eth0, eno1)
  --config-only \
  ipvlan-swarm-config
```

---

## 🖥️ Step 2: Create the Swarm-Scoped IPvlan Network (One-Time Setup)

> Run this on **one Swarm manager node only**.

```bash
docker network create -d ipvlan \
  --scope swarm \
  --config-from ipvlan-swarm-config \
  swarm-ipvlan
```

---

## 🧾 Step 3: Deploy NetAlertX with Docker Compose

Use the following Compose snippet to deploy NetAlertX with a **static LAN IP** assigned via the `swarm-ipvlan` network.

```yaml
services:
  netalertx:
    image: ghcr.io/jokob-sk/netalertx:latest
...
    networks:
      swarm-ipvlan:
        ipv4_address: 192.168.1.240     # ⚠️ Choose a free IP from your LAN
    deploy:
      mode: replicated
      replicas: 1
      restart_policy:
        condition: on-failure
      placement:
        constraints:
          - node.role == manager        # 🔄 Or use: node.labels.netalertx == true

networks:
  swarm-ipvlan:
    external: true
```

---

## ✅ Notes

* The `ipvlan` setup allows **NetAlertX** to have a direct IP on your LAN.
* Replace `eno1` with your interface, IP addresses, and volume paths to match your environment.
* Make sure the assigned IP (`192.168.1.240` above) is not in use or managed by DHCP.
* You may also use a node label constraint instead of `node.role == manager` for more control.

