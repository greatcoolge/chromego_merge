import json
import logging

# 确保日志记录级别为DEBUG，以查看详细的调试信息
logging.basicConfig(level=logging.DEBUG)

def test_process_xray(file_path):
    with open(file_path, 'r') as file:
        data = file.read()
        process_xray(data, 0)

# 测试 `process_xray` 函数
test_process_xray('xray_sample.json')
