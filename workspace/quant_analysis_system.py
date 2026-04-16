import requests
import pandas as pd
import time
import matplotlib.pyplot as plt
from datetime import datetime
import json

class QuantAnalysisSystem:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.crypto_data = {}
        self.stock_data = {}
        
    def load_config(self, config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.default_config()
    
    def default_config(self):
        return {
            'crypto_symbols': ['BTC', 'ETH', 'USDT', 'BNB', 'ADA'],
            'stock_symbols': ['600000.SH', '600519.SH', '000001.SZ', '000858.SZ', '000333.SZ'],
            'crypto_api_url': 'https://api.binance.com/api/v3/ticker/price',
            'stock_api_url': 'https://api.tushare.pro',
            'tushare_token': '',  # 需要用户填写
            'refresh_interval': 60,  # 秒
            'alert_threshold': 5.0  # 涨跌幅阈值
        }
    
    def get_crypto_data(self):
        try:
            response = requests.get(self.config['crypto_api_url'])
            data = response.json()
            for item in data:
                symbol = item['symbol']
                for crypto in self.config['crypto_symbols']:
                    if symbol == f'{crypto}USDT':
                        self.crypto_data[crypto] = {
                            'price': float(item['price']),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
            return True
        except Exception as e:
            print(f"获取加密货币数据失败: {e}")
            return False
    
    def get_stock_data(self):
        if not self.config['tushare_token']:
            print("请在config.json中填写tushare_token")
            return False
        
        try:
            import tushare as ts
            ts.set_token(self.config['tushare_token'])
            pro = ts.pro_api()
            
            for symbol in self.config['stock_symbols']:
                code = symbol.split('.')[0]
                market = symbol.split('.')[1].lower()
                df = pro.daily(ts_code=symbol, end_date=datetime.now().strftime('%Y%m%d'), count=1)
                if not df.empty:
                    self.stock_data[symbol] = {
                        'open': df['open'].iloc[0],
                        'close': df['close'].iloc[0],
                        'high': df['high'].iloc[0],
                        'low': df['low'].iloc[0],
                        'change': df['change'].iloc[0],
                        'pct_chg': df['pct_chg'].iloc[0],
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
            return True
        except Exception as e:
            print(f"获取股票数据失败: {e}")
            return False
    
    def calculate_change(self, current_price, previous_price):
        if previous_price == 0:
            return 0
        return ((current_price - previous_price) / previous_price) * 100
    
    def monitor_market(self):
        print("开始监测市场...")
        previous_crypto_data = {}
        previous_stock_data = {}
        
        while True:
            # 获取最新数据
            self.get_crypto_data()
            self.get_stock_data()
            
            # 分析加密货币
            print("\n加密货币市场:")
            for crypto, data in self.crypto_data.items():
                current_price = data['price']
                previous_price = previous_crypto_data.get(crypto, {}).get('price', current_price)
                change = self.calculate_change(current_price, previous_price)
                print(f"{crypto}: ¥{current_price:.2f}, 涨跌幅: {change:.2f}%")
                
                if abs(change) >= self.config['alert_threshold']:
                    print(f"⚠️  警报: {crypto} 涨跌幅超过 {self.config['alert_threshold']}%")
                
                previous_crypto_data[crypto] = data
            
            # 分析股票
            print("\nA股市场:")
            for stock, data in self.stock_data.items():
                print(f"{stock}: ¥{data['close']:.2f}, 涨跌幅: {data['pct_chg']:.2f}%")
                
                if abs(data['pct_chg']) >= self.config['alert_threshold']:
                    print(f"⚠️  警报: {stock} 涨跌幅超过 {self.config['alert_threshold']}%")
            
            # 等待下一次更新
            time.sleep(self.config['refresh_interval'])
    
    def visualize_data(self, data_type='crypto', days=7):
        # 这里可以添加可视化功能
        print(f"可视化{data_type}数据，过去{days}天")
        # 实现数据可视化逻辑

if __name__ == "__main__":
    # 创建配置文件
    default_config = {
        "crypto_symbols": ["BTC", "ETH", "USDT", "BNB", "ADA"],
        "stock_symbols": ["600000.SH", "600519.SH", "000001.SZ", "000858.SZ", "000333.SZ"],
        "crypto_api_url": "https://api.binance.com/api/v3/ticker/price",
        "stock_api_url": "https://api.tushare.pro",
        "tushare_token": "",  # 需要用户填写
        "refresh_interval": 10,  # 测试时缩短间隔
        "alert_threshold": 5.0
    }
    
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=4)
    
    print("配置文件已创建，请在config.json中填写tushare_token")
    print("然后运行: python quant_analysis_system.py monitor")
    
    # 简单的命令行参数处理
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'monitor':
        print("启动监测模式...")
        system = QuantAnalysisSystem()
        print("初始化完成，开始获取数据...")
        # 先测试获取加密货币数据
        print("测试获取加密货币数据...")
        success = system.get_crypto_data()
        print(f"获取加密货币数据结果: {success}")
        print(f"加密货币数据: {system.crypto_data}")
        # 开始监测
        print("开始持续监测...")
        system.monitor_market()