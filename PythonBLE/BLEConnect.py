import asyncio
from bleak import BleakClient, BleakScanner
import aioconsole

# ESP32のBLEデバイス名
DEVICE_NAME = "MyBLEDevice"

# UUIDs
SERVICE_UUID = "55725ac1-066c-48b5-8700-2d9fb3603c5e"
CHARACTERISTIC_UUID = "69ddb59c-d601-4ea4-ba83-44f679a670ba"

async def notification_handler(sender, data):
    """通知を処理するコールバック関数"""
    print(f"\nReceived notification: {data.decode()}")
    #print("Enter command (00: LED OFF, 01: LED ON, q: quit): ", end='', flush=True)

async def user_input(client):
    while True:
        #command = await aioconsole.ainput("Enter command (00: LED OFF, 01: LED ON, q: quit): ")
        command = await aioconsole.ainput("")
        if command.lower() == 'q':
            return False
        elif command in ['00', '01']:
            await client.write_gatt_char(CHARACTERISTIC_UUID, command.encode())
            print(f"Sent command: {command}")
        else:
            print("Invalid command. Please enter 00, 01, or q.")

async def main():
    device = await BleakScanner.find_device_by_name(DEVICE_NAME)
    
    if not device:
        print(f"Could not find device with name '{DEVICE_NAME}'")
        return

    async with BleakClient(device) as client:
        print(f"Connected to {device.name}")

        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

        try:
            await user_input(client)
        except asyncio.CancelledError:
            pass

        await client.stop_notify(CHARACTERISTIC_UUID)

    print("Disconnected")

asyncio.run(main())