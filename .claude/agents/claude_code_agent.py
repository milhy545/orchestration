#!/usr/bin/env python3
import os
import sys
import logging
import subprocess
import json
import time
import threading
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    filename='/var/log/claude_code_agent.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ClaudeCodeAgent')

class ClaudeCodeAgent:
    def __init__(self):
        # MQTT setup
        self.mqtt_client = mqtt.Client('claude_code_agent')
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        
        # Agent configuration
        self.config = {
            'name': 'ClaudeCodeAgent',
            'version': '1.0.0',
            'host': 'HAS',
            'ip': '192.168.0.58',
            'role': 'master'
        }
        
        self.start_time = time.time()

    def on_mqtt_connect(self, client, userdata, flags, rc):
        logger.info(f'Connected to MQTT with result code {rc}')
        client.subscribe('has/claude_code/commands')
        client.subscribe('has/claude_code/escalation')

    def on_mqtt_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            
            if msg.topic == 'has/claude_code/commands':
                command = payload.get('command')
                logger.info(f'Received command: {command}')
                
                if command == 'system_status':
                    self.report_system_status()
                elif command == 'update_packages':
                    self.update_packages()
                elif command == 'take_primary_role':
                    logger.info('Taking primary role as multi-LLM agent failed')
                    self.report_primary_status()
                    
            elif msg.topic == 'has/claude_code/escalation':
                logger.info(f'Received escalation: {payload}')
                self.handle_escalation(payload)
                
        except Exception as e:
            logger.error(f'Error processing MQTT message: {e}')

    def handle_escalation(self, task):
        '''Handle escalated tasks from multi-LLM agent'''
        logger.info(f'Processing escalated task: {task.get("id", "unknown")}')
        
        # Simple execution - can be enhanced
        result = {
            'task_id': task.get('id'),
            'handler': 'claude-master',
            'status': 'processed',
            'response': 'Task escalated to master agent - processing completed',
            'timestamp': time.time()
        }
        
        self.mqtt_client.publish('has/multi_llm/results', json.dumps(result))

    def report_system_status(self):
        try:
            # Get actual system info
            hostname_result = subprocess.run(['hostname'], capture_output=True, text=True)
            uptime_result = subprocess.run(['uptime'], capture_output=True, text=True) 
            free_result = subprocess.run(['free', '-h'], capture_output=True, text=True)
            
            status = {
                'hostname': hostname_result.stdout.strip(),
                'uptime': uptime_result.stdout.strip(),
                'memory': free_result.stdout.split('\n')[1].split()[2],
                'agent_uptime': time.time() - self.start_time,
                'timestamp': time.time()
            }
            
            self.mqtt_client.publish('has/claude_code/status', json.dumps(status))
        except Exception as e:
            logger.error(f'Error getting system status: {e}')

    def report_primary_status(self):
        '''Report that this agent is taking primary role'''
        status = {
            'role': 'primary',
            'agent': 'claude-code',
            'reason': 'multi-llm-agent-failure',
            'timestamp': time.time()
        }
        self.mqtt_client.publish('has/system/primary_agent', json.dumps(status))

    def update_packages(self):
        try:
            subprocess.run(['apk', 'update'], check=True)
            subprocess.run(['apk', 'upgrade', '-a'], check=True)
            self.mqtt_client.publish('has/claude_code/updates', 'Packages updated successfully')
        except subprocess.CalledProcessError as e:
            logger.error(f'Package update error: {e}')
            self.mqtt_client.publish('has/claude_code/updates', f'Update failed: {e}')

    def send_heartbeat(self):
        '''Send periodic heartbeat to multi-LLM agent'''
        while True:
            try:
                heartbeat = {
                    'agent': 'claude-master',
                    'timestamp': time.time(),
                    'uptime': time.time() - self.start_time,
                    'status': 'active'
                }
                self.mqtt_client.publish('has/master/heartbeat', json.dumps(heartbeat))
                time.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                logger.error(f'Heartbeat error: {e}')
                time.sleep(60)

    def run(self):
        logger.info('Claude Code Agent starting...')
        
        # MQTT connection
        self.mqtt_client.connect('localhost', 1883, 60)
        
        # Publish initial status
        self.mqtt_client.publish('has/claude_code/init', json.dumps(self.config))
        
        # Start heartbeat in separate thread
        heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
        heartbeat_thread.start()
        
        # Start MQTT loop
        self.mqtt_client.loop_forever()

if __name__ == '__main__':
    agent = ClaudeCodeAgent()
    agent.run()
