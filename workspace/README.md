# 量化分析系统

## 系统功能
- 监测加密货币合约市场的实时价格和涨跌幅
- 监测A股股票的实时价格和涨跌幅
- 显示涨幅榜前十（24h成交额≥1000万USDT的USDT永续合约）
- 监测一分钟涨跌幅超过5%的币种（24h成交额≥1000万USDT的USDT永续合约）
- 监测一分钟涨跌幅超过3%的币种（24h成交额≥1000万USDT的USDT永续合约）
- 配置监测指定的主流币种
- 微信通知功能（当币种涨跌幅超过阈值时）
- 网页版监测界面，数据实时更新
- 数据可视化功能

## 安装步骤

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置API Token
- 加密货币数据：使用Binance合约API，无需注册
- A股数据：需要注册Tushare账号并获取API Token（可选）
  - 注册地址：https://tushare.pro/register
  - 登录后在个人中心获取Token
  - 将Token填入config.json文件中的`tushare_token`字段

### 3. 配置微信通知（可选）
- 注册Server酱账号：https://sct.ftqq.com/
- 获取SendKey
- 在web_app.py文件中更新`server_chan_sendkey`变量

## 使用方法

### 1. 启动服务器
```bash
python web_app.py
```

### 2. 访问监测界面
打开浏览器，访问：http://127.0.0.1:5000

### 3. 配置文件说明
系统会自动创建默认的config.json配置文件，可根据需要修改：
- `crypto_symbols`：要监测的主流加密货币列表
- `stock_symbols`：要监测的A股股票列表
- `crypto_api_url`：加密货币API地址（使用Binance合约API）
- `stock_api_url`：A股API地址
- `tushare_token`：Tushare API Token
- `refresh_interval`：数据刷新间隔（秒）
- `alert_threshold`：涨跌幅警报阈值（百分比）

## 配置示例

```json
{
    "crypto_symbols": ["BTC", "ETH", "USDT", "BNB", "SOL", "HYPE", "RAVE"],
    "stock_symbols": ["600000.SH", "600519.SH", "000001.SZ", "000858.SZ", "000333.SZ"],
    "crypto_api_url": "https://fapi.binance.com/fapi/v1/ticker/price",
    "stock_api_url": "https://api.tushare.pro",
    "tushare_token": "your_tushare_token_here",
    "refresh_interval": 10,
    "alert_threshold": 5.0
}
```

## 系统架构

- **QuantAnalysisSystem类**：核心类，负责数据获取、分析和监测
- **get_crypto_data()**：从Binance合约API获取加密货币数据
- **get_stock_data()**：从Tushare API获取A股数据
- **start_monitoring()**：启动后台监测线程
- **send_wechat_notification()**：发送微信通知
- **Flask Web应用**：提供网页版监测界面

## 注意事项
- 加密货币数据来自Binance合约API，使用的是USDT永续合约
- 系统会筛选24h成交额≥1000万USDT的币种
- 建议合理设置refresh_interval，避免过于频繁的API调用
- 微信通知功能需要Server酱SendKey
- A股数据获取需要Tushare API Token，免费用户有调用次数限制

## 技术特点
- 使用Flask Web框架构建网页界面
- 多线程后台监测，不阻塞Web服务
- 实时数据更新，10秒刷新一次
- 响应式设计，适配不同设备
- 数据可视化，使用Chart.js
- 微信通知，及时预警市场变动