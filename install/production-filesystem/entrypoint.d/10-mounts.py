#!/usr/bin/env python3

import os
import sys
from dataclasses import dataclass

@dataclass
class MountCheckResult:
    """Object to track mount status and potential issues."""
    var_name: str
    path: str = ""
    is_writeable: bool = False
    is_mounted: bool = False
    is_ramdisk: bool = False
    underlying_fs_is_ramdisk: bool = False # Track this separately
    fstype: str = "N/A"
    error: bool = False
    write_error: bool = False
    performance_issue: bool = False
    dataloss_risk: bool = False

def get_mount_info():
    """Parses /proc/mounts to get a dict of {mount_point: fstype}."""
    mounts = {}
    try:
        with open('/proc/mounts', 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    mount_point = parts[1].replace('\\040', ' ')
                    fstype = parts[2]
                    mounts[mount_point] = fstype
    except FileNotFoundError:
        print("Error: /proc/mounts not found. Not a Linux system?", file=sys.stderr)
        return None
    return mounts

def analyze_path(var_name, is_persistent, mounted_filesystems, non_persistent_fstypes, read_only_vars):
    """
    Analyzes a single path, checking for errors, performance, and dataloss.
    """
    result = MountCheckResult(var_name=var_name)
    target_path = os.environ.get(var_name)

    if target_path is None:
        result.path = f"({var_name} unset)"
        result.error = True
        return result
    
    result.path = target_path

    # --- 1. Check Write Permissions ---
    is_writeable = os.access(target_path, os.W_OK)
    
    if not is_writeable and not os.path.exists(target_path):
        parent_dir = os.path.dirname(target_path)
        if os.access(parent_dir, os.W_OK):
            is_writeable = True
            
    result.is_writeable = is_writeable
    
    if var_name not in read_only_vars and not result.is_writeable:
        result.error = True
        result.write_error = True

    # --- 2. Check Filesystem Type (Parent and Self) ---
    parent_mount_fstype = ""
    longest_mount = ""

    for mount_point, fstype in mounted_filesystems.items():
        if target_path.startswith(mount_point):
            if len(mount_point) > len(longest_mount):
                longest_mount = mount_point
                parent_mount_fstype = fstype
    
    result.underlying_fs_is_ramdisk = parent_mount_fstype in non_persistent_fstypes
    
    if parent_mount_fstype:
        result.fstype = parent_mount_fstype

    # --- 3. Check if path IS a mount point ---
    if target_path in mounted_filesystems:
        result.is_mounted = True
        result.fstype = mounted_filesystems[target_path]
        result.is_ramdisk = result.fstype in non_persistent_fstypes
    else:
        result.is_mounted = False
        result.is_ramdisk = False

    # --- 4. Apply Risk Logic ---
    if is_persistent:
        if result.underlying_fs_is_ramdisk:
            result.dataloss_risk = True
        
        if not result.is_mounted:
            result.dataloss_risk = True
            
    else:
        # Performance issue if it's not a ramdisk mount
        if not result.is_mounted or not result.is_ramdisk:
            result.performance_issue = True
            
    return result

def print_warning_message():
    """Prints a formatted warning to stderr."""
    YELLOW = '\033[1;33m'
    RESET = '\033[0m'
    
    message = (
        "══════════════════════════════════════════════════════════════════════════════\n"
        "⚠️  ATTENTION: Configuration issues detected (marked with ❌).\n\n"
        "    Your configuration has write permission, dataloss, or performance issues\n"
        "    as shown in the table above.\n\n"
        "    We recommend starting with the default docker-compose.yml as the\n"
        "    configuration can be quite complex.\n\n"
        "    Review the documentation for a correct setup:\n"
        "    https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md\n"
        "══════════════════════════════════════════════════════════════════════════════\n"
    )
    
    print(f"{YELLOW}{message}{RESET}", file=sys.stderr)

def main():
    NON_PERSISTENT_FSTYPES = {'tmpfs', 'ramfs'}
    PERSISTENT_VARS = {'NETALERTX_DB', 'NETALERTX_CONFIG'}
    # Define all possible read-only vars
    READ_ONLY_VARS = {'SYSTEM_NGINX_CONFIG', 'SYSTEM_SERVICES_ACTIVE_CONFIG'}
    
    # Base paths to check
    PATHS_TO_CHECK = {
        'NETALERTX_DB': True,
        'NETALERTX_CONFIG': True,
        'NETALERTX_API': False,
        'NETALERTX_LOG': False,
        'SYSTEM_SERVICES_RUN': False,
    }

    # *** KEY CHANGE: Conditionally add path based on PORT ***
    port_val = os.environ.get("PORT")
    if port_val is not None and port_val != "20211":
        PATHS_TO_CHECK['SYSTEM_SERVICES_ACTIVE_CONFIG'] = False
    # *** END KEY CHANGE ***

    mounted_filesystems = get_mount_info()
    if mounted_filesystems is None:
        sys.exit(1)

    results = []
    has_issues = False
    for var_name, is_persistent in PATHS_TO_CHECK.items():
        result = analyze_path(
            var_name, is_persistent, 
            mounted_filesystems, NON_PERSISTENT_FSTYPES, READ_ONLY_VARS
        )
        if result.performance_issue or result.dataloss_risk or result.error:
            has_issues = True
        results.append(result)

    if has_issues:
        # --- Print Table ---
        headers = ["Path", "Writeable", "Mount", "RAMDisk", "Performance", "DataLoss"]
        
        CHECK_SYMBOL = "✅"
        CROSS_SYMBOL = "❌"
        BLANK_SYMBOL = "➖" 
        
        bool_to_check = lambda is_good: CHECK_SYMBOL if is_good else CROSS_SYMBOL

        col_widths = [len(h) for h in headers]
        for r in results:
             col_widths[0] = max(col_widths[0], len(str(r.path)))

        header_fmt = (
            f" {{:<{col_widths[0]}}} |"
            f" {{:^{col_widths[1]}}} |"
            f" {{:^{col_widths[2]}}} |"
            f" {{:^{col_widths[3]}}} |"
            f" {{:^{col_widths[4]}}} |"
            f" {{:^{col_widths[5]}}} "
        )
        
        row_fmt = (
            f" {{:<{col_widths[0]}}} |"
            f" {{:^{col_widths[1]}}}|"  # No space
            f" {{:^{col_widths[2]}}}|"  # No space
            f" {{:^{col_widths[3]}}}|"  # No space
            f" {{:^{col_widths[4]}}}|"  # No space
            f" {{:^{col_widths[5]}}} "  # DataLoss is last, needs space
        )
        
        separator = (
            "-" * (col_widths[0] + 2) + "+" +
            "-" * (col_widths[1] + 2) + "+" +
            "-" * (col_widths[2] + 2) + "+" +
            "-" * (col_widths[3] + 2) + "+" +
            "-" * (col_widths[4] + 2) + "+" +
            "-" * (col_widths[5] + 2)
        )

        print(header_fmt.format(*headers))
        print(separator)
        for r in results:
            is_persistent = r.var_name in PERSISTENT_VARS
            
            # --- Symbol Logic ---
            write_symbol = bool_to_check(r.is_writeable)
            # Special case for read-only vars
            if r.var_name in READ_ONLY_VARS:
                write_symbol = CHECK_SYMBOL
                
            mount_symbol = CHECK_SYMBOL if r.is_mounted else CROSS_SYMBOL
            
            ramdisk_symbol = ""
            if is_persistent:
                ramdisk_symbol = CROSS_SYMBOL if r.underlying_fs_is_ramdisk else BLANK_SYMBOL
            else:
                ramdisk_symbol = CHECK_SYMBOL if r.is_ramdisk else CROSS_SYMBOL

            if is_persistent:
                perf_symbol = BLANK_SYMBOL
            else:
                perf_symbol = bool_to_check(not r.performance_issue)
            
            dataloss_symbol = bool_to_check(not r.dataloss_risk)
            
            print(row_fmt.format(
                r.path,
                write_symbol,
                mount_symbol,
                ramdisk_symbol,
                perf_symbol,
                dataloss_symbol
            ))

        # --- Print Warning ---
        print("\n", file=sys.stderr)
        print_warning_message()
        sys.exit(1)

if __name__ == "__main__":
    main()