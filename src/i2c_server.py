#!/usr/bin/env python3
"""
I2C Remote Server
Runs on the remote target (BeagleBone) to provide I2C access over network.
"""

import socket
import struct
import time
import logging
from typing import Optional, Tuple, List
import smbus2 as smbus
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class I2CServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 8888, bus_number: int = 1):
        self.host = host
        self.port = port
        self.bus_number = bus_number
        self.bus: Optional[smbus.SMBus] = None
        self.server_socket: Optional[socket.socket] = None

    def init_i2c(self) -> bool:
        """Initialize I2C bus"""
        try:
            self.bus = smbus.SMBus(self.bus_number)
            logger.info(f"I2C bus {self.bus_number} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize I2C bus {self.bus_number}: {e}")
            return False

    def start_server(self):
        """Start the I2C server"""
        if not self.init_i2c():
            return

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            logger.info(f"I2C server listening on {self.host}:{self.port}")

            while True:
                client_socket, client_address = self.server_socket.accept()
                logger.info(f"Client connected from {client_address}")
                self.handle_client(client_socket)

        except KeyboardInterrupt:
            logger.info("Server shutting down...")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
            if self.bus:
                self.bus.close()

    def handle_client(self, client_socket: socket.socket):
        """Handle client connection"""
        try:
            while True:
                # Receive command
                data = client_socket.recv(1024)
                if not data:
                    break

                try:
                    command = json.loads(data.decode('utf-8'))
                    logger.debug(f"Received command: {command}")

                    result = self.process_command(command)
                    response = json.dumps(result).encode('utf-8')

                    # Send response length first, then data
                    client_socket.send(struct.pack('!I', len(response)))
                    client_socket.send(response)

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    error_response = json.dumps({"error": "Invalid JSON"}).encode('utf-8')
                    client_socket.send(struct.pack('!I', len(error_response)))
                    client_socket.send(error_response)

        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def process_command(self, command: dict) -> dict:
        """Process I2C command"""
        try:
            cmd_type = command.get('type')

            if cmd_type == 'write_byte':
                address = command['address']
                value = command['value']
                self.bus.write_byte(address, value)
                return {"status": "success"}

            elif cmd_type == 'read_byte':
                address = command['address']
                value = self.bus.read_byte(address)
                return {"status": "success", "value": value}

            elif cmd_type == 'write_byte_data':
                address = command['address']
                register = command['register']
                value = command['value']
                self.bus.write_byte_data(address, register, value)
                return {"status": "success"}

            elif cmd_type == 'read_byte_data':
                address = command['address']
                register = command['register']
                value = self.bus.read_byte_data(address, register)
                return {"status": "success", "value": value}

            elif cmd_type == 'write_word_data':
                address = command['address']
                register = command['register']
                value = command['value']
                self.bus.write_word_data(address, register, value)
                return {"status": "success"}

            elif cmd_type == 'read_word_data':
                address = command['address']
                register = command['register']
                value = self.bus.read_word_data(address, register)
                return {"status": "success", "value": value}

            elif cmd_type == 'write_i2c_block_data':
                address = command['address']
                register = command['register']
                data = command['data']
                self.bus.write_i2c_block_data(address, register, data)
                return {"status": "success"}

            elif cmd_type == 'read_i2c_block_data':
                address = command['address']
                register = command['register']
                length = command['length']
                data = self.bus.read_i2c_block_data(address, register, length)
                return {"status": "success", "data": data}

            elif cmd_type == 'scan':
                devices = []
                for addr in range(0x03, 0x78):
                    try:
                        self.bus.read_byte(addr)
                        devices.append(addr)
                    except:
                        pass
                return {"status": "success", "devices": devices}

            elif cmd_type == 'reset_interface':
                # Reset I2C interface in case of errors
                logger.info("Resetting I2C interface...")
                try:
                    # Close and reopen the bus
                    if self.bus:
                        self.bus.close()
                    self.bus = smbus.SMBus(self.bus_number)
                    logger.info("I2C interface reset successful")
                    return {"status": "success", "message": "I2C interface reset"}
                except Exception as e:
                    logger.error(f"Failed to reset I2C interface: {e}")
                    return {"status": "error", "message": f"Reset failed: {str(e)}"}

            else:
                return {"status": "error", "message": f"Unknown command type: {cmd_type}"}

        except Exception as e:
            logger.error(f"Error processing command {command}: {e}")
            return {"status": "error", "message": str(e)}

def main():
    import argparse

    parser = argparse.ArgumentParser(description='I2C Remote Server')
    parser.add_argument('--host', default='0.0.0.0', help='Server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8888, help='Server port (default: 8888)')
    parser.add_argument('--bus', type=int, default=1, help='I2C bus number (default: 1)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    server = I2CServer(args.host, args.port, args.bus)
    server.start_server()

if __name__ == '__main__':
    main()