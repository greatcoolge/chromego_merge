import base64
import json
import urllib.request
import yaml
import codecs
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
def get_physical_location(address):
    address = re.sub(':.*', '', address)  # 用正则表达式去除端口部分
    try:
        ip_address = socket.gethostbyname(address)
    except socket.gaierror:
        ip_address = address

    try:
        reader = geoip2.database.Reader('GeoLite2-City.mmdb')  # 这里的路径需要指向你自己的数据库文件
        response = reader.city(ip_address)
        country = response.country.name
        city = response.city.name
        #return f"{country}_{city}"
        return f"{country}"
    except geoip2.errors.AddressNotFoundError as e:
        print(f"Error: {e}")
        return "Unknown"


def process_clash(data, index):
    # 解析YAML格式的内容
    content = yaml.safe_load(data)

    # 提取proxies部分并合并到merged_proxies中
    proxies = content.get('proxies', [])
    
    for proxy in proxies:
        proxy_type = proxy.get('type', '')
        server = proxy.get("server", "")
        port = int(proxy.get("port", 443))
        insecure = int(proxy.get("skip-cert-verify", 0))
        uuid = proxy.get("uuid", "")
        network = proxy.get("network", "")
        tls = int(proxy.get("tls", 0))
        sni = proxy.get("servername", "")
        flow = proxy.get("flow", "")
        publicKey = proxy.get('reality-opts', {}).get('public-key', '')
        short_id = proxy.get('reality-opts', {}).get('short-id', '')
        fp = proxy.get("client-fingerprint", "")
        grpc_serviceName = proxy.get('grpc-opts', {}).get('grpc-service-name', '')
        ws_path = proxy.get('ws-opts', {}).get('path', '')
        ws_headers_host = proxy.get('ws-opts', {}).get('headers', {}).get('Host', '')
        
        if proxy_type == 'vless':
            security = 'none' if tls == 0 else ('reality' if publicKey != '' else 'tls')
            location = get_physical_location(server)
            name = f"{location} vless {index}"
            vless_meta = (f"vless://{uuid}@{server}:{port}?security={security}&allowInsecure={insecure}&flow={flow}&"
                          f"type={network}&fp={fp}&pbk={publicKey}&sid={short_id}&sni={sni}&serviceName={grpc_serviceName}"
                          f"&path={ws_path}&host={ws_headers_host}#{name}")
            merged_proxies.append(vless_meta)

        elif proxy_type == 'vmess':
            security = "none" if tls == 0 else "tls"
            location = get_physical_location(server)
            name = f"{location} vmess {index}"
            vmess_meta = (f"vmess://{uuid}@{server}:{port}?security={security}&allowInsecure={insecure}&type={network}&fp={fp}"
                          f"&sni={sni}&path={ws_path}&host={ws_headers_host}#{name}")
            merged_proxies.append(vmess_meta)

        elif proxy_type == 'tuic':
            password = proxy.get("password", "")
            sni = proxy.get("sni", "")
            udp_relay_mode = proxy.get("udp-relay-mode", "naive")
            congestion = proxy.get("congestion-controller", "bbr")
            alpn = proxy.get("alpn", [])[0] if proxy.get("alpn") and len(proxy["alpn"]) > 0 else None
            location = get_physical_location(server)
            name = f"{location} tuic {index}"
            tuic_meta = (f"tuic://{uuid}:{password}@{server}:{port}?sni={sni}&congestion_control={congestion}"
                         f"&udp_relay_mode={udp_relay_mode}&alpn={alpn}&allow_insecure={insecure}#{name}")
            merged_proxies.append(tuic_meta)

        elif proxy_type == "hysteria2":
            auth = proxy.get("password", "")
            obfs = proxy.get("obfs", "")
            obfs_password = proxy.get("obfs-password", "")
            sni = proxy.get("sni", "")
            location = get_physical_location(server)
            name = f"{location} hysteria2 {index}"
            hy2_meta = (f"hysteria2://{auth}@{server}:{port}?insecure={insecure}&sni={sni}&obfs={obfs}&obfs-password={obfs_password}#{name}")
            merged_proxies.append(hy2_meta)

        elif proxy_type == 'hysteria':
            protocol = proxy.get("protocol", "udp")
            up_mbps = 50
            down_mbps = 80                   
            alpn = proxy.get("alpn", [])[0] if proxy.get("alpn") and len(proxy["alpn"]) > 0 else None
            obfs = proxy.get("obfs", "")
            fast_open = int(proxy.get("fast_open", 1))
            auth = proxy.get("auth-str", "")
            location = get_physical_location(server)
            name = f"{location} hysteria {index}"
            hysteria_meta = (f"hysteria://{server}:{port}?peer={sni}&auth={auth}&insecure={insecure}&upmbps={up_mbps}"
                             f"&downmbps={down_mbps}&alpn={alpn}&mport={port}&obfs={obfs}&protocol={protocol}&fastopen={fast_open}#{name}")
            merged_proxies.append(hysteria_meta)

        elif proxy_type == 'ssr':
            password = base64.b64encode(proxy.get("password", "").encode()).decode()
            cipher = proxy.get("cipher", "")
            obfs = proxy.get("obfs", "")
            protocol = proxy.get("protocol", "")
            protocol_param = base64.b64encode(proxy.get("protocol-param", "").encode()).decode()
            obfs_param = base64.b64encode(proxy.get("obfs-param", "").encode()).decode()
            ssr_source = (f"{server}:{port}:{protocol}:{cipher}:{obfs}:{password}/?obfsparam={obfs_param}"
                          f"&protoparam={protocol_param}&remarks=ssr_meta_{index}&protoparam{protocol_param}=&obfsparam={obfs_param}")
            ssr_source = base64.b64encode(ssr_source.encode()).decode()
            ssr_meta = f"ssr://{ssr_source}"
            merged_proxies.append(ssr_meta)

        elif proxy_type == 'sstest':
            password = proxy.get("password", "")
            cipher = proxy.get("cipher", "")
            ss_source = f"{cipher}:{password}@{server}:{port}"
            ss_source = base64.b64encode(ss_source.encode()).decode()
            ss_meta = f"ss://{ss_source}"
            merged_proxies.append(ss_meta)

def process_naive(data, index):
    try:
        json_data = json.loads(data)
        proxy_str = json_data["proxy"]
        naiveproxy = base64.b64encode(proxy_str.encode()).decode()
        merged_proxies.append(naiveproxy)
    except Exception as e:
        logging.error(f"Error processing naive data for index {index}: {e}")

def process_sb(data, index):
    try:
        json_data = json.loads(data)
        server = json_data["outbounds"][1].get("server", "")
        server_port = json_data["outbounds"][1].get("server_port", "")
        method = json_data["outbounds"][0].get("method", "")
        password = json_data["outbounds"][0].get("password", "")
        version = int(json_data["outbounds"][1].get("version", 0))
        host = json_data["outbounds"][1]["tls"].get("server_name", "")
        shadowtls_password = json_data["outbounds"][1].get("password", "")
        ss = f"{method}:{password}@{server}:{server_port}"
        shadowtls = f'{{"version": "{version}", "host": "{host}", "password": "{shadowtls_password}"}}'
        shadowtls_proxy = "ss://"+base64.b64encode(ss.encode()).decode()+"?shadow-tls="+base64.b64encode(shadowtls.encode()).decode()+f"#shadowtls{index}"
        merged_proxies.append(shadowtls_proxy)
    except Exception as e:
        logging.error(f"Error processing shadowtls data for index {index}: {e}")

def process_hysteria(data, index):
    try:
        json_data = json.loads(data)
        server = json_data.get("server", "")
        protocol = json_data.get("protocol", "")
        up_mbps = json_data.get("up_mbps", "")
        down_mbps = json_data.get("down_mbps", "")
        alpn = json_data.get("alpn", "")
        obfs = json_data.get("obfs", "")
        insecure = int(json_data.get("insecure", 0))
        server_name = json_data.get("server_name", "")
        fast_open = int(json_data.get("fast_open", 0))
        auth = json_data.get("auth_str", "")
        location = get_physical_location(server)
        name = f"{location} hy {index}"
        hysteria = (f"hysteria://{server}?peer={server_name}&auth={auth}&insecure={insecure}&upmbps={up_mbps}"
                    f"&downmbps={down_mbps}&alpn={alpn}&obfs={obfs}&protocol={protocol}&fastopen={fast_open}#{name}")
        merged_proxies.append(hysteria)
    except Exception as e:
        logging.error(f"Error processing hysteria data for index {index}: {e}")

def process_hysteria2(data, index):
    try:
        json_data = json.loads(data)
        server = json_data.get("server", "")
        password = json_data.get("password", "")
        insecure = int(json_data.get("insecure", 0))
        obfs = json_data.get("obfs", "")
        obfs_password = json_data.get("obfs_password", "")
        sni = json_data.get("sni", "")
        location = get_physical_location(server)
        name = f"{location} hy2 {index}"
        hysteria2 = (f"hysteria2://{server}:{password}?insecure={insecure}&obfs={obfs}&obfs_password={obfs_password}&sni={sni}#{name}")
        merged_proxies.append(hysteria2)
    except Exception as e:
        logging.error(f"Error processing hysteria2 data for index {index}: {e}")

#处理xray
def process_xray(data, index):
    try:
        json_data = json.loads(data)
        protocol = json_data["outbounds"][0].get("protocol", "")

        if protocol == "vless":
            vnext = json_data["outbounds"][0]["settings"].get("vnext", [])

            if vnext:
                server = vnext[0].get("address", "")
                port = vnext[0].get("port", "")
                users = vnext[0].get("users", [])

                if users:
                    user = users[0]
                    uuid = user.get("id", "")
                    flow = user.get("flow", "")

            stream_settings = json_data["outbounds"][0].get("streamSettings", {})
            network = stream_settings.get("network", "")
            security = stream_settings.get("security", "")
            reality_settings = stream_settings.get("realitySettings", {})

            publicKey = reality_settings.get("publicKey", "")
            short_id = reality_settings.get("shortId", "")
            sni = reality_settings.get("serverName", "")

            # tls
            tls_settings = stream_settings.get("tlsSettings", {})
            sni = tls_settings.get("serverName", sni)
            insecure = int(tls_settings.get("allowInsecure", 0))

            fp = reality_settings.get("fingerprint", "")
            fp = tls_settings.get("fingerprint", fp)
            spx = reality_settings.get("spiderX", "")

            grpc_settings = stream_settings.get("grpcSettings", {})
            grpc_serviceName = grpc_settings.get("serviceName", "")

            ws_settings = stream_settings.get("wsSettings", {})
            ws_path = ws_settings.get("path", "")
            ws_headers_host = ws_settings.get("headers", {}).get("Host", "")
            location = get_physical_location(server)
            name = f"{location} vless {index}"
            xray_proxy = (f"vless://{uuid}@{server}:{port}?security={security}&allowInsecure={insecure}&flow={flow}&"
                          f"type={network}&fp={fp}&pbk={publicKey}&sid={short_id}&sni={sni}&serviceName={grpc_serviceName}"
                          f"&path={ws_path}&host={ws_headers_host}#{name}")

            # 将当前proxy字典添加到所有proxies列表中
            merged_proxies.append(xray_proxy)

        elif protocol == "shadowsocks":
            servers = json_data["outbounds"][0]["settings"].get("servers", [{}])
            server_info = servers[0]
            server = server_info.get("address", "")
            method = server_info.get("method", "")
            password = server_info.get("password", "")
            port = server_info.get("port", "")
            # 生成URL
            ss_source = f"{method}:{password}@{server}:{port}"
            ss_source = base64.b64encode(ss_source.encode()).decode()
            xray_proxy = f"ss://{ss_source}#{index}"

            # 将当前proxy字典添加到所有proxies列表中
            merged_proxies.append(xray_proxy)
    except Exception as e:
        logging.error(f"Error processing xray data for index {index}: {e}")

# 定义一个空列表用于存储合并后的代理配置
merged_proxies = []

# 处理 clash URLs
process_urls('./urls/clash_urls.txt', process_clash)

# 处理 shadowtls URLs
#process_urls('./urls/sb_urls.txt', process_sb)

# 处理 naive URLs
process_urls('./urls/naiverproxy_urls.txt', process_naive)

# 处理 hysteria URLs
process_urls('./urls/hysteria_urls.txt', process_hysteria)

# 处理 hysteria2 URLs
process_urls('./urls/hysteria2_urls.txt', process_hysteria2)

# 处理 xray URLs
process_urls('./urls/xray_urls.txt', process_xray)

# 将结果写入文件
merged_content = "\n".join(merged_proxies)

try:
    encoded_content = base64.b64encode(merged_content.encode("utf-8")).decode("utf-8")
    
    with open("./sub/shadowrocket_base64.txt", "w") as encoded_file:
        encoded_file.write(encoded_content)
        
    print("Content successfully encoded and written to shadowrocket_base64.txt.")
except Exception as e:
    print(f"Error encoding and writing to file: {e}")

