import requests
import os
import urllib.parse

# 原始配置 URL
config_url = "https://raw.githubusercontent.com/yaney01/chromego_merge/main/sub/shadowrocket_base64.txt"

# Sing-Box 配置 URL
base_url = "https://singbox.nyc.mn/singbox"

# 对配置 URL 进行 URL 编码
encoded_config_url = urllib.parse.quote(config_url)

# 构建请求 URL
request_url = f"{base_url}?config={encoded_config_url}"

# 发送 HTTP GET 请求
response = requests.get(request_url)

# 检查请求是否成功
if response.status_code == 200:
    # 确保输出文件夹存在
    output_folder = "sub"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 构建输出文件路径
    output_filename = "sb_singbox.json"
    output_path = os.path.join(output_folder, output_filename)

    # 将转换后的内容写入文件
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(response.text)

    print(f"成功将内容写入 {output_path}")
else:
    print(f"请求失败，状态码: {response.status_code}")
