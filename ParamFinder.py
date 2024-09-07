import os
import re
import time
import errno
import random
import argparse
import requests
import subprocess
from colorama import Fore
from urllib.parse import unquote

start_time = time.time()

def save_func(final_urls, outfile, domain):
    filename = os.path.join('output', f'{outfile if outfile else domain}.txt')
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        for url in final_urls:
            f.write(url + "\n")

def connector(url):
    user_agent_list = [
        # Chrome
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        # Firefox
        'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
    ]
    headers = {'User-Agent': random.choice(user_agent_list)}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text, False
    except requests.exceptions.RequestException as e:
        print(f"\u001b[31;1m{e}.\u001b[0m")
        return None, True

def param_extract(response, level, black_list, placeholder):
    parsed = list(set(re.findall(r'.*?:\/\/.*\?.*\=[^$]', response)))
    final_uris = []

    for i in parsed:
        delim = i.find('=')
        second_delim = i.find('=', delim + 1)
        if not any(ext in i for ext in black_list):
            if placeholder:
                final_uris.append(i[:delim + 1] + placeholder)
                if level == 'high' and second_delim != -1:
                    final_uris.append(i[:second_delim + 1] + placeholder)
            else:
                final_uris.append(i[:delim + 1])
                if level == 'high' and second_delim != -1:
                    final_uris.append(i[:second_delim + 1])

    return list(set(final_uris))

def parser_arguments():
    parser = argparse.ArgumentParser(description='ParamSpider: a parameter discovery suite')
    parser.add_argument('-d', '--domain', help='Domain name of the target [ex: hackerone.com]', required=True)
    parser.add_argument('-s', '--subs', help='Set False for no subdomains [ex: --subs False]', type=bool, default=True)
    parser.add_argument('-l', '--level', help='For nested parameters [ex: --level high]', default='low')
    parser.add_argument('-e', '--exclude', help='Extensions to exclude [ex: --exclude php,aspx]')
    parser.add_argument('-o', '--output', help='Output file name [by default it is \'domain.txt\']')
    parser.add_argument('-p', '--placeholder', help='The string to add as a placeholder after the parameter name.',
                        default="")
    parser.add_argument('-q', '--quiet', help='Do not print the results to the screen', action='store_true')
    parser.add_argument('-r', '--retries', help='Specify number of retries for 4xx and 5xx errors', type=int, default=3)
    return parser.parse_args()

def main():
    args = parser_arguments()

    url = f"https://web.archive.org/cdx/search/cdx?url={'*.' if args.subs else ''}{args.domain}/*&output=txt&fl=original&collapse=urlkey&page=/"
    retries = 0
    while retries < args.retries:
        response, retry = connector(url)
        if not retry:
            break
        retries += 1

    if not response:
        print("\u001b[31;1mFailed to retrieve data after multiple retries.\u001b[0m")
        return

    response = unquote(response)
    black_list = [f".{ext}" for ext in args.exclude.split(",")] if args.exclude else []

    if black_list:
        print(
            f"\u001b[31m[!] URLs containing these extensions will be excluded from the results: {black_list}\u001b[0m\n")

    final_uris = param_extract(response, args.level, black_list, args.placeholder)
    save_func(final_uris, args.output, args.domain)

    if not args.quiet:
        print("\u001b[32;1m")
        print('\n'.join(final_uris))
        print("\u001b[0m")

    print(f"\n\u001b[32m[+] Total number of retries:  {retries}\u001b[31m")
    print(f"\u001b[32m[+] Total unique URLs found: {len(final_uris)}\u001b[31m")
    output_path = f"output/{args.output if args.output else args.domain}.txt"
    print(f"\u001b[32m[+] Output is saved here: \u001b[31m\u001b[36m{output_path}\u001b[31m")
    print(f"\n\u001b[31m[!] Total execution time: {int(time.time() - start_time)}s\u001b[0m")

if __name__ == "__main__":
    main()
