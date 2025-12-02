"""
Executor Client Module (SSH Version)
====================================
Communicates with the Ubuntu Muscle Node via SSH.
Logs all operations to Documents/logs/executor.log.
"""

import paramiko
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config import load_config

# Setup Logging
log_dir = Path(__file__).parent.parent.parent / "Documents" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=log_dir / "executor.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

class ExecutorClient:
    """SSH Client for the Ubuntu Muscle Node"""
    
    def __init__(self):
        self.config = load_config()
        # Hardcoded for now based on user input/deploy.py, ideally move to config/env
        self.host = "10.24.22.176"
        self.port = 8080
        self.username = "dell"
        self.password = "gdut2021"
        self.conda_path = "/BioAnalyse/miniconda3"
        
    def check_health(self) -> bool:
        """Check if SSH connection is possible"""
        try:
            client = self._connect()
            client.close()
            return True
        except Exception as e:
            logging.error(f"Health Check Failed: {e}")
            print(f"⚠️ SSH Connection Failed: {e}")
            return False
            
    def _connect(self):
        """Establish SSH connection"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            self.host, 
            port=self.port, 
            username=self.username, 
            password=self.password,
            timeout=10
        )
        return client

    def run_command(self, script: str, cwd: str = None, env_name: str = "base") -> Dict[str, Any]:
        """
        Run a shell command on the Ubuntu node via SSH.
        """
        logging.info(f"REQUEST: Run command in '{cwd or '.'}' (env: {env_name})")
        logging.info(f"SCRIPT: {script}")
        
        client = None
        try:
            client = self._connect()
            
            # Construct command with environment activation
            # 1. Source conda
            # 2. Activate env
            # 3. Go to cwd (if provided)
            # 4. Run script
            
            full_cmd = f"source {self.conda_path}/etc/profile.d/conda.sh && conda activate {env_name}"
            if cwd:
                # Ensure cwd exists
                full_cmd += f" && mkdir -p {cwd} && cd {cwd}"
            
            full_cmd += f" && {script}"
            
            logging.info(f"FULL_CMD: {full_cmd}")
            
            # Execute
            stdin, stdout, stderr = client.exec_command(full_cmd, timeout=None)
            
            # Read output with timeout mechanism for long-running commands
            # Instead of blocking indefinitely, we poll for completion
            out_str = ""
            err_str = ""
            exit_status = None
            
            # Wait for channel to complete, but with periodic checks
            channel = stdout.channel
            start_time = time.time()
            last_log_time = start_time
            
            while not channel.exit_status_ready():
                # Sleep briefly to avoid busy waiting
                time.sleep(1)
                
                # Log progress every 30 seconds for long-running commands
                elapsed = time.time() - last_log_time
                if elapsed > 30:
                    logging.info(f"Command still running... (elapsed: {int(time.time() - start_time)}s)")
                    last_log_time = time.time()
            
            # Command finished, read all output
            out_str = stdout.read().decode().strip()
            err_str = stderr.read().decode().strip()
            exit_status = channel.recv_exit_status()
            
            total_time = int(time.time() - start_time)
            logging.info(f"EXIT_CODE: {exit_status} (execution time: {total_time}s)")
            if out_str: logging.info(f"STDOUT: {out_str}")
            if err_str: logging.error(f"STDERR: {err_str}")
            
            return {
                "stdout": out_str,
                "stderr": err_str,
                "return_code": exit_status
            }
            
        except Exception as e:
            error_msg = f"SSH Execution Error: {str(e)}"
            logging.error(error_msg)
            return {
                "stdout": "",
                "stderr": error_msg,
                "return_code": -1
            }
        finally:
            if client:
                client.close()

if __name__ == "__main__":
    # Test the client
    client = ExecutorClient()
    
    print("🏥 Checking SSH Connection...")
    if client.check_health():
        print("✅ SSH is Online!")
        
        print("\n🚀 Running Test Command (ls -la)...")
        result = client.run_command("ls -la", cwd="/media/dell/eDNA3/Lab")
        print(f"Return Code: {result['return_code']}")
        print(f"Output:\n{result['stdout']}")
    else:
        print("❌ SSH is Offline.")
