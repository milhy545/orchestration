#!/usr/bin/env python3
import os
import sys
import logging
import json
import time
import subprocess
from typing import Dict, Any
from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/backup_coordinator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('BackupCoordinator')

app = Flask(__name__)

class BackupCoordinator:
    def __init__(self):
        self.config = {
            'name': 'BackupCoordinator',
            'version': '1.0.0',
            'port': 7999,
            'mqtt_port': 1883
        }
        
        self.agent_status = {
            'claude-code': {'last_seen': 0, 'status': 'unknown'},
            'multi-llm': {'last_seen': 0, 'status': 'unknown'}
        }
        
        # MQTT setup
        self.mqtt_client = mqtt.Client('backup_coordinator')
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        
    def on_mqtt_connect(self, client, userdata, flags, rc):
        logger.info(f'Backup Coordinator connected to MQTT with result code {rc}')
        # Subscribe to all agent topics
        client.subscribe('has/claude_code/+')
        client.subscribe('has/multi_llm/+')
        client.subscribe('has/backup/commands')

    def on_mqtt_message(self, client, userdata, msg):
        try:
            topic_parts = msg.topic.split('/')
            agent_type = topic_parts[1] if len(topic_parts) > 1 else 'unknown'
            
            # Track agent activity
            if agent_type in self.agent_status:
                self.agent_status[agent_type]['last_seen'] = time.time()
                self.agent_status[agent_type]['status'] = 'active'
            
            # Handle emergency commands
            if msg.topic == 'has/backup/commands':
                payload = json.loads(msg.payload.decode())
                self.handle_emergency_command(payload)
                
        except Exception as e:
            logger.error(f'Error processing MQTT message: {e}')

    def handle_emergency_command(self, command: Dict[str, Any]):
        """Handle emergency coordination commands"""
        cmd_type = command.get('command')
        
        if cmd_type == 'agent_failure':
            failed_agent = command.get('agent')
            logger.warning(f"Agent failure reported: {failed_agent}")
            self.initiate_failover(failed_agent)
            
        elif cmd_type == 'system_recovery':
            self.initiate_system_recovery()
            
        elif cmd_type == 'health_check':
            health = self.get_system_health()
            self.mqtt_client.publish('has/backup/health', json.dumps(health))

    def initiate_failover(self, failed_agent: str):
        """Initiate failover procedures"""
        logger.info(f"Initiating failover for {failed_agent}")
        
        if failed_agent == 'multi-llm':
            # Restart multi-llm agent
            try:
                subprocess.run(['rc-service', 'multi-llm-agent', 'restart'], check=True)
                logger.info("Multi-LLM agent restart initiated")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to restart multi-llm agent: {e}")
                # Fall back to original claude-code agent
                self.mqtt_client.publish('has/claude_code/commands', 
                                       json.dumps({'command': 'take_primary_role'}))
        
        elif failed_agent == 'claude-code':
            # Try to restart claude-code
            try:
                subprocess.run(['rc-service', 'claude-code', 'restart'], check=True)
                logger.info("Claude-Code agent restart initiated")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to restart claude-code agent: {e}")

    def initiate_system_recovery(self):
        """Emergency system recovery"""
        logger.info("Initiating system recovery procedures")
        
        recovery_steps = [
            'rc-service mosquitto restart',
            'rc-service claude-code start',
            'rc-service multi-llm-agent start',
            'docker-compose -f /home/orchestration/docker-compose.yml restart'
        ]
        
        results = []
        for step in recovery_steps:
            try:
                result = subprocess.run(step.split(), capture_output=True, text=True)
                results.append({
                    'step': step,
                    'success': result.returncode == 0,
                    'output': result.stdout + result.stderr
                })
                logger.info(f"Recovery step completed: {step}")
            except Exception as e:
                results.append({'step': step, 'success': False, 'error': 'failed'})
                logger.error(f"Recovery step failed: {step} - {e}")
        
        # Publish recovery results
        self.mqtt_client.publish('has/backup/recovery_results', json.dumps(results))

    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health"""
        current_time = time.time()
        
        # Check agent health
        for agent, status in self.agent_status.items():
            age = current_time - status['last_seen']
            if age > 120:  # 2 minutes timeout
                status['status'] = 'inactive'
            elif age > 60:  # 1 minute warning
                status['status'] = 'warning'
        
        # Check services
        service_health = {}
        services = ['mosquitto', 'claude-code', 'multi-llm-agent']
        
        for service in services:
            try:
                result = subprocess.run(['rc-service', service, 'status'], 
                                      capture_output=True, text=True)
                service_health[service] = 'started' in result.stdout
            except:
                service_health[service] = False
        
        return {
            'timestamp': current_time,
            'agents': self.agent_status,
            'services': service_health,
            'coordinator_uptime': current_time - self.start_time
        }

    def start_mqtt_monitoring(self):
        """Start MQTT monitoring in separate thread"""
        def mqtt_loop():
            self.mqtt_client.connect('localhost', self.config['mqtt_port'], 60)
            self.mqtt_client.loop_forever()
        
        mqtt_thread = threading.Thread(target=mqtt_loop, daemon=True)
        mqtt_thread.start()
        logger.info("MQTT monitoring started")

    def run(self):
        """Run backup coordinator"""
        self.start_time = time.time()
        logger.info(f"Backup Coordinator starting on port {self.config['port']}")
        
        # Start MQTT monitoring
        self.start_mqtt_monitoring()
        
        # Publish coordinator startup
        time.sleep(2)  # Wait for MQTT connection
        self.mqtt_client.publish('has/backup/init', json.dumps(self.config))
        
        return app

# Flask routes
coordinator = BackupCoordinator()

@app.route('/health', methods=['GET'])
def health():
    return jsonify(coordinator.get_system_health())

@app.route('/agents/status', methods=['GET'])  
def agents_status():
    return jsonify(coordinator.agent_status)

@app.route('/emergency/restart/<agent>', methods=['POST'])
def emergency_restart(agent):
    coordinator.initiate_failover(agent)
    return jsonify({'status': 'failover_initiated', 'agent': agent})

@app.route('/recovery', methods=['POST'])
def system_recovery():
    coordinator.initiate_system_recovery() 
    return jsonify({'status': 'recovery_initiated'})

if __name__ == '__main__':
    app_instance = coordinator.run()
    app_instance.run(host='0.0.0.0', port=7999, debug=False)

@app.route('/wake/workstation', methods=['POST'])
def wake_workstation():
    """HTTP endpoint for Wake-on-LAN"""
    try:
        logger.info("Executing Wake-on-LAN via HTTP endpoint")
        result = subprocess.run(['/usr/local/bin/wake-workstation.sh'], 
                              capture_output=True, text=True, timeout=90)
        
        return jsonify({
            'status': 'success' if result.returncode == 0 else 'failed',
            'output': result.stdout,
            'error': result.stderr if result.stderr else None,
            'timestamp': time.time(),
            'returncode': result.returncode
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'timeout',
            'message': 'Wake-on-LAN timed out after 90 seconds',
            'timestamp': time.time()
        }), 408
        
    except Exception as e:
        logger.error(f"Wake-on-LAN failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'wake-on-lan failed',
            'timestamp': time.time()
        }), 500

@app.route('/wake/status', methods=['GET'])
def wake_status():
    """Check workstation connectivity status"""
    import subprocess
    
    workstation_ip = '192.168.0.10'
    tailscale_ip = '100.80.66.70'
    
    local_ping = subprocess.run(['ping', '-c', '1', '-W', '1', workstation_ip], 
                               capture_output=True).returncode == 0
    tailscale_ping = subprocess.run(['ping', '-c', '1', '-W', '1', tailscale_ip], 
                                   capture_output=True).returncode == 0
    
    return jsonify({
        'workstation_status': {
            'local_ip': workstation_ip,
            'local_reachable': local_ping,
            'tailscale_ip': tailscale_ip, 
            'tailscale_reachable': tailscale_ping,
            'overall_status': 'online' if (local_ping or tailscale_ping) else 'offline'
        },
        'timestamp': time.time()
    })
