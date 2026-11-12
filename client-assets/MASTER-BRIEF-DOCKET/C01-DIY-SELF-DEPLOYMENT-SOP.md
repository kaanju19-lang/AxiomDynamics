# C01 — DIY Self-Deployment SOP

**Docket position:** C01. The self-deployment manual for the Railroad's own IT team. **This document is why the operating model in D14 works.** Without it, "the Railroad installs it" is a fiction.

> **Drafting status:** Commercial grade. Instructions assume a Linux administrator with competency in package management, environment variables, systemd or equivalent, and basic Python troubleshooting. No rail-domain knowledge is required.

---

## Part A — Prerequisites

### A1. Platform requirements

| Component | Requirement | Notes |
|---|---|---|
| **Operating System** | Linux (Ubuntu 20.04 LTS or later, RHEL 8+, or equivalent) | Windows and macOS are not supported. |
| **Python** | Python 3.11.9 or 3.11.x patch version | Exact: `python3 --version` must report `Python 3.11.9` or a later 3.11.x patch release. Do not use Python 3.10 or earlier, or Python 3.12+. |
| **pip** | Current, matching the Python version | `pip3 --version` must report `pip` for `python3.11`. |
| **git** | Recommended for source retrieval | Not required if you obtain the release archive by other means. |
| **System packages** | `build-essential` (or equivalent), `python3-dev` (or equivalent) | Needed to compile numpy from source if a binary wheel is unavailable. `sudo apt-get install build-essential python3-dev` on Debian/Ubuntu. |
| **CPU** | Any modern x86_64, ARM64, or ARM (e.g., Raspberry Pi 3+) | The application is single-threaded and memory-efficient. |
| **RAM** | Minimum 512 MB; 2 GB recommended | Typical runtime footprint is <200 MB. |
| **Disk** | 100 MB for application and dependencies; 1–50 GB for the SQLite database depending on retention policy | Database growth rate depends on advisory volume and retention settings (see **D09 §5.1**). |
| **Network** | None required in normal operation; one-time outbound for initial deployment (see §A4) | After initial setup, the application is fully air-gapped. No outbound calls. |

### A2. Network and connectivity

**Initial deployment:**
- **If downloading:** the deployment machine needs **temporary outbound HTTPS access** to retrieve the application archive and dependencies from PyPI (specifically, `pypi.org`). If air-gap deployment is mandatory from the start, obtain the archive and dependencies on an internet-connected machine, transfer them via approved media (see Part C §C3), and proceed offline from §B3 onward.
- **If air-gapped from day one:** the installation machine and the target host must be able to exchange files via approved media (USB drive, secure transfer appliance, etc.). See Part C for the air-gap procedure.

**After installation:**
- **Zero outbound network.** The Platform does not and will not contact external networks, cloud services, phone-home URLs, or any external host. See B05 in the Master Brief Docket.
- **Firewall rules:** restrict outbound from the application host to deny all. The application will not attempt to bypass this.

### A3. Installation method: choose one

**Option A (Standard, recommended):** Clone or download the release from the AxiomDynamics repository, install dependencies from PyPI in one step, test, run.

**Option B (Air-gapped):** Obtain a sealed archive containing the application, dependencies pre-cached, and setup scripts. Transfer via approved media. Extract, verify integrity (see Part C §C3), install from local cache, test, run.

**Option C (Containerized):** Use the supplied Dockerfile to build a container image and deploy via Docker or Podman. Recommended if your infrastructure already uses containers and you have a private registry.

Proceed to the section matching your choice: **A4** for Standard, **B3** for Air-gapped, or **Part D** for Containerized.

### A4. Pre-installation checks (all methods)

On the target Linux host, as the user who will run the application (or as `root` if installing as a service):

```bash
# Check Python version
python3 --version    # Expected output: Python 3.11.x

# Check pip is available for Python 3.11
pip3 --version       # Expected output: pip X.Y.Z from ... (python 3.11)

# Ensure the work directory exists and is writable
mkdir -p /opt/axiom  # (or your chosen path)
cd /opt/axiom
pwd                  # Confirm you are in the directory

# (Optional but recommended) Create a Python virtual environment
python3 -m venv venv
source venv/bin/activate
# Prompt should change to show (venv) at the start

# Verify pip in the virtual environment (if created)
pip --version        # Should report the venv's pip
```

If any command fails (Python not found, version mismatch, permission denied), **stop here** and resolve the issue before proceeding.

---

## Part B — Standard Deployment (Option A)

### B1. Obtain the application

**Using git:**
```bash
cd /opt/axiom
git clone [AxiomDynamics distribution repository URL — supplied with the release package] .
cd AxiomDynamics
```

**Using download (no git):**
1. Visit [release artefact location, supplied with the Order and verified against the SHA-256 in the release notes].
2. Download the release zip to a temporary directory.
3. Unzip to `/opt/axiom`.
4. `cd /opt/axiom`.

### B2. Install dependencies

```bash
# If you created a virtual environment (recommended), activate it first
source venv/bin/activate

# Install from requirements.txt
pip install -r requirements.txt

# Verify the installation
python3 -c "import numpy; import axiom.backend.main; print('OK')"
# Expected output: OK (no errors)

# List installed packages to confirm
pip list | grep -i numpy
# Expected output: numpy    X.Y.Z
```

If `pip install` fails:
- Check internet connectivity.
- If numpy fails to compile, install build tools: `sudo apt-get install build-essential python3-dev`.
- Run `pip install --verbose -r requirements.txt` to see the detailed error.

### B3. Configure the environment

Create a `.env` file in the application directory or set environment variables:

```bash
# Create the .env file
cat > /opt/axiom/.env <<EOF
# Network
AXIOM_HOST=127.0.0.1           # Change to 0.0.0.0 only if behind a firewall
PORT=8420                        # Change if another process uses port 8420
AXIOM_PORT=8420                 # Alternative name; PORT takes precedence

# Database
AXIOM_DB_PATH=/opt/axiom/axiom.db  # Path where the SQLite database will be stored

# Optional: application logging (if supported)
# LOG_LEVEL=INFO
EOF

# Verify the file
cat /opt/axiom/.env
```

**Explanation:**
- `AXIOM_HOST`: the IP address the application will listen on. Use `127.0.0.1` (localhost) if only local connections are needed. Use `0.0.0.0` if remote clients (e.g., a web UI on another machine) need to reach the API. **Do not expose to the internet.**
- `PORT`: the TCP port the API server will listen on. Choose an unused port in the range 1024–65535 (e.g., 8420 is default; 8000, 5000, and 3000 are common alternatives).
- `AXIOM_DB_PATH`: the full path where the SQLite database file will be created and stored. Must be on a filesystem with sufficient free space (see Part A §1).

### B4. Run tests (optional but recommended)

```bash
# Activate the virtual environment if you created one
source venv/bin/activate

# Run the test suite
python3 tests/run_tests.py

# Expected output:
# PASS: test_physics.py::test_axle_load
# PASS: test_physics.py::test_bearing_temp
# ... (21 tests total)
# All tests passed

# Check the exit code
echo $?
# Expected: 0 (success)
```

If tests fail, review the error output. Common causes:
- Wrong Python version (see Part A §4).
- Numpy not installed correctly (`pip install --force-reinstall numpy`).
- Database file permissions (see Part C §2).

### B5. Start the application (manual)

```bash
# Activate the virtual environment
source venv/bin/activate

# Start the application
python3 -m axiom.backend.main

# Expected output:
# Starting AxiomDynamics API on 127.0.0.1:8420
# Listening for requests...
```

The application is now running. In another terminal, verify it is responding:

```bash
# On the same machine (if AXIOM_HOST is 127.0.0.1)
curl http://127.0.0.1:8420/api/fleet

# Expected output: JSON list of fleet entities (may be empty on first run)
# [ ... ]
```

To stop the application, press `Ctrl+C` in the terminal where it is running.

### B6. Start the application (as a systemd service)

To run as a persistent service that starts automatically on reboot, create a systemd unit file:

```bash
# Create the systemd service file
sudo tee /etc/systemd/system/axiom.service > /dev/null <<EOF
[Unit]
Description=AxiomDynamics Predictive Maintenance Platform
After=network.target

[Service]
Type=simple
User=axiom                           # Change to the user who runs the application
WorkingDirectory=/opt/axiom
ExecStart=/opt/axiom/venv/bin/python3 -m axiom.backend.main
Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create the service user (if not present)
sudo useradd -r -s /bin/false axiom 2>/dev/null || true

# Set ownership
sudo chown -R axiom:axiom /opt/axiom

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable axiom
sudo systemctl start axiom

# Check the status
sudo systemctl status axiom

# View logs
sudo journalctl -u axiom -f
```

To stop or restart:
```bash
sudo systemctl stop axiom
sudo systemctl restart axiom
```

---

## Part C — Air-Gapped Deployment (Option B)

### C1. Prerequisites for air-gapped deployment

You will need **two machines:**
1. **Internet machine:** has internet access, used to prepare the sealed archive.
2. **Target machine:** the air-gapped host where the Platform will run. No internet access.

You will need **approved transfer media:**
- USB drive, encrypted external disk, or network transfer appliance approved by your security policy.
- This document does not mandate a specific technology; use what your security policy requires.

### C2. Prepare the sealed archive (on internet machine)

On the internet machine:

```bash
# Create a work directory
mkdir -p /tmp/axiom-build
cd /tmp/axiom-build

# Clone or download the application (as in B1)
git clone [AxiomDynamics distribution repository URL — supplied with the release package]
cd AxiomDynamics

# Create a directory for offline dependencies
mkdir -p ../offline-deps

# Download all dependencies (with no installation)
pip download -r requirements.txt -d ../offline-deps

# Verify downloads
ls ../offline-deps/
# Expected output: numpy-*.whl, and a few build-dependency files

# Create a checksum manifest
sha256sum ../offline-deps/* > ../offline-deps/MANIFEST.sha256

# Create the sealed archive
cd ..
tar czf axiom-release-YYYY-MM-DD.tar.gz AxiomDynamics/ offline-deps/ offline-deps/MANIFEST.sha256
ls -lh axiom-release-YYYY-MM-DD.tar.gz
```

### C3. Transfer and extract (on air-gapped machine)

Transfer `axiom-release-YYYY-MM-DD.tar.gz` via approved media to the target machine.

On the target machine:

```bash
# Verify the file was transferred
ls -l axiom-release-YYYY-MM-DD.tar.gz

# Extract the archive
mkdir -p /opt/axiom
cd /opt/axiom
tar xzf /path/to/axiom-release-YYYY-MM-DD.tar.gz

# Verify contents
ls
# Expected output: AxiomDynamics/, offline-deps/

# Verify integrity of downloads (if checksum file is present)
cd offline-deps
sha256sum -c MANIFEST.sha256
# Expected output: [filename]: OK (for each file)
```

### C4. Install from offline cache

```bash
# Move to the application directory
cd /opt/axiom/AxiomDynamics

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies from the offline cache (not from PyPI)
pip install --no-index --find-links ../offline-deps -r requirements.txt

# Verify
python3 -c "import numpy; print('OK')"
# Expected output: OK
```

### C5. Configure and start

From this point, follow **B3** (Configure), **B4** (Test), **B5** (Start Manual), or **B6** (Start as Service).

---

## Part D — Containerized Deployment (Option C)

### D1. Prerequisites for containerized deployment

- Docker (v20+) or Podman (v3+) installed and running.
- A private container registry (Docker Hub, ECR, GCR, or local registry) if you plan to archive the image.
- Network access to build the image (one-time).

### D2. Build the container image

```bash
# Clone or obtain the application (as in B1)
cd /opt/axiom/AxiomDynamics

# Build the image using the supplied Dockerfile
docker build -t axiom:latest .

# (Optional) Tag for a registry
docker tag axiom:latest your-registry/axiom:latest

# Verify the image
docker images | grep axiom
# Expected output: axiom  latest  [IMAGE ID]  [SIZE]
```

### D3. Run the container

```bash
# Create a directory for the database (on the host)
mkdir -p /data/axiom
chmod 700 /data/axiom

# Run the container
docker run -d \
  --name axiom \
  -p 8420:8420 \
  -e AXIOM_HOST=0.0.0.0 \
  -e AXIOM_DB_PATH=/var/lib/axiom/axiom.db \
  -v /data/axiom:/var/lib/axiom \
  axiom:latest

# Check if it is running
docker ps | grep axiom

# View logs
docker logs -f axiom

# Test connectivity
curl http://localhost:8420/api/fleet
```

### D4. Persist across restarts

```bash
# Stop and remove the container
docker stop axiom
docker rm axiom

# Run with restart policy
docker run -d \
  --name axiom \
  --restart unless-stopped \
  -p 8420:8420 \
  -e AXIOM_HOST=0.0.0.0 \
  -e AXIOM_DB_PATH=/var/lib/axiom/axiom.db \
  -v /data/axiom:/var/lib/axiom \
  axiom:latest
```

---

## Part E — Post-Deployment Verification

### E1. API connectivity test

```bash
# Test the main endpoints
curl -s http://AXIOM_HOST:PORT/api/fleet | python3 -m json.tool
curl -s http://AXIOM_HOST:PORT/api/alerts | python3 -m json.tool

# Expected output: JSON (may be empty on first run)
# If connection refused: check PORT and AXIOM_HOST
# If permission denied: check firewall rules
```

### E2. Database verification

```bash
# Check that the database file exists and is readable
ls -lh /path/to/axiom.db

# Query the database directly (if sqlite3 is installed)
sqlite3 /path/to/axiom.db ".tables"
# Expected output: (table list or message that no tables exist yet)
```

### E2a. Establish the ledger export key and take a first signed export

Do this **once**, at commissioning, before any disposition is recorded, and again only when rotating the key under D09 §4.5. The export key is what lets the Railroad prove, later and without trusting the platform host, that the ledger it holds is the ledger that was written.

```bash
cd /opt/axiom/AxiomDynamics
# 1. Generate the signing key. It is written mode 0600, and it must never be
#    copied onto the platform host's backups or into the source tree.
python3 -m backend.ledger_export keygen --key-file /root/axiom-export.key

# 2. RECORD THE KEY_ID IT PRINTS in the custody log (D09 §4.5.2). Anyone
#    holding a bundle can compare its key_id to this figure.

# 3. Take a baseline export immediately.
python3 -m backend.ledger_export export \
    --key-file /root/axiom-export.key \
    --out /var/lib/axiom-export/ledger-$(date +%Y%m%d).json

# 4. Verify it on a DIFFERENT machine that has neither the database nor this
#    checkout -- the whole point is that verification does not need them.
python3 tools/verify_ledger_export.py \
    --key-file /path/to/copied/key \
    --bundle ledger-20261109.json
# Expected final line: "OK — every check passed."
```

**Reviewer credentials are a separate key and a separate procedure.** The export key above signs bundles; it is **not** a reviewer key and must never be registered as one (D09 §8.4.7). Each reviewer is issued their own key when they join, and that key is what attests their dispositions:

```bash
# For each reviewer, from a signed F08 only (D09 §8.4.2 step 1):
python3 -I tools/issue_reviewer_key.py \
    --reviewer "Hoffman" --cert CERT-H-0001 \
    --key-file /root/reviewer-keys/hoffman.key --note "F08 dated 2026-11-11"

# It prints the key_id. RECORD THAT -- and never the key -- in the custody
# log (D09 §8.4.6). Give the key file to the reviewer, or to the sealed
# store; do NOT leave it beside the export bundles.
```

**The joiner/mover/leaver procedure itself is D09 §8.4** and is the part a script cannot do. Read it before issuing a credential: step 1 is a signed F08, and there is no path to step 2 without it.

**Every subsequent export passes the previous one, and this is not optional:**

```bash
python3 -m backend.ledger_export export \
    --key-file /root/axiom-export.key \
    --out /var/lib/axiom-export/ledger-$(date +%Y%m%d).json \
    --previous-export-hash <the previous bundle's digest>

# and verify with the prior bundle supplied, which is what detects a ledger
# that has SHRUNK since the last export:
python3 tools/verify_ledger_export.py --key-file /path/to/key \
    --bundle ledger-20261110.json --previous-bundle ledger-20261109.json
```

**Two operational rules, both of which are controls rather than housekeeping.** Keep every bundle you are given — do not overwrite last month's with this month's, because the sequence is what detects a ledger truncated or rewritten between exports, and a single bundle cannot testify about its own past (D09 §4.5.4). And copy the key off the host into sealed storage at commissioning; a key that exists only on the platform host is lost with the disk, and every bundle it signed becomes unverifiable.

**Let the Platform produce the series rather than exporting by hand.** The commands above are the one-bundle case. For a real deployment the cadence in D09 §4.5.4 is executed by `backend/ledger_replication.py`, which decides what is due, chains each bundle to the last, keeps a zero-record week instead of skipping it, and never overwrites. One scheduler entry is all it needs:

```bash
# Run daily; it produces only what is due (weekly incremental, monthly full).
# A run with nothing due exits 0 without writing a bundle, so daily is safe.
0 2 * * * cd /opt/axiom/AxiomDynamics && python3 -m backend.ledger_replication run \
    --key-file /root/axiom-export.key --series-dir /var/lib/axiom-export/series \
    >> /var/log/axiom-replication.log 2>&1

# Quarterly, and before any bundle is taken off the host:
python3 -m backend.ledger_replication inspect \
    --series-dir /var/lib/axiom-export/series --key-file /root/axiom-export.key
# Expected: "OK — series is continuous and every bundle verifies"
```

**The Platform does not carry the series off the box.** D09 §3.2 promises no outbound network, so there is nothing to configure and nothing that transmits: the series accumulates in `--series-dir` on the platform host. Copying it to backup media is your step under D09 §3.3, and it is the step that stops a lost disk from losing the ledger. If `inspect` reports a gap or an unrecorded bundle, do not delete anything — preserve the directory and treat it under D09 §4.5.6.

**No HTTP route performs this.** Export is deliberately an operator command on the box, because the server has no **administrator** credential (B01 §4.5a) — reviewer sessions and collector tokens were added on 2026-11-11, but neither is the right principal for a full ledger export. Do not expose a route until an authenticated administrator session means something.

### E3. Log file inspection

```bash
# For systemd deployment
sudo journalctl -u axiom -n 50   # Last 50 lines
sudo journalctl -u axiom -f      # Follow logs in real time

# For manual deployment (logs go to stdout; redirect if needed)
# See the terminal where you ran 'python3 -m axiom.backend.main'

# For container deployment
docker logs axiom -n 50
docker logs axiom -f
```

### E4. Fire wall and network confirmation

```bash
# Verify the application is listening on the expected port
netstat -tln | grep 8420
# Or: ss -tln | grep 8420
# Expected output: LISTEN on [AXIOM_HOST]:8420

# Verify outbound network is blocked (should fail or time out after seconds)
timeout 3 curl https://example.com || echo "Outbound blocked (expected)"
```

---

## Part F — Configuration Attestation

Once the application is running and verified, **the Railroad's IT Director (or equivalent) must sign the Configuration Attestation** (defined in D14 §6 of the Master Brief Docket).

The attestation confirms:
1. The application is installed and running at the documented host and port.
2. The configuration matches the agreed-upon architecture (air-gapped, database location, listener address).
3. Initial testing has been completed and the platform is operational.
4. The IT team is prepared to operate it.

**Template attestation statement:**
> I, __________________ (name and title), on behalf of __________________ (Railroad), certify that:
> 1. AxiomDynamics has been installed at __________________ (site) on ____________________(date).
> 2. The installation follows the specifications in C01 of the Master Brief Docket, using method: ☐ Standard ☐ Air-gapped ☐ Containerized.
> 3. The application is accessible at `http://AXIOM_HOST:PORT` and is passing health checks.
> 4. Database location: __________________ (path).
> 5. The IT team responsible for operations has been trained per C02 and has confirmed readiness.
> 6. This deployment is confirmed as the **Commissioning Date** for the purposes of the Master Pilot Agreement (D02).

**Signature:** __________________  **Date:** __________________

---

## Part G — Troubleshooting

| Symptom | Cause | Resolution |
|---|---|---|
| `ModuleNotFoundError: No module named 'axiom'` | PYTHONPATH is not set correctly, or you are not in the right directory. | Ensure `pwd` shows `/opt/axiom/AxiomDynamics` or add it to PYTHONPATH: `export PYTHONPATH=/opt/axiom/AxiomDynamics:$PYTHONPATH` |
| `ModuleNotFoundError: No module named 'numpy'` | numpy is not installed. | Run `pip install numpy` (or `pip install -r requirements.txt` if the virtual environment is not activated). |
| `Port 8420 already in use` | Another process is listening on that port. | Change PORT in the .env file (e.g., PORT=8421) or identify and stop the other process: `lsof -i :8420` (or `netstat -tln \| grep 8420`). |
| `Permission denied: /opt/axiom/axiom.db` | The database file or directory is not writable by the user running the application. | `chmod 644 /opt/axiom/axiom.db` (or `chown axiom:axiom /opt/axiom/axiom.db` if running as the `axiom` user). |
| `curl: Connection refused` | The application is not running or not listening on the expected address. | Check process: `ps aux \| grep axiom`. Check listener: `netstat -tln \| grep 8420`. Review logs for startup errors. |
| Tests fail with `AssertionError` or `ZeroDivisionError` | Physics model logic or test data issue. | Run `python3 tests/run_tests.py -v` for verbose output. Check that the detector data being used is well-formed. |
| Database grows very large very quickly | Retention policy is set too high, or dispositions are not being cleaned up. | Review **C02 §5** (certification registry and audit) and **D09 §5.1** (retention) for retention settings. Consider implementing a purge policy. |

---

## Part H — Security considerations

1. **Network isolation:** The application must not have outbound network access. Firewall rules should deny all egress by default.
2. **Host hardening:** Run the application under a non-root user (e.g., `axiom:axiom`) with minimal privileges.
3. **Database encryption:** Consider encrypting the SQLite database at rest using `sqlcipher` or filesystem encryption, per the Railroad's security policy.
4. **Access logs:** Configure systemd or syslog to capture and archive application logs. See D09 (Data Processing Addendum) for retention requirements.
5. **Backup:** Back up the database file regularly. Ensure backups are stored in a secure location and tested for recovery.
6. **Credential management:** If environment variables or `.env` files contain sensitive data (e.g., database encryption keys), store them in a secrets manager (e.g., HashiCorp Vault, AWS Secrets Manager) and retrieve them at runtime, rather than storing them in plain text.

---

*This SOP is a deployment guide for the Railroad's IT team. For technical support, contact AxiomDynamics. For questions about regulatory compliance or operational policy, contact your Chief Engineer or IT Director.*
