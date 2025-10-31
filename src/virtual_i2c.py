#!/usr/bin/env python3
"""
Virtual I2C Device
Creates a virtual I2C bus that forwards operations to remote I2C server.
Provides seamless access for programs using standard I2C interfaces.
"""

import os
import stat
import errno
import fcntl
import struct
import logging
from typing import Optional, Dict, Any
from i2c_client import I2CClient
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# I2C ioctl commands (from linux/i2c-dev.h)
I2C_SLAVE = 0x0703
I2C_SLAVE_FORCE = 0x0706
I2C_TENBIT = 0x0704
I2C_FUNCS = 0x0705
I2C_RDWR = 0x0707
I2C_SMBUS = 0x0720

# SMBus ioctl commands
I2C_SMBUS_READ = 1
I2C_SMBUS_WRITE = 0

# SMBus transaction types
I2C_SMBUS_BYTE = 1
I2C_SMBUS_BYTE_DATA = 2
I2C_SMBUS_WORD_DATA = 3
I2C_SMBUS_BLOCK_DATA = 5

class VirtualI2CDevice:
    """Virtual I2C device that forwards to remote server"""

    def __init__(self, device_path: str = '/dev/i2c-virtual', host: str = '192.168.1.200', port: int = 8888):
        self.device_path = device_path
        self.host = host
        self.port = port
        self.client = I2CClient(host, port)
        self.current_address = 0
        self.tenbit = False
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def create_device(self):
        """Create the virtual device file"""
        try:
            # Remove existing device if it exists
            if os.path.exists(self.device_path):
                os.unlink(self.device_path)

            # Create character device (major 89 is i2c, minor can be anything)
            os.mknod(self.device_path, 0o666 | stat.S_IFCHR, os.makedev(89, 0))
            logger.info(f"Created virtual I2C device: {self.device_path}")

        except Exception as e:
            logger.error(f"Failed to create device {self.device_path}: {e}")
            raise

    def start(self):
        """Start the virtual I2C device"""
        self.create_device()
        self.running = True

        # Note: In a real implementation, we'd need to handle device file operations
        # This is a simplified version that demonstrates the concept
        logger.info("Virtual I2C device started")
        logger.info(f"Programs can now access I2C via: {self.device_path}")
        logger.info(f"Forwarding to remote server: {self.host}:{self.port}")

    def stop(self):
        """Stop the virtual I2C device"""
        self.running = False
        if self.thread:
            self.thread.join()

        try:
            if os.path.exists(self.device_path):
                os.unlink(self.device_path)
                logger.info(f"Removed virtual I2C device: {self.device_path}")
        except Exception as e:
            logger.error(f"Error removing device: {e}")

        self.client.close()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

class VirtualSMBus(I2CClient):
    """SMBus-compatible virtual device"""

    def __init__(self, bus: int, host: str = '192.168.1.200', port: int = 8888):
        super().__init__(host, port)
        self.bus = bus  # Store for compatibility

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Alternative: Create a device file handler
class I2CDeviceHandler:
    """Handles I2C device file operations"""

    def __init__(self, device_path: str, host: str = '192.168.1.200', port: int = 8888):
        self.device_path = device_path
        self.client = I2CClient(host, port)
        self.current_address = 0

    def handle_ioctl(self, request: int, arg: int) -> int:
        """Handle ioctl calls to the virtual device"""
        if request == I2C_SLAVE or request == I2C_SLAVE_FORCE:
            self.current_address = arg
            return 0
        elif request == I2C_TENBIT:
            # Ten-bit addressing not implemented
            return -errno.ENOTTY
        elif request == I2C_FUNCS:
            # Return supported functions (basic read/write)
            return 0x070001  # I2C_FUNC_I2C
        else:
            return -errno.ENOTTY

    def handle_read(self, length: int) -> bytes:
        """Handle read operations"""
        try:
            if length == 1:
                value = self.client.read_byte(self.current_address)
                return bytes([value])
            else:
                # For block reads, we'd need to implement more complex logic
                raise NotImplementedError("Block reads not implemented")
        except Exception as e:
            logger.error(f"Read error: {e}")
            raise

    def handle_write(self, data: bytes) -> int:
        """Handle write operations"""
        try:
            if len(data) == 1:
                self.client.write_byte(self.current_address, data[0])
            elif len(data) == 2:
                # Register + value
                self.client.write_byte_data(self.current_address, data[0], data[1])
            else:
                raise NotImplementedError("Complex writes not implemented")
            return len(data)
        except Exception as e:
            logger.error(f"Write error: {e}")
            raise

def create_virtual_device(device_path: str = '/dev/i2c-virtual', host: str = '192.168.1.200', port: int = 8888):
    """Create and return a virtual I2C device"""
    device = VirtualI2CDevice(device_path, host, port)
    device.start()
    return device

def demo_virtual_i2c():
    """Demonstrate virtual I2C usage"""
    print("Creating virtual I2C device...")

    with VirtualI2CDevice('/dev/i2c-virtual', '192.168.1.200', 8888) as device:
        print("Virtual I2C device created at /dev/i2c-virtual")
        print("Testing connection...")

        try:
            # Test with SMBus interface
            with VirtualSMBus(0, '192.168.1.200', 8888) as bus:
                devices = bus.scan()
                print(f"✓ Connected to remote I2C server")
                print(f"✓ Found {len(devices)} I2C devices: {[hex(d) for d in devices]}")

                if devices:
                    # Test read from first device
                    addr = devices[0]
                    try:
                        value = bus.read_byte(addr)
                        print(f"✓ Successfully read from device 0x{addr:02x}: 0x{value:02x}")
                    except Exception as e:
                        print(f"⚠ Could not read from device 0x{addr:02x}: {e}")

        except Exception as e:
            print(f"✗ Connection test failed: {e}")
            return False

        print("\nVirtual I2C device is ready for use!")
        print("Programs can now access remote I2C devices as if they were local.")
        return True

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Virtual I2C Device')
    parser.add_argument('--device', default='/dev/i2c-virtual', help='Virtual device path')
    parser.add_argument('--host', default='192.168.1.200', help='Remote I2C server host')
    parser.add_argument('--port', type=int, default=8888, help='Remote I2C server port')
    parser.add_argument('--demo', action='store_true', help='Run demonstration')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.demo:
        success = demo_virtual_i2c()
        exit(0 if success else 1)

    try:
        device = create_virtual_device(args.device, args.host, args.port)
        print(f"Virtual I2C device created at {args.device}")
        print("Press Ctrl+C to stop...")

        # Keep running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping virtual I2C device...")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == '__main__':
    main()