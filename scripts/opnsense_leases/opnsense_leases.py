#!/usr/bin/env python3
import paramiko
from datetime import datetime
import argparse
import sys
from pathlib import Path
import time
import logging

logger = None


def setup_logging(debug=False):
    """Configure logging based on debug flag."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


def parse_timestamp(date_str):
    """Convert OPNsense timestamp to Unix epoch time."""
    try:
        # Format from OPNsense: "1 2025/02/17 20:08:29"
        # Remove the leading number and convert
        clean_date = ' '.join(date_str.split()[1:])
        dt = datetime.strptime(clean_date, '%Y/%m/%d %H:%M:%S')
        return int(dt.timestamp())
    except Exception as e:
        logger.error(f"Failed to parse timestamp: {date_str} ({e})")
        return None


def get_lease_file(hostname, username, password=None, key_filename=None, port=22, debug=False):
    """Retrieve the lease file content from OPNsense via SSH."""
    logger = logging.getLogger(__name__)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        logger.debug(f"Attempting to connect to {hostname}:{port} as {username}")

        ssh.connect(
            hostname,
            port=port,
            username=username,
            password=password,
            key_filename=key_filename
        )

        # Get an interactive shell session
        logger.debug("Opening interactive SSH channel")
        channel = ssh.invoke_shell()
        time.sleep(2)  # Wait for the menu to load

        if debug:
            # Read and log the initial menu
            while channel.recv_ready():
                initial_output = channel.recv(4096).decode('utf-8')
                logger.debug(f"Initial menu output:\n{initial_output}")

        # Send '8' to access the shell
        logger.debug("Sending option 8 to access shell")
        channel.send('8\n')
        time.sleep(2)  # Wait for shell access

        # Send the command to read the lease file
        command = 'cat /var/dhcpd/var/db/dhcpd.leases\n'
        logger.debug(f"Sending command: {command}")
        channel.send(command)
        time.sleep(2)  # Wait for command execution

        # Receive the output
        output = ""
        while channel.recv_ready():
            chunk = channel.recv(4096).decode('utf-8')
            output += chunk
            if debug:
                logger.debug(f"Received chunk:\n{chunk}")

        # Clean up the output by removing the command echo and shell prompts
        lines = output.split('\n')
        # Remove first line (command echo) and any lines containing shell prompts
        # cleaned_lines = [line for line in lines
        #     if not line.strip().startswith(command.strip()) and not line.strip().endswith('> ') and not line.strip().endswith('# ')]
        cmd = command.strip()

        cleaned_lines = []
        for line in lines:
            stripped = line.strip()

            if stripped.startswith(cmd):
                continue
            if stripped.endswith('> '):
                continue
            if stripped.endswith('# '):
                continue

            cleaned_lines.append(line)

        cleaned_output = '\n'.join(cleaned_lines)

        logger.debug(f"Final cleaned output length: {len(cleaned_output)} characters")

        # Exit the shell properly
        channel.send('exit\n')
        ssh.close()

        return cleaned_output

    except Exception as e:
        logger.error(f"Error during SSH operation: {str(e)}")
        raise


def parse_lease_file(lease_content):
    """Parse the DHCP lease file content and return a list of valid leases."""
    logger = logging.getLogger(__name__)
    leases = []
    current_lease = None

    for line in lease_content.split('\n'):
        line = line.strip()

        if not line or line.startswith('root@') or line.startswith('#'):
            continue

        logger.debug(f"Processing line: {line}")

        # Start of a lease block
        if line.startswith('lease'):
            if current_lease:
                leases.append(current_lease)
                logger.debug(f"Added lease: {current_lease}")
            current_lease = {}
            ip = line.split()[1]
            current_lease['ip'] = ip

        # MAC address
        elif 'hardware ethernet' in line:
            mac = line.split()[2].rstrip(';')
            current_lease['mac'] = mac

        # Hostname
        elif 'client-hostname' in line:
            hostname = line.split('"')[1] if '"' in line else line.split()[1].rstrip(';')
            current_lease['hostname'] = hostname

        # Lease state
        elif line.startswith('binding state '):
            state = line.split('binding state')[1].strip().rstrip(';')
            current_lease['state'] = state

        # End time
        elif line.startswith('ends'):
            date_str = ' '.join(line.split()[1:]).rstrip(';')
            current_lease['ends'] = date_str

        # Client ID
        elif line.startswith('uid'):
            uid = line.split('"')[1] if '"' in line else line.split()[1].rstrip(';')
            current_lease['uid'] = uid

        # End of lease block
        elif line.strip() == '}':
            if current_lease:
                leases.append(current_lease)
                logger.debug(f"Added lease at block end: {current_lease}")
            current_lease = None

    # Add the last lease if exists
    if current_lease:
        leases.append(current_lease)
        logger.debug(f"Added final lease: {current_lease}")

    # Filter only active leases
    active_leases = [lease for lease in leases
                     if lease.get('state') == 'active' and 'mac' in lease and 'ip' in lease]

    logger.debug(f"Found {len(active_leases)} active leases out of {len(leases)} total leases")
    logger.debug("Active leases:")
    for lease in active_leases:
        logger.debug(f"  {lease}")

    return active_leases


def convert_to_dnsmasq(leases):
    """Convert leases to dnsmasq lease file format."""
    logger = logging.getLogger(__name__)
    dnsmasq_lines = []

    for lease in leases:
        logger.debug(f"Converting lease: {lease}")
        if 'mac' in lease and 'ip' in lease:
            # Get expiry time as Unix timestamp
            expiry = lease.get('ends', '')
            if expiry:
                expiry_epoch = parse_timestamp(expiry)
                if not expiry_epoch:
                    logger.error(f"Skipping lease due to invalid timestamp: {lease}")
                    continue
            else:
                logger.error(f"Skipping lease due to missing expiry time: {lease}")
                continue

            # Get required fields
            mac = lease['mac']
            ip = lease['ip']
            hostname = lease.get('hostname', '*')

            # Format client ID - if not available, use MAC address with '01:' prefix
            client_id = lease.get('uid', f"01:{mac}")
            # Clean up client ID - remove escape sequences and quotes
            client_id = client_id.replace('\\', '').replace('"', '')
            if not client_id.startswith('01:'):
                client_id = f"01:{mac}"

            # Format: [epoch timestamp] [MAC address] [IP address] [hostname] [client ID]
            line = f"{expiry_epoch} {mac} {ip} {hostname} {client_id}"
            dnsmasq_lines.append(line)
            logger.debug(f"Added dnsmasq lease line: {line}")

    return dnsmasq_lines


def main():
    parser = argparse.ArgumentParser(description='Convert OPNsense DHCP leases to dnsmasq format')
    parser.add_argument('--host', required=True, help='OPNsense hostname or IP')
    parser.add_argument('--username', required=True, help='SSH username')
    parser.add_argument('--password', help='SSH password (if not using key-based auth)')
    parser.add_argument('--key-file', help='SSH private key file path')
    parser.add_argument('--port', type=int, default=22, help='SSH port (default: 22)')
    parser.add_argument('--output', required=True, help='Output file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    # Setup logging
    global logger
    logger = setup_logging(args.debug)

    try:
        # Get lease file content
        logger.info("Retrieving lease file from OPNsense")
        lease_content = get_lease_file(
            args.host,
            args.username,
            password=args.password,
            key_filename=args.key_file,
            port=args.port,
            debug=args.debug
        )

        # Parse leases
        logger.info("Parsing lease file content")
        leases = parse_lease_file(lease_content)

        # Convert to dnsmasq format
        logger.info("Converting to dnsmasq format")
        dnsmasq_lines = convert_to_dnsmasq(leases)

        # Write output file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Writing output to {args.output}")
        with open(output_path, 'w') as f:
            f.write('\n'.join(dnsmasq_lines) + '\n')

        logger.info(f"Successfully wrote {len(dnsmasq_lines)} entries to {args.output}")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
