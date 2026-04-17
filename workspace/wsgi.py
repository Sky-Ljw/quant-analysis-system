from flask import Flask, render_template, jsonify
import requests
import json
from datetime import datetime
import threading
import time

# 创建Flask应用实例
app = Flask(__name__)

class QuantAnalysisSystem:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.crypto_data = {}
        self.crypto_top10 = {}  # 加密货币涨幅榜
        self.crypto_minute_change = {}  # 一分钟价格变化监测（5%）
        self.crypto_minute_change_3p = {}  # 一分钟价格变化监测（3%）
        self.stock_data = {}
        self.running = False
        self.thread = None
        # 股票名称映射
        self.stock_names = {
            '600000.SH': '浦发银行',
            '600519.SH': '贵州茅台',
            '000001.SZ': '平安银行',
            '000858.SZ': '五粮液',
            '000333.SZ': '美的集团'
        }
        # 保存上一次的加密货币价格，用于计算涨跌幅
        self.previous_crypto_prices = {}
        # 保存一分钟前的加密货币价格，用于计算一分钟变化
        self.minute_ago_crypto_prices = {}
        # 记录上次更新一分钟数据的时间
        self.last_minute_update_time = datetime.now()
        # 记录已通知的加密货币，避免重复通知
        self.notified_crypto = set()
        self.notified_crypto_3p = set()
        # Server酱配置
        self.server_chan_sendkey = "SCT338792TvvP77UXzGqvPK4ysS5XEVoPL"
    
    def send_wechat_notification(self, message):
        """发送微信通知"""
        try:
            url = f"https://sctapi.ftqq.com/{self.server_chan_sendkey}.send"
            title = "加密货币警报"
            params = {
                "title": title,
                "desp": message
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    print(f"微信通知发送成功: {title}")
                else:
                    print(f"微信通知发送失败: {result.get('message')}")
            else:
                print(f"微信通知发送失败: HTTP状态码 {response.status_code}")
        except Exception as e:
            print(f"发送微信通知失败: {e}")
    
    def load_config(self, config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.default_config()
    
    def default_config(self):
        return {
            'crypto_symbols': ['BTC', 'ETH', 'USDT', 'BNB', 'SOL', 'HYPE', 'RAVE'],
            'stock_symbols': ['600000.SH', '600519.SH', '000001.SZ', '000858.SZ', '000333.SZ'],
            'crypto_api_url': 'https://fapi.binance.com/fapi/v1/ticker/price',
            'stock_api_url': 'https://api.tushare.pro',
            'tushare_token': '',
            'refresh_interval': 10,
            'alert_threshold': 5.0
        }
    
    def get_crypto_data(self):
        try:
            # 获取所有加密货币的24小时数据，包含成交额
            ticker_response = requests.get('https://fapi.binance.com/fapi/v1/ticker/24hr')
            # 检查响应状态码
            if ticker_response.status_code != 200:
                print(f"Binance API 响应错误: {ticker_response.status_code}")
                print(f"响应内容: {ticker_response.text}")
                return False
            
            # 尝试解析 JSON
            try:
                ticker_data = ticker_response.json()
            except json.JSONDecodeError as e:
                print(f"JSON 解析失败: {e}")
                print(f"响应内容: {ticker_response.text}")
                return False
            
            # 检查数据格式
            if not isinstance(ticker_data, list):
                print(f"数据格式错误，预期是列表，实际是: {type(ticker_data)}")
                return False
            
            # 构建成交额字典
            volume_dict = {}
            for item in ticker_data:
                if not isinstance(item, dict):
                    continue
                symbol = item.get('symbol')
                if not symbol:
                    continue
                quote_volume = item.get('quoteVolume')
                if quote_volume:
                    try:
                        volume_dict[symbol] = float(quote_volume)
                    except (ValueError, TypeError):
                        pass
            
            # 处理数据
            all_crypto_data = {}
            current_time = datetime.now()
            
            # 检查是否需要更新一分钟前的价格
            time_diff = (current_time - self.last_minute_update_time).total_seconds()
            if time_diff >= 60:  # 一分钟更新一次
                print("更新一分钟前的价格数据")
                # 保存当前价格作为一分钟前的价格
                self.minute_ago_crypto_prices = {k: v['price'] for k, v in all_crypto_data.items() if 'price' in v}
                self.last_minute_update_time = current_time
                # 清空已通知记录，重新开始通知
                self.notified_crypto.clear()
                self.notified_crypto_3p.clear()
            
            for item in ticker_data:
                if not isinstance(item, dict):
                    continue
                symbol = item.get('symbol')
                if not symbol or not symbol.endswith('USDT'):
                    continue
                # 确保是永续合约（币安永续合约以USDT结尾，且没有其他特殊后缀）
                # 过滤掉交割合约（如BTCUSDT_210924）
                if '_' in symbol:
                    continue
                crypto = symbol[:-4]  # 去掉USDT后缀
                price = item.get('lastPrice')
                change_24h = item.get('priceChangePercent')
                if price and change_24h:
                    try:
                        current_price = float(price)
                        change_24h_float = float(change_24h)
                        previous_price = self.previous_crypto_prices.get(crypto, current_price)
                        change = ((current_price - previous_price) / previous_price) * 100 if previous_price > 0 else 0
                        
                        # 计算一分钟涨跌幅
                        minute_ago_price = self.minute_ago_crypto_prices.get(crypto, current_price)
                        minute_change = ((current_price - minute_ago_price) / minute_ago_price) * 100 if minute_ago_price > 0 else 0
                        
                        # 获取24h成交额
                        volume = volume_dict.get(symbol, 0)
                        
                        all_crypto_data[crypto] = {
                            'price': current_price,
                            'change': round(change, 2),
                            'change_24h': round(change_24h_float, 2),
                            'minute_change': round(minute_change, 2),
                            'volume': volume,
                            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        self.previous_crypto_prices[crypto] = current_price
                    except (ValueError, TypeError):
                        pass
            
            # 筛选24h成交额在1000万以上的加密货币
            filtered_crypto_data = {}
            for crypto, data in all_crypto_data.items():
                if data.get('volume', 0) >= 10000000:  # 1000万USDT
                    filtered_crypto_data[crypto] = data
            
            # 按24h涨跌幅排序，获取前10（只包含成交额>=1000万的USDT永续合约）
            sorted_crypto = sorted(filtered_crypto_data.items(), key=lambda x: x[1]['change_24h'], reverse=True)[:10]
            # 构建涨幅榜数据
            self.crypto_top10 = {}
            for i, (crypto, data) in enumerate(sorted_crypto, 1):
                self.crypto_top10[crypto] = {
                    'rank': i,
                    'price': data['price'],
                    'change': data['change_24h'],
                    'volume': data['volume'],
                    'timestamp': data['timestamp']
                }
            
            # 筛选一分钟涨跌幅超过5%的加密货币（成交额>=1000万的USDT永续合约）
            minute_change_crypto = {}
            for crypto, data in filtered_crypto_data.items():
                if 'minute_change' in data and abs(data['minute_change']) >= 5.0:
                    minute_change_crypto[crypto] = {
                        'price': data['price'],
                        'minute_change': data['minute_change'],
                        'volume': data['volume'],
                        'timestamp': data['timestamp']
                    }
                    
                    # 发送微信通知（避免重复通知）
                    if crypto not in self.notified_crypto:
                        change_type = "上涨" if data['minute_change'] >= 0 else "下跌"
                        message = f"""
⚠️ 加密货币警报：{crypto} 一分钟{change_type} {abs(data['minute_change']):.2f}%

- 币种：{crypto}
- 当前价格：${data['price']:.2f}
- 一分钟涨跌幅：{data['minute_change']:.2f}%
- 24h成交额：${data['volume']:.2f}
- 时间：{data['timestamp']}
                        """
                        self.send_wechat_notification(message)
                        self.notified_crypto.add(crypto)
                        print(f"已发送 {crypto} 的微信通知")
            
            # 按涨跌幅绝对值排序，取前10
            sorted_minute_change = sorted(minute_change_crypto.items(), key=lambda x: abs(x[1]['minute_change']), reverse=True)[:10]
            self.crypto_minute_change = {}
            for i, (crypto, data) in enumerate(sorted_minute_change, 1):
                self.crypto_minute_change[crypto] = {
                    'rank': i,
                    'price': data['price'],
                    'minute_change': data['minute_change'],
                    'volume': data['volume'],
                    'timestamp': data['timestamp']
                }
            
            # 筛选一分钟涨跌幅超过3%的加密货币（成交额>=1000万的USDT永续合约）
            minute_change_crypto_3p = {}
            for crypto, data in filtered_crypto_data.items():
                if 'minute_change' in data and abs(data['minute_change']) >= 3.0:
                    minute_change_crypto_3p[crypto] = {
                        'price': data['price'],
                        'minute_change': data['minute_change'],
                        'volume': data['volume'],
                        'timestamp': data['timestamp']
                    }
                    
                    # 发送微信通知（避免重复通知）
                    if crypto not in self.notified_crypto_3p:
                        change_type = "上涨" if data['minute_change'] >= 0 else "下跌"
                        message = f"""
⚠️ 加密货币警报：{crypto} 一分钟{change_type} {abs(data['minute_change']):.2f}%

- 币种：{crypto}
- 当前价格：${data['price']:.2f}
- 一分钟涨跌幅：{data['minute_change']:.2f}%
- 24h成交额：${data['volume']:.2f}
- 时间：{data['timestamp']}
                        """
                        self.send_wechat_notification(message)
                        self.notified_crypto_3p.add(crypto)
                        print(f"已发送 {crypto} 的3%微信通知")
            
            # 按涨跌幅绝对值排序，取前10
            sorted_minute_change_3p = sorted(minute_change_crypto_3p.items(), key=lambda x: abs(x[1]['minute_change']), reverse=True)[:10]
            self.crypto_minute_change_3p = {}
            for i, (crypto, data) in enumerate(sorted_minute_change_3p, 1):
                self.crypto_minute_change_3p[crypto] = {
                    'rank': i,
                    'price': data['price'],
                    'minute_change': data['minute_change'],
                    'volume': data['volume'],
                    'timestamp': data['timestamp']
                }
            
            # 保留配置中的加密货币数据
            for crypto in self.config['crypto_symbols']:
                if crypto in all_crypto_data:
                    self.crypto_data[crypto] = all_crypto_data[crypto]
            
            return True
        except Exception as e:
            print(f"获取加密货币数据失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_stock_data(self):
        if not self.config['tushare_token']:
            return False
        
        try:
            import tushare as ts
            ts.set_token(self.config['tushare_token'])
            pro = ts.pro_api()
            
            for symbol in self.config['stock_symbols']:
                df = pro.daily(ts_code=symbol, end_date=datetime.now().strftime('%Y%m%d'), count=1)
                if not df.empty:
                    self.stock_data[symbol] = {
                        'open': df['open'].iloc[0],
                        'close': df['close'].iloc[0],
                        'high': df['high'].iloc[0],
                        'low': df['low'].iloc[0],
                        'change': df['change'].iloc[0],
                        'pct_chg': df['pct_chg'].iloc[0],
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'name': self.stock_names.get(symbol, '未知')
                    }
            return True
        except Exception as e:
            print(f"获取股票数据失败: {e}")
            return False
    
    # def start_monitoring(self):
    #     self.running = True
    #     def monitor():
    #         while self.running:
    #             self.get_crypto_data()
    #             self.get_stock_data()
    #             time.sleep(self.config['refresh_interval'])
    #     
    #     self.thread = threading.Thread(target=monitor)
    #     self.thread.daemon = True
    #     self.thread.start()
    # 
    # def stop_monitoring(self):
    #     self.running = False
    #     if self.thread:
    #         self.thread.join()

# 确保配置文件存在
def ensure_config_exists():
    default_config = {
        "crypto_symbols": ["BTC", "ETH", "USDT", "BNB", "SOL", "HYPE", "RAVE"],
        "stock_symbols": ["600000.SH", "600519.SH", "000001.SZ", "000858.SZ", "000333.SZ"],
        "crypto_api_url": "https://fapi.binance.com/fapi/v1/ticker/price",
        "stock_api_url": "https://api.tushare.pro",
        "tushare_token": "",
        "refresh_interval": 10,
        "alert_threshold": 5.0
    }
    
    try:
        with open('config.json', 'r') as f:
            pass
    except FileNotFoundError:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)

# 确保templates目录存在
def ensure_templates_dir_exists():
    import os
    if not os.path.exists('templates'):
        os.makedirs('templates')

# 初始化应用所需的目录和文件
ensure_config_exists()
ensure_templates_dir_exists()

# 初始化系统
system = QuantAnalysisSystem()
# system.start_monitoring()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    return jsonify({
        'crypto': system.crypto_data,
        'crypto_top10': system.crypto_top10,
        'crypto_minute_change': system.crypto_minute_change,
        'crypto_minute_change_3p': system.crypto_minute_change_3p,
        'stock': system.stock_data,
        'config': system.config
    })

# Vercel需要的应用导出
# 确保应用在模块级别可用
