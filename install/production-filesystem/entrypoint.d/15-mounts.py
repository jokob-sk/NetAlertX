#!/usr/bin/env python3

"""
Mount Diagnostic Tool

Analyzes container mount points for permission issues, persistence risks, and performance problems.

TODO: Future Enhancements (Roadmap Step 3 & 4)
1. Text-based Output: Replace emoji status indicators (✅, ❌) with plain text (e.g., [OK], [FAIL])
   to ensure compatibility with all terminal types and logging systems.
2. OverlayFS/Copy-up Support: Improve detection logic for filesystems like Synology's OverlayFS
   where files may appear writable but fail on specific operations (locking, mmap).
3. Root-to-User Context: Ensure this tool remains accurate when the container starts as root
   to fix permissions and then drops privileges to the 'netalertx' user. The check should
   reflect the *effective* permissions of the application user.
"""

import os
import sys
from dataclasses import dataclass

# if NETALERTX_DEBUG is 1 then exit
if os.environ.get("NETALERTX_DEBUG") == "1":
    sys.exit(0)


@dataclass
class MountCheckResult:
    """Object to track mount status and potential issues."""

    var_name: str
    path: str = ""
    is_writeable: bool = False
    is_readable: bool = False
    is_mounted: bool = False
    is_mount_point: bool = False
    is_ramdisk: bool = False
    underlying_fs_is_ramdisk: bool = False  # Track this separately
    fstype: str = "N/A"
    error: bool = False
    write_error: bool = False
    read_error: bool = False
    performance_issue: bool = False
    dataloss_risk: bool = False
    category: str = ""
    role: str = ""
    group: str = ""


@dataclass(frozen=True)
class PathSpec:
    """Describes how a filesystem path should behave."""

    var_name: str
    category: str  # e.g. persist, ramdisk
    role: str  # primary, sub, secondary
    group: str  # logical grouping for primary/sub relationships


PATH_SPECS = (
    PathSpec("NETALERTX_DATA", "persist", "primary", "data"),
    PathSpec("NETALERTX_DB", "persist", "sub", "data"),
    PathSpec("NETALERTX_CONFIG", "persist", "sub", "data"),
    PathSpec("SYSTEM_SERVICES_RUN_TMP", "ramdisk", "primary", "tmp"),
    PathSpec("NETALERTX_API", "ramdisk", "sub", "tmp"),
    PathSpec("NETALERTX_LOG", "ramdisk", "sub", "tmp"),
    PathSpec("SYSTEM_SERVICES_RUN", "ramdisk", "sub", "tmp"),
    PathSpec("SYSTEM_SERVICES_ACTIVE_CONFIG", "ramdisk", "secondary", "tmp"),
)


def get_mount_info():
    """Parses /proc/mounts to get a dict of {mount_point: fstype}."""
    mounts = {}
    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    mount_point = parts[1].replace("\\040", " ")
                    fstype = parts[2]
                    mounts[mount_point] = fstype
    except FileNotFoundError:
        print("Error: /proc/mounts not found. Not a Linux system?", file=sys.stderr)
        return None
    return mounts


def _resolve_writeable_state(target_path: str) -> bool:
    """Determine if a path is writeable, ascending to the first existing parent."""

    current = target_path
    seen: set[str] = set()
    while True:
        if current in seen:
            break
        seen.add(current)

        if os.path.exists(current):
            if not os.access(current, os.W_OK):
                return False

            # OverlayFS/Copy-up check: Try to actually write a file to verify
            if os.path.isdir(current):
                test_file = os.path.join(current, f".netalertx_write_test_{os.getpid()}")
                try:
                    with open(test_file, "w") as f:
                        f.write("test")
                    os.remove(test_file)
                    return True
                except OSError:
                    return False

            return True

        parent_dir = os.path.dirname(current)
        if not parent_dir or parent_dir == current:
            break
        current = parent_dir

    return False


def _resolve_readable_state(target_path: str) -> bool:
    """Determine if a path is readable, ascending to the first existing parent."""

    current = target_path
    seen: set[str] = set()
    while True:
        if current in seen:
            break
        seen.add(current)

        if os.path.exists(current):
            return os.access(current, os.R_OK)

        parent_dir = os.path.dirname(current)
        if not parent_dir or parent_dir == current:
            break
        current = parent_dir

    return False


def analyze_path(
    spec: PathSpec,
    mounted_filesystems,
    non_persistent_fstypes,
):
    """
    Analyzes a single path, checking for errors, performance, and dataloss.
    """
    result = MountCheckResult(
        var_name=spec.var_name,
        category=spec.category,
        role=spec.role,
        group=spec.group,
    )
    target_path = os.environ.get(spec.var_name)

    if target_path is None:
        result.path = f"({spec.var_name} unset)"
        result.error = True
        return result

    result.path = target_path

    # --- 1. Check Read/Write Permissions ---
    result.is_writeable = _resolve_writeable_state(target_path)
    result.is_readable = _resolve_readable_state(target_path)

    if not result.is_writeable:
        result.error = True
        if spec.role != "secondary":
            result.write_error = True

    if not result.is_readable:
        result.error = True
        if spec.role != "secondary":
            result.read_error = True

    # --- 2. Check Filesystem Type (Parent and Self) ---
    parent_mount_fstype = ""
    longest_mount = ""

    for mount_point, fstype in mounted_filesystems.items():
        normalized = mount_point.rstrip("/") if mount_point != "/" else "/"
        if target_path == normalized or target_path.startswith(f"{normalized}/"):
            if len(normalized) > len(longest_mount):
                longest_mount = normalized
                parent_mount_fstype = fstype

    result.underlying_fs_is_ramdisk = parent_mount_fstype in non_persistent_fstypes

    if parent_mount_fstype:
        result.fstype = parent_mount_fstype

    # --- 3. Check if path IS a mount point ---
    if target_path in mounted_filesystems:
        result.is_mounted = True
        result.is_mount_point = True
        result.fstype = mounted_filesystems[target_path]
        result.is_ramdisk = result.fstype in non_persistent_fstypes
    else:
        result.is_mounted = False
        result.is_ramdisk = False
        if longest_mount and longest_mount != "/":
            if target_path == longest_mount or target_path.startswith(
                f"{longest_mount}/"
            ):
                result.is_mounted = True
                result.fstype = parent_mount_fstype
                result.is_ramdisk = parent_mount_fstype in non_persistent_fstypes

    # --- 4. Apply Risk Logic ---
    # Keep risk flags about persistence/performance properties of the mount itself.
    # Read/write permission problems are surfaced via the R/W columns and error flags.
    if spec.category == "persist":
        if result.underlying_fs_is_ramdisk or result.is_ramdisk:
            result.dataloss_risk = True

        if not result.is_mounted:
            result.dataloss_risk = True

    elif spec.category == "ramdisk":
        if not result.is_mounted or not result.is_ramdisk:
            result.performance_issue = True

    return result


def print_warning_message(results: list[MountCheckResult]):
    """Prints a formatted warning to stderr."""
    YELLOW = "\033[1;33m"
    RESET = "\033[0m"

    print(f"{YELLOW}══════════════════════════════════════════════════════════════════════════════", file=sys.stderr)
    print("⚠️  ATTENTION: Configuration issues detected (marked with ❌).\n", file=sys.stderr)

    for r in results:
        issues = []
        if not r.is_writeable:
            issues.append("error writing")
        if not r.is_readable:
            issues.append("error reading")
        if not r.is_mounted and (r.category == "persist" or r.category == "ramdisk"):
            issues.append("not mounted")
        if r.dataloss_risk:
            issues.append("risk of dataloss")
        if r.performance_issue:
            issues.append("performance issue")

        if issues:
            print(f"    * {r.path} {', '.join(issues)}", file=sys.stderr)

    message = (
        "\n    We recommend starting with the default docker-compose.yml as the\n"
        "    configuration can be quite complex.\n\n"
        "    Review the documentation for a correct setup:\n"
        "    https://docs.netalertx.com/DOCKER_COMPOSE\n"
        "    https://docs.netalertx.com/docker-troubleshooting/mount-configuration-issues\n"
        "══════════════════════════════════════════════════════════════════════════════\n"
    )

    print(f"{message}{RESET}", file=sys.stderr)


def _get_active_specs() -> list[PathSpec]:
    """Return the path specifications that should be evaluated for this run."""

    return list(PATH_SPECS)


def _sub_result_is_healthy(result: MountCheckResult) -> bool:
    """Determine if a sub-path result satisfies its expected constraints."""

    if result.category == "persist":
        if not result.is_mounted:
            return False
        if result.dataloss_risk or result.write_error or result.read_error or result.error:
            return False
        return True

    if result.category == "ramdisk":
        if not result.is_mounted or not result.is_ramdisk:
            return False
        if result.performance_issue or result.write_error or result.read_error or result.error:
            return False
        return True

    return False


def _apply_primary_rules(specs: list[PathSpec], results_map: dict[str, MountCheckResult]) -> list[MountCheckResult]:
    """Suppress or flag primary rows based on the state of their sub-paths."""

    final_results: list[MountCheckResult] = []
    specs_by_group: dict[str, list[PathSpec]] = {}
    for spec in specs:
        specs_by_group.setdefault(spec.group, []).append(spec)

    for spec in specs:
        result = results_map.get(spec.var_name)
        if result is None:
            continue

        if spec.role == "primary":
            group_specs = specs_by_group.get(spec.group, [])
            sub_results_all = [
                results_map[s.var_name]
                for s in group_specs
                if s.var_name in results_map and s.var_name != spec.var_name
            ]
            core_sub_results = [
                results_map[s.var_name]
                for s in group_specs
                if s.var_name in results_map and s.role == "sub"
            ]

            sub_mount_points = [sub for sub in sub_results_all if sub.is_mount_point]
            core_mount_points = [sub for sub in core_sub_results if sub.is_mount_point]
            all_core_subs_healthy = bool(core_sub_results) and all(
                _sub_result_is_healthy(sub) for sub in core_sub_results
            )
            all_core_subs_are_mounts = bool(core_sub_results) and len(core_mount_points) == len(core_sub_results)

            suppress_primary = False
            if all_core_subs_healthy and all_core_subs_are_mounts:
                suppress_primary = True

            if suppress_primary:
                # All sub-paths are healthy and mounted; suppress the aggregate row.
                continue

            if sub_mount_points and result.is_mount_point:
                result.error = True
                if result.category == "persist":
                    result.dataloss_risk = True
                elif result.category == "ramdisk":
                    result.performance_issue = True

        final_results.append(result)

    return final_results


def main():
    NON_PERSISTENT_FSTYPES = {"tmpfs", "ramfs"}

    active_specs = _get_active_specs()

    mounted_filesystems = get_mount_info()
    if mounted_filesystems is None:
        sys.exit(1)

    results_map: dict[str, MountCheckResult] = {}
    for spec in active_specs:
        results_map[spec.var_name] = analyze_path(
            spec,
            mounted_filesystems,
            NON_PERSISTENT_FSTYPES,
        )

    results = _apply_primary_rules(active_specs, results_map)

    has_issues = any(
        r.dataloss_risk or r.error or r.write_error or r.read_error or r.performance_issue
        for r in results
    )
    has_rw_errors = any(
        (r.write_error or r.read_error) and r.category == "persist"
        for r in results
    )
    has_primary_dataloss = any(
        r.category == "persist" and r.role == "primary" and r.dataloss_risk and r.is_mount_point
        for r in results
    )

    # --- Print Table ---
    headers = ["Path", "R", "W", "Mount", "RAMDisk", "Performance", "DataLoss"]

    CHECK_SYMBOL = "✅"
    CROSS_SYMBOL = "❌"
    BLANK_SYMBOL = "➖"

    def bool_to_check(is_good):
        return CHECK_SYMBOL if is_good else CROSS_SYMBOL

    col_widths = [len(h) for h in headers]
    for r in results:
        col_widths[0] = max(col_widths[0], len(str(r.path)))

    header_fmt = (
        f" {{:<{col_widths[0]}}} |"
        f" {{:^{col_widths[1]}}} |"
        f" {{:^{col_widths[2]}}} |"
        f" {{:^{col_widths[3]}}} |"
        f" {{:^{col_widths[4]}}} |"
        f" {{:^{col_widths[5]}}} |"
        f" {{:^{col_widths[6]}}} "
    )

    row_fmt = (
        f" {{:<{col_widths[0]}}} |"
        f" {{:^{col_widths[1]}}}|"  # No space - intentional
        f" {{:^{col_widths[2]}}}|"  # No space - intentional
        f" {{:^{col_widths[3]}}}|"  # No space - intentional
        f" {{:^{col_widths[4]}}}|"  # No space - intentional
        f" {{:^{col_widths[5]}}}|"  # No space - intentional
        f" {{:^{col_widths[6]}}} "  # DataLoss is last, needs space
    )

    separator = "".join([
        "-" * (col_widths[0] + 2),
        "+",
        "-" * (col_widths[1] + 2),
        "+",
        "-" * (col_widths[2] + 2),
        "+",
        "-" * (col_widths[3] + 2),
        "+",
        "-" * (col_widths[4] + 2),
        "+",
        "-" * (col_widths[5] + 2),
        "+",
        "-" * (col_widths[6] + 2)
    ])

    print(header_fmt.format(*headers), file=sys.stderr)
    print(separator, file=sys.stderr)
    for r in results:
        # Symbol Logic
        read_symbol = bool_to_check(r.is_readable)
        write_symbol = bool_to_check(r.is_writeable)

        mount_symbol = CHECK_SYMBOL if r.is_mounted else CROSS_SYMBOL

        if r.category == "persist":
            if r.underlying_fs_is_ramdisk or r.is_ramdisk:
                ramdisk_symbol = CROSS_SYMBOL
            else:
                ramdisk_symbol = BLANK_SYMBOL
            perf_symbol = BLANK_SYMBOL
        elif r.category == "ramdisk":
            ramdisk_symbol = CHECK_SYMBOL if r.is_ramdisk else CROSS_SYMBOL
            perf_symbol = bool_to_check(not r.performance_issue)
        else:
            ramdisk_symbol = BLANK_SYMBOL
            perf_symbol = bool_to_check(not r.performance_issue)

        dataloss_symbol = bool_to_check(not r.dataloss_risk)

        print(
            row_fmt.format(
                r.path,
                read_symbol,
                write_symbol,
                mount_symbol,
                ramdisk_symbol,
                perf_symbol,
                dataloss_symbol,
            ),
            file=sys.stderr
        )

    # --- Print Warning ---
    if has_issues:
        print("\n", file=sys.stderr)
        print_warning_message(results)

    # Exit with error only if there are read/write permission issues
    if (has_rw_errors or has_primary_dataloss) and os.environ.get("NETALERTX_DEBUG") != "1":
        sys.exit(1)


if __name__ == "__main__":
    main()
