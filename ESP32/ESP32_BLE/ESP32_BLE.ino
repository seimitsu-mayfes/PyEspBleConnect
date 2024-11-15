#include <BLEDevice.h>  // BLEデバイスの機能を使用するためのヘッダーファイル
#include <BLEServer.h>  // BLEサーバーの機能を使用するためのヘッダーファイル
#include <BLEUtils.h>   // BLEユーティリティ関数を使用するためのヘッダーファイル
#include <BLE2902.h>    // BLE通知記述子を使用するためのヘッダーファイル
#include "driver/mcpwm.h"
#define AVENUM 4
#define SWPIN 16
#define LEDPIN 15

volatile uint32_t aveInterval[4];
volatile uint16_t eventCount[4]={0, 0, 0, 0};

uint32_t initialInterval[4];
#define SERVICE_UUID        "55725ac1-066c-48b5-8700-2d9fb3603c5e"  // BLEサービスのUUID
#define CHARACTERISTIC_UUID "69ddb59c-d601-4ea4-ba83-44f679a670ba"  // BLEキャラクタリスティックのUUID
#define BLE_DEVICE_NAME     "MyBLEDevice"  // BLEデバイスの名前
#define LED_PIN             22  // LEDが接続されているピン番号
#define BUTTON_PIN          23  // ボタンが接続されているピン番号

BLEServer *pServer = NULL;  // BLEサーバーのポインタ
BLECharacteristic *pCharacteristic = NULL;  // BLEキャラクタリスティックのポインタ
bool deviceConnected = false;  // デバイスの接続状態
bool oldDeviceConnected = false;  // 前回のループでのデバイスの接続状態
String rxValue;  // 受信したデータを格納する変数
bool bleOn = false;  // LEDの状態を管理する変数
bool buttonPressed = false;  // ボタンの状態を管理する変数
int buttonCount = 0;  // ボタンが押された回数をカウントする変数

class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer *pServer) {  // デバイスが接続された時に呼ばれる関数
    deviceConnected = true;
    Serial.println("DEBUG: Device connected");
  }
  
  void onDisconnect(BLEServer *pServer) {  // デバイスが切断された時に呼ばれる関数
    deviceConnected = false;
    Serial.println("DEBUG: Device disconnected");
  }
};

class MyCharacteristicCallbacks: public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) {  // データが書き込まれた時に呼ばれる関数
    rxValue = pCharacteristic->getValue().c_str();  // 受信したデータを文字列として取得
    Serial.print("DEBUG: Received value: ");
    Serial.println(rxValue);
    
    if (rxValue.length() > 0) {  // 受信したデータが空でない場合
      if (rxValue == "00") {  // "00"を受信した場合
        bleOn = false;
      } else if (rxValue == "01") {  // "01"を受信した場合
        bleOn = true;
      } else {
        Serial.println("DEBUG: Unrecognized command");
      }
      Serial.print("DEBUG: LED State set to: ");
      Serial.println(bleOn ? "ON" : "OFF");
    }
  }
};

void setup() {
  pinMode(SWPIN, INPUT_PULLUP);
  pinMode(LEDPIN, OUTPUT);
  iCapSetup();
  Serial.begin(9600);

  pinMode(LED_PIN, OUTPUT);  // LEDピンを出力モードに設定
  pinMode(BUTTON_PIN, INPUT_PULLUP);  // ボタンピンをプルアップ入力モードに設定
  Serial.begin(115200);  // シリアル通信を開始
  Serial.println("DEBUG: Setup started");

  BLEDevice::init(BLE_DEVICE_NAME);  // BLEデバイスを初期化
  pServer = BLEDevice::createServer();  // BLEサーバーを作成
  pServer->setCallbacks(new MyServerCallbacks());  // サーバーコールバックを設定
  
  BLEService *pService = pServer->createService(SERVICE_UUID);  // BLEサービスを作成
  pCharacteristic = pService->createCharacteristic(  // BLEキャラクタリスティックを作成
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_NOTIFY 
  );
  
  pCharacteristic->setCallbacks(new MyCharacteristicCallbacks());  // キャラクタリスティックコールバックを設定
  pCharacteristic->addDescriptor(new BLE2902());  // 通知記述子を追加
  
  pService->start();  // サービスを開始
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();  // アドバタイジングオブジェクトを取得
  pAdvertising->addServiceUUID(SERVICE_UUID);  // サービスUUIDをアドバタイジングデータに追加
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x0);
  BLEDevice::startAdvertising();  // アドバタイジングを開始
  Serial.println("DEBUG: BLE Advertising started");
}

void loop() {
  if (!deviceConnected && oldDeviceConnected) {  // デバイスが切断された場合
    delay(500);  // Bluetoothスタックの準備のために少し待機
    pServer->startAdvertising();  // アドバタイジングを再開
    Serial.println("DEBUG: Restarting advertising");
    oldDeviceConnected = deviceConnected;
  }
  
  if (deviceConnected && !oldDeviceConnected) {  // デバイスが新たに接続された場合
    oldDeviceConnected = deviceConnected;
  }
  
  digitalWrite(LED_PIN, bleOn ? HIGH : LOW);  // LEDの状態を更新
  
  static unsigned long lastDebounceTime = 0;
  unsigned long debounceDelay = 50;  // デバウンス時間（ミリ秒）

  if (digitalRead(BUTTON_PIN) == LOW) {  // ボタンが押された場合
    if ((millis() - lastDebounceTime) > debounceDelay) {
      if (!buttonPressed) {  // ボタンが前回のループで押されていなかった場合
        buttonCount++;
        String str = "BTN:" + String(buttonCount);
        Serial.print("DEBUG: Button pressed. Count: ");
        Serial.println(buttonCount);

        if (deviceConnected) {  // デバイスが接続されている場合
          pCharacteristic->setValue(str.c_str());  // キャラクタリスティックの値を設定
          pCharacteristic->notify();  // 接続されているデバイスに通知
          Serial.println("DEBUG: Notification sent to client");
        }
        buttonPressed = true;
      }
      lastDebounceTime = millis();
    }
  } else {
    buttonPressed = false;  // ボタンが離された場合、状態をリセット
  }

  if(digitalRead(SWPIN)==0){
    for(int i=0; i<4; i++){
      initialInterval[i] = aveInterval[i];
    }
  }

  Serial.print(initialInterval[0]);
  Serial.print(" ");
  Serial.print(aveInterval[0]);
  Serial.print(" ");
  Serial.print(aveInterval[1]);
  Serial.print(" ");
  Serial.print(aveInterval[2]);
  Serial.print(" ");
  Serial.println(aveInterval[3]);

  if(aveInterval[0] > initialInterval[0]*1.5){
    digitalWrite(LEDPIN, HIGH);
  }else{
    digitalWrite(LEDPIN, LOW);
  }
  delay(100);
}