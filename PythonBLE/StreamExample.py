import numpy as np
import plotly.graph_objs as go
from dash import Dash, dcc, html
import dash.dependencies as dd
import time
import threading

# Dashアプリケーションの作成
app = Dash(__name__)  # Dashアプリケーションのインスタンスを作成

# グローバル変数
x_data = []  # x軸のデータを格納するリスト
y_data = []  # y軸のデータを格納するリスト
duration = 10  # プロットする時間（秒）
update_interval = 0.05  # データ生成間隔（秒）
graph_update_interval = 500  # グラフ更新間隔（ミリ秒）
pre=time.time()

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

def generate_data():
    """sin波データを生成する関数"""
    global x_data, y_data  # グローバル変数を使用することを宣言
    start_time = time.time()  # スタートタイムを取得（データ生成開始時刻）
    
    while True:  # 無限ループでデータ生成を続ける
        current_time = time.time()  # 現在時刻を取得
        
        # データの更新
        x_value = current_time  # 現在時刻をx軸データとして使用
        y_value = np.sin(2 * np.pi * x_value)  # sin波の値を計算
        
        # 最新のデータを保持するためにリストを更新
        x_data.append(x_value)  # x軸データに新しい値を追加
        y_data.append(y_value)  # y軸データに新しい値を追加
        
        # 現在時刻からduration秒前までのデータのみ保持する
        cutoff_time = current_time - duration  # 切り捨てる時間（duration秒前）
        
        while len(x_data) > 0 and x_data[0] < cutoff_time:  # 古いデータがcutoff_timeより小さい場合
            removed_x = x_data.pop(0)  # 古いxデータを削除
            removed_y = y_data.pop(0)  # 古いyデータを削除
            
            print(f"Removed data point: x={removed_x}, y={removed_y}")  # 削除したデータポイントのログ
            
        print(f"Current data points: {len(x_data)}")  # 現在保持しているデータポイント数
        
        time.sleep(update_interval)  # 次のデータ生成まで待機

@app.callback(
    dd.Output('live-graph', 'figure'),  
    [dd.Input('graph-update', 'n_intervals')]  
)
def update_graph(n):
    """グラフを更新するコールバック関数"""
    global pre
    current_time = time.time()  
    
    figure = {
        'data': [go.Scatter(
            x=[t - current_time  for t in x_data],  # 現在時刻からduration秒前までの相対時間でプロット
            y=y_data,  
            mode='lines+markers',  
            name='sin wave'  
        )],
        'layout': go.Layout(
            title='Real-time Sin Wave',  
            xaxis=dict(
                title='Time (s)',
                range=[-duration, 0], 
                dtick=1,          # x軸目盛りの間隔（1秒ごと）
                tickformat="%H:%M:%S",   # 時刻表示形式
            ),  
            yaxis=dict(title='Amplitude', range=[-1.5, 1.5])  
        )
    }
    
    elapsed_time = current_time - pre  # 前回の更新からの経過時間
    print(f"Updated graph with {len(x_data)} data points.")  # 更新されたグラフに関するログ
    print(f"Time elapsed since last update: {elapsed_time:.3f} seconds.")  # 前回の更新からの経過時間
    pre=current_time    
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
    data_thread = threading.Thread(target=generate_data)  
    data_thread.daemon = True  
    
    data_thread.start()  

    app.run_server(debug=True)