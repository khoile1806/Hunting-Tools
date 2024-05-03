import os
import csv
import json
import sqlite3
import requests
import argparse
from colorama import Fore
from datetime import datetime

API_KEY_FILE = 'api_key.txt'


def check_ip_virustotal(ip, api_key):
    url = f'https://www.virustotal.com/api/v3/ip_addresses/{ip}'
    headers = {'x-apikey': api_key}
    response = requests.get(url, headers=headers)
    if response.ok:
        data = response.json()
        last_scanned = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        engines_detected = [engine for engine, detection in data['data']['attributes']['last_analysis_results'].items()
                            if detection['category'] == 'malicious']
        harmless_votes = data['data']['attributes']['last_analysis_stats']['harmless']
        suspicous_votes = data['data']['attributes']['last_analysis_stats']['suspicious']
        undetected_votes = data['data']['attributes']['last_analysis_stats']['undetected']
        malicious_votes = data['data']['attributes']['last_analysis_stats']['malicious']
        score = f"{malicious_votes}/{malicious_votes + harmless_votes + suspicous_votes + undetected_votes}"
        result = {
            'IP': ip,
            'Last_scanned': last_scanned,
            'Score': score,
            'Detected_by': ', '.join(engines_detected),
            'Link': f"https://www.virustotal.com/gui/ip-address/{ip}/detection"
        }
        return result
    else:
        print(f"Unable to check the IP: {ip}")


def check_md5_virustotal(md5, api_key):
    url = "https://www.virustotal.com/vtapi/v2/file/report"
    params = {'apikey': api_key, 'resource': md5}
    response = requests.get(url, params=params)
    if response.ok:
        result = response.json()
        if result.get('response_code') == 1:
            scan_date_str = result.get('scan_date')
            scan_date = datetime.strptime(scan_date_str, '%Y-%m-%d %H:%M:%S') if isinstance(scan_date_str,
                                                                                            str) else datetime.fromtimestamp(
                scan_date_str)
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
            print(f"File with MD5 {md5} is not found in VirusTotal database.")
    else:
        print(f"Unable to check the MD5: {md5}")


def check_domain_virustotal(domain, api_key):
    url = f'https://www.virustotal.com/api/v3/domains/{domain}'
    headers = {'x-apikey': api_key}
    response = requests.get(url, headers=headers)
    if response.ok:
        data = response.json()
        last_modified = data['data']['attributes']['last_modification_date']
        last_scanned = datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S') if last_modified else 'N/A'
        malicious_votes = data['data']['attributes']['last_analysis_stats']['malicious']
        harmless_votes = data['data']['attributes']['last_analysis_stats']['harmless']
        suspicous_votes = data['data']['attributes']['last_analysis_stats']['suspicious']
        undetected_votes = data['data']['attributes']['last_analysis_stats']['undetected']
        score = f"{malicious_votes}/{malicious_votes + harmless_votes + suspicous_votes + undetected_votes}"
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
        print(f"Unable to check the domain: {domain}")


def save_api_key(api_key):
    with open(API_KEY_FILE, 'w') as file:
        file.write(api_key)
    print("API key saved successfully.")


def clear_api_key():
    if os.path.exists(API_KEY_FILE):
        os.remove(API_KEY_FILE)
        print("API key has been cleared.")
    else:
        print("No API key to clear.")


def get_saved_api_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, 'r') as file:
            return file.read().strip()
    return None


def parse_arguments():
    parser = argparse.ArgumentParser(description='VirusTotal IoC Checker Created by Khoilg')
    parser.add_argument('-i', nargs='+', metavar='IP', help='Check one or more IP addresses')
    parser.add_argument('-m', nargs='+', metavar='MD5', help='Check one or more MD5 hashes')
    parser.add_argument('-d', nargs='+', metavar='DOMAIN', help='Check one or more domains')
    parser.add_argument('-f', '--file', metavar='FILE', help='Check IoCs from a file containing one IoC per line')
    parser.add_argument('-o', '--output', metavar='OUTPUT_FILE', help='Save results to a file')
    parser.add_argument('-t', '--type', choices=['csv', 'db', 'txt'], default='txt',
                        help='Choose the type of output file (CSV, Sqlite3 or TXT), default is TXT')
    parser.add_argument('-a', '--api-key', metavar='APIKEY', help='Add or update the VirusTotal API key')
    parser.add_argument('-c', '--clear-api', action='store_true', help='Clear the saved VirusTotal API key')
    parser.add_argument('-s', '--check-api', action='store_true',
                        help='Check if the VirusTotal API key exists and display it.')
    return parser.parse_args()

banner = """

▄█ ████▄ ▄█▄       ▄▄▄▄▄       ▄█▄     ▄  █ ▄███▄   ▄█▄    █  █▀ ▄█    ▄     ▄▀  
██ █   █ █▀ ▀▄    █     ▀▄     █▀ ▀▄  █   █ █▀   ▀  █▀ ▀▄  █▄█   ██     █  ▄▀    
██ █   █ █   ▀  ▄  ▀▀▀▀▄       █   ▀  ██▀▀█ ██▄▄    █   ▀  █▀▄   ██ ██   █ █ ▀▄  
▐█ ▀████ █▄  ▄▀  ▀▄▄▄▄▀        █▄  ▄▀ █   █ █▄   ▄▀ █▄  ▄▀ █  █  ▐█ █ █  █ █   █ 
 ▐       ▀███▀                 ▀███▀     █  ▀███▀   ▀███▀    █    ▐ █  █ █  ███  
                                        ▀                   ▀       █   ██       
                    
v3.2
By Khoilg
"""

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

    if args.i:
        for ip in args.i:
            result = check_ip_virustotal(ip, api_key)
            if result:
                results.append(result)
                print_result(result)

    if args.m:
        for md5 in args.m:
            result = check_md5_virustotal(md5, api_key)
            if result:
                results.append(result)
                print_result(result)

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
            print(f"=> Kết quả đã được lưu vào tệp .db tại {os.path.abspath(output_file)}")


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