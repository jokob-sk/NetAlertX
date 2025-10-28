# NetAlertX Security: A Layered Defense

Your network security monitor has the "keys to the kingdom," making it a prime target for attackers. If it gets compromised, the game is over.

NetAlertX is engineered from the ground up to prevent this. It's not just an app; it's a purpose-built **security appliance.** Its core design is built on a **zero-trust** philosophy, which is a modern way of saying we **assume a breach will happen** and plan for it. This isn't a single "lock on the door"; it's a **"defense-in-depth"** strategy, more like a medieval castle with a moat, high walls, and guards at every door.

Here’s a breakdown of the defensive layers you get, right out of the box using the default configuration.

### Feature 1: The "Digital Concrete" Filesystem

**Methodology:** The core application and its system files are treated as immutable. Once built, the app's code is "set in concrete," preventing attackers from modifying it or planting malware.

* **Immutable Filesystem:** At runtime, the container's entire filesystem is set to `read_only: true`. The application code, system libraries, and all other files are literally frozen. This single control neutralizes a massive range of common attacks.

* **"Ownership-as-a-Lock" Pattern:** During the build, all system files are assigned to a special `readonly` user. This user has no login shell and no power to write to *any* files, even its own. It’s a clever, defense-in-depth locking mechanism.

* **Data Segregation:** All user-specific data (like configurations and the device database) is stored completely outside the container in Docker volumes. The application is disposable; the data is persistent.

**What's this mean to you:** Even if an attacker gets in, they **cannot modify the application code or plant malware.** It's like the app is set in digital concrete.

### Feature 2: Surgical, "Keycard-Only" Access

**Methodology:** The principle of least privilege is strictly enforced. Every process gets only the absolute minimum set of permissions needed for its specific job.

* **Non-Privileged Execution:** The entire NetAlertX stack runs as a dedicated, low-power, non-root user (`netalertx`). No "god mode" privileges are available to the application.

* **Kernel-Level Capability Revocation:** The container is launched with `cap_drop: - ALL`, which tells the Linux kernel to revoke *all* "root-like" special powers.

* **Binary-Specific Privileges (setcap):** This is the "keycard" metaphor in action. After revoking all powers, the system uses `setcap` to grant specific, necessary permissions *only* to the binaries that absolutely require them (like `nmap` and `arp-scan`). This means that even if an attacker compromises the web server, they can't start scanning the network. The web server's "keycard" doesn't open the "scanning" door.

**What's this mean to you:** A security breach is **firewalled.** An attacker who gets into the web UI **does not have the "keycard"** to start scanning your network or take over the system. The breach is contained.

### Feature 3: Attack Surface "Amputation"

**Methodology:** The potential attack surface is aggressively minimized by removing every non-essential tool an attacker would want to use.

* **Package Manager Removal:** The `hardened` build stage explicitly deletes the Alpine package manager (`apk del apk-tools`). This makes it impossible for an attacker to simply `apk add` their malicious toolkit.

* **`sudo` Neutralization:** All `sudo` configurations are removed, and the `/usr/bin/sudo` command is replaced with a non-functional shim. Any attempt to escalate privileges this way will fail.

* **Build Toolchain Elimination:** The `Dockerfile` uses a multi-stage build. The initial "builder" stage, which contains all the powerful compilers (`gcc`) and development tools, is completely discarded. The final production image is lean and contains no build tools.

* **Minimal User & Group Files:** The `hardened` stage scrubs the system's `passwd` and `group` files, removing all default system users to minimize potential avenues for privilege escalation.

**What's this mean to you:** An attacker who breaks in finds themselves in an **empty room with no tools.** They have no `sudo` to get more power, no package manager to download weapons, and no compilers to build new ones.

### Feature 4: "Self-Cleaning" Writable Areas

**Methodology:** All writable locations are treated as untrusted, temporary, and non-executable by default.

* **In-Memory Volatile Storage:** The `docker-compose.yml` configuration maps all temporary directories (e.g., `/app/log`, `/app/api`, `/tmp`) to in-memory `tmpfs` filesystems. They do not exist on the host's disk.

* **Volatile Data:** Because these locations exist only in RAM, their contents are **instantly and irrevocably erased** when the container is stopped. This provides a "self-cleaning" mechanism that purges any attacker-dropped files or payloads on every single restart.

* **Secure Mount Flags:** These in-memory mounts are configured with the `noexec` flag. This is a critical security control: it **prohibits the execution of any binary or script** from a location that is writable.

**What's this mean to you:** Any malicious file an attacker *does* manage to drop is **written in invisible, non-permanent ink.** The file is written to RAM, not disk, so it **vaporizes the instant you restart** the container. Even worse for them, the `noexec` flag means they **can't even run the file** in the first place.

### Feature 5: Built-in Resource Guardrails

**Methodology:** The container is constrained by resource limits to function as a "good citizen" on the host system. This prevents a compromised or runaway process from consuming excessive resources, a common vector for Denial of Service (DoS) attacks.

* **Process Limiting:** The `docker-compose.yml` defines a `pids_limit: 512`. This directly mitigates "fork bomb" attacks, where a process attempts to crash the host by recursively spawning thousands of new processes.

* **Memory & CPU Limits:** The configuration file defines strict resource limits to prevent any single process from exhausting the host's available system resources.

**What's this mean to you:** NetAlertX is a "good neighbor" and **can't be used to crash your host machine.** Even if a process is compromised, it's in a digital straitjacket and **cannot** pull a "denial of service" attack by hogging all your CPU or memory.

### Feature 6: The "Pre-Flight" Self-Check

**Methodology:** Before any services start, NetAlertX runs a comprehensive "pre-flight" check to ensure its own security and configuration are sound. It's like a built-in auditor that verifies its own defenses.

* **Active Self-Diagnosis:** On every single boot, NetAlertX runs a series of startup pre-checks—and it's fast. The entire self-check process typically completes in less than a second, letting you get to the web UI in about three seconds from startup.

* **Validates Its Own Security:** These checks actively inspect the other security features. For example, `check-0-permissions.sh` validates that all the "Digital Concrete" files are locked down and all the "Self-Cleaning" areas are writable, just as they should be. It also checks that the correct `netalertx` user is running the show, not `root`.

* **Catches Misconfigurations:** This system acts as a "safety inspector" that catches misconfigurations *before* they can become security holes. If you've made a mistake in your configuration (like a bad folder permission or incorrect network mode), NetAlertX will tell you in the logs *why* it can't start, rather than just failing silently.

**What's this mean to you:** The system is **self-aware and checks its own work.** You get instant feedback if a setting is wrong, and you get peace of mind on every single boot knowing all these security layers are **active and verified,** all in about one second.

### Conclusion: Security by Default

No single security control is a silver bullet. The robust security posture of NetAlertX is achieved through **defense in depth**, layering these methodologies.

An adversary must not only gain initial access but must also find a way to write a payload to a non-executable, in-memory location, without access to any standard system tools, `sudo`, or a package manager. And they must do this while operating as an unprivileged user in a resource-limited environment where the application code is immutable and *actively checks its own integrity on every boot*.