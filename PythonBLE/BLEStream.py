import asyncio
from bleak import BleakClient, BleakScanner
import numpy as np
import plotly.graph_objs as go
from dash import Dash, dcc, html
import dash.dependencies as dd
import threading
import time

# ESP32のBLEデバイス名
DEVICE_NAME = "MyBLEDevice"

# UUIDs
SERVICE_UUID = "55725ac1-066c-48b5-8700-2d9fb3603c5e"
CHARACTERISTIC_UUID = "69ddb59c-d601-4ea4-ba83-44f679a670ba"

# Dashアプリケーションの作成
app = Dash(__name__)

# グローバル変数
data_points = []  # BLEから受信したデータを格納するリスト
timestamps = []   # データ受信時刻を格納するリスト
duration = 10     # プロットする時間（秒）
graph_update_interval = 500  # グラフ更新間隔（ミリ秒）

# グラフレイアウトの設定
app.layout = html.Div([
    dcc.Graph(id='live-graph', animate=True),  # リアルタイムで更新されるグラフ
    dcc.Interval(
        id='graph-update',
        interval=graph_update_interval,  # グラフ更新の間隔を設定（ミリ秒）
        n_intervals=0  # 初期値として0を設定
    ),
    html.Div(id='time-display', style={'fontSize': 20})  # 現在時刻を表示するためのDiv
])



async def notification_handler(sender, data):
    """通知を処理するコールバック関数"""
    decoded_data = data.decode()
    if ':' in decoded_data:
        value = int(decoded_data.split(':')[1])  # コロンの後ろの数値部分を抽出して変換
    else:
        value = int(decoded_data)  # 数値のみの場合はそのまま変換
    current_time = time.time()

    print(f"\nReceived notification: {value}")
    
    # 最新のデータポイントとその受信時刻を保持するためにリストを更新
    data_points.append(value)
    timestamps.append(current_time)  # タイムスタンプも追加
    
    # データポイントの数が上限を超えた場合、古いデータを削除
    Max_data_number = 256
    while len(data_points) > Max_data_number:
        removed_value = data_points.pop(0)
        removed_timestamp = timestamps.pop(0)
        print(f"Removed data point: value={removed_value}, timestamp={removed_timestamp}")

    print(f"Current data points: {len(data_points)}")
    print(f"Current timestamps: {len(timestamps)}")
    
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
            await asyncio.Event().wait()  # 無限待機（他の処理が必要な場合はここで置き換える）
        except asyncio.CancelledError:
            pass

        await client.stop_notify(CHARACTERISTIC_UUID)

    print("Disconnected")

def run_asyncio():
    """非同期処理用の関数"""
    asyncio.run(main())  # mainコルーチンを実行

@app.callback(
    dd.Output('live-graph', 'figure'),  
    [dd.Input('graph-update', 'n_intervals')]  
)
def update_graph(n):
    """グラフを更新するコールバック関数"""
    current_time = time.time()
    
    figure = {
        'data': [go.Scatter(
            x=[t - current_time for t in timestamps],  # 現在時刻からduration秒前までの相対時間でプロット
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
                range=[0, 500000000]  # y軸の範囲を0から10000に固定
            )
        )
    }
    
    print(f"Updated graph with {len(data_points)} data points.")  # 更新されたグラフに関するログ
    
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
    data_thread = threading.Thread(target=run_asyncio)  # run_asyncio関数をスレッドで実行
    data_thread.daemon = True
    
    data_thread.start()  

    app.run_server(debug=True)  # Dashアプリケーションのサーバーを起動