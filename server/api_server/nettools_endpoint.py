import subprocess
import re
import sys
import ipaddress
from flask import jsonify

# Register NetAlertX directories
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

def wakeonlan(mac):  

    # Validate MAC
    if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac):
        return jsonify({"success": False, "error": f"Invalid MAC: {mac}"}), 400

    try:
        result = subprocess.run(
            ["wakeonlan", mac],
            capture_output=True,
            text=True,
            check=True
        )
        return jsonify({"success": True, "message": "WOL packet sent", "output": result.stdout.strip()})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": "Failed to send WOL packet", "details": e.stderr.strip()}), 500

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
            ["traceroute", ip],       # Command and argument
            capture_output=True,      # Capture stdout/stderr
            text=True,                # Return output as string
            check=True                # Raise CalledProcessError on non-zero exit
        )
        # Return success response with traceroute output
        return jsonify({"success": True, "output": result.stdout.strip()})

    # --------------------------
    # Step 3: Handle command errors
    # --------------------------
    except subprocess.CalledProcessError as e:
        # Return 500 if traceroute fails
        return jsonify({
            "success": False,
            "error": "Traceroute failed",
            "details": e.stderr.strip()
        }), 500


def speedtest():
    """
    API endpoint to run a speedtest using speedtest-cli.
    Returns JSON with the test output or error.
    """
    try:
        # Run speedtest-cli command
        result = subprocess.run(
            [f"{INSTALL_PATH}/back/speedtest-cli", "--secure", "--simple"],
            capture_output=True,
            text=True,
            check=True
        )

        # Return each line as a list
        output_lines = result.stdout.strip().split("\n")
        return jsonify({"success": True, "output": output_lines})

    except subprocess.CalledProcessError as e:
        return jsonify({
            "success": False,
            "error": "Speedtest failed",
            "details": e.stderr.strip()
        }), 500


def nslookup(ip):
    """
    Run an nslookup on the given IP address.
    Returns JSON with the lookup output or error.
    """
    # Validate IP
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return jsonify({
            "success": False,
            "error": "Invalid IP address"
        }), 400

    try:
        # Run nslookup command
        result = subprocess.run(
            ["nslookup", ip],
            capture_output=True,
            text=True,
            check=True
        )

        output_lines = result.stdout.strip().split("\n")
        return jsonify({"success": True, "output": output_lines})

    except subprocess.CalledProcessError as e:
        return jsonify({
            "success": False,
            "error": "nslookup failed",
            "details": e.stderr.strip()
        }), 500


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
        return jsonify({
            "success": False,
            "error": "Invalid IP address"
        }), 400

    # Map scan modes to nmap arguments
    mode_args = {
        "fast": ["-F"],
        "normal": [],
        "detail": ["-A"],
        "skipdiscovery": ["-Pn"]
    }

    if mode not in mode_args:
        return jsonify({
            "success": False,
            "error": f"Invalid scan mode '{mode}'"
        }), 400

    try:
        # Build and run nmap command
        cmd = ["nmap"] + mode_args[mode] + [ip]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        output_lines = result.stdout.strip().split("\n")
        return jsonify({
            "success": True,
            "mode": mode,
            "ip": ip,
            "output": output_lines
        })

    except subprocess.CalledProcessError as e:
        return jsonify({
            "success": False,
            "error": "nmap scan failed",
            "details": e.stderr.strip()
        }), 500


def internet_info():
    """
    API endpoint to fetch internet info using ipinfo.io.
    Returns JSON with the info or error.
    """
    try:
        # Perform the request via curl
        result = subprocess.run(
            ["curl", "-s", "https://ipinfo.io"],
            capture_output=True,
            text=True,
            check=True
        )

        output = result.stdout.strip()
        if not output:
            raise ValueError("Empty response from ipinfo.io")

        # Clean up the JSON-like string by removing { } , and "
        cleaned_output = output.replace("{", "").replace("}", "").replace(",", "").replace('"', "")

        return jsonify({"success": True, "output": cleaned_output})

    except (subprocess.CalledProcessError, ValueError) as e:
        return jsonify({
            "success": False,
            "error": "Failed to fetch internet info",
            "details": str(e)
        }), 500
