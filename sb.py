import requests
import os

# 原始 URL
base_url = "https://raw.githubusercontent.com/yaney01/chromego_merge/main/sub/shadowrocket_base64.txt"
# 订阅转换服务链接
conversion_url = "https://singbox.yaney.eu.org/config"

# 拼接 URL
url = f"{base_url}?conversion_url={requests.utils.quote(conversion_url)}"
output_folder = "sub"
output_filename = "sb.json"

# 发送HTTP请求
response = requests.get(url)

# 检查请求是否成功
if response.status_code == 200:
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 构建输出文件路径
    output_path = os.path.join(output_folder, output_filename)

    # 将响应内容写入文件，使用utf-8编码
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(response.text)

    print(f"成功将内容写入 {output_path}")
else:
    print(f"HTTP请求失败，状态码: {response.status_code}")
