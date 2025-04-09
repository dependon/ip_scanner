import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import platform
import queue
import time
from concurrent.futures import ThreadPoolExecutor
import locale
import webbrowser
import json

class IPScanner:
    def __init__(self):
        self.is_running = False
        self.result_queue = queue.Queue()
        self.current_ip_queue = queue.Queue()
        self.network_segment = "192.168.2"  # 默认网段
        self.thread_pool = ThreadPoolExecutor(max_workers=50)  # 创建线程池，最大50个线程

    def ping(self, ip):
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', ip]
        try:
            output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1)
            return output.returncode == 0
        except subprocess.TimeoutExpired:
            return False

    def set_network_segment(self, segment):
        self.is_running = False  # 停止当前扫描
        self.network_segment = segment
        self.result_queue = queue.Queue()  # 清空结果队列
        self.current_ip_queue = queue.Queue()  # 清空进度队列

    def scan_ip(self, i, total):
        if not self.is_running:
            return
        ip = f'{self.network_segment}.{i}'
        self.current_ip_queue.put((ip, (i - 1) / total * 100))
        if self.ping(ip):
            self.result_queue.put(ip)

    def scan_range(self, start_ip, end_ip):
        total = end_ip - start_ip + 1
        futures = []
        for i in range(start_ip, end_ip + 1):
            if not self.is_running:
                break
            futures.append(self.thread_pool.submit(self.scan_ip, i, total))
            
        # 等待所有任务完成
        for future in futures:
            future.result()

class App:
    def __init__(self, root):
        self.root = root
        
        # 加载配置
        self.config_file = 'ip_scanner_config.json'
        self.language = self.load_config() or ('zh' if (locale.getlocale()[0] or locale.getdefaultlocale()[0]).startswith('zh') else 'en')
        
        # 多语言文本
        self.texts = {
            'zh': {
                'title': 'IP扫描器',
                'status_ready': '准备扫描...',
                'network_label': '网段:',
                'start_button': '开始扫描',
                'stop_button': '停止扫描',
                'result_frame': '扫描结果',
                'error_empty': '请输入网段！',
                'scanning': '正在扫描: {ip}',
                'scan_complete': '扫描完成',
                'found_ip': '发现活动IP: {ip}'
            },
            'en': {
                'title': 'IP Scanner',
                'status_ready': 'Ready to scan...',
                'network_label': 'Network:',
                'start_button': 'Start Scan',
                'stop_button': 'Stop Scan',
                'result_frame': 'Scan Results',
                'error_empty': 'Please enter network segment!',
                'scanning': 'Scanning: {ip}',
                'scan_complete': 'Scan complete',
                'found_ip': 'Active IP found: {ip}'
            }
        }
        
        self.root.title(self.texts[self.language]['title'])
        self.root.geometry('400x500')
        
        self.scanner = IPScanner()
        self.scan_thread = None
        
        # 创建界面元素
        self.create_widgets()
        
    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config.get('language')
        except (FileNotFoundError, json.JSONDecodeError):
            return None
            
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump({'language': self.language}, f)
            
    def switch_language(self):
        self.language = 'en' if self.language == 'zh' else 'zh'
        self.save_config()
        # 重启程序

        os.execv(sys.executable, ['python'] + sys.argv)
        
    def update_ui_text(self):
        # 更新所有UI文本
        self.status_label.config(text=self.texts[self.language]['status_ready'])
        self.start_button.config(text=self.texts[self.language]['start_button'])
        self.stop_button.config(text=self.texts[self.language]['stop_button'])
        self.segment_frame.winfo_children()[0].config(text=self.texts[self.language]['network_label'])
        self.result_frame.config(text=self.texts[self.language]['result_frame'])
        
    def create_widgets(self):
        # 控制框架
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10, padx=10, fill='x')
        
        # 状态标签
        self.status_label = ttk.Label(self.root, text=self.texts[self.language]['status_ready'])
        self.status_label.pack(pady=5)
        
        # 网段输入框
        segment_frame = ttk.Frame(control_frame)
        segment_frame.pack(side='left', padx=5)
        
        ttk.Label(segment_frame, text=self.texts[self.language]['network_label']).pack(side='left')
        self.segment_entry = ttk.Entry(segment_frame, width=15)
        self.segment_entry.pack(side='left')
        self.segment_entry.insert(0, '192.168.2')
        
        self.start_button = ttk.Button(control_frame, text=self.texts[self.language]['start_button'], command=self.start_scan)
        self.start_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(control_frame, text=self.texts[self.language]['stop_button'], command=self.stop_scan, state='disabled')
        self.stop_button.pack(side='left', padx=5)
        
        # 进度条
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(pady=10, padx=10, fill='x')
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(self.root, text=self.texts[self.language]['result_frame'])
        result_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        self.result_text = tk.Text(result_frame, height=15)
        self.result_text.pack(pady=5, padx=5, fill='both', expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, command=self.result_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        # GitHub链接标签
        github_frame = ttk.Frame(self.root)
        github_frame.pack(side='bottom', pady=5)
        # 语言切换按钮
        language_button = ttk.Button(github_frame, text="中文/English", command=self.switch_language)
        language_button.pack(side='left', padx=5)
        
        github_label = ttk.Label(github_frame, text="GitHub: https://github.com/dependon/ip_scanner", cursor="hand2")
        github_label.pack(side='left', padx=5)
        github_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/dependon/ip_scanner"))
        
    def start_scan(self):
        # 获取并设置网段
        network_segment = self.segment_entry.get().strip()
        if not network_segment:
            tk.messagebox.showerror(self.texts[self.language]['title'], self.texts[self.language]['error_empty'])
            return
        
        self.scanner.set_network_segment(network_segment)
        self.result_text.delete(1.0, tk.END)
        self.progress['value'] = 0
        self.scanner.is_running = True
        self.start_button['state'] = 'disabled'
        self.stop_button['state'] = 'normal'
        
        # 启动扫描线程
        self.scan_thread = threading.Thread(target=self.scan_process)
        self.scan_thread.start()
        
        # 启动更新界面的线程
        self.update_ui()
    
    def stop_scan(self):
        self.scanner.is_running = False
        self.start_button['state'] = 'normal'
        self.stop_button['state'] = 'disabled'
    
    def scan_process(self):
        self.scanner.scan_range(1, 254)
    
    def update_ui(self):
        if not self.scanner.is_running and self.scan_thread and not self.scan_thread.is_alive():
            self.start_button['state'] = 'normal'
            self.stop_button['state'] = 'disabled'
            self.progress['value'] = 100
            self.status_label.config(text=self.texts[self.language]['scan_complete'])
            return
        
        # 更新当前扫描的IP和进度条
        while not self.scanner.current_ip_queue.empty():
            ip, progress = self.scanner.current_ip_queue.get()
            self.status_label.config(text=self.texts[self.language]['scanning'].format(ip=ip))
            self.progress['value'] = progress
        
        # 检查并显示结果
        while not self.scanner.result_queue.empty():
            ip = self.scanner.result_queue.get()
            self.result_text.insert(tk.END, self.texts[self.language]['found_ip'].format(ip=ip)+'\n')
            self.result_text.see(tk.END)
        
        self.root.after(100, self.update_ui)

def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == '__main__':
    main()