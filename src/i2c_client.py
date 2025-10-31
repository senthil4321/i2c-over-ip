#!/usr/bin/env python3
"""
I2C Remote Client
Provides local I2C interface that forwards requests to remote I2C server.
Compatible with smbus2 library interface.
"""

import socket
import struct
import json
import logging
from typing import List, Optional
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class I2CClient:
    """I2C client that forwards requests to remote server"""

    def __init__(self, host: str, port: int = 8888, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None

    def _connect(self) -> bool:
        """Connect to remote server"""
        try:
            if self.socket:
                self.socket.close()

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            logger.debug(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}:{self.port}: {e}")
            return False

    def _send_command(self, command: dict) -> dict:
        """Send command to server and receive response"""
        if not self.socket and not self._connect():
            raise ConnectionError(f"Cannot connect to {self.host}:{self.port}")

        try:
            # Send command
            data = json.dumps(command).encode('utf-8')
            self.socket.send(data)

            # Receive response length
            length_data = self.socket.recv(4)
            if len(length_data) != 4:
                raise ConnectionError("Failed to receive response length")

            response_length = struct.unpack('!I', length_data)[0]

            # Receive response
            response_data = b''
            while len(response_data) < response_length:
                chunk = self.socket.recv(min(4096, response_length - len(response_data)))
                if not chunk:
                    raise ConnectionError("Connection closed while receiving response")
                response_data += chunk

            response = json.loads(response_data.decode('utf-8'))

            if response.get('status') == 'error':
                raise RuntimeError(response.get('message', 'Unknown error'))

            return response

        except Exception as e:
            logger.error(f"Communication error: {e}")
            # Try to reconnect on next call
            if self.socket:
                self.socket.close()
                self.socket = None
            raise

    def write_byte(self, address: int, value: int):
        """Write byte to I2C device"""
        command = {
            'type': 'write_byte',
            'address': address,
            'value': value
        }
        self._send_command(command)

    def read_byte(self, address: int) -> int:
        """Read byte from I2C device"""
        command = {
            'type': 'read_byte',
            'address': address
        }
        response = self._send_command(command)
        return response['value']

    def write_byte_data(self, address: int, register: int, value: int):
        """Write byte to register"""
        command = {
            'type': 'write_byte_data',
            'address': address,
            'register': register,
            'value': value
        }
        self._send_command(command)

    def read_byte_data(self, address: int, register: int) -> int:
        """Read byte from register"""
        command = {
            'type': 'read_byte_data',
            'address': address,
            'register': register
        }
        response = self._send_command(command)
        return response['value']

    def write_word_data(self, address: int, register: int, value: int):
        """Write word to register"""
        command = {
            'type': 'write_word_data',
            'address': address,
            'register': register,
            'value': value
        }
        self._send_command(command)

    def read_word_data(self, address: int, register: int) -> int:
        """Read word from register"""
        command = {
            'type': 'read_word_data',
            'address': address,
            'register': register
        }
        response = self._send_command(command)
        return response['value']

    def write_i2c_block_data(self, address: int, register: int, data: List[int]):
        """Write block of data"""
        command = {
            'type': 'write_i2c_block_data',
            'address': address,
            'register': register,
            'data': data
        }
        self._send_command(command)

    def read_i2c_block_data(self, address: int, register: int, length: int) -> List[int]:
        """Read block of data"""
        command = {
            'type': 'read_i2c_block_data',
            'address': address,
            'register': register,
            'length': length
        }
        response = self._send_command(command)
        return response['data']

    def scan(self) -> List[int]:
        """Scan for I2C devices"""
        command = {'type': 'scan'}
        response = self._send_command(command)
        return response['devices']

    def reset_interface(self) -> str:
        """Reset the I2C interface on the remote server"""
        command = {'type': 'reset_interface'}
        response = self._send_command(command)
        if response.get('status') == 'success':
            return response.get('message', 'Interface reset successful')
        else:
            raise RuntimeError(response.get('message', 'Reset failed'))

    def close(self):
        """Close connection"""
        if self.socket:
            self.socket.close()
            self.socket = None

class SMBus(I2CClient):
    """SMBus-compatible interface for drop-in replacement"""

    def __init__(self, bus: int, host: str = 'localhost', port: int = 8888):
        # bus parameter is ignored for remote access
        super().__init__(host, port)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def main():
    import argparse

    parser = argparse.ArgumentParser(description='I2C Remote Client Test')
    parser.add_argument('--host', default='192.168.1.200', help='Server host (default: 192.168.1.200)')
    parser.add_argument('--port', type=int, default=8888, help='Server port (default: 8888)')
    parser.add_argument('--scan', action='store_true', help='Scan for I2C devices')
    parser.add_argument('--test', action='store_true', help='Run basic connectivity test')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    client = I2CClient(args.host, args.port)

    try:
        if args.scan:
            print("Scanning for I2C devices...")
            devices = client.scan()
            if devices:
                print(f"Found devices at addresses: {[hex(addr) for addr in devices]}")
            else:
                print("No I2C devices found")

        elif args.test:
            print("Testing I2C connectivity...")
            try:
                devices = client.scan()
                print(f"✓ Connected to server at {args.host}:{args.port}")
                print(f"✓ I2C bus accessible, found {len(devices)} devices")
            except Exception as e:
                print(f"✗ Test failed: {e}")

        else:
            print("Use --scan to scan for devices or --test for connectivity test")
            print(f"Server: {args.host}:{args.port}")

    finally:
        client.close()

if __name__ == '__main__':
    main()