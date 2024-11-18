import asyncio
import aiohttp
import csv
import socket

def get_ip_from_domain(domain):
    try:
        ip = socket.gethostbyname(domain)
        return ip
    except Exception as e:
        print(f"Error resolving domain {domain}: {e}")
        return None

async def check_ip_async(ip, api_key, retries=3):
    url = "https://api.abuseipdb.com/api/v2/check"
    querystring = {"ipAddress": ip, "maxAgeInDays": "90"}
    headers = {"Accept": "application/json", "Key": api_key}

    for attempt in range(1, retries + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=querystring) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Attempt {attempt}: API returned status {response.status}")
        except aiohttp.ClientError as e:
            print(f"Attempt {attempt}: Error connecting to API: {e}")
        await asyncio.sleep(2)

    print(f"Failed to fetch data for IP {ip} after {retries} retries.")
    return None

def read_domains_from_file(file_path):
    with open(file_path, 'r') as file:
        domains = [line.strip() for line in file if line.strip()]
    return domains

async def process_domains(domains, api_key, output_csv):
    # Mở tệp CSV để ghi kết quả
    with open(output_csv, mode='w', newline='') as csv_file:
        fieldnames = ['domain', 'ip', 'country', 'hostnames']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for domain in domains:
            ip = get_ip_from_domain(domain)
            if not ip:
                print(f"Could not resolve IP for domain: {domain}")
                continue

            print(f"Checking IP for domain: {domain} (IP: {ip})")
            result = await check_ip_async(ip, api_key)
            if result and 'data' in result:
                data = result['data']
                writer.writerow({
                    'domain': domain,
                    'ip': data.get('ipAddress', 'N/A'),
                    'country': data.get('countryCode', 'N/A'),
                    'hostnames': ', '.join(data.get('hostnames', []))
                })
                print(f"Success: {domain} -> {ip}")
            else:
                print(f"No data found for IP {ip} from domain {domain}.")
            await asyncio.sleep(2)

if __name__ == "__main__":
    api_key = ""
    file_path = "ioc.txt"
    output_csv = "results.csv"

    domains = read_domains_from_file(file_path)
    asyncio.run(process_domains(domains, api_key, output_csv))