# Odoo Server Tuner

A command-line utility to analyze your Linux server running Odoo and recommend optimal `odoo.conf` and systemd limits settings based on your machine's resources.

## Features

* Auto-detects running Odoo systemd service(s) and prompts you to select one if multiple are found.
* Gathers current `ulimit` values, systemd limits (`LimitNOFILE`, `LimitNPROC`), total RAM, CPU count.
* Calculates recommended settings:

  * `limit_memory_soft` (≈90% of RAM)
  * `limit_memory_hard` (≈150% of RAM)
  * `limit_time_cpu`, `limit_time_real`, `limit_request`
  * `workers` (CPUs - 1)
  * `LimitNOFILE` for systemd override
* Supports verbosity (`-v/--verbose`) with detailed logs.
* Outputs both JSON (`--output`) and human-readable config snippets.
* Interactive service selection when multiple Odoo services are running.

## Installation

Clone the repository or fetch the script directly:

```bash
# Using curl\ n\curl -fsSL https://raw.githubusercontent.com/Paulius11/odoo-server-tuner/main/odoo_sys_tuner.py -o odoo_sys_tuner.py

# Or using wget\ n
wget -O odoo_sys_tuner.py https://raw.githubusercontent.com/Paulius11/odoo-server-tuner/main/odoo_sys_tuner.py
```

Make it executable:

```bash
chmod +x odoo_sys_tuner.py
```

## Usage

```bash
# Basic run
./odoo_sys_tuner.py

# Specify service manually
./odoo_sys_tuner.py --service odoo.service

# Output JSON to file
./odoo_sys_tuner.py --output recommendations.json

# Enable verbose logging
./odoo_sys_tuner.py -v
```

Example output:

```ini
# Odoo configuration recommendations
[options]
limit_memory_soft = 7730941132  # ~90% of RAM in bytes
limit_memory_hard = 12884901888  # 1.5× RAM in bytes
limit_time_cpu    = 1800  # seconds
limit_time_real   = 3600  # seconds
limit_request     = 0  # count, 0=unlimited
workers           = 3  # number of workers
max_cron_threads  = 1

# Systemd override recommendations
Service: odoo.service
[Service]
LimitNOFILE       = 65536  # soft file-descriptors
LimitNPROC        = 31312  # as detected or unchanged
```

