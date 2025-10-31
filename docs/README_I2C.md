# Remote I2C Access System

This system allows you to access I2C devices on a remote target (like BeagleBone Black) from your local Linux machine seamlessly.

## Architecture

```
Local Machine                    Remote Target (BeagleBone)
┌─────────────────┐             ┌─────────────────┐
│   Program       │             │   I2C Server    │
│   (Python/C)    │◄────────────►│   (i2c_server.py)
│                 │             │                 │
│ Virtual I2C Bus │             │ Physical I2C Bus│
│ (/dev/i2c-*)    │             │ (/dev/i2c-1)    │
└─────────────────┘             └─────────────────┘
        ▲                               ▲
        │                               │
        └───────────────────────────────┘
                I2C Devices
```

## Components

### 1. I2C Server (`i2c_server.py`)
- Runs on the remote target (BeagleBone)
- Provides network interface to I2C bus
- Supports all standard SMBus operations

### 2. I2C Client (`i2c_client.py`)
- Provides local I2C interface
- Forwards requests to remote server
- Compatible with smbus2 library

### 3. Virtual I2C Device (`virtual_i2c.py`)
- Creates virtual I2C bus for seamless access
- Programs can use standard I2C interfaces
- Drop-in replacement for local I2C

### 4. Examples (`i2c_example.py`)
- Demonstrates usage with common I2C devices
- BMP280 sensor and EEPROM examples

## Setup Instructions

### Step 1: Install Dependencies

On both local machine and remote target:

```bash
pip3 install smbus2
```

### Step 2: Start I2C Server on Remote Target

On the BeagleBone (192.168.1.200):

```bash
python3 i2c_server.py --host 0.0.0.0 --port 8888 --bus 1
```

Or run in background:

```bash
nohup python3 i2c_server.py &
```

### Step 3: Test Connection from Local Machine

```bash
# Test basic connectivity
python3 i2c_client.py --host 192.168.1.200 --test

# Scan for I2C devices
python3 i2c_client.py --host 192.168.1.200 --scan
```

### Step 4: Use Virtual I2C Device

```bash
# Create virtual I2C device
python3 virtual_i2c.py --demo

# Or run examples
python3 i2c_example.py
python3 i2c_example.py --sensor
python3 i2c_example.py --eeprom
```

## Usage Examples

### Basic I2C Operations

```python
from virtual_i2c import VirtualSMBus

# Connect to remote I2C bus
with VirtualSMBus(bus=0, host='192.168.1.200', port=8888) as bus:
    # Scan for devices
    devices = bus.scan()
    print(f"Found devices: {[hex(addr) for addr in devices]}")

    # Read from device
    if devices:
        value = bus.read_byte(devices[0])
        print(f"Read: 0x{value:02x}")

        # Read from register
        reg_value = bus.read_byte_data(devices[0], 0)
        print(f"Register 0: 0x{reg_value:02x}")
```

### Drop-in Replacement

The `VirtualSMBus` class is compatible with existing smbus2 code:

```python
import smbus2
from virtual_i2c import VirtualSMBus

# Replace: bus = smbus2.SMBus(1)
bus = VirtualSMBus(1, host='192.168.1.200')

# Rest of your code works unchanged!
with bus:
    bus.write_byte_data(0x50, 0, 0x55)
    value = bus.read_byte_data(0x50, 0)
```

## Supported I2C Operations

- `write_byte(address, value)` - Write byte to device
- `read_byte(address)` - Read byte from device
- `write_byte_data(address, register, value)` - Write to register
- `read_byte_data(address, register)` - Read from register
- `write_word_data(address, register, value)` - Write word to register
- `read_word_data(address, register)` - Read word from register
- `write_i2c_block_data(address, register, data)` - Write block
- `read_i2c_block_data(address, register, length)` - Read block
- `scan()` - Scan for I2C devices

## Configuration

### Server Options

```bash
python3 i2c_server.py --help
# --host HOST        Server host (default: 0.0.0.0)
# --port PORT        Server port (default: 8888)
# --bus BUS          I2C bus number (default: 1)
# --verbose, -v      Enable verbose logging
```

### Client Options

```bash
python3 i2c_client.py --help
# --host HOST        Server host (default: 192.168.1.200)
# --port PORT        Server port (default: 8888)
# --scan             Scan for I2C devices
# --test             Run connectivity test
# --verbose, -v      Enable verbose logging
```

### Virtual Device Options

```bash
python3 virtual_i2c.py --help
# --device DEVICE    Virtual device path (default: /dev/i2c-virtual)
# --host HOST        Remote server host (default: 192.168.1.200)
# --port PORT        Remote server port (default: 8888)
# --demo             Run demonstration
# --verbose, -v      Enable verbose logging
```

## Troubleshooting

### Connection Issues

1. Check if I2C server is running on remote target
2. Verify network connectivity between machines
3. Check firewall settings (port 8888)

### I2C Device Issues

1. Verify devices are connected to remote target's I2C bus
2. Check device addresses and power
3. Use `--scan` to verify device detection

### Permission Issues

1. Ensure user has access to I2C bus on remote target
2. Check device permissions if using virtual device

## Security Notes

- This system transmits I2C data over network unencrypted
- Use only on trusted networks
- Consider adding authentication/encryption for production use
- The server accepts connections from any host by default

## Performance

- Network latency adds ~1-5ms to each I2C operation
- Suitable for most sensor and control applications
- Not recommended for high-speed or real-time critical applications

## Integration with Yocto

To integrate with your Yocto build system:

1. Add the Python scripts to your image
2. Install smbus2 in the target image
3. Configure systemd service for automatic startup
4. Add network configuration for communication

See the recipes in `recipes-srk/` for examples of Yocto integration.

## Components

### 1. I2C Server (`i2c_server.py`)

- Runs on the remote target (BeagleBone)
- Provides network interface to I2C bus
- Supports all standard SMBus operations

### 2. I2C Client (`i2c_client.py`)

- Provides local I2C interface
- Forwards requests to remote server
- Compatible with smbus2 library

### 3. Virtual I2C Device (`virtual_i2c.py`)

- Creates virtual I2C bus for seamless access
- Programs can use standard I2C interfaces
- Drop-in replacement for local I2C

### 4. Examples (`i2c_example.py`)

- Demonstrates usage with common I2C devices
- BMP280 sensor and EEPROM examples

## Setup Instructions

### Step 1: Install Dependencies

On both local machine and remote target:

```bash
pip3 install smbus2
```

### Step 2: Start I2C Server on Remote Target

On the BeagleBone (192.168.1.200):

```bash
python3 i2c_server.py --host 0.0.0.0 --port 8888 --bus 1
```

Or run in background:

```bash
nohup python3 i2c_server.py &
```

### Step 3: Test Connection from Local Machine

```bash
# Test basic connectivity
python3 i2c_client.py --host 192.168.1.200 --test

# Scan for I2C devices
python3 i2c_client.py --host 192.168.1.200 --scan
```

### Step 4: Use Virtual I2C Device

```bash
# Create virtual I2C device
python3 virtual_i2c.py --demo

# Or run examples
python3 i2c_example.py
python3 i2c_example.py --sensor
python3 i2c_example.py --eeprom
```

## Usage Examples

### Basic I2C Operations

```python
from virtual_i2c import VirtualSMBus

# Connect to remote I2C bus
with VirtualSMBus(bus=0, host='192.168.1.200', port=8888) as bus:
    # Scan for devices
    devices = bus.scan()
    print(f"Found devices: {[hex(addr) for addr in devices]}")

    # Read from device
    if devices:
        value = bus.read_byte(devices[0])
        print(f"Read: 0x{value:02x}")

        # Read from register
        reg_value = bus.read_byte_data(devices[0], 0)
        print(f"Register 0: 0x{reg_value:02x}")
```

### Drop-in Replacement

The `VirtualSMBus` class is compatible with existing smbus2 code:

```python
import smbus2
from virtual_i2c import VirtualSMBus

# Replace: bus = smbus2.SMBus(1)
bus = VirtualSMBus(1, host='192.168.1.200')

# Rest of your code works unchanged!
with bus:
    bus.write_byte_data(0x50, 0, 0x55)
    value = bus.read_byte_data(0x50, 0)
```

## Supported I2C Operations

- `write_byte(address, value)` - Write byte to device
- `read_byte(address)` - Read byte from device
- `write_byte_data(address, register, value)` - Write to register
- `read_byte_data(address, register)` - Read from register
- `write_word_data(address, register, value)` - Write word to register
- `read_word_data(address, register)` - Read word from register
- `write_i2c_block_data(address, register, data)` - Write block
- `read_i2c_block_data(address, register, length)` - Read block
- `scan()` - Scan for I2C devices

## Configuration

### Server Options

```bash
python3 i2c_server.py --help
# --host HOST        Server host (default: 0.0.0.0)
# --port PORT        Server port (default: 8888)
# --bus BUS          I2C bus number (default: 1)
# --verbose, -v      Enable verbose logging
```

### Client Options

```bash
python3 i2c_client.py --help
# --host HOST        Server host (default: 192.168.1.200)
# --port PORT        Server port (default: 8888)
# --scan             Scan for I2C devices
# --test             Run connectivity test
# --verbose, -v      Enable verbose logging
```

### Virtual Device Options

```bash
python3 virtual_i2c.py --help
# --device DEVICE    Virtual device path (default: /dev/i2c-virtual)
# --host HOST        Remote server host (default: 192.168.1.200)
# --port PORT        Remote server port (default: 8888)
# --demo             Run demonstration
# --verbose, -v      Enable verbose logging
```

## Troubleshooting

### Connection Issues

1. Check if I2C server is running on remote target
2. Verify network connectivity between machines
3. Check firewall settings (port 8888)

### I2C Device Issues

1. Verify devices are connected to remote target's I2C bus
2. Check device addresses and power
3. Use `--scan` to verify device detection

### Permission Issues

1. Ensure user has access to I2C bus on remote target
2. Check device permissions if using virtual device

## Security Notes

- This system transmits I2C data over network unencrypted
- Use only on trusted networks
- Consider adding authentication/encryption for production use
- The server accepts connections from any host by default

## Performance

- Network latency adds ~1-5ms to each I2C operation
- Suitable for most sensor and control applications
- Not recommended for high-speed or real-time critical applications

## Integration with Yocto

To integrate with your Yocto build system:

1. Add the Python scripts to your image
2. Install smbus2 in the target image
3. Configure systemd service for automatic startup
4. Add network configuration for communication

See the recipes in `recipes-srk/` for examples of Yocto integration.

## Components

### 1. I2C Server (`i2c_server.py`)
- Runs on the remote target (BeagleBone)
- Provides network interface to I2C bus
- Supports all standard SMBus operations

### 2. I2C Client (`i2c_client.py`)
- Provides local I2C interface
- Forwards requests to remote server
- Compatible with smbus2 library

### 3. Virtual I2C Device (`virtual_i2c.py`)
- Creates virtual I2C bus for seamless access
- Programs can use standard I2C interfaces
- Drop-in replacement for local I2C

### 4. Examples (`i2c_example.py`)
- Demonstrates usage with common I2C devices
- BMP280 sensor and EEPROM examples

## Setup Instructions

### Step 1: Install Dependencies

On both local machine and remote target:
```bash
pip3 install smbus2
```

### Step 2: Start I2C Server on Remote Target

On the BeagleBone (192.168.1.200):
```bash
python3 i2c_server.py --host 0.0.0.0 --port 8888 --bus 1
```

Or run in background:
```bash
nohup python3 i2c_server.py &
```

### Step 3: Test Connection from Local Machine

```bash
# Test basic connectivity
python3 i2c_client.py --host 192.168.1.200 --test

# Scan for I2C devices
python3 i2c_client.py --host 192.168.1.200 --scan
```

### Step 4: Use Virtual I2C Device

```bash
# Create virtual I2C device
python3 virtual_i2c.py --demo

# Or run examples
python3 i2c_example.py
python3 i2c_example.py --sensor
python3 i2c_example.py --eeprom
```

## Usage Examples

### Basic I2C Operations

```python
from virtual_i2c import VirtualSMBus

# Connect to remote I2C bus
with VirtualSMBus(bus=0, host='192.168.1.200', port=8888) as bus:
    # Scan for devices
    devices = bus.scan()
    print(f"Found devices: {[hex(d) for d in devices]}")

    # Read from device
    if devices:
        value = bus.read_byte(devices[0])
        print(f"Read: 0x{value:02x}")

        # Read from register
        reg_value = bus.read_byte_data(devices[0], 0)
        print(f"Register 0: 0x{reg_value:02x}")
```

### Drop-in Replacement

The `VirtualSMBus` class is compatible with existing smbus2 code:

```python
import smbus2
from virtual_i2c import VirtualSMBus

# Replace: bus = smbus2.SMBus(1)
bus = VirtualSMBus(1, host='192.168.1.200')

# Rest of your code works unchanged!
with bus:
    bus.write_byte_data(0x50, 0, 0x55)
    value = bus.read_byte_data(0x50, 0)
```

## Supported I2C Operations

- `write_byte(address, value)` - Write byte to device
- `read_byte(address)` - Read byte from device
- `write_byte_data(address, register, value)` - Write to register
- `read_byte_data(address, register)` - Read from register
- `write_word_data(address, register, value)` - Write word to register
- `read_word_data(address, register)` - Read word from register
- `write_i2c_block_data(address, register, data)` - Write block
- `read_i2c_block_data(address, register, length)` - Read block
- `scan()` - Scan for I2C devices

## Configuration

### Server Options
```bash
python3 i2c_server.py --help
# --host HOST        Server host (default: 0.0.0.0)
# --port PORT        Server port (default: 8888)
# --bus BUS          I2C bus number (default: 1)
# --verbose, -v      Enable verbose logging
```

### Client Options
```bash
python3 i2c_client.py --help
# --host HOST        Server host (default: 192.168.1.200)
# --port PORT        Server port (default: 8888)
# --scan             Scan for I2C devices
# --test             Run connectivity test
# --verbose, -v      Enable verbose logging
```

### Virtual Device Options
```bash
python3 virtual_i2c.py --help
# --device DEVICE    Virtual device path (default: /dev/i2c-virtual)
# --host HOST        Remote server host (default: 192.168.1.200)
# --port PORT        Remote server port (default: 8888)
# --demo             Run demonstration
# --verbose, -v      Enable verbose logging
```

## Troubleshooting

### Connection Issues
1. Check if I2C server is running on remote target
2. Verify network connectivity between machines
3. Check firewall settings (port 8888)

### I2C Device Issues
1. Verify devices are connected to remote target's I2C bus
2. Check device addresses and power
3. Use `--scan` to verify device detection

### Permission Issues
1. Ensure user has access to I2C bus on remote target
2. Check device permissions if using virtual device

## Security Notes

- This system transmits I2C data over network unencrypted
- Use only on trusted networks
- Consider adding authentication/encryption for production use
- The server accepts connections from any host by default

## Performance

- Network latency adds ~1-5ms to each I2C operation
- Suitable for most sensor and control applications
- Not recommended for high-speed or real-time critical applications

## Integration with Yocto

To integrate with your Yocto build system:

1. Add the Python scripts to your image
2. Install smbus2 in the target image
3. Configure systemd service for automatic startup
4. Add network configuration for communication

See the recipes in `recipes-srk/` for examples of Yocto integration.