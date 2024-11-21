import csv
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_ip_from_domain(domain):
    try:
        ip_address = socket.gethostbyname(domain)
        return ip_address
    except socket.gaierror:
        return None

def process_domain(domain):
    domain = domain.strip()
    if not domain:
        return None, None
    ip = get_ip_from_domain(domain)
    return domain, ip

def process_domains_from_file(file_path, output_csv, max_workers=20):
    results = []
    try:
        with open(file_path, "r") as file:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(process_domain, line): line for line in file}

                for future in as_completed(futures):
                    domain, ip = future.result()
                    if domain:
                        if ip:
                            print(f"{domain} - {ip}")
                            results.append((domain, ip))
                        else:
                            print(f"{domain} - IP not found")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if results:
            with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Domain", "IP"])
                writer.writerows(results)

if __name__ == "__main__":
    input_file = ""
    output_file = ""
    process_domains_from_file(input_file, output_file)