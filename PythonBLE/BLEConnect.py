import asyncio
from bleak import BleakClient, BleakScanner

# ESP32のBLEデバイス名
DEVICE_NAME = "MyBLEDevice"

# UUIDs
SERVICE_UUID = "55725ac1-066c-48b5-8700-2d9fb3603c5e"
CHARACTERISTIC_UUID = "69ddb59c-d601-4ea4-ba83-44f679a670ba"

async def notification_handler(sender, data):
    """通知を処理するコールバック関数"""
    print(f"Received notification: {data.decode()}")

async def main():
    # デバイスをスキャン
    device = await BleakScanner.find_device_by_name(DEVICE_NAME)
    
    if not device:
        print(f"Could not find device with name '{DEVICE_NAME}'")
        return

    async with BleakClient(device) as client:
        print(f"Connected to {device.name}")

        # 通知を有効化
        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

        while True:
            command = input("Enter command (00: LED OFF, 01: LED ON, q: quit): ")
            
            if command.lower() == 'q':
                break
            elif command in ['00', '01']:
                # LEDの状態を変更
                await client.write_gatt_char(CHARACTERISTIC_UUID, command.encode())
                print(f"Sent command: {command}")
            else:
                print("Invalid command. Please enter 00, 01, or q.")

        # 通知を無効化
        await client.stop_notify(CHARACTERISTIC_UUID)

    print("Disconnected")

asyncio.run(main())