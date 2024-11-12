#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define SERVICE_UUID        "55725ac1-066c-48b5-8700-2d9fb3603c5e"
#define CHARACTERISTIC_UUID "69ddb59c-d601-4ea4-ba83-44f679a670ba"
#define BLE_DEVICE_NAME     "MyBLEDevice"
#define LED_PIN             22
#define BUTTON_PIN          23

BLEServer *pServer = NULL;
BLECharacteristic *pCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;
String rxValue;
String txValue;
bool bleOn = false;
bool buttonPressed = false;
int buttonCount = 0;

class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer *pServer) {
    deviceConnected = true;
    Serial.println("DEBUG: Device connected");
  }
  
  void onDisconnect(BLEServer *pServer) {
    deviceConnected = false;
    Serial.println("DEBUG: Device disconnected");
  }
};

class MyCharacteristicCallbacks: public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) {
    rxValue = pCharacteristic->getValue().c_str();
    if (rxValue.length() > 0) {
      bleOn = (rxValue[0] != '0');
      Serial.print("DEBUG: Received Value: ");
      Serial.println(rxValue);
      Serial.print("DEBUG: LED State: ");
      Serial.println(bleOn ? "ON" : "OFF");
    }
  }
};

void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  Serial.begin(115200);
  Serial.println("DEBUG: Setup started");

  BLEDevice::init(BLE_DEVICE_NAME);
  Serial.println("DEBUG: BLE Device initialized");
  
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());
  Serial.println("DEBUG: BLE Server created");
  
  BLEService *pService = pServer->createService(SERVICE_UUID);
  Serial.println("DEBUG: BLE Service created");
  
  pCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_WRITE | 
    BLECharacteristic::PROPERTY_NOTIFY 
  );
  
  pCharacteristic->setCallbacks(new MyCharacteristicCallbacks());
  pCharacteristic->addDescriptor(new BLE2902());
  Serial.println("DEBUG: BLE Characteristic created");
  
  pService->start();
  Serial.println("DEBUG: BLE Service started");
  
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x0);
  
  BLEDevice::startAdvertising();
  Serial.println("DEBUG: BLE Advertising started");
}

void loop() {
  if (!deviceConnected && oldDeviceConnected) {
    delay(500);
    pServer->startAdvertising();
    Serial.println("DEBUG: Restarting advertising");
    oldDeviceConnected = deviceConnected;
  }
  
  if (deviceConnected && !oldDeviceConnected) {
    Serial.println("DEBUG: Device connection status changed");
    oldDeviceConnected = deviceConnected;
  }
  
  digitalWrite(LED_PIN, bleOn ? HIGH : LOW);
  
  if (digitalRead(BUTTON_PIN) == LOW) {
    if (!buttonPressed) {
      buttonCount++;
      String str = "BTN:" + String(buttonCount);
      Serial.print("DEBUG: Button pressed. Count: ");
      Serial.println(buttonCount);

      if (deviceConnected) {
        txValue = str;
        pCharacteristic->setValue(txValue);
        pCharacteristic->notify();
        Serial.println("DEBUG: Notification sent to client");
      }
      buttonPressed = true;
      delay(50);
    }
  } else {
    if (buttonPressed) {
      buttonPressed = false;
      delay(50);
    }
  }
}