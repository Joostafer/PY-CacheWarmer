import tkinter as tk
from tkinter import ttk
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import Counter
from urllib.parse import urlparse
from datetime import datetime


class LinkExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Link Extractor")

        # Create a label and entry for the URL input
        self.label = tk.Label(root, text="Enter URL:")
        self.label.pack(padx=10, pady=10)
        self.url_entry = tk.Entry(root, width=50)
        self.url_entry.insert(0, self.load_last_url())
        self.url_entry.pack(padx=10, pady=10)
        self.url_entry.bind('<Command-v>', self.paste)


        # Create the buttons to start the extraction
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(padx=10, pady=10)
        self.get_internal_button = tk.Button(self.button_frame, text="Extract Internal Links",
                                             command=self.extract_internal_links)
        self.get_external_button = tk.Button(self.button_frame, text="Extract External Links",
                                             command=self.extract_external_links)
        self.get_internal_button.pack(side=tk.LEFT)
        self.get_external_button.pack(side=tk.LEFT)

        # Create a Treeview for the extracted URLs
        self.tree = ttk.Treeview(root, columns=("URLs", "Count"), show="headings")
        self.tree.heading("URLs", text="Extracted URLs")
        self.tree.heading("Count", text="Count")
        self.tree.pack(padx=10, pady=10, expand=True, fill='both')
        self.tree.bind("<Double-1>", self.on_double_click)

        process_button = ttk.Button(root, text="Process All Links", command=self.process_all_links)
        process_button.pack()

    def on_double_click(self, event):
        selected_item = self.tree.selection()[0]
        selected_url = self.tree.item(selected_item)['values'][1]

        # Send a request to the URL
        start_time = datetime.now()
        try:
            response = requests.get(selected_url)
            elapsed_time = (datetime.now() - start_time).total_seconds()

            # Insert the status and elapsed time in the treeview
            self.tree.item(selected_item, values=(
                *self.tree.item(selected_item)["values"], response.status_code, elapsed_time))

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")

    def on_tree_select(self):
        selected_item = self.tree.selection()[0]

    def process_all_links(self, step=0):
        children = self.tree.get_children()
        if not children or step >= len(children):
            return

        self.tree.selection_set(children[step])
        selected_item = self.tree.selection()[0]

        if selected_item:
            self.on_double_click(None)

        self.root.after(200, lambda: self.process_all_links(step + 1))

    def paste(self, event):
        self.url_entry.insert(tk.INSERT, self.root.clipboard_get())

    def extract_internal_links(self):
        # Delete the previous entries
        # Add additional columns in the treeview
        self.tree["columns"] = ("№", "URLs", "Count", "Status Code", "Response Time")
        self.tree.heading("№", text="№")
        self.tree.column("№", width=30)
        self.tree.heading("URLs", text="URLs")
        self.tree.heading("Count", text="Count")
        self.tree.heading("Status Code", text="Status Code")
        self.tree.heading("Response Time", text="Response Time")
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Fetch the URL from the entry
        url = self.url_entry.get()
        self.save_last_url(url)

        # Extract and add links to the treeview
        links = self.fetch_links(url, internal=True)
        for index, (link, count) in enumerate(sorted(links.items(), key=lambda item: item[1], reverse=True), start=1):
            self.tree.insert('', 'end', values=(index, link, count))

    def save_last_url(self, url):
        with open('last_url.txt', 'w') as f:
            f.write(url)

    def load_last_url(self):
        try:
            with open('last_url.txt', 'r') as f:
                url = f.read()
            return url
        except IOError:
            # If no file is found, simply return an empty string.
            return ""

    def extract_external_links(self):
        # Delete the previous entries
        for i in self.tree.get_children():
            self.tree.delete(i)

            # Fetch the URL from the entry
        url = self.url_entry.get()
        self.save_last_url(url)

        # Extract and add links to the treeview
        links = self.fetch_links(url, internal=False)
        for link, count in sorted(links.items(), key=lambda item: item[1], reverse=True):
            self.tree.insert('', 'end', values=(link, count))

    @staticmethod
    def fetch_links(url, internal):
        try:
            response = requests.get(url)
            if response.ok:
                soup = BeautifulSoup(response.text, 'html.parser')

                base_url = url
                base_domain = urlparse(url).netloc
                extracted_links = [a.get('href') for a in soup.find_all('a', href=True)]
                filtered_links = []

                for link in extracted_links:
                    if not (link.startswith('mailto:') or link.startswith('tel:') or link.startswith('javascript:')):
                        absolute_link = urljoin(base_url, link)  # Convert relative links to absolute
                        link_domain = urlparse(absolute_link).netloc
                        if internal and link_domain == base_domain:
                            filtered_links.append(absolute_link)
                        elif not internal and link_domain and link_domain != base_domain:
                            filtered_links.append(absolute_link)

                return dict(Counter(filtered_links))  # count duplicate links
            else:
                print("Error fetching the webpage.")
        except Exception as e:
            print(f"Error: {e}")
        return {}


if __name__ == "__main__":
    root = tk.Tk()
    app = LinkExtractorApp(root)
    root.mainloop()
