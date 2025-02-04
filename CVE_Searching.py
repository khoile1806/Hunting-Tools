import csv
import json
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

def search_cve_improved(keyword, output_format=None, year=None, severity=None, sort_by=None):
    encoded_keyword = quote(keyword)
    search_url = f"https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword={encoded_keyword}"

    try:
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    results_table = soup.find('div', {'id': 'TableWithRules'})

    if not results_table:
        print("No results found.")
        return

    cve_list = []
    rows = results_table.find_all('tr')[1:]
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 2:
            cve_id = cols[0].get_text(strip=True)
            description = cols[1].get_text(strip=True)
            cve_url = f"https://www.cve.org/CVERecord?id={cve_id}"

            if year and year not in cve_id:
                continue

            if severity and severity.lower() not in description.lower():
                continue

            cve_list.append({"id": cve_id, "url": cve_url, "description": description})

    if not cve_list:
        print("No CVEs found.")
        return

    if sort_by == "newest":
        cve_list.sort(key=lambda x: x["id"], reverse=True)
    elif sort_by == "oldest":
        cve_list.sort(key=lambda x: x["id"])

    for cve in cve_list:
        print(f"{cve['id']}: {cve['url']}\nDescription: {cve['description']}\n")

    if output_format == "txt":
        output_txt_filename = "cve_results.txt"
        with open(output_txt_filename, "w", encoding="utf-8") as file:
            file.write(f"Found {len(cve_list)} CVEs related to '{keyword}':\n\n")
            for cve in cve_list:
                file.write(f"{cve['id']}: {cve['url']}\nDescription: {cve['description']}\n\n")
        print(f"Results saved to {output_txt_filename}")
    elif output_format == "csv":
        output_csv_filename = "cve_results.csv"
        with open(output_csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["ID", "URL", "Description"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for cve in cve_list:
                writer.writerow({"ID": cve['id'], "URL": cve['url'], "Description": cve['description']})
        print(f"Results saved to {output_csv_filename}")
    elif output_format == "json":
        output_json_filename = "cve_results.json"
        with open(output_json_filename, "w", encoding="utf-8") as jsonfile:
            json.dump(cve_list, jsonfile, indent=4, ensure_ascii=False)
        print(f"Results saved to {output_json_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search CVEs using a keyword or CVE ID with filtering options.")
    parser.add_argument("-k", "--keyword", type=str, required=True, help="Keyword or CVE ID to search for")
    parser.add_argument("-o", "--output", type=str, choices=["txt", "csv", "json"],
                        help="Output format: 'txt', 'csv' or 'json' (optional)")
    parser.add_argument("-y", "--year", type=str, help="Filter CVEs by year (e.g., 2024)")
    parser.add_argument("-s", "--severity", type=str,
                        help="Filter CVEs by severity (e.g., critical, high, medium, low)")
    parser.add_argument("--sort", type=str, choices=["newest", "oldest"], help="Sort results by 'newest' or 'oldest'")
    args = parser.parse_args()

    search_cve_improved(args.keyword, args.output, args.year, args.severity, args.sort)