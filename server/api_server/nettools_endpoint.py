import subprocess
import re
from flask import jsonify

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

