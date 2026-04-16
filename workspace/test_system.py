import requests
import json
from datetime import datetime

# 测试加密货币数据获取
def test_crypto_data():
    print("测试加密货币数据获取...")
    url = "https://api.binance.com/api/v3/ticker/price"
    try:
        response = requests.get(url)
        data = response.json()
        print(f"获取成功，返回 {len(data)} 条数据")
        # 打印一些主要加密货币的数据
        crypto_symbols = ['BTC', 'ETH', 'BNB', 'ADA']
        for item in data:
            symbol = item['symbol']
            for crypto in crypto_symbols:
                if symbol == f'{crypto}USDT':
                    print(f"{crypto}: ${item['price']}")
        return True
    except Exception as e:
        print(f"获取加密货币数据失败: {e}")
        return False

# 测试配置文件创建
def test_config_creation():
    print("\n测试配置文件创建...")
    default_config = {
        "crypto_symbols": ["BTC", "ETH", "USDT", "BNB", "ADA"],
        "stock_symbols": ["600000.SH", "600519.SH", "000001.SZ", "000858.SZ", "000333.SZ"],
        "crypto_api_url": "https://api.binance.com/api/v3/ticker/price",
        "stock_api_url": "https://api.tushare.pro",
        "tushare_token": "",
        "refresh_interval": 60,
        "alert_threshold": 5.0
    }
    
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=4)
    print("配置文件创建成功")
    return True

if __name__ == "__main__":
    test_config_creation()
    test_crypto_data()
    print("\n测试完成！")