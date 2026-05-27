from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

NWS_API_BASE = "https://api.weather.gov" # 美国国家气象局的API基础URL
USER_AGENT = "weather-app/1.0" # 用户代理字符串，标识应用程序的名称和版本

async def make_nws_request(url: str) -> dict[str, Any] | None:  # async: 声明异步函数
    """向NWS API发起请求并进行适当的错误处理。"""
    # 以API的要求设置请求头
    # Accept: 指定期望的响应数据格式 (GeoJSON)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"} 

    # async with: 创建一个异步上下文管理器，确保在进入代码块时执行初始化操作，在退出代码块时自动执行清理操作。
    # 使用httpx库的AsyncClient来发起异步HTTP请求
    # as client: 将httpx.AsyncClient()实例命名为client

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0) # 发起异步请求并接受响应
            response.raise_for_status() # 检查响应状态码
            return response.json() # 将响应内容解析为JSON格式并返回
        except Exception:
            return None # 如果发生错误，返回None


def format_alert(feature: dict) -> str:
    """将天气警报特征格式化为可读字符串。"""
    # 获取Json数据中的属性部分
    props = feature["properties"]
    # 使用props.get()方法从字典中获取特定键的值，如果键不存在则返回默认值。这种方式可以避免KeyError异常，并提供更友好的输出。
    # f: 字符串格式化，允许你在字符串内部直接使用花括号 {} 来嵌入表达式或变量。
    return f"""
Event: {props.get("event", "Unknown")}
Area: {props.get("areaDesc", "Unknown")}
Severity: {props.get("severity", "Unknown")}
Description: {props.get("description", "No description available")}
Instructions: {props.get("instruction", "No specific instructions provided")}
"""

@mcp.tool() # 用 @mcp.tool() 把普通 async 函数注册为 MCP tool
async def get_alerts(state: str) -> str:
    """获取美国某个州的天气警报。
    Args:
        state: 两个字母的州代码 (如CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]] 
    return "\n---\n".join(alerts) # .join() 方法将列表中的元素连接成一个字符串，以前面的字符串作为分隔符


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """获取某个位置的天气预报。

    Args:
        latitude: 纬度
        longitude: 经度
    """
    # 获取预报网格端点
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # 从点数据的属性中获取预报URL
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # 把预报数据格式化为可读字符串
    periods = forecast_data["properties"]["periods"]
    forecasts = []

    # 只取前 5 个时间段，避免返回内容过长占用模型上下文
    for period in periods[:5]:  
        forecast = f"""
{period["name"]}:
Temperature: {period["temperature"]}°{period["temperatureUnit"]}
Wind: {period["windSpeed"]} {period["windDirection"]}
Forecast: {period["detailedForecast"]}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

def main():
    # mcp.run(): 1. 启动 MCP server 2. 初始化注册的 tool 3. 监听 tool 调用并处理请求 
    # 使用 stdio transport 启动 MCP server：
    # 服务器通过标准输出 (stdout) 发送 JSON-RPC 消息给客户端。
    # 服务器通过标准输入 (stdin) 接收来自客户端的 JSON-RPC 消息。
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()