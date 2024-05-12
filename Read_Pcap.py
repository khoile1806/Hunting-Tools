import csv
import os
import sqlite3
import argparse
from scapy.all import *
from collections import Counter

def get_ip_counts(packets, ip_layer, ip_field):
    ips = [packet[ip_layer].getfieldval(ip_field) for packet in packets if packet.haslayer(ip_layer)]
    return Counter(ips)

def write_to_file(filename, lines):
    with open(filename, 'w') as file:
        file.writelines(lines)
    print_file_saved_message(os.path.abspath(filename))

def print_file_saved_message(file_path):
    print(f"=> The results have been saved in {file_path}")

def write_ips_to_csv(filename, ips_count):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['IP', 'Count'])
        for ip, count in ips_count.items():
            writer.writerow([ip, count])
    print_file_saved_message(os.path.abspath(filename))

def write_ips_to_db(db_filename, ips_count):
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS ip_counts
                      (source_ip TEXT, destination_ip TEXT, count INTEGER)''')
    for ip, count in ips_count.items():
        cursor.execute("INSERT INTO ip_counts (source_ip, destination_ip, count) VALUES (?, ?, ?)",
                       (ip, ip, count))
    conn.commit()
    conn.close()
    print_file_saved_message(os.path.abspath(db_filename))

def get_ip_pairs(packets):
    ip_pairs = [(packet[IP].src, packet[IP].dst) for packet in packets if packet.haslayer(IP)]
    return ip_pairs

def get_ip_flags_pairs(packets):
    ip_flags_pairs = [(packet[IP].src, packet[IP].dst, packet[TCP].sprintf("%TCP.flags%"))
                      for packet in packets if packet.haslayer(IP) and packet.haslayer(TCP)]
    return ip_flags_pairs

parser = argparse.ArgumentParser(description='Analyze pcap file Created by Khoilg')
parser.add_argument('-i', '--input', help='Path to the pcap file to analyze', required=True)
parser.add_argument('-p', '--print', action='store_true', help='Print connection of file to terminal')
parser.add_argument('-o', '--output', help='Path to save the output files. If ".", files will be saved in the current directory')
parser.add_argument('-t', '--type', help='Type of the output file (txt, csv or db)', choices=['txt', 'csv','db'], default='txt')
args = parser.parse_args()

if not any([args.output, args.type != 'txt', args.print]):
    parser.print_help()
    print("\nPlease select additional options.")
    exit()

pcap_file = args.input
if not os.path.isfile(pcap_file):
    print(f"The file {pcap_file} does not exist. Please try again.")
    exit()

try:
    packets = rdpcap(pcap_file)
    ip_flags_pairs = get_ip_flags_pairs(packets)
except Exception as e:
    print(f"Error: {e}")
    exit()

destination_ip_counts = get_ip_counts(packets, IP, 'dst')
source_ip_counts = get_ip_counts(packets, IP, 'src')

output_terminal_lines = ["Connections Tracking \n"]
output_terminal_lines += [f"{src} <=> [{flags}] <=> {dst}\n" for src, dst, flags in ip_flags_pairs]

if args.print:
    print(''.join(output_terminal_lines))
elif args.output:
    output_path = args.output if args.output != '.' else ''
    if args.type == 'txt':
        output_file_lines = [f"{ip}\n" for ip in destination_ip_counts.keys()]
        output_filename = os.path.join(output_path, "ip.txt")
        write_to_file(output_filename, output_file_lines)
    elif args.type == 'csv':
        output_csv_filename = os.path.join(output_path, "ip.csv")
        write_ips_to_csv(output_csv_filename, destination_ip_counts)
    elif args.type == 'db':
        db_filename = os.path.join(output_path, "ip.db")
        write_ips_to_db(db_filename, destination_ip_counts)