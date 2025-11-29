import subprocess
import re
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
import sqlite3
from helper import get_setting_value
from database import get_temp_db_connection

tools_bp = Blueprint('tools', __name__)


def check_auth():
    """Check API_TOKEN authorization."""
    token = request.headers.get("Authorization")
    expected_token = f"Bearer {get_setting_value('API_TOKEN')}"
    return token == expected_token


@tools_bp.route('/trigger_scan', methods=['POST'])
def trigger_scan():
    """
    Forces NetAlertX to run a specific scan type immediately.
    Arguments: scan_type (Enum: arp, nmap_fast, nmap_deep), target (optional IP/CIDR)
    """
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    scan_type = data.get('scan_type', 'nmap_fast')
    target = data.get('target')

    # Validate scan_type
    if scan_type not in ['arp', 'nmap_fast', 'nmap_deep']:
        return jsonify({"error": "Invalid scan_type. Must be 'arp', 'nmap_fast', or 'nmap_deep'"}), 400

    # Determine command
    cmd = []
    if scan_type == 'arp':
        # ARP scan usually requires sudo or root, assuming container runs as root or has caps
        cmd = ["arp-scan", "--localnet", "--interface=eth0"]  # Defaulting to eth0, might need detection
        if target:
            cmd = ["arp-scan", target]
    elif scan_type == 'nmap_fast':
        cmd = ["nmap", "-F"]
        if target:
            cmd.append(target)
        else:
            # Default to local subnet if possible, or error if not easily determined
            # For now, let's require target for nmap if not easily deducible,
            # or try to get it from settings.
            # NetAlertX usually knows its subnet.
            # Let's try to get the scan subnet from settings if not provided.
            scan_subnets = get_setting_value("SCAN_SUBNETS")
            if scan_subnets:
                # Take the first one for now
                cmd.append(scan_subnets.split(',')[0].strip())
            else:
                return jsonify({"error": "Target is required and no default SCAN_SUBNETS found"}), 400
    elif scan_type == 'nmap_deep':
        cmd = ["nmap", "-A", "-T4"]
        if target:
            cmd.append(target)
        else:
            scan_subnets = get_setting_value("SCAN_SUBNETS")
            if scan_subnets:
                cmd.append(scan_subnets.split(',')[0].strip())
            else:
                return jsonify({"error": "Target is required and no default SCAN_SUBNETS found"}), 400

    try:
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return jsonify({
            "success": True,
            "scan_type": scan_type,
            "command": " ".join(cmd),
            "output": result.stdout.strip().split('\n')
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            "success": False,
            "error": "Scan failed",
            "details": e.stderr.strip()
        }), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@tools_bp.route('/list_devices', methods=['POST'])
def list_devices():
    """List all devices."""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_temp_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute("SELECT devName, devMac, devLastIP as devIP, devVendor, devFirstConnection, devLastConnection FROM Devices ORDER BY devFirstConnection DESC")
        rows = cur.fetchall()
        devices = [dict(row) for row in rows]
        return jsonify(devices)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@tools_bp.route('/get_device_info', methods=['POST'])
def get_device_info():
    """Get detailed info for a specific device."""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    query = data['query']

    conn = get_temp_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        # Search by MAC, Name, or partial IP
        sql = "SELECT * FROM Devices WHERE devMac LIKE ? OR devName LIKE ? OR devLastIP LIKE ?"
        cur.execute(sql, (f"%{query}%", f"%{query}%", f"%{query}%"))
        rows = cur.fetchall()

        if not rows:
            return jsonify({"message": "No devices found"}), 404

        devices = [dict(row) for row in rows]
        return jsonify(devices)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@tools_bp.route('/get_latest_device', methods=['POST'])
def get_latest_device():
    """Get full details of the most recently discovered device."""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_temp_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        # Get the device with the most recent devFirstConnection
        cur.execute("SELECT * FROM Devices ORDER BY devFirstConnection DESC LIMIT 1")
        row = cur.fetchone()

        if not row:
            return jsonify({"message": "No devices found"}), 404

        # Return as a list to be consistent with other endpoints
        return jsonify([dict(row)])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@tools_bp.route('/get_open_ports', methods=['POST'])
def get_open_ports():
    """
    Specific query for the port-scan results of a target.
    Arguments: target (IP or MAC)
    """
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    target = data.get('target')

    if not target:
        return jsonify({"error": "Target is required"}), 400

    # If MAC is provided, try to resolve to IP
    if re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", target):
        conn = get_temp_db_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            cur.execute("SELECT devLastIP FROM Devices WHERE devMac = ?", (target,))
            row = cur.fetchone()
            if row and row['devLastIP']:
                target = row['devLastIP']
            else:
                return jsonify({"error": f"Could not resolve IP for MAC {target}"}), 404
        finally:
            conn.close()

    try:
        # Run nmap -F for fast port scan
        cmd = ["nmap", "-F", target]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=120
        )

        # Parse output for open ports
        open_ports = []
        for line in result.stdout.split('\n'):
            if '/tcp' in line and 'open' in line:
                parts = line.split('/')
                port = parts[0].strip()
                service = line.split()[2] if len(line.split()) > 2 else "unknown"
                open_ports.append({"port": int(port), "service": service})

        return jsonify({
            "success": True,
            "target": target,
            "open_ports": open_ports,
            "raw_output": result.stdout.strip().split('\n')
        })

    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": "Port scan failed", "details": e.stderr.strip()}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@tools_bp.route('/get_network_topology', methods=['GET'])
def get_network_topology():
    """
    Returns the "Parent/Child" relationships.
    """
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_temp_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute("SELECT devName, devMac, devParentMAC, devParentPort, devVendor FROM Devices")
        rows = cur.fetchall()

        nodes = []
        links = []

        for row in rows:
            nodes.append({
                "id": row['devMac'],
                "name": row['devName'],
                "vendor": row['devVendor']
            })
            if row['devParentMAC']:
                links.append({
                    "source": row['devParentMAC'],
                    "target": row['devMac'],
                    "port": row['devParentPort']
                })

        return jsonify({
            "nodes": nodes,
            "links": links
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@tools_bp.route('/get_recent_alerts', methods=['POST'])
def get_recent_alerts():
    """
    Fetches the last N system alerts.
    Arguments: hours (lookback period, default 24)
    """
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    hours = data.get('hours', 24)

    conn = get_temp_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        # Calculate cutoff time
        cutoff = datetime.now() - timedelta(hours=int(hours))
        cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')

        cur.execute("""
            SELECT eve_DateTime, eve_EventType, eve_MAC, eve_IP, devName
            FROM Events
            LEFT JOIN Devices ON Events.eve_MAC = Devices.devMac
            WHERE eve_DateTime > ?
            ORDER BY eve_DateTime DESC
        """, (cutoff_str,))

        rows = cur.fetchall()
        alerts = [dict(row) for row in rows]

        return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@tools_bp.route('/set_device_alias', methods=['POST'])
def set_device_alias():
    """
    Updates the name (alias) of a device.
    Arguments: mac, alias
    """
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    mac = data.get('mac')
    alias = data.get('alias')

    if not mac or not alias:
        return jsonify({"error": "MAC and Alias are required"}), 400

    conn = get_temp_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("UPDATE Devices SET devName = ? WHERE devMac = ?", (alias, mac))
        conn.commit()

        if cur.rowcount == 0:
            return jsonify({"error": "Device not found"}), 404

        return jsonify({"success": True, "message": f"Device {mac} renamed to {alias}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@tools_bp.route('/wol_wake_device', methods=['POST'])
def wol_wake_device():
    """
    Sends a Wake-on-LAN magic packet.
    Arguments: mac OR ip
    """
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    mac = data.get('mac')
    ip = data.get('ip')

    if not mac and not ip:
        return jsonify({"error": "MAC address or IP address is required"}), 400

    # Resolve IP to MAC if MAC is missing
    if not mac and ip:
        conn = get_temp_db_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            # Try to find device by IP (devLastIP)
            cur.execute("SELECT devMac FROM Devices WHERE devLastIP = ?", (ip,))
            row = cur.fetchone()
            if row and row['devMac']:
                mac = row['devMac']
            else:
                return jsonify({"error": f"Could not resolve MAC for IP {ip}"}), 404
        except Exception as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            conn.close()

    # Validate MAC
    if not re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", mac):
        return jsonify({"success": False, "error": f"Invalid MAC: {mac}"}), 400

    try:
        # Using wakeonlan command
        result = subprocess.run(
            ["wakeonlan", mac], capture_output=True, text=True, check=True, timeout=10 
        )
        return jsonify(
            {
                "success": True,
                "message": f"WOL packet sent to {mac}",
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


@tools_bp.route('/openapi.json', methods=['GET'])
def openapi_spec():
    """Return OpenAPI specification for tools."""
    # No auth required for spec to allow easy import, or require it if preferred.
    # Open WebUI usually needs to fetch spec without auth first or handles it.
    # We'll allow public access to spec for simplicity of import.

    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "NetAlertX Tools",
            "description": "API for NetAlertX device management tools",
            "version": "1.1.0"
        },
        "servers": [
            {"url": "/api/tools"}
        ],
        "paths": {
            "/list_devices": {
                "post": {
                    "summary": "List all devices (Summary)",
                    "description": (
                        "Retrieve a SUMMARY list of all devices, sorted by newest first. "
                        "IMPORTANT: This only provides basic info (Name, IP, Vendor). "
                        "For FULL details (like custom props, alerts, etc.), you MUST use 'get_device_info' or 'get_latest_device'."
                    ),
                    "operationId": "list_devices",
                    "responses": {
                        "200": {
                            "description": "List of devices (Summary)",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "devName": {"type": "string"},
                                                "devMac": {"type": "string"},
                                                "devIP": {"type": "string"},
                                                "devVendor": {"type": "string"},
                                                "devStatus": {"type": "string"},
                                                "devFirstConnection": {"type": "string"},
                                                "devLastConnection": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/get_device_info": {
                "post": {
                    "summary": "Get device info (Full Details)",
                    "description": (
                        "Get COMPREHENSIVE information about a specific device by MAC, Name, or partial IP. "
                        "Use this to see all available properties, alerts, and metadata not shown in the list."
                    ),
                    "operationId": "get_device_info",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "MAC address, Device Name, or partial IP to search for"
                                        }
                                    },
                                    "required": ["query"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Device details (Full)",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"type": "object"}
                                    }
                                }
                            }
                        },
                        "404": {"description": "Device not found"}
                    }
                }
            },
            "/get_latest_device": {
                "post": {
                    "summary": "Get latest device (Full Details)",
                    "description": "Get COMPREHENSIVE information about the most recently discovered device (latest devFirstConnection).",
                    "operationId": "get_latest_device",
                    "responses": {
                        "200": {
                            "description": "Latest device details (Full)",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"type": "object"}
                                    }
                                }
                            }
                        },
                        "404": {"description": "No devices found"}
                    }
                }
            },
            "/trigger_scan": {
                "post": {
                    "summary": "Trigger Active Scan",
                    "description": "Forces NetAlertX to run a specific scan type immediately.",
                    "operationId": "trigger_scan",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "scan_type": {
                                            "type": "string",
                                            "enum": ["arp", "nmap_fast", "nmap_deep"],
                                            "default": "nmap_fast"
                                        },
                                        "target": {
                                            "type": "string",
                                            "description": "IP address or CIDR to scan"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Scan started/completed successfully"},
                        "400": {"description": "Invalid input"}
                    }
                }
            },
            "/get_open_ports": {
                "post": {
                    "summary": "Get Open Ports",
                    "description": "Specific query for the port-scan results of a target.",
                    "operationId": "get_open_ports",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "target": {
                                            "type": "string",
                                            "description": "IP or MAC address"
                                        }
                                    },
                                    "required": ["target"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "List of open ports"},
                        "404": {"description": "Target not found"}
                    }
                }
            },
            "/get_network_topology": {
                "get": {
                    "summary": "Get Network Topology",
                    "description": "Returns the Parent/Child relationships for network visualization.",
                    "operationId": "get_network_topology",
                    "responses": {
                        "200": {"description": "Graph data (nodes and links)"}
                    }
                }
            },
            "/get_recent_alerts": {
                "post": {
                    "summary": "Get Recent Alerts",
                    "description": "Fetches the last N system alerts.",
                    "operationId": "get_recent_alerts",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "hours": {
                                            "type": "integer",
                                            "default": 24
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "List of alerts"}
                    }
                }
            },
            "/set_device_alias": {
                "post": {
                    "summary": "Set Device Alias",
                    "description": "Updates the name (alias) of a device.",
                    "operationId": "set_device_alias",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "mac": {"type": "string"},
                                        "alias": {"type": "string"}
                                    },
                                    "required": ["mac", "alias"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Alias updated"},
                        "404": {"description": "Device not found"}
                    }
                }
            },
            "/wol_wake_device": {
                "post": {
                    "summary": "Wake on LAN",
                    "description": "Sends a Wake-on-LAN magic packet to the target MAC or IP. If IP is provided, it resolves to MAC first.",
                    "operationId": "wol_wake_device",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "mac": {"type": "string", "description": "Target MAC address"},
                                        "ip": {"type": "string", "description": "Target IP address (resolves to MAC)"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "WOL packet sent"},
                        "404": {"description": "IP not found"}
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        "security": [
            {"bearerAuth": []}
        ]
    }
    return jsonify(spec)
