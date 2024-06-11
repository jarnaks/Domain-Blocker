import os
import platform
import shutil
import requests
import re
import json
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

CONFIG_FILE = 'config.json'

def get_hosts_file_path():
    if platform.system() == 'Windows':
        path = r'C:\blocked_hosts\hosts'
    else:
        path = '/etc/blocked_hosts/hosts'
    return path

def backup_hosts_file(hosts_path):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = f"{hosts_path}_backup_{timestamp}"
    try:
        shutil.copy2(hosts_path, backup_path)
        shutil.copy2(hosts_path, 'hosts_last_used')
        return backup_path
    except FileNotFoundError:
        messagebox.showerror("Error", f"Hosts file not found at {hosts_path}. Creating a new one.")
        ensure_directory_exists(hosts_path)
        open(hosts_path, 'w').close()  # Create an empty hosts file
        backup_hosts_file(hosts_path)  # Retry backing up the newly created hosts file
    except PermissionError:
        messagebox.showerror("Error", f"Permission denied: Unable to access {hosts_path}. Please run the script as an administrator.")
        raise

def restore_hosts_file():
    hosts_path = get_hosts_file_path()
    if os.path.exists('hosts_last_used'):
        shutil.copy2('hosts_last_used', hosts_path)
        messagebox.showinfo("Restore", "Hosts file restored to the last used state.")
    else:
        messagebox.showerror("Restore", "No backup found to restore.")

#def download_and_parse_lists(urls):
    #domains = set()
    #for url in urls:
        #try:
            #response = requests.get(url)
            #response.raise_for_status()
            #domains.update(re.findall(r'^\s*(?:0\.0\.0\.0|127\.0\.0\.1)\s+(\S+)', response.text, re.MULTILINE))
        #except requests.RequestException as e:
            #print(f"Failed to download {url}: {e}")
    #return domains

def download_and_parse_lists(urls):
    domains = set()
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            # Debug print to check the content of the response
            print(f"Content from {url}:\n{response.text[:500]}...\n")  # Print first 500 characters
            for line in response.text.splitlines():
                line = line.strip()  # Remove leading/trailing whitespace
                if line.startswith('0.0.0.0') or line.startswith('127.0.0.1'):
                    parts = line.split()
                    if len(parts) > 1:
                        domain = parts[1]
                        domains.add(domain)
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
        urls.extend(config.get('ad_block_lists', []))

    if not urls:
        messagebox.showerror("Error", "No block lists selected.")
        return

    domains = download_and_parse_lists(urls)
    hosts_path = get_hosts_file_path()
    try:
        backup_hosts_file(hosts_path)
        append_to_hosts_file(hosts_path, domains)
        messagebox.showinfo("Success", "Hosts file updated successfully.")
    except PermissionError:
        # If backup_hosts_file raises a PermissionError catch here.
        return
        
def create_gui():
    root = tk.Tk()
    root.title("Hosts-Based Domain Blocker")

    tk.Label(root, text="Select the types of content to block:").pack(pady=10)

    block_ads = tk.BooleanVar()
    block_malware = tk.BooleanVar()
    block_tracking = tk.BooleanVar()
    block_malicious = tk.BooleanVar()

    tk.Checkbutton(root, text="Advertisements", variable=block_ads).pack(anchor='w')
    tk.Checkbutton(root, text="Malware", variable=block_malware).pack(anchor='w')
    tk.Checkbutton(root, text="Tracking", variable=block_tracking).pack(anchor='w')
    tk.Checkbutton(root, text="Malicious", variable=block_malicious).pack(anchor='w')

    tk.Button(root, text="Update Hosts File", command=lambda: update_hosts_file(block_ads.get(), block_malware.get(), block_tracking.get(), block_malicious)).pack(pady=10)
    tk.Button(root, text="Restore Hosts File", command=restore_hosts_file).pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    create_gui()
