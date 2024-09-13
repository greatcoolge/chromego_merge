import requests
import urllib.parse
import os

# 配置 URL
config_url = "https://raw.githubusercontent.com/yaney01/chromego_merge/main/sub/shadowrocket_base64.txt"

# URL 编码配置 URL
encoded_config_url = urllib.parse.quote(config_url)

# 可选参数（如果有的话）
selected_rules = ""  # 这里可以填写预定义规则集名称，如 'balanced'，如果不需要可以保持为空
custom_rules = ""    # 这里可以填写自定义规则的 JSON 数组，如果不需要可以保持为空

# 构建请求 URL
base_url = "https://singbox.nyc.mn/singbox"
request_url = f"{base_url}?config={encoded_config_url}"

if selected_rules:
    request_url += f"&selectedRules={urllib.parse.quote(selected_rules)}"
if custom_rules:
    request_url += f"&customRules={urllib.parse.quote(custom_rules)}"

# 发送 HTTP GET 请求
try:
    response = requests.get(request_url)
    response.raise_for_status()  # 如果响应状态码不是 200，将引发 HTTPError
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
except requests.exceptions.RequestException as e:
    print(f"请求出现错误: {e}")
