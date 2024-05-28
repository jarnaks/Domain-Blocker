import os
import platform
import shutil
import requests
import re
import json
from argparse import ArgumentParser

# Configuration
CONFIG_FILE = 'config.json'
BACKUP_HOSTS_FILE = 'hosts_backup'
LAST_USED_HOSTS_FILE = 'hosts_last_used'

# Determine the hosts file path based on the OS
def get_hosts_file_path():
    if platform.system() == 'Windows':
        return r'C:\Windows\System32\drivers\etc\hosts'
    else:
        return '/etc/hosts'

# Backup the original hosts file
def backup_hosts_file(hosts_path):
    shutil.copy2(hosts_path, BACKUP_HOSTS_FILE)
    shutil.copy2(hosts_path, LAST_USED_HOSTS_FILE)

# Restore the original hosts file
def restore_hosts_file(hosts_path):
    shutil.copy2(BACKUP_HOSTS_FILE, hosts_path)

# Download and parse block lists
def download_and_parse_lists(urls):
    domains = set()
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.text
            # Extract domains using regex
            found_domains = re.findall(r'^\s*(?:0\.0\.0\.0|127\.0\.0\.1)\s+(\S+)', content, re.MULTILINE)
            domains.update(found_domains)
        except requests.RequestException as e:
            print(f"Failed to download {url}: {e}")
    return domains

# Append domains to the hosts file
def append_to_hosts_file(hosts_path, domains):
    with open(hosts_path, 'a') as hosts_file:
        for domain in domains:
            hosts_file.write(f"0.0.0.0 {domain}\n")

# Main function
def main(block_ads, block_malware, block_tracking):
    # Load configuration
    with open(CONFIG_FILE, 'r') as file:
        config = json.load(file)

    # Collect URLs based on user choice
    urls_to_download = []
    if block_ads:
        urls_to_download.extend(config.get('ad_block_lists', []))
    if block_malware:
        urls_to_download.extend(config.get('malware_block_lists', []))
    if block_tracking:
        urls_to_download.extend(config.get('tracking_block_lists', []))

    if not urls_to_download:
        print("No block lists selected. Exiting.")
        return

    # Download and parse the lists
    domains = download_and_parse_lists(urls_to_download)

    # Get the hosts file path
    hosts_path = get_hosts_file_path()

    # Backup the original hosts file
    backup_hosts_file(hosts_path)

    # Append domains to the hosts file
    append_to_hosts_file(hosts_path, domains)

    print("Hosts file updated successfully.")

if __name__ == '__main__':
    parser = ArgumentParser(description="Hosts-Based Domain Blocker")
    parser.add_argument('--block-ads', action='store_true', help="Block advertisement domains")
    parser.add_argument('--block-malware', action='store_true', help="Block malware domains")
    parser.add_argument('--block-tracking', action='store_true', help="Block tracking domains")
    args = parser.parse_args()

    main(args.block_ads, args.block_malware, args.block_tracking)
