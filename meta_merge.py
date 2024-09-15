import yaml
import json
import urllib.request
import logging
import geoip2.database
import socket
import re
# 提取节点
def process_urls(url_file, processor):
    try:
        with open(url_file, 'r') as file:
            urls = file.read().splitlines()

        for index, url in enumerate(urls):
            try:
                response = urllib.request.urlopen(url)
                data = response.read().decode('utf-8')
                processor(data, index)
            except Exception as e:
                logging.error(f"Error processing URL {url}: {e}")
    except Exception as e:
        logging.error(f"Error reading file {url_file}: {e}")
#提取clash节点
def process_clash(data, index):
    content = yaml.safe_load(data)
    proxies = content.get('proxies', [])
    for i, proxy in enumerate(proxies):
        location = get_physical_location(proxy['server'])
        proxy['name'] = f"{location} {proxy['type']} {index}{i+1}"
    merged_proxies.extend(proxies)

def get_physical_location(address):
    address = re.sub(':.*', '', address)  # 去掉端口部分
    try:
        # 尝试使用 ipinfo.io API 获取国家
        response = requests.get(f"https://ipinfo.io/{address}/json")
        data = response.json()
        country = data.get("country", "Unknown Country")
        return country
    except Exception as e:
        logging.error(f"Error fetching location from ipinfo.io for address {address}: {e}")

    # 如果 API 请求失败，回退到 GeoLite2-City 数据库
    try:
        ip_address = socket.gethostbyname(address)
        reader = geoip2.database.Reader('GeoLite2-City.mmdb')
        response = reader.city(ip_address)
        country = response.country.name
        return country
    except geoip2.errors.AddressNotFoundError as e:
        logging.error(f"GeoLite2 database error: {e}")
        return "Unknown"
    except FileNotFoundError:
        logging.error("GeoLite2 database file not found.")
        return "Database not found"
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return "Error"
    finally:
        if 'reader' in locals():
            reader.close()  # 确保数据库文件被关闭

# 处理sb，待办
def process_sb(data, index):
    try:
        json_data = json.loads(data)
        # 处理 shadowtls 数据

        # 提取所需字段
        method = json_data["outbounds"][0]["method"]
        password = json_data["outbounds"][0]["password"]
        server = json_data["outbounds"][1]["server"]
        server_port = json_data["outbounds"][1]["server_port"]
        server_name = json_data["outbounds"][1]["tls"]["server_name"]
        shadowtls_password = json_data["outbounds"][1]["password"]
        version = json_data["outbounds"][1]["version"]
        location = get_physical_location(server)
        name = f"{location} ss {index}"
        # 创建当前网址的proxy字典
        proxy = {
            "name": name,
            "type": "ss",
            "server": server,
            "port": server_port,
            "cipher": method,
            "password": password,
            "plugin": "shadow-tls",
            "client-fingerprint": "chrome",
            "plugin-opts": {
                "host": server_name,
                "password": shadowtls_password,
                "version": int(version)
            }
        }

        # 将当前proxy字典添加到所有proxies列表中
        merged_proxies.append(proxy)

    except Exception as e:
        logging.error(f"Error processing shadowtls data for index {index}: {e}")

def process_hysteria(data, index):
    try:
        json_data = json.loads(data)
        # 处理 hysteria 数据
        # 提取所需字段
        auth = json_data["auth_str"]
        server_ports = json_data["server"]
        server_ports_slt = server_ports.split(":")
        server = server_ports_slt[0]
        ports = server_ports_slt[1]
        ports_slt = ports.split(",")
        server_port = int(ports_slt[0])
        if len(ports_slt) > 1:
            mport = ports_slt[1]
        else:
            mport = server_port
        #fast_open = json_data["fast_open"]
        fast_open = True
        insecure = json_data["insecure"]
        server_name = json_data["server_name"]
        alpn = json_data["alpn"]
        protocol = json_data["protocol"]
        location = get_physical_location(server)
        name = f"{location} hysteria {index}"

        # 创建当前网址的proxy字典
        proxy = {
            "name": name,
            "type": "hysteria",
            "server": server,
            "port": server_port,
            "ports": mport,
            "auth_str": auth,
            "up": 80,
            "down": 100,
            "fast-open": fast_open,
            "protocol": protocol,
            "sni": server_name,
            "skip-cert-verify": insecure,
            "alpn": [alpn]
        }

        # 将当前proxy字典添加到所有proxies列表中
        merged_proxies.append(proxy)

    except Exception as e:
        logging.error(f"Error processing hysteria data for index {index}: {e}")
# 处理hysteria2
def process_hysteria2(data, index):
    try:
        json_data = json.loads(data)
        # 处理 hysteria2 数据
        # 提取所需字段
        auth = json_data["auth"]
        server_ports = json_data["server"]
        server_ports_slt = server_ports.split(":")
        server = server_ports_slt[0]
        ports = server_ports_slt[1]
        ports_slt = ports.split(",")
        server_port = int(ports_slt[0])
        #fast_open = json_data["fastOpen"]
        fast_open = True
        insecure = json_data["tls"]["insecure"]
        sni = json_data["tls"]["sni"]
        location = get_physical_location(server)
        name = f"{location} hysteria2 {index}"

        # 创建当前网址的proxy字典
        proxy = {
            "name": name,
            "type": "hysteria2",
            "server": server,
            "port": server_port,
            "password": auth,
            "fast-open": fast_open,
            "sni": sni,
            "skip-cert-verify": insecure
        }

        # 将当前proxy字典添加到所有proxies列表中
        merged_proxies.append(proxy)

    except Exception as e:
        logging.error(f"Error processing hysteria2 data for index {index}: {e}")

#处理xray
def process_xray(data, index):
    proxy = None
    try:
        json_data = json.loads(data)
        logging.debug(f"Processing data for index {index}: {json_data}")

        outbounds = json_data.get("outbounds", [])
        if not outbounds:
            logging.warning(f"No 'outbounds' found for index {index}")
            return

        first_outbound = outbounds[0]
        protocol = first_outbound.get("protocol", "")
        logging.debug(f"Protocol found: {protocol}")

        if protocol == "vless":
            settings = first_outbound.get("settings", {})
            vnext = settings.get("vnext", [{}])[0]
            streamSettings = first_outbound.get("streamSettings", {})

            server = vnext.get("address", "")
            port = vnext.get("port", "")
            uuid = vnext.get("users", [{}])[0].get("id", "")
            istls = True
            flow = vnext.get("users", [{}])[0].get("flow", "")
            network = streamSettings.get("network", "")
            realitySettings = streamSettings.get("realitySettings", {})
            publicKey = realitySettings.get("publicKey", "")
            shortId = realitySettings.get("shortId", "")
            serverName = realitySettings.get("serverName", "")
            fingerprint = realitySettings.get("fingerprint", "")
            isudp = True
            location = get_physical_location(server)
            name = f"{location} vless {index}"

            if network == "tcp":
                proxy = {
                    "name": name,
                    "type": protocol,
                    "server": server,
                    "port": port,
                    "uuid": uuid,
                    "network": network,
                    "tls": istls,
                    "udp": isudp,
                    "flow": flow,
                    "client-fingerprint": fingerprint,
                    "servername": serverName,
                    "reality-opts": {
                        "public-key": publicKey,
                        "short-id": shortId
                    }
                }
                logging.debug(f"TCP Proxy: {proxy}")

            elif network == "grpc":
                grpcSettings = streamSettings.get("grpcSettings", {})
                serviceName = grpcSettings.get("serviceName", "")
                proxy = {
                    "name": name,
                    "type": protocol,
                    "server": server,
                    "port": port,
                    "uuid": uuid,
                    "network": network,
                    "tls": istls,
                    "udp": isudp,
                    "flow": flow,
                    "client-fingerprint": fingerprint,
                    "servername": serverName,
                    "grpc-opts": {
                        "grpc-service-name": serviceName
                    },
                    "reality-opts": {
                        "public-key": publicKey,
                        "short-id": shortId
                    }
                }
                logging.debug(f"GRPC Proxy: {proxy}")

        elif protocol == "vmess":
            settings = first_outbound.get("settings", {})
            vnext = settings.get("vnext", [{}])[0]
            streamSettings = first_outbound.get("streamSettings", {})

            server = vnext.get("address", "")
            port = vnext.get("port", "")
            uuid = vnext.get("users", [{}])[0].get("id", "")
            alterId = vnext.get("users", [{}])[0].get("alterId", 0)
            network = streamSettings.get("network", "")
            security = streamSettings.get("security", "none")
            location = get_physical_location(server)
            name = f"{location} vmess {index}"

            if network == "tcp":
                proxy = {
                    "name": name,
                    "type": protocol,
                    "server": server,
                    "port": port,
                    "uuid": uuid,
                    "alterId": alterId,
                    "cipher": "auto",
                    "network": network,
                    "tls": security == "tls",
                    "udp": True
                }
                logging.debug(f"TCP Proxy: {proxy}")

            elif network == "ws":
                wsSettings = streamSettings.get("wsSettings", {})
                path = wsSettings.get("path", "")
                headers = wsSettings.get("headers", {})
                proxy = {
                    "name": name,
                    "type": protocol,
                    "server": server,
                    "port": port,
                    "uuid": uuid,
                    "alterId": alterId,
                    "cipher": "auto",
                    "network": network,
                    "tls": security == "tls",
                    "servername": streamSettings.get("serverName", ""),
                    "ws-opts": {
                        "path": path,
                        "headers": headers
                    }
                }
                logging.debug(f"WS Proxy: {proxy}")

        else:
            logging.warning(f"Unsupported protocol: {protocol}")

        if proxy:
            merged_proxies.append(proxy)
        else:
            logging.warning(f"No proxy configuration found for index {index}")

    except Exception as e:
        logging.error(f"Error processing xray data for index {index}: {e}")
merged_proxies = []

# 处理 clash URLs
process_urls('./urls/clash_urls.txt', process_clash)

# 处理 shadowtls URLs
#process_urls('./urls/sb_urls.txt', process_sb)

# 处理 hysteria URLs
process_urls('./urls/hysteria_urls.txt', process_hysteria)

# 处理 hysteria2 URLs
process_urls('./urls/hysteria2_urls.txt', process_hysteria2)

# 处理 xray URLs
process_urls('./urls/xray_urls.txt', process_xray)

# 读取普通的配置文件内容
with open('./templates/clash_template.yaml', 'r', encoding='utf-8') as file:
    config_data = yaml.safe_load(file)

# 读取warp配置文件内容
with open('./templates/clash_warp_template.yaml', 'r', encoding='utf-8') as file:
    config_warp_data = yaml.safe_load(file)

# 添加合并后的代理到proxies部分
if 'proxies' not in config_data or not config_data['proxies']:
    config_data['proxies'] = merged_proxies
else:
    config_data['proxies'].extend(merged_proxies)

if 'proxies' not in config_warp_data or not config_warp_data['proxies']:
    config_warp_data['proxies'] = merged_proxies
else:
    config_warp_data['proxies'].extend(merged_proxies)


# 更新自动选择和节点选择的proxies的name部分
update_proxy_groups(config_data, merged_proxies)
update_warp_proxy_groups(config_warp_data, merged_proxies)

# 将更新后的数据写入到一个YAML文件中，并指定编码格式为UTF-8
with open('./sub/merged_proxies_new.yaml', 'w', encoding='utf-8') as file:
    yaml.dump(config_data, file, sort_keys=False, allow_unicode=True)

with open('./sub/merged_warp_proxies_new.yaml', 'w', encoding='utf-8') as file:
    yaml.dump(config_warp_data, file, sort_keys=False, allow_unicode=True)

print("聚合完成")

