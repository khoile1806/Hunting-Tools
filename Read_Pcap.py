from scapy.all import *
from collections import Counter
import csv

def get_ip_counts(packets, ip_layer, ip_field):
    ips = [packet[ip_layer].getfieldval(ip_field) for packet in packets if packet.haslayer(ip_layer)]
    return Counter(ips)

def write_to_file(filename, lines):
    with open(filename, 'w') as file:
        file.writelines(lines)

def write_ips_to_csv(filename, ips_count):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['IP', 'Count'])
        for ip, count in ips_count.items():
            writer.writerow([ip, count])

def get_ip_pairs(packets):
    ip_pairs = [(packet[IP].src, packet[IP].dst) for packet in packets if packet.haslayer(IP)]
    return ip_pairs

def get_ip_flags_pairs(packets):
    ip_flags_pairs = [(packet[IP].src, packet[IP].dst, packet[TCP].sprintf("%TCP.flags%"))
                      for packet in packets if packet.haslayer(IP) and packet.haslayer(TCP)]
    return ip_flags_pairs

pcap_file = ''
while not pcap_file:
    pcap_file = input("Enter the path to the pcap file: ")
    if not os.path.isfile(pcap_file):
        print(f"The file {pcap_file} does not exist. Please try again.")
        pcap_file = ''

try:
    packets = rdpcap(pcap_file)
    ip_flags_pairs = get_ip_flags_pairs(packets)
except Scapy_Exception as e:
    print(f"Error: {e}")
    exit()

destination_ip_counts = get_ip_counts(packets, IP, 'dst')
source_ip_counts = get_ip_counts(packets, IP, 'src')

output_terminal_lines = ["Connections Tracking \n"]
output_terminal_lines += [f"Source_ip {src} - [{flags}] - Destination_ip {dst}\n" for src, dst, flags in ip_flags_pairs]

print(''.join(output_terminal_lines))

print(''.join(output_terminal_lines))

output_file_lines = [f"{ip}\n" for ip in destination_ip_counts.keys()]
output_filename = "destination_ips.txt"
write_to_file(output_filename, output_file_lines)

output_csv_filename = "destination_ip_counts.csv"
write_ips_to_csv(output_csv_filename, destination_ip_counts)

print("=> TXT File results are saved in " + output_filename)
print("=> CSV File results are saved in " + output_csv_filename)