import os
import re
import csv
import time
import json
import socket
import sqlite3
import hashlib
import requests
import argparse
from colorama import Fore
from datetime import datetime

API_KEY_FILE = 'api_key.txt'

def check_ip_virustotal(ip, api_key):
    url = f'https://www.virustotal.com/api/v3/ip_addresses/{ip}'
    params = {'x-apikey': api_key}
    response = requests.get(url, headers=params)

    if response.status_code != 200:
        if response.status_code == 401:
            raise Exception("Invalid API key")
        elif response.status_code == 429:
            raise Exception("API quota exceeded")
        else:
            raise Exception(f"Unexpected status code: {response.status_code}")

    if response.ok:
        data = response.json()
        last_scanned = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        engines_detected = [engine for engine, detection in data['data']['attributes']['last_analysis_results'].items()
                            if detection['category'] == 'malicious']
        harmless_votes = data['data']['attributes']['last_analysis_stats']['harmless']
        suspicious_votes = data['data']['attributes']['last_analysis_stats']['suspicious']
        undetected_votes = data['data']['attributes']['last_analysis_stats']['undetected']
        malicious_votes = data['data']['attributes']['last_analysis_stats']['malicious']
        score = f"{malicious_votes}/{malicious_votes + harmless_votes + suspicious_votes + undetected_votes}"
        result = {
            'IP': ip,
            'Last_scanned': last_scanned,
            'Score': score,
            'Detected_by': ', '.join(engines_detected),
            'Link': f"https://www.virustotal.com/gui/ip-address/{ip}/detection"
        }
        return result
    else:
        raise Exception(f"Unable to check the IP: {ip}")

def check_md5_virustotal(md5, api_key):
    url = f'https://www.virustotal.com/vtapi/v2/file/report'
    params = {'apikey': api_key, 'resource': md5}

    max_retries = 5
    for attempt in range(max_retries):
        response = requests.get(url, params=params)

        if response.status_code == 204:
            print(f"Received status code 204 for MD5: {md5}. Retrying...")
            time.sleep(3)
            continue
        elif response.status_code != 200:
            if response.status_code == 401:
                raise Exception("Invalid API key")
            elif response.status_code == 429:
                raise Exception("API quota exceeded")
            else:
                raise Exception(f"Unexpected status code: {response.status_code}")

        result = response.json()
        if result.get('response_code') == 1:
            scan_date_str = result.get('scan_date')
            if isinstance(scan_date_str, str):
                scan_date = datetime.strptime(scan_date_str, '%Y-%m-%d %H:%M:%S')
            else:
                scan_date = datetime.fromtimestamp(scan_date_str)

            engines_detected = [engine_name for engine_name, engine_data in result.get('scans', {}).items() if
                                engine_data.get('detected')]
            result = {
                'MD5': md5,
                'Last_scanned': scan_date.strftime('%Y-%m-%d %H:%M:%S'),
                'Score': f"{result.get('positives', 0)}/{result.get('total', 0)}",
                'Detected_by': ', '.join(engines_detected),
                'Link': result.get('permalink')
            }
            return result
        else:
            raise Exception(f"Unable to check the MD5: {md5}")
    raise Exception(f"Failed to retrieve data for MD5: {md5} after {max_retries} attempts")

def check_sha256_virustotal(sha256, api_key):
    url = f'https://www.virustotal.com/vtapi/v2/file/report'
    params = {'apikey': api_key, 'resource': sha256}
    response = requests.get(url, params=params)

    max_retries = 5
    for attempt in range(max_retries):
        response = requests.get(url, params=params)

        if response.status_code == 204:
            print(f"Received status code 204 for MD5: {sha256}. Retrying...")
            time.sleep(3)
            continue
        elif response.status_code != 200:
            if response.status_code == 401:
                raise Exception("Invalid API key")
            elif response.status_code == 429:
                raise Exception("API quota exceeded")
            else:
                raise Exception(f"Unexpected status code: {response.status_code}")

        result = response.json()
        if result.get('response_code') == 1:
            scan_date_str = result.get('scan_date')
            if isinstance(scan_date_str, str):
                scan_date = datetime.strptime(scan_date_str, '%Y-%m-%d %H:%M:%S')
            else:
                scan_date = datetime.fromtimestamp(scan_date_str)

            engines_detected = [engine_name for engine_name, engine_data in result.get('scans', {}).items() if
                                engine_data.get('detected')]
            result = {
                'SHA256': sha256,
                'Last_scanned': scan_date.strftime('%Y-%m-%d %H:%M:%S'),
                'Score': f"{result.get('positives', 0)}/{result.get('total', 0)}",
                'Detected_by': ', '.join(engines_detected),
                'Link': result.get('permalink')
            }
            return result
        else:
            print(response)
            raise Exception(f"Unable to check the SHA256: {sha256}")
    raise Exception(f"Failed to retrieve data for MD5: {sha256} after {max_retries} attempts")

def check_sha1_virustotal(sha1, api_key):
    url = f'https://www.virustotal.com/vtapi/v2/file/report'
    params = {'apikey': api_key, 'resource': sha1}
    response = requests.get(url, params=params)

    max_retries = 5
    for attempt in range(max_retries):
        response = requests.get(url, params=params)

        if response.status_code == 204:
            print(f"Received status code 204 for MD5: {sha1}. Retrying...")
            time.sleep(3)
            continue
        elif response.status_code != 200:
            if response.status_code == 401:
                raise Exception("Invalid API key")
            elif response.status_code == 429:
                raise Exception("API quota exceeded")
            else:
                raise Exception(f"Unexpected status code: {response.status_code}")

        result = response.json()
        if result.get('response_code') == 1:
            scan_date_str = result.get('scan_date')
            if isinstance(scan_date_str, str):
                scan_date = datetime.strptime(scan_date_str, '%Y-%m-%d %H:%M:%S')
            else:
                scan_date = datetime.fromtimestamp(scan_date_str)

            engines_detected = [engine_name for engine_name, engine_data in result.get('scans', {}).items() if
                                engine_data.get('detected')]
            result = {
                'SHA1': sha1,
                'Last_scanned': scan_date.strftime('%Y-%m-%d %H:%M:%S'),
                'Score': f"{result.get('positives', 0)}/{result.get('total', 0)}",
                'Detected_by': ', '.join(engines_detected),
                'Link': result.get('permalink')
            }
            return result
        else:
            print(response)
            raise Exception(f"Unable to check the SHA1: {sha1}")
    raise Exception(f"Failed to retrieve data for MD5: {sha1} after {max_retries} attempts")

def check_domain_virustotal(domain, api_key):
    url = f'https://www.virustotal.com/api/v3/domains/{domain}'
    params = {'x-apikey': api_key}
    response = requests.get(url, headers=params)

    if response.status_code != 200:
        if response.status_code == 401:
            raise Exception("Invalid API key")
        elif response.status_code == 429:
            raise Exception("API quota exceeded")
        else:
            raise Exception(f"Unexpected status code: {response.status_code}")

    if response.ok:
        data = response.json()
        last_modified = data['data']['attributes']['last_modification_date']
        last_scanned = datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S') if last_modified else 'N/A'
        malicious_votes = data['data']['attributes']['last_analysis_stats']['malicious']
        harmless_votes = data['data']['attributes']['last_analysis_stats']['harmless']
        suspicious_votes = data['data']['attributes']['last_analysis_stats']['suspicious']
        undetected_votes = data['data']['attributes']['last_analysis_stats']['undetected']
        score = f"{malicious_votes}/{malicious_votes + harmless_votes + suspicious_votes + undetected_votes}"
        detected_by = [engine_name for engine_name, scan_result in
                       data['data']['attributes']['last_analysis_results'].items() if
                       scan_result['category'] == 'malicious']
        detected_by_string = ', '.join(detected_by) if detected_by else 'No detections'
        result = {
            'Domain': domain,
            'Last_scanned': last_scanned,
            'Score': score,
            'Detected_by': detected_by_string,
            'Link': f"https://www.virustotal.com/gui/domain/{domain}/detection"
        }
        return result
    else:
        raise Exception(f"Unable to check the domain: {domain}")

def save_api_key(api_key):
    with open(API_KEY_FILE, 'w') as file:
        file.write(api_key)
    print("API key saved successfully.")

def clear_api_key():
    """Clear the saved API key."""
    try:
        os.remove(API_KEY_FILE)
        print("API key has been cleared.")
    except FileNotFoundError:
        print("No API key to clear.")

def get_saved_api_key():
    """Retrieve the saved API key."""
    try:
        with open(API_KEY_FILE, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

def is_valid_ip(address):
    try:
        socket.inet_aton(address)
        return True
    except:
        return False

def is_valid_md5(md5):
    """Check if a string is a valid MD5 hash."""
    if len(md5) != 32:
        return False
    if not re.match(r'[0-9a-fA-F]{32}', md5):
        return False
    return True

def is_valid_sha256(sha256):
    """Check if a string is a valid SHA256 hash."""
    if len(sha256) != 64:
        return False
    if not re.match(r'[0-9a-fA-F]{64}', sha256):
        return False
    return True

def is_valid_sha1(sha1):
    """Check if a string is a valid SHA1 hash."""
    if len(sha1) != 40:
        return False
    if not re.match(r'[0-9a-fA-F]{40}', sha1):
        return False
    return True

def hash_file(filename):
    """This function returns the MD5 hash of the file."""
    h = hashlib.md5()
    with open(filename, 'rb') as file:
        chunk = 0
        while chunk != b'':
            chunk = file.read(1024)
            h.update(chunk)
    return h.hexdigest()

def calculate_md5_hash(filename):
    """This function returns the MD5 hash of the file."""
    h = hashlib.md5()
    with open(filename, 'rb') as file:
        chunk = 0
        while chunk != b'':
            chunk = file.read(1024)
            h.update(chunk)
    return h.hexdigest()

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='VirusTotal IoC Checker Created by Khoilg')
    parser.add_argument('-i', nargs='+', metavar='IP', help='Check one or more IP addresses')
    parser.add_argument('-m', nargs='+', metavar='MD5', help='Check one or more MD5 hashes')
    parser.add_argument('-sha256', nargs='+', metavar='SHA256', help='Check one or more SHA256 hashes')
    parser.add_argument('-sha1', nargs='+', metavar='SHA1', help='Check one or more SHA1 hashes')
    parser.add_argument('-d', nargs='+', metavar='DOMAIN', help='Check one or more domains')
    parser.add_argument('-dir', '--directory', metavar='DIRECTORY', help='Check all files in a directory')
    parser.add_argument('-f', '--file', metavar='FILE', help='Check IoCs from a file containing one IoC per line')
    parser.add_argument('-o', '--output', metavar='OUTPUT_FILE', help='Save results to a file')
    parser.add_argument('-t', '--type', choices=['csv', 'db', 'txt'], default='txt',
                        help='Choose the type of output file (CSV, Sqlite3 or TXT), default is TXT')
    parser.add_argument('-a', '--api-key', metavar='APIKEY', help='Add or update the VirusTotal API key')
    parser.add_argument('-c', '--clear-api', action='store_true', help='Clear the saved VirusTotal API key')
    parser.add_argument('-s', '--check-api', action='store_true',
                        help='Check if the VirusTotal API key exists and display it')
    return parser.parse_args()

banner_part1 = """

 ██▓ ▒█████   ▄████▄    ██████     ▄████▄   ██░ ██ ▓█████  ▄████▄   ██ ▄█▀ ██▓ ███▄    █   ▄████    
▓██▒▒██▒  ██▒▒██▀ ▀█  ▒██    ▒    ▒██▀ ▀█  ▓██░ ██▒▓█   ▀ ▒██▀ ▀█   ██▄█▒ ▓██▒ ██ ▀█   █  ██▒ ▀█▒   
▒██▒▒██░  ██▒▒▓█    ▄ ░ ▓██▄      ▒▓█    ▄ ▒██▀▀██░▒███   ▒▓█    ▄ ▓███▄░ ▒██▒▓██  ▀█ ██▒▒██░▄▄▄░   
░██░▒██   ██░▒▓▓▄ ▄██▒  ▒   ██▒   ▒▓▓▄ ▄██▒░▓█ ░██ ▒▓█  ▄ ▒▓▓▄ ▄██▒▓██ █▄ ░██░▓██▒  ▐▌██▒░▓█  ██▓   
░██░░ ████▓▒░▒ ▓███▀ ░▒██████▒▒   ▒ ▓███▀ ░░▓█▒░██▓░▒████▒▒ ▓███▀ ░▒██▒ █▄░██░▒██░   ▓██░░▒▓███▀▒   
░▓  ░ ▒░▒░▒░ ░ ░▒ ▒  ░▒ ▒▓▒ ▒ ░   ░ ░▒ ▒  ░ ▒ ░░▒░▒░░ ▒░ ░░ ░▒ ▒  ░▒ ▒▒ ▓▒░▓  ░ ▒░   ▒ ▒  ░▒   ▒    
 ▒ ░  ░ ▒ ▒░   ░  ▒   ░ ░▒  ░ ░     ░  ▒    ▒ ░▒░ ░ ░ ░  ░  ░  ▒   ░ ░▒ ▒░ ▒ ░░ ░░   ░ ▒░  ░   ░    
 ▒ ░░ ░ ░ ▒  ░        ░  ░  ░     ░         ░  ░░ ░   ░   ░        ░ ░░ ░  ▒ ░   ░   ░ ░ ░ ░   ░    
 ░      ░ ░  ░ ░            ░     ░ ░       ░  ░  ░   ░  ░░ ░      ░  ░    ░           ░       ░    
             ░                    ░                       ░                                                                  
"""

banner_part2 = """
v3.1.4
By Khoilg
"""
banner = banner_part1 + banner_part2

def main():
    print(Fore.RESET + banner)
    print(Fore.WHITE)

    args = parse_arguments()
    results = []

    if args.check_api:
        api_key = get_saved_api_key()
        if api_key:
            print("The current API key is: " + api_key)
        else:
            print("No API key has been set.")
        return

    if args.api_key:
        save_api_key(args.api_key)
        return

    if args.clear_api:
        clear_api_key()
        return

    api_key = get_saved_api_key()
    if not api_key:
        print("No API key found. Please add an API key with the -a option.")
        return

    try:
        if args.i:
            for ip in args.i:
                if is_valid_ip(ip):
                    result = check_ip_virustotal(ip, api_key)
                    if result:
                        results.append(result)
                        print_result(result)
                else:
                    print(f"Invalid IP address: {ip}")

        if args.m:
            for md5 in args.m:
                if is_valid_md5(md5):
                    result = check_md5_virustotal(md5, api_key)
                    if result:
                        results.append(result)
                        print_result(result)
                else:
                    print(f"Invalid MD5 hash: {md5}")

        if args.sha256:
            for sha256 in args.sha256:
                if is_valid_sha256(sha256):
                    result = check_sha256_virustotal(sha256, api_key)
                    if result:
                        results.append(result)
                        print_result(result)
                else:
                    print(f"Invalid SHA256 hash: {sha256}")

        if args.sha1:
            for sha1 in args.sha1:
                if is_valid_sha1(sha1):
                    result = check_sha1_virustotal(sha1, api_key)
                    if result:
                        results.append(result)
                        print_result(result)
                else:
                    print(f"Invalid SHA1 hash: {sha1}")

        if args.directory:
            if os.path.isdir(args.directory):
                files = os.listdir(args.directory)
                if not files:
                    print(f"The directory {args.directory} is empty.")
                else:
                    with open('hashes.txt', 'w') as hashes_file:
                        for root, dirs, files in os.walk(args.directory):
                            for file in files:
                                file_path = os.path.join(root, file)
                                md5 = calculate_md5_hash(file_path)
                                hashes_file.write(md5 + '\n')

                    with open('hashes.txt', 'r') as hashes_file:
                        for line in hashes_file:
                            md5 = line.strip()
                            try:
                                result = check_md5_virustotal(md5, api_key)
                                if result:
                                    results.append(result)
                                    print_result(result)
                            except Exception as e:
                                print(e)
            else:
                print(f"The directory {args.directory} does not exist.")

        if args.d:
            for domain in args.d:
                result = check_domain_virustotal(domain, api_key)
                if result:
                    results.append(result)
                    print_result(result)

        if args.file:
            if os.path.isfile(args.file):
                with open(args.file, 'r') as file:
                    for line in file:
                        line = line.strip()
                        if line:
                            if all(char.isdigit() or char == '.' for char in line):
                                result = check_ip_virustotal(line, api_key)
                            elif '.' in line and not any(char.isdigit() for char in line.split('.')[0]):
                                result = check_domain_virustotal(line, api_key)
                            else:
                                result = check_md5_virustotal(line, api_key)
                            if result:
                                results.append(result)
                                print_result(result)
            else:
                print(f"The file {args.f} does not exist.")
    except Exception as e:
        print(str(e))
    finally:
        if args.output:
            output_dir = os.path.dirname(args.output)
            if not output_dir:
                output_dir = os.getcwd()
            output_filename = f"IoC_Check_Result.{args.type}"
            output_file = os.path.join(output_dir, output_filename)
            if os.path.isdir(args.output):
                output_file = os.path.join(args.output, output_filename)
            save_results(results, output_file, args.type)

def save_results(results, output_file, file_type):
    existing_iocs = set()

    if file_type == 'db' and os.path.exists(output_file):
        conn = sqlite3.connect(output_file)
        cursor = conn.cursor()
        cursor.execute("SELECT ioc FROM iocs")
        existing_iocs.update(row[0] for row in cursor.fetchall())
        conn.close()

    if file_type == 'csv' and os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader, None)
            for row in csv_reader:
                if row:
                    existing_iocs.add(row[0])

    with open(output_file, 'a', newline='', encoding='utf-8') as file:
        if file_type == 'csv':
            csv_writer = csv.writer(file)
            if output_file not in existing_iocs:
                file.seek(0, 2)
                if file.tell() == 0:
                    csv_writer.writerow(['IoCs', 'Engine', 'Link', 'Date'])
            for result in results:
                if result.get('Detected_by'):
                    ioc = result.get('IP', '') or result.get('MD5', '') or result.get('Domain', '')
                    if ioc not in existing_iocs:
                        detected_by = ', '.join(result['Detected_by']) if isinstance(result.get('Detected_by'),
                                                                                     list) else result.get(
                            'Detected_by')
                        csv_writer.writerow(
                            [ioc, detected_by, result.get('Link', 'none'), result.get('Last_scanned', 'none')])
                        existing_iocs.add(ioc)
            print(f"=> CSV File results are saved in {os.path.abspath(output_file)}")

        elif file_type == 'txt':
            for result in results:
                ioc = result.get('IP', '') or result.get('MD5', '') or result.get('Domain', '')
                if ioc and ioc not in existing_iocs:
                    json_result = json.dumps(result, indent=4)
                    json_result = json_result.replace('"', '')
                    json_result = json_result.replace('{', '')
                    json_result = json_result.replace('}', '')
                    json_result = json_result.replace(',', '')
                    file.write(json_result + '\n')
                    existing_iocs.add(ioc)
            print(f"=> TXT File results are saved in {os.path.abspath(output_file)}")

        elif file_type == 'db':
            conn = sqlite3.connect(output_file)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS iocs (ioc TEXT PRIMARY KEY, score TEXT, last_scanned TEXT)''')
            for result in results:
                ioc = result.get('IP', '') or result.get('MD5', '') or result.get('Domain', '')
                score = result.get('Score', '0/90')
                score_value = int(score.split('/')[0]) if '/' in score else 0
                if ioc and ioc not in existing_iocs and score_value >= 1:
                    cursor.execute("INSERT INTO iocs (ioc, score, last_scanned) VALUES (?, ?, ?)",
                                   (ioc, score, result.get('Last_scanned', 'none')))
                    existing_iocs.add(ioc)
            conn.commit()
            conn.close()
            print(f"=> DB File results are saved in {os.path.abspath(output_file)}")

def print_result(result):
    if 'IP' in result:
        print(f"IP: {result['IP']}")
    elif 'Domain' in result:
        print(f"Domain: {result['Domain']}")
    elif 'MD5' in result:
        print(f"MD5: {result['MD5']}")
    print(f"Last Scanned: {result['Last_scanned']}")
    print(f"Score: {result['Score']}")
    print(f"Detected by: {result['Detected_by']}")
    print(f"Link: {result['Link']}\n")

if __name__ == "__main__":
    main()