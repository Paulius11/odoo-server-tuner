import subprocess
import re
import argparse
import logging
import json
import psutil

class OdooServerTuner:
    def __init__(self, service=None, verbose=False):
        self.data = {}
        self.service = service
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

    def run_cmd(self, cmd):
        if self.verbose:
            self.logger.debug(f"Running command: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0 and self.verbose:
            self.logger.warning(f"Command failed ({result.returncode}): {cmd}\nstderr: {result.stderr.strip()}")
        return result.stdout.strip()

    def detect_service(self):
        if self.service:
            self.data['service'] = self.service
            return
        out = self.run_cmd("systemctl list-units --type=service --no-legend --no-pager")
        services = [line.split()[0] for line in out.splitlines() if 'odoo' in line.lower()]
        if not services:
            raise RuntimeError("No Odoo systemd services detected. Use --service to specify manually.")
        if len(services) == 1:
            self.service = services[0]
        else:
            print("Multiple Odoo services detected:")
            for idx, svc in enumerate(services, 1):
                print(f"  {idx}. {svc}")
            choice = None
            while choice is None:
                try:
                    sel = int(input(f"Select service [1-{len(services)}]: "))
                    if 1 <= sel <= len(services):
                        choice = services[sel-1]
                    else:
                        print("Invalid selection.")
                except ValueError:
                    print("Enter a number.")
            self.service = choice
        self.data['service'] = self.service
        if self.verbose:
            self.logger.debug(f"Using service: {self.service}")

    def gather_ulimits(self):
        out = self.run_cmd('ulimit -a')
        limits = {}
        for line in out.splitlines():
            m = re.match(r"(.+?)\s+\(-(.+?)\)\s+(.*)", line)
            if m:
                _, key, val = m.groups()
                limits[key] = val
        self.data['ulimits'] = limits

    def gather_systemd_limits(self):
        cmd = f"systemctl show {self.service} --property=LimitNOFILE --property=LimitNPROC"
        out = self.run_cmd(cmd)
        limits = {}
        for line in out.splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                try:
                    limits[k] = int(v)
                except ValueError:
                    limits[k] = v
        self.data['systemd_limits'] = limits

    def gather_memory(self):
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        self.data['memory'] = {'total': mem.total, 'available': mem.available, 'swap_total': swap.total}

    def gather_cpus(self):
        self.data['cpus'] = psutil.cpu_count()

    def recommend(self):
        rec = {}
        mem_gb = self.data['memory']['total'] / (1024**3)
        rec['limit_memory_soft'] = int(mem_gb * 0.9 * 1024**3)
        rec['limit_memory_hard'] = int(mem_gb * 1.5 * 1024**3)
        u_n = int(self.data['ulimits'].get('n', '1024'))
        rec['LimitNOFILE'] = max(u_n, 65536)
        rec['workers'] = max(1, self.data['cpus'] - 1)
        rec['limit_time_cpu'] = 1800
        rec['limit_time_real'] = 3600
        rec['limit_request'] = 0
        self.data['recommendations'] = rec

    def output(self, output_path=None):
        # Always write JSON if requested
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(self.data, f, indent=2)
            print(f"Recommendations written to {output_path}")
        # Print human-readable settings
        rec = self.data.get('recommendations', {})
        print("\n# Odoo configuration recommendations")
        print("[options]")
        print(f"limit_memory_soft = {rec.get('limit_memory_soft')}  # ~90% of RAM in bytes")
        print(f"limit_memory_hard = {rec.get('limit_memory_hard')}  # 1.5× RAM in bytes")
        print(f"limit_time_cpu    = {rec.get('limit_time_cpu')}  # seconds")
        print(f"limit_time_real   = {rec.get('limit_time_real')}  # seconds")
        print(f"limit_request     = {rec.get('limit_request')}  # count, 0=unlimited")
        print(f"workers           = {rec.get('workers')}  # number of workers")
