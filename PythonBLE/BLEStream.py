import asyncio
from bleak import BleakClient, BleakScanner
import numpy as np
import plotly.graph_objs as go
from dash import Dash, dcc, html
import dash.dependencies as dd
import threading
import time
import queue

# ESP32のBLEデバイス名
DEVICE_NAME = "MyBLEDevice"

# UUIDs
SERVICE_UUID = "55725ac1-066c-48b5-8700-2d9fb3603c5e"
CHARACTERISTIC_UUID = "69ddb59c-d601-4ea4-ba83-44f679a670ba"

# Dashアプリケーションの作成
app = Dash(__name__)

# グローバル変数
data_queue = queue.Queue()  # スレッド間でデータを安全に受け渡すためのキュー
duration = 10     # プロットする時間（秒）
graph_update_interval = 500  # グラフ更新間隔（ミリ秒）

# グラフレイアウトの設定
app.layout = html.Div([
    dcc.Graph(id='live-graph', animate=True),
    dcc.Interval(
        id='graph-update',
        interval=graph_update_interval,
        n_intervals=0
    ),
    html.Div(id='time-display', style={'fontSize': 20})
])

async def notification_handler(sender, data):
    decoded_data = data.decode()
    if ':' in decoded_data:
        value = int(decoded_data.split(':')[1])  # コロンの後ろの数値部分を抽出して変換
    else:
        value = int(decoded_data)  # 数値のみの場合はそのまま変換
    current_time = time.time()
    data_queue.put((value, current_time))  # この行を追加
    print(f"\nReceived notification: {value}")

async def main():
    """BLEデバイスに接続し、通知を受信するメイン関数"""
    device = await BleakScanner.find_device_by_name(DEVICE_NAME)
    
    if not device:
        print(f"Could not find device with name '{DEVICE_NAME}'")
        return

    async with BleakClient(device) as client:
        print(f"Connected to {device.name}")

        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pass

        await client.stop_notify(CHARACTERISTIC_UUID)

    print("Disconnected")

def run_asyncio():
    """非同期処理用の関数"""
    asyncio.run(main())

# データ処理用のグローバル変数
data_points = []
timestamps = []

def process_data():
    """データ処理用の関数"""
    while True:
        try:
            value, timestamp = data_queue.get(timeout=1)
            data_points.append(value)
            timestamps.append(timestamp)
            print(f"Added data point: {value} at {timestamp}")  # この行を追加

            current_time = time.time()
            cutoff_time = current_time - duration

            while len(timestamps) > 0 and timestamps[0] < cutoff_time:
                data_points.pop(0)
                timestamps.pop(0)

        except queue.Empty:
            pass

@app.callback(
    dd.Output('live-graph', 'figure'),  
    [dd.Input('graph-update', 'n_intervals')]  
)
def update_graph(n):
    """グラフを更新するコールバック関数"""
    current_time = time.time()
    
    figure = {
        'data': [go.Scatter(
            x=[t - current_time for t in timestamps],
            y=data_points,
            mode='lines+markers',
            name='BLE Data'
        )],
        'layout': go.Layout(
            title='Real-time BLE Data',
            xaxis=dict(
                title='Time (s)',
                range=[-duration, 0],
                dtick=1,
                tickformat="%H:%M:%S",
            ),
            yaxis=dict(
                title='Value',
                range=[0, 100000]  # y軸の範囲を0から100000に設定（必要に応じて調整）
            )
        )
    }
    
    print(f"Updated graph with {len(data_points)} data points.")
    
    return figure

@app.callback(
    dd.Output('time-display', 'children'),  
    [dd.Input('graph-update', 'n_intervals')]  
)
def update_time_display(n):
    """現在時刻を表示するコールバック関数"""
    current_time = time.time()  
    
    seconds_since_epoch = int(current_time) % 60  
    minutes_since_epoch = (int(current_time) // 60) % 60  
    hours_since_epoch = (int(current_time) // 3600) % 24  
    
    elapsed_time = current_time % 1  
    milliseconds = int(elapsed_time * 1000)

    formatted_time = f"{hours_since_epoch}時{minutes_since_epoch}分{seconds_since_epoch}秒.{milliseconds:03d}"  
    
    return f'Current Time: {formatted_time}'

if __name__ == '__main__':
    ble_thread = threading.Thread(target=run_asyncio)
    ble_thread.daemon = True
    ble_thread.start()

    data_process_thread = threading.Thread(target=process_data)
    data_process_thread.daemon = True
    data_process_thread.start()

    app.run_server(debug=True)