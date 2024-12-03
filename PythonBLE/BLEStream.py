import asyncio
from bleak import BleakClient, BleakScanner
import aioconsole
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
duration = 10  # プロットする時間（秒）
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
    value = int.from_bytes(data, byteorder='little')  # 受信データを整数に変換
    print(f"\nReceived notification: {value}")
    
    # 最新のデータポイントを保持するためにリストを更新
    data_points.append(value)
    
    # 現在時刻からduration秒前までのデータのみ保持するロジック
    if len(data_points) > duration * (1000 / graph_update_interval):  # データポイント数が制限を超えた場合
        removed_value = data_points.pop(0)  # 古いデータポイントを削除
        print(f"Removed data point: {removed_value}")  # 削除したデータポイントのログ

async def main():
    device = await BleakScanner.find_device_by_name(DEVICE_NAME)
    
    if not device:
        print(f"Could not find device with name '{DEVICE_NAME}'")
        return

    async with BleakClient(device) as client:
        print(f"Connected to {device.name}")

        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

        try:
            await asyncio.Event().wait()  # 無限待機（実際には他の処理が必要な場合に置き換えてください）
        except asyncio.CancelledError:
            pass

        await client.stop_notify(CHARACTERISTIC_UUID)

    print("Disconnected")

@app.callback(
    dd.Output('live-graph', 'figure'),  
    [dd.Input('graph-update', 'n_intervals')]  
)
def update_graph(n):
    """グラフを更新するコールバック関数"""
    current_time = np.arange(len(data_points)) * (graph_update_interval / 1000) - duration
    
    figure = {
        'data': [go.Scatter(
            x=current_time[:len(data_points)],  # 現在時刻からduration秒前までの相対時間でプロット
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
            yaxis=dict(title='Value')  
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
    data_thread = threading.Thread(target=main)
    data_thread.daemon = True
    
    data_thread.start()  

    app.run_server(debug=True)