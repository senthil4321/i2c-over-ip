#!/usr/bin/env python3
"""
Example: Using Virtual I2C Device
Demonstrates how to access remote I2C devices seamlessly.
"""

from virtual_i2c import VirtualSMBus
import time

def main():
    print("Virtual I2C Device Example")
    print("=" * 40)

    # Connect to virtual I2C bus (forwards to remote server)
    try:
        with VirtualSMBus(bus=0, host='192.168.1.200', port=8888) as bus:
            print("✓ Connected to virtual I2C bus")

            # Scan for devices
            print("\nScanning for I2C devices...")
            devices = bus.scan()
            print(f"Found {len(devices)} devices: {[hex(addr) for addr in devices]}")

            if not devices:
                print("No I2C devices found. Make sure devices are connected to remote target.")
                return

            # Test with first device found
            device_addr = devices[0]
            print(f"\nTesting device at address 0x{device_addr:02x}")

            try:
                # Try to read a byte (device-specific)
                value = bus.read_byte(device_addr)
                print(f"✓ Read byte: 0x{value:02x}")

                # Try to read from register 0 (common for many devices)
                reg_value = bus.read_byte_data(device_addr, 0)
                print(f"✓ Read register 0: 0x{reg_value:02x}")

                # Write to register (be careful with this!)
                # bus.write_byte_data(device_addr, 0, 0x55)
                # print("✓ Wrote 0x55 to register 0")

            except Exception as e:
                print(f"⚠ Device communication failed: {e}")
                print("This is normal if the device requires specific initialization.")

    except Exception as e:
        print(f"✗ Failed to connect to virtual I2C bus: {e}")
        print("Make sure the I2C server is running on the remote target.")

def sensor_example():
    """Example for a common I2C sensor (BMP280 temperature/pressure sensor)"""
    print("\nBMP280 Sensor Example")
    print("=" * 30)

    try:
        with VirtualSMBus(bus=0, host='192.168.1.200', port=8888) as bus:
            BMP280_ADDR = 0x76  # or 0x77

            # Read chip ID (should be 0x58 for BMP280)
            chip_id = bus.read_byte_data(BMP280_ADDR, 0xD0)
            print(f"BMP280 Chip ID: 0x{chip_id:02x}")

            if chip_id == 0x58:
                print("✓ BMP280 sensor detected!")

                # Read temperature (simplified - actual implementation needs calibration)
                # This is just a demonstration
                temp_msb = bus.read_byte_data(BMP280_ADDR, 0xFA)
                temp_lsb = bus.read_byte_data(BMP280_ADDR, 0xFB)
                temp_xlsb = bus.read_byte_data(BMP280_ADDR, 0xFC)

                raw_temp = (temp_msb << 12) | (temp_lsb << 4) | (temp_xlsb >> 4)
                print(f"Raw temperature reading: {raw_temp}")
            else:
                print("⚠ BMP280 not found at expected address")

    except Exception as e:
        print(f"✗ Sensor example failed: {e}")

def eeprom_example():
    """Example for I2C EEPROM (24LC256 or similar)"""
    print("\nEEPROM Example (24LC256)")
    print("=" * 30)

    try:
        with VirtualSMBus(bus=0, host='192.168.1.200', port=8888) as bus:
            EEPROM_ADDR = 0x50

            # Write some test data
            test_data = [0x48, 0x65, 0x6C, 0x6C, 0x6F]  # "Hello"
            bus.write_i2c_block_data(EEPROM_ADDR, 0x00, test_data)
            print("✓ Wrote test data to EEPROM")

            # Wait for write to complete
            time.sleep(0.01)

            # Read back the data
            read_data = bus.read_i2c_block_data(EEPROM_ADDR, 0x00, len(test_data))
            print(f"✓ Read back: {[hex(b) for b in read_data]}")

            if read_data == test_data:
                print("✓ Data integrity verified!")
            else:
                print("⚠ Data mismatch!")

    except Exception as e:
        print(f"✗ EEPROM example failed: {e}")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Virtual I2C Examples')
    parser.add_argument('--sensor', action='store_true', help='Run BMP280 sensor example')
    parser.add_argument('--eeprom', action='store_true', help='Run EEPROM example')

    args = parser.parse_args()

    main()

    if args.sensor:
        sensor_example()

    if args.eeprom:
        eeprom_example()