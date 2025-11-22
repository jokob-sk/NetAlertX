# !/usr/bin/env python3

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
    is_mounted: bool = False
    is_mount_point: bool = False
    is_ramdisk: bool = False
    underlying_fs_is_ramdisk: bool = False  # Track this separately
    fstype: str = "N/A"
    error: bool = False
    write_error: bool = False
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
            return os.access(current, os.W_OK)

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

    # --- 1. Check Write Permissions ---
    result.is_writeable = _resolve_writeable_state(target_path)

    if not result.is_writeable:
        result.error = True
        if spec.role != "secondary":
            result.write_error = True

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
    if spec.category == "persist":
        if result.underlying_fs_is_ramdisk or result.is_ramdisk:
            result.dataloss_risk = True

        if not result.is_mounted:
            result.dataloss_risk = True

    elif spec.category == "ramdisk":
        if not result.is_mounted or not result.is_ramdisk:
            result.performance_issue = True

    return result


def print_warning_message():
    """Prints a formatted warning to stderr."""
    YELLOW = "\033[1;33m"
    RESET = "\033[0m"

    message = (
        "══════════════════════════════════════════════════════════════════════════════\n"
        "⚠️  ATTENTION: Configuration issues detected (marked with ❌).\n\n"
        "    Your configuration has write permission, dataloss, or performance issues\n"
        "    as shown in the table above.\n\n"
        "    We recommend starting with the default docker-compose.yml as the\n"
        "    configuration can be quite complex.\n\n"
        "    Review the documentation for a correct setup:\n"
        "    https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md\n"
        "    https://github.com/jokob-sk/NetAlertX/blob/main/docs/docker-troubleshooting/mount-configuration-issues.md\n"
        "══════════════════════════════════════════════════════════════════════════════\n"
    )

    print(f"{YELLOW}{message}{RESET}", file=sys.stderr)


def _get_active_specs() -> list[PathSpec]:
    """Return the path specifications that should be evaluated for this run."""

    return list(PATH_SPECS)


def _sub_result_is_healthy(result: MountCheckResult) -> bool:
    """Determine if a sub-path result satisfies its expected constraints."""

    if result.category == "persist":
        if not result.is_mounted:
            return False
        if result.dataloss_risk or result.write_error or result.error:
            return False
        return True

    if result.category == "ramdisk":
        if not result.is_mounted or not result.is_ramdisk:
            return False
        if result.performance_issue or result.write_error or result.error:
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

            if all_core_subs_healthy:
                if result.write_error:
                    result.write_error = False
                if not result.is_writeable:
                    result.is_writeable = True
                if spec.category == "persist" and result.dataloss_risk:
                    result.dataloss_risk = False
                if result.error and not (result.performance_issue or result.dataloss_risk or result.write_error):
                    result.error = False

            suppress_primary = False
            if all_core_subs_healthy and all_core_subs_are_mounts:
                if not result.is_mount_point and not result.error and not result.write_error:
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
        r.dataloss_risk or r.error or r.write_error or r.performance_issue
        for r in results
    )
    has_write_errors = any(r.write_error for r in results)

    if has_issues or True:  # Always print table for diagnostic purposes
        # --- Print Table ---
        headers = ["Path", "Writeable", "Mount", "RAMDisk", "Performance", "DataLoss"]

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
            "-" * (col_widths[5] + 2)
        ])

        print(header_fmt.format(*headers))
        print(separator)
        for r in results:
            # Symbol Logic
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
                    write_symbol,
                    mount_symbol,
                    ramdisk_symbol,
                    perf_symbol,
                    dataloss_symbol,
                )
            )

        # --- Print Warning ---
        if has_issues:
            print("\n", file=sys.stderr)
            print_warning_message()

        # Exit with error only if there are write permission issues
        if has_write_errors and os.environ.get("NETALERTX_DEBUG") != "1":
            sys.exit(1)


if __name__ == "__main__":
    main()
