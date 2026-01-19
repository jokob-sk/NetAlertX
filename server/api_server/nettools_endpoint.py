import subprocess
import re
import json
import sys
import ipaddress
import shutil
import os
from flask import jsonify
from const import NATIVE_SPEEDTEST_PATH

# Resolve speedtest-cli path once at module load and validate it.
# We do this once to avoid repeated PATH lookups and to fail fast when
# the binary isn't available or executable.
SPEEDTEST_CLI_PATH = None



def _get_speedtest_cli_path():
    """Resolve and validate the speedtest-cli executable path."""
    path = shutil.which("speedtest-cli")
    if path is None:
        raise RuntimeError(
            "speedtest-cli not found in PATH. Please install it: "
            "pip install speedtest-cli"
        )
    if not os.access(path, os.X_OK):
        raise RuntimeError(
            f"speedtest-cli found at {path} but is not executable"
        )
    return path


try:
    SPEEDTEST_CLI_PATH = _get_speedtest_cli_path()
except Exception as e:
    # Warn but don't crash import — the endpoint will return 503 when called.
    print(f"Warning: {e}", file=sys.stderr)
    SPEEDTEST_CLI_PATH = None


def wakeonlan(mac):
    # Validate MAC
    if not re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", mac):
        return jsonify({"success": False, "error": f"Invalid MAC: {mac}"}), 400

    try:
        result = subprocess.run(
            ["wakeonlan", mac], capture_output=True, text=True, check=True
        )
        return jsonify(
            {
                "success": True,
                "message": "WOL packet sent",
                "output": result.stdout.strip(),
            }
        )
    except subprocess.CalledProcessError as e:
        return jsonify(
            {
                "success": False,
                "error": "Failed to send WOL packet",
                "details": e.stderr.strip(),
            }
        ), 500


def traceroute(ip):
    """
    Executes a traceroute to the given IP address.

    Parameters:
        ip (str): The target IP address to trace.

    Returns:
        JSON response with:
            - success (bool)
            - output (str) if successful
            - error (str) and details (str) if failed
    """
    # --------------------------
    # Step 1: Validate IP address
    # --------------------------
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        # Return 400 if IP is invalid
        return jsonify({"success": False, "error": f"Invalid IP: {ip}"}), 400

    # --------------------------
    # Step 2: Execute traceroute
    # --------------------------
    try:
        result = subprocess.run(
            ["traceroute", ip],  # Command and argument
            capture_output=True,  # Capture stdout/stderr
            text=True,  # Return output as string
            check=True,  # Raise CalledProcessError on non-zero exit
        )
        # Return success response with traceroute output
        return jsonify({"success": True, "output": result.stdout.strip().splitlines()})

    # --------------------------
    # Step 3: Handle command errors
    # --------------------------
    except subprocess.CalledProcessError as e:
        # Return 500 if traceroute fails
        return jsonify(
            {
                "success": False,
                "error": "Traceroute failed",
                "details": e.stderr.strip(),
            }
        ), 500


def speedtest():
    """
    API endpoint to run a speedtest using native binary or speedtest-cli.
    Returns JSON with the test output or error.
    """
    # Prefer native speedtest binary
    if os.path.exists(NATIVE_SPEEDTEST_PATH):
        try:
            result = subprocess.run(
                [NATIVE_SPEEDTEST_PATH, "--format=json", "--accept-license", "--accept-gdpr"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    download = round(data['download']['bandwidth'] * 8 / 10**6, 2)
                    upload = round(data['upload']['bandwidth'] * 8 / 10**6, 2)
                    ping = data['ping']['latency']
                    isp = data['isp']
                    server = f"{data['server']['name']} - {data['server']['location']} ({data['server']['id']})"
                    
                    output_lines = [
                        f"Server: {server}",
                        f"ISP: {isp}",
                        f"Latency: {ping} ms",
                        f"Download: {download} Mbps",
                        f"Upload: {upload} Mbps"
                    ]
                    
                    if 'packetLoss' in data:
                        output_lines.append(f"Packet Loss: {data['packetLoss']}%")
                    
                    return jsonify({"success": True, "output": output_lines})
                
                except (json.JSONDecodeError, KeyError, TypeError) as parse_error:
                    print(f"Failed to parse native speedtest output: {parse_error}", file=sys.stderr)
                    # Fall through to CLI fallback
            else:
                print(f"Native speedtest exited with code {result.returncode}: {result.stderr}", file=sys.stderr)

        except subprocess.TimeoutExpired:
            print("Native speedtest timed out after 60s, falling back to CLI", file=sys.stderr)
        except Exception as e:
            # Fall back to speedtest-cli if native fails
            print(f"Native speedtest failed: {e}, falling back to CLI", file=sys.stderr)

    # If the CLI wasn't found at module load, return a 503 so the caller
    # knows the service is unavailable rather than failing unpredictably.
    if SPEEDTEST_CLI_PATH is None:
        return jsonify(
            {
                "success": False,
                "error": "speedtest-cli is not installed or not found in PATH",
            }
        ), 503

    try:
        # Run speedtest-cli command using the resolved absolute path
        result = subprocess.run(
            [SPEEDTEST_CLI_PATH, "--secure", "--simple"],
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )

        # Return each line as a list
        output_lines = result.stdout.strip().split("\n")
        return jsonify({"success": True, "output": output_lines})

    except subprocess.TimeoutExpired:
        return jsonify(
            {
                "success": False,
                "error": "Speedtest timed out after 60 seconds",
            }
        ), 504

    except subprocess.CalledProcessError as e:
        return jsonify(
            {
                "success": False,
                "error": "Speedtest failed",
                "details": e.stderr.strip(),
            }
        ), 500

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "error": "Failed to run speedtest",
                "details": str(e),
            }
        ), 500


def nslookup(ip):
    """
    Run an nslookup on the given IP address.
    Returns JSON with the lookup output or error.
    """
    # Validate IP
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid IP address"}), 400

    try:
        # Run nslookup command
        result = subprocess.run(
            ["nslookup", ip], capture_output=True, text=True, check=True
        )

        output_lines = result.stdout.strip().split("\n")
        return jsonify({"success": True, "output": output_lines})

    except subprocess.CalledProcessError as e:
        return jsonify(
            {
                "success": False,
                "error": "nslookup failed",
                "details": e.stderr.strip(),
            }
        ), 500


def nmap_scan(ip, mode):
    """
    Run an nmap scan on the given IP address with the requested mode.
    Modes supported:
        - "fast"          → nmap -F <ip>
        - "normal"        → nmap <ip>
        - "detail"        → nmap -A <ip>
        - "skipdiscovery" → nmap -Pn <ip>
    Returns JSON with the scan output or error.
    """
    # Validate IP
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid IP address"}), 400

    # Map scan modes to nmap arguments
    mode_args = {
        "fast": ["-F"],
        "normal": [],
        "detail": ["-A"],
        "skipdiscovery": ["-Pn"],
    }

    if mode not in mode_args:
        return jsonify(
            {"success": False, "error": f"Invalid scan mode '{mode}'"}
        ), 400

    try:
        # Build and run nmap command
        cmd = ["nmap"] + mode_args[mode] + [ip]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        output_lines = result.stdout.strip().split("\n")
        return jsonify(
            {"success": True, "mode": mode, "ip": ip, "output": output_lines}
        )

    except subprocess.CalledProcessError as e:
        return jsonify(
            {
                "success": False,
                "error": "nmap scan failed",
                "details": e.stderr.strip(),
            }
        ), 500


def internet_info():
    """
    API endpoint to fetch internet info using ipinfo.io.
    Returns JSON with the info or error.
    """
    try:
        result = subprocess.run(
            ["curl", "-s", "https://ipinfo.io/json"],
            capture_output=True,
            text=True,
            check=True,
        )

        if not result.stdout:
            raise ValueError("Empty response from ipinfo.io")

        data = json.loads(result.stdout)

        return jsonify({
            "success": True,
            "output": data
        })

    except (subprocess.CalledProcessError, ValueError, json.JSONDecodeError) as e:
        return jsonify(
            {
                "success": False,
                "error": "Failed to fetch internet info",
                "details": str(e),
            }
        ), 500


def network_interfaces():
    """
    API endpoint to fetch network interface info using `nmap --iflist`.
    Returns JSON with interface info and RX/TX bytes.
    """
    try:
        # Run Nmap
        nmap_output = subprocess.run(
            ["nmap", "--iflist"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        # Read /proc/net/dev for RX/TX
        rx_tx = {}
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                if ":" not in line:
                    continue
                iface, data = line.split(":")
                iface = iface.strip()
                cols = data.split()
                rx_bytes = int(cols[0])
                tx_bytes = int(cols[8])
                rx_tx[iface] = {"rx": rx_bytes, "tx": tx_bytes}

        interfaces = {}

        for line in nmap_output.splitlines():
            line = line.strip()
            if not line:
                continue

            # Skip header line
            if line.startswith("DEV") or line.startswith("----"):
                continue

            # Regex to parse: DEV (SHORT) IP/MASK TYPE UP MTU MAC
            match = re.match(
                r"^(\S+)\s+\(([^)]*)\)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*(\S*)",
                line
            )
            if not match:
                continue

            dev, short, ipmask, type_, state, mtu_str, mac = match.groups()

            # Only parse MTU if it's a number
            try:
                mtu = int(mtu_str)
            except ValueError:
                mtu = None

            if dev not in interfaces:
                interfaces[dev] = {
                    "name": dev,
                    "short": short,
                    "type": type_,
                    "state": state.lower(),
                    "mtu": mtu,
                    "mac": mac if mac else None,
                    "ipv4": [],
                    "ipv6": [],
                    "rx_bytes": rx_tx.get(dev, {}).get("rx", 0),
                    "tx_bytes": rx_tx.get(dev, {}).get("tx", 0),
                }

            # Parse IP/MASK
            if ipmask != "(none)/0":
                if ":" in ipmask:
                    interfaces[dev]["ipv6"].append(ipmask)
                else:
                    interfaces[dev]["ipv4"].append(ipmask)

        return jsonify({"success": True, "interfaces": interfaces}), 200

    except (subprocess.CalledProcessError, ValueError, FileNotFoundError) as e:
        return jsonify(
            {
                "success": False,
                "error": "Failed to fetch network interface info",
                "details": str(e),
            }
        ), 500
