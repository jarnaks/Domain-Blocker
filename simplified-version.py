import requests
import platform
import re
import json
import tkinter as tk
from tkinter import messagebox

CONFIG_FILE = 'config.json'

def get_hosts_file_path():
   return r'D:\test\hosts' if platform.system() == 'Windows' else '/etc/hosts'

def download_and_parse_lists(urls):
    domains = set()
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            domains.update(re.findall(r'^\s*(?:0\.0\.0\.0|127\.0\.0\.1)\s+(\S+)', response.text, re.MULTILINE))
        except requests.RequestException as e:
            print(f"Failed to download {url}: {e}")
    return domains

def append_to_hosts_file(hosts_path, domains):
    with open(hosts_path, 'a') as hosts_file:
        hosts_file.write('\n'.join(f"0.0.0.0 {domain}" for domain in domains) + '\n')

def update_hosts_file(block_ads, block_malware, block_tracking, block_malicious):
    with open(CONFIG_FILE, 'r') as file:
        config = json.load(file)

    urls = []
    if block_ads:
        urls.extend(config.get('ad_block_lists', []))
    if block_malware:
        urls.extend(config.get('malware_block_lists', []))
    if block_tracking:
        urls.extend(config.get('tracking_block_lists', []))
    if block_malicious:
        urls.extend(config.get('malicious_block_lists', []))

    if not urls:
        messagebox.showerror("Error", "No block lists selected.")
        return

    domains = download_and_parse_lists(urls)
    hosts_path = get_hosts_file_path()
    append_to_hosts_file(hosts_path, domains)
    messagebox.showinfo("Success", "Hosts file updated successfully.")

def create_gui():
    root = tk.Tk()
    root.title("Hosts-Based Domain Blocker")

    block_ads = tk.BooleanVar()
    block_malware = tk.BooleanVar()
    block_tracking = tk.BooleanVar()
    block_malicious = tk.BooleanVar()

    tk.Checkbutton(root, text="Advertisements", variable=block_ads).pack(anchor='w')
    tk.Checkbutton(root, text="Malware", variable=block_malware).pack(anchor='w')
    tk.Checkbutton(root, text="Tracking", variable=block_tracking).pack(anchor='w')
    tk.Checkbutton(root, text="Malicious", variable=block_malicious).pack(anchor='w')

    tk.Button(root, text="Update Hosts File", command=lambda: update_hosts_file(block_ads.get(), block_malware.get(), block_tracking.get(), block_malicious.get())).pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    create_gui()
