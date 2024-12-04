# PyEspBleConnect
pythonとESP32をbluetooth low energy で接続する方法

<br>
python3 -m venv myenv<br>
source myenv/bin/activate<br>
pip install -r requirements.txt<br>
cd PythonBLE <br>

python3 BLEConnect.py<br> 
python3 StreamExample.py<br>
python3 BLEStream.py<br>
    http://127.0.0.1:8050/ に移動<br>


#　グラフ可視化の方法をBokehにした理由
データ可視化ライブラリとしてはSeabornやMatplotlibなどもあったがインタラクティブ性でPlotlyとBokehで迷った。
何となく簡単そうなのでPlotlyにした。
↑描画の遅延が溜まっていくのがきつい、StreamExampleで500msが限界だった。
## 以下を参考にしました
<https://www.skygroup.jp/tech-blog/article/438/>
<https://www.lac.co.jp/lacwatch/people/20221128_003192.html>
<https://qiita.com/alchemist/items/544d45480ce9c1ca2c16>

