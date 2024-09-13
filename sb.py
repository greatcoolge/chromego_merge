import requests
import os

# 原始数据链接
original_url = "https://raw.githubusercontent.com/yaney01/chromego_merge/main/sub/shadowrocket_base64.txt"

# 转换服务链接
conversion_url = "https://singbox.nyc.mn/config"

# 发送 HTTP 请求获取原始数据
response = requests.get(original_url)

# 检查请求是否成功
if response.status_code == 200:
    # 获取原始数据
    original_data = response.text
    
    # 构建请求数据
    conversion_data = {
        'data': original_data,
        'format': 'singbox'  # 假设转换服务要求指定格式
    }

    # 发送数据到转换服务
    conversion_response = requests.post(conversion_url, json=conversion_data)

    # 检查转换请求是否成功
    if conversion_response.status_code == 200:
        # 确保输出文件夹存在
        output_folder = "sub"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # 构建输出文件路径
        output_filename = "sb_singbox.json"
        output_path = os.path.join(output_folder, output_filename)

        # 将转换后的内容写入文件
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(conversion_response.text)

        print(f"成功将内容写入 {output_path}")
    else:
        print(f"转换服务请求失败，状态码: {conversion_response.status_code}")
else:
    print(f"原始数据请求失败，状态码: {response.status_code}")
