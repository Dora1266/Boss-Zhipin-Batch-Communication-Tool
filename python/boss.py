import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import json
import time
import random
import threading
import urllib.parse
import re


class BossZhipinBot:
    def __init__(self, root):
        self.root = root
        self.root.title("Boss直聘批量沟通工具")
        self.root.geometry("1200x800")
        self.session = requests.Session()

        self.style = ttk.Style()
        self.style.configure("TButton", padding=6)
        self.style.configure("Success.TButton", foreground="green")
        self.style.configure("Primary.TButton", background="#4a7eff")

        self.all_jobs = []
        self.setup_variables()

        self.create_ui()

        self.setup_bindings()

    def setup_variables(self):
        self.random_var = tk.BooleanVar(value=True)
        self.retry_var = tk.BooleanVar(value=True)
        self.consider_salary_multiple_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="就绪")

        self.current_tab = tk.StringVar(value="jobs")

    def setup_bindings(self):
        self.jobs_tree.bind("<Button-1>", self.on_tree_click)

        self.tab_buttons["settings"].config(command=lambda: self.change_tab("settings"))
        self.tab_buttons["filters"].config(command=lambda: self.change_tab("filters"))
        self.tab_buttons["jobs"].config(command=lambda: self.change_tab("jobs"))

    def create_ui(self):
        self.create_main_layout()

        self.create_sidebar()

        self.create_tab_content()

        self.create_status_bar()

        for tab_name in self.tab_frames:
            self.tab_frames[tab_name].grid(row=0, column=0, sticky="nsew")
            self.tab_frames[tab_name].grid_remove()

        self.change_tab("jobs")

    def create_main_layout(self):
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)

        self.main_container.columnconfigure(0, weight=2)
        self.main_container.columnconfigure(1, weight=8)
        self.main_container.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self.main_container, relief="groove", borderwidth=1, width=240)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.sidebar.grid_propagate(False)

        self.content = ttk.Frame(self.main_container)
        self.content.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.tab_frames = {}
        for tab in ["settings", "filters", "jobs"]:
            self.tab_frames[tab] = ttk.Frame(self.content)
            for i in range(5):
                self.tab_frames[tab].columnconfigure(i, weight=1)

        self.content.rowconfigure(0, weight=9)
        self.content.rowconfigure(1, weight=1)
        self.content.columnconfigure(0, weight=1)

        self.logs_frame = ttk.LabelFrame(self.content, text="日志")
        self.logs_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=5)

        self.logs_text = scrolledtext.ScrolledText(self.logs_frame, height=8)
        self.logs_text.pack(fill="both", expand=True, padx=5, pady=5)

    def create_sidebar(self):
        self.sidebar.rowconfigure(0, weight=0)
        self.sidebar.rowconfigure(1, weight=0)
        self.sidebar.rowconfigure(2, weight=1)
        self.sidebar.rowconfigure(3, weight=0)
        self.sidebar.columnconfigure(0, weight=1)

        app_title = ttk.Label(self.sidebar, text="Boss直聘批量沟通", font=("Helvetica", 12, "bold"))
        app_title.grid(row=0, column=0, padx=10, pady=15)

        nav_frame = ttk.LabelFrame(self.sidebar, text="导航")
        nav_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        self.tab_buttons = {}
        nav_buttons = [
            ("jobs", "职位列表"),
            ("filters", "筛选条件"),
            ("settings", "基本设置"),
        ]

        for i, (tab_id, tab_name) in enumerate(nav_buttons):
            btn = ttk.Button(nav_frame, text=tab_name, width=20)
            btn.pack(pady=5, padx=10, fill="x")
            self.tab_buttons[tab_id] = btn

        action_frame = ttk.LabelFrame(self.sidebar, text="操作")
        action_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

        self.fetch_button = ttk.Button(
            action_frame,
            text="获取职位列表",
            command=self.fetch_jobs,
            style="Primary.TButton",
            width=20
        )
        self.fetch_button.pack(pady=5, padx=10, fill="x")

        self.apply_filter_button = ttk.Button(
            action_frame,
            text="应用筛选",
            command=self.apply_filters,
            width=20
        )
        self.apply_filter_button.pack(pady=5, padx=10, fill="x")

        self.start_button = ttk.Button(
            action_frame,
            text="开始批量沟通",
            command=self.start_communication,
            style="Primary.TButton",
            width=20
        )
        self.start_button.pack(pady=5, padx=10, fill="x")

        selection_frame = ttk.Frame(action_frame)
        selection_frame.pack(pady=5, padx=10, fill="x")

        self.select_all_button = ttk.Button(
            selection_frame,
            text="全选",
            command=self.select_all,
            width=9
        )
        self.select_all_button.pack(side=tk.LEFT, padx=(0, 5), fill="x", expand=True)

        self.deselect_all_button = ttk.Button(
            selection_frame,
            text="取消全选",
            command=self.deselect_all,
            width=9
        )
        self.deselect_all_button.pack(side=tk.RIGHT, fill="x", expand=True)

    def create_tab_content(self):
        self.create_settings_tab()

        self.create_filters_tab()

        self.create_jobs_tab()

    def create_settings_tab(self):
        tab = self.tab_frames["settings"]

        tab.columnconfigure(0, weight=1)

        cookie_frame = ttk.LabelFrame(tab, text="登录凭证")
        cookie_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        cookie_frame.columnconfigure(0, weight=0)
        cookie_frame.columnconfigure(1, weight=1)

        ttk.Label(cookie_frame, text="Cookie:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.cookie_entry = ttk.Entry(cookie_frame)
        self.cookie_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        greeting_frame = ttk.LabelFrame(tab, text="打招呼文本")
        greeting_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        greeting_frame.columnconfigure(0, weight=1)
        greeting_frame.rowconfigure(0, weight=1)

        self.greeting_text = scrolledtext.ScrolledText(greeting_frame, height=6)
        self.greeting_text.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.greeting_text.insert("1.0", "")

        fetch_frame = ttk.LabelFrame(tab, text="获取设置")
        fetch_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        fetch_frame.columnconfigure(0, weight=0)
        fetch_frame.columnconfigure(1, weight=1)
        fetch_frame.columnconfigure(2, weight=0)
        fetch_frame.columnconfigure(3, weight=1)

        ttk.Label(fetch_frame, text="要获取的职位数量:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.job_count_entry = ttk.Entry(fetch_frame, width=10)
        self.job_count_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.job_count_entry.insert(0, "150")

        ttk.Label(fetch_frame, text="最大批量数:").grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.max_batch_entry = ttk.Entry(fetch_frame, width=10)
        self.max_batch_entry.grid(row=0, column=3, padx=10, pady=10, sticky="w")
        self.max_batch_entry.insert(0, "10")

        comm_frame = ttk.LabelFrame(tab, text="沟通设置")
        comm_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)

        comm_frame.columnconfigure(0, weight=0)
        comm_frame.columnconfigure(1, weight=1)
        comm_frame.columnconfigure(2, weight=0)

        ttk.Label(comm_frame, text="间隔时间(秒):").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.delay_entry = ttk.Entry(comm_frame, width=10)
        self.delay_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.delay_entry.insert(0, "3")

        ttk.Checkbutton(
            comm_frame,
            text="随机延迟(±1.5秒)",
            variable=self.random_var
        ).grid(row=0, column=2, padx=10, pady=10, sticky="w")

        ttk.Checkbutton(
            comm_frame,
            text="错误自动重试",
            variable=self.retry_var
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        tab.rowconfigure(4, weight=1)

    def create_filters_tab(self):
        tab = self.tab_frames["filters"]

        tab.rowconfigure(0, weight=0)
        tab.rowconfigure(1, weight=0)
        tab.rowconfigure(2, weight=1)
        tab.columnconfigure(0, weight=1)

        basic_filter_frame = ttk.LabelFrame(tab, text="基本筛选")
        basic_filter_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        basic_filter_frame.columnconfigure(0, weight=0)
        basic_filter_frame.columnconfigure(1, weight=1)
        basic_filter_frame.columnconfigure(2, weight=0)
        basic_filter_frame.columnconfigure(3, weight=1)
        basic_filter_frame.columnconfigure(4, weight=0)

        ttk.Label(basic_filter_frame, text="职位关键词包含:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.keyword_entry = ttk.Entry(basic_filter_frame)
        self.keyword_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ttk.Label(basic_filter_frame, text="职位关键词排除:").grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.exclude_keyword_entry = ttk.Entry(basic_filter_frame)
        self.exclude_keyword_entry.grid(row=0, column=3, padx=10, pady=10, sticky="ew")

        ttk.Label(basic_filter_frame, text="多个关键词用英文逗号分隔").grid(row=0, column=4, padx=10, pady=10,
                                                                            sticky="w")

        ttk.Label(basic_filter_frame, text="城市:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.city_entry = ttk.Entry(basic_filter_frame)
        self.city_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ttk.Label(basic_filter_frame, text="多个城市用英文逗号分隔").grid(row=1, column=2, columnspan=2, padx=10,
                                                                          pady=10, sticky="w")

        salary_frame = ttk.LabelFrame(tab, text="薪资范围")
        salary_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        salary_frame.columnconfigure(0, weight=0)
        salary_frame.columnconfigure(1, weight=1)
        salary_frame.columnconfigure(2, weight=0)
        salary_frame.columnconfigure(3, weight=1)
        salary_frame.columnconfigure(4, weight=0)
        salary_frame.columnconfigure(5, weight=0)

        ttk.Label(salary_frame, text="薪资范围:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.min_salary_entry = ttk.Entry(salary_frame, width=10)
        self.min_salary_entry.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        ttk.Label(salary_frame, text="K -").grid(row=0, column=2, padx=0, pady=10, sticky="w")

        self.max_salary_entry = ttk.Entry(salary_frame, width=10)
        self.max_salary_entry.grid(row=0, column=3, padx=5, pady=10, sticky="w")

        ttk.Label(salary_frame, text="K").grid(row=0, column=4, padx=0, pady=10, sticky="w")

        ttk.Checkbutton(
            salary_frame,
            text="考虑薪资倍数(例如16薪)",
            variable=self.consider_salary_multiple_var
        ).grid(row=0, column=5, padx=10, pady=10, sticky="w")

        adv_filter_frame = ttk.LabelFrame(tab, text="高级筛选")
        adv_filter_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        adv_filter_frame.columnconfigure(0, weight=1)
        adv_filter_frame.columnconfigure(1, weight=1)
        adv_filter_frame.columnconfigure(2, weight=1)
        adv_filter_frame.rowconfigure(0, weight=1)

        scale_frame = ttk.LabelFrame(adv_filter_frame, text="公司规模")
        scale_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        scale_frame.columnconfigure(0, weight=1)
        scale_frame.rowconfigure(0, weight=0)
        scale_frame.rowconfigure(1, weight=1)

        scale_btn_frame = ttk.Frame(scale_frame)
        scale_btn_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        scale_btn_frame.columnconfigure(0, weight=1)
        scale_btn_frame.columnconfigure(1, weight=1)

        ttk.Button(
            scale_btn_frame,
            text="全选",
            command=lambda: self.select_all_items(self.company_scale_listbox),
            width=10
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        ttk.Button(
            scale_btn_frame,
            text="取消选择",
            command=lambda: self.deselect_all_items(self.company_scale_listbox),
            width=10
        ).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        scale_list_frame = ttk.Frame(scale_frame)
        scale_list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        scale_list_frame.columnconfigure(0, weight=1)
        scale_list_frame.rowconfigure(0, weight=1)

        scale_scrollbar = ttk.Scrollbar(scale_list_frame)
        scale_scrollbar.grid(row=0, column=1, sticky="ns")

        self.company_scale_listbox = tk.Listbox(
            scale_list_frame,
            selectmode=tk.MULTIPLE,
            yscrollcommand=scale_scrollbar.set,
            exportselection=0,
            height=12
        )
        self.company_scale_listbox.grid(row=0, column=0, sticky="nsew")
        scale_scrollbar.config(command=self.company_scale_listbox.yview)

        company_scales = [
            "0-20人",
            "20-99人",
            "100-499人",
            "500-999人",
            "1000-9999人",
            "10000人以上"
        ]
        for scale in company_scales:
            self.company_scale_listbox.insert(tk.END, scale)

        exp_frame = ttk.LabelFrame(adv_filter_frame, text="经验要求")
        exp_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        exp_frame.columnconfigure(0, weight=1)
        exp_frame.rowconfigure(0, weight=0)
        exp_frame.rowconfigure(1, weight=1)

        exp_btn_frame = ttk.Frame(exp_frame)
        exp_btn_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        exp_btn_frame.columnconfigure(0, weight=1)
        exp_btn_frame.columnconfigure(1, weight=1)

        ttk.Button(
            exp_btn_frame,
            text="全选",
            command=lambda: self.select_all_items(self.experience_listbox),
            width=10
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        ttk.Button(
            exp_btn_frame,
            text="取消选择",
            command=lambda: self.deselect_all_items(self.experience_listbox),
            width=10
        ).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        exp_list_frame = ttk.Frame(exp_frame)
        exp_list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        exp_list_frame.columnconfigure(0, weight=1)
        exp_list_frame.rowconfigure(0, weight=1)

        exp_scrollbar = ttk.Scrollbar(exp_list_frame)
        exp_scrollbar.grid(row=0, column=1, sticky="ns")

        self.experience_listbox = tk.Listbox(
            exp_list_frame,
            selectmode=tk.MULTIPLE,
            yscrollcommand=exp_scrollbar.set,
            exportselection=0,
            height=12
        )
        self.experience_listbox.grid(row=0, column=0, sticky="nsew")
        exp_scrollbar.config(command=self.experience_listbox.yview)

        experiences = [
            "在校/应届",
            "经验不限",
            "1年以内",
            "1-3年",
            "3-5年",
            "5-10年",
            "10年以上"
        ]
        for exp in experiences:
            self.experience_listbox.insert(tk.END, exp)

        edu_frame = ttk.LabelFrame(adv_filter_frame, text="教育程度")
        edu_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        edu_frame.columnconfigure(0, weight=1)
        edu_frame.rowconfigure(0, weight=0)
        edu_frame.rowconfigure(1, weight=1)

        edu_btn_frame = ttk.Frame(edu_frame)
        edu_btn_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        edu_btn_frame.columnconfigure(0, weight=1)
        edu_btn_frame.columnconfigure(1, weight=1)

        ttk.Button(
            edu_btn_frame,
            text="全选",
            command=lambda: self.select_all_items(self.education_listbox),
            width=10
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        ttk.Button(
            edu_btn_frame,
            text="取消选择",
            command=lambda: self.deselect_all_items(self.education_listbox),
            width=10
        ).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        edu_list_frame = ttk.Frame(edu_frame)
        edu_list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        edu_list_frame.columnconfigure(0, weight=1)
        edu_list_frame.rowconfigure(0, weight=1)

        edu_scrollbar = ttk.Scrollbar(edu_list_frame)
        edu_scrollbar.grid(row=0, column=1, sticky="ns")

        self.education_listbox = tk.Listbox(
            edu_list_frame,
            selectmode=tk.MULTIPLE,
            yscrollcommand=edu_scrollbar.set,
            exportselection=0,
            height=12
        )
        self.education_listbox.grid(row=0, column=0, sticky="nsew")
        edu_scrollbar.config(command=self.education_listbox.yview)

        education_degrees = [
            "博士",
            "硕士",
            "本科",
            "大专",
            "中专",
            "高中",
            "学历不限"
        ]
        for degree in education_degrees:
            self.education_listbox.insert(tk.END, degree)

    def create_jobs_tab(self):
        tab = self.tab_frames["jobs"]

        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)

        tree_frame = ttk.LabelFrame(tab, text="职位列表")
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.rowconfigure(1, weight=0)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.columnconfigure(1, weight=0)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.grid(row=0, column=1, sticky="ns")

        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.grid(row=1, column=0, sticky="ew")

        self.jobs_tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode="browse"
        )

        vsb.config(command=self.jobs_tree.yview)
        hsb.config(command=self.jobs_tree.xview)

        self.jobs_tree.grid(row=0, column=0, sticky="nsew")

        self.jobs_tree["columns"] = (
            "id", "job_name", "company", "salary", "city", "experience",
            "boss_name", "security_id", "company_scale", "education"
        )

        self.jobs_tree.column("#0", width=50, stretch=tk.NO)
        self.jobs_tree.column("id", width=120, stretch=tk.NO)
        self.jobs_tree.column("job_name", width=180)
        self.jobs_tree.column("company", width=160)
        self.jobs_tree.column("salary", width=100, stretch=tk.NO)
        self.jobs_tree.column("city", width=70, stretch=tk.NO)
        self.jobs_tree.column("experience", width=70, stretch=tk.NO)
        self.jobs_tree.column("education", width=70, stretch=tk.NO)
        self.jobs_tree.column("boss_name", width=70, stretch=tk.NO)
        self.jobs_tree.column("security_id", width=0, stretch=tk.NO)
        self.jobs_tree.column("company_scale", width=100, stretch=tk.NO)

        self.jobs_tree.heading("#0", text="选择")
        self.jobs_tree.heading("id", text="职位ID")
        self.jobs_tree.heading("job_name", text="职位名称")
        self.jobs_tree.heading("company", text="公司名称")
        self.jobs_tree.heading("salary", text="薪资")
        self.jobs_tree.heading("city", text="城市")
        self.jobs_tree.heading("experience", text="经验")
        self.jobs_tree.heading("education", text="学历")
        self.jobs_tree.heading("boss_name", text="招聘人")
        self.jobs_tree.heading("security_id", text="Security ID")
        self.jobs_tree.heading("company_scale", text="公司规模")

        self.style.configure("Treeview", rowheight=25)
        self.style.map("Treeview", background=[("selected", "#4a7eff")])

    def create_status_bar(self):
        self.status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def change_tab(self, tab_name):
        for frame in self.tab_frames.values():
            frame.grid_remove()

        self.tab_frames[tab_name].grid()

        self.current_tab.set(tab_name)

        for tab_id, button in self.tab_buttons.items():
            if tab_id == tab_name:
                button.configure(style="Primary.TButton")
            else:
                button.configure(style="TButton")

    def select_all_items(self, listbox):
        listbox.select_set(0, tk.END)

    def deselect_all_items(self, listbox):
        listbox.selection_clear(0, tk.END)

    def log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.logs_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.logs_text.see(tk.END)

    def on_tree_click(self, event):
        region = self.jobs_tree.identify_region(event.x, event.y)
        if region == "tree" or region == "cell":
            item_id = self.jobs_tree.identify_row(event.y)
            if item_id:
                current_tags = self.jobs_tree.item(item_id, "tags")

                if "checked" in current_tags:
                    self.jobs_tree.item(item_id, tags=("unchecked",))
                    self.jobs_tree.item(item_id, text="")
                else:
                    self.jobs_tree.item(item_id, tags=("checked",))
                    self.jobs_tree.item(item_id, text="✓")

    def select_all(self):
        for item in self.jobs_tree.get_children():
            self.jobs_tree.item(item, tags=("checked",))
            self.jobs_tree.item(item, text="✓")

    def deselect_all(self):
        for item in self.jobs_tree.get_children():
            self.jobs_tree.item(item, tags=("unchecked",))
            self.jobs_tree.item(item, text="")

    def parse_cookies(self, cookie_str):
        cookies = {}
        if cookie_str:
            cookie_pairs = cookie_str.split(';')
            for pair in cookie_pairs:
                pair = pair.strip()
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    cookies[key.strip()] = value.strip()
        return cookies

    def parse_salary(self, salary_str):
        try:
            min_salary = 0
            max_salary = 0
            multiple = 1

            multiple_match = re.search(r'(\d+)薪', salary_str)
            if multiple_match:
                multiple = int(multiple_match.group(1))

            salary_match = re.search(r'(\d+)(?:\.?\d*)?-(\d+)(?:\.?\d*)?[kK]', salary_str)
            if salary_match:
                min_salary = float(salary_match.group(1))
                max_salary = float(salary_match.group(2))
                return min_salary, max_salary, multiple

            single_salary_match = re.search(r'(\d+)(?:\.?\d*)?[kK]', salary_str)
            if single_salary_match:
                min_salary = max_salary = float(single_salary_match.group(1))
                return min_salary, max_salary, multiple

            return min_salary, max_salary, multiple
        except Exception as e:
            self.log(f"解析薪资错误: {salary_str}, {str(e)}")
            return 0, 0, 1

    def fetch_jobs(self):
        for item in self.jobs_tree.get_children():
            self.jobs_tree.delete(item)

        self.all_jobs = []

        cookie_str = self.cookie_entry.get()
        self.cookies = self.parse_cookies(cookie_str)

        self.session.cookies.update(self.cookies)

        try:
            target_job_count = int(self.job_count_entry.get())
        except ValueError:
            target_job_count = 150

        self.log(f"开始获取职位列表，目标数量: {target_job_count}...")
        self.status_var.set("正在获取职位列表...")

        self.change_tab("jobs")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Referer': 'https://www.zhipin.com/web/geek/recommend',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.zhipin.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }

        try:
            page = 1
            total_fetched = 0
            consecutive_empty_pages = 0
            max_empty_pages = 3

            while total_fetched < target_job_count and consecutive_empty_pages < max_empty_pages:
                self.log(f"获取第 {page} 页职位数据...")

                url = "https://www.zhipin.com/wapi/zpgeek/pc/recommend/job/list.json"
                params = {
                    'page': page,
                    'pageSize': 15,
                    'encryptExpectId': '',
                    'mixExpectType': '',
                    'expectInfo': '',
                    'jobType': '',
                    'salary': '',
                    'experience': '',
                    'degree': '',
                    'industry': '',
                    'scale': '',
                    '_': str(int(time.time() * 1000))
                }

                response = self.session.get(url, params=params, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == 0:
                        job_list = data.get('zpData', {}).get('jobList', [])

                        if not job_list:
                            consecutive_empty_pages += 1
                            self.log(f"第 {page} 页没有职位数据")
                        else:
                            consecutive_empty_pages = 0
                            self.all_jobs.extend(job_list)
                            total_fetched += len(job_list)
                            self.log(f"已获取 {total_fetched} 个职位数据")
                    else:
                        self.log(f"API返回错误: {data.get('message', '未知错误')}")
                        break
                else:
                    self.log(f"HTTP错误: {response.status_code}")
                    break

                page += 1

                if page > 1:
                    delay = random.uniform(1.0, 3.0)
                    time.sleep(delay)

                if total_fetched >= target_job_count:
                    break

            self.log(f"总共获取到 {len(self.all_jobs)} 个职位")

            self.apply_filters()

        except Exception as e:
            self.log(f"获取职位列表时发生错误: {str(e)}")
            self.status_var.set("获取失败")
            messagebox.showerror("错误", f"发生错误: {str(e)}")

    def apply_filters(self):
        if not self.all_jobs:
            messagebox.showinfo("提示", "请先获取职位列表")
            return

        for item in self.jobs_tree.get_children():
            self.jobs_tree.delete(item)

        include_keywords = [k.strip().lower() for k in self.keyword_entry.get().strip().split(',') if k.strip()]
        exclude_keywords = [k.strip().lower() for k in self.exclude_keyword_entry.get().strip().split(',') if k.strip()]
        cities = [c.strip() for c in self.city_entry.get().strip().split(',') if c.strip()]

        selected_scales_indices = self.company_scale_listbox.curselection()
        selected_scales = [self.company_scale_listbox.get(i) for i in selected_scales_indices]

        selected_exp_indices = self.experience_listbox.curselection()
        selected_experiences = [self.experience_listbox.get(i) for i in selected_exp_indices]

        selected_edu_indices = self.education_listbox.curselection()
        selected_educations = [self.education_listbox.get(i) for i in selected_edu_indices]

        try:
            min_salary = float(self.min_salary_entry.get()) if self.min_salary_entry.get() else 0
        except ValueError:
            min_salary = 0

        try:
            max_salary = float(self.max_salary_entry.get()) if self.max_salary_entry.get() else float('inf')
        except ValueError:
            max_salary = float('inf')

        consider_multiple = self.consider_salary_multiple_var.get()

        filtered_jobs = []

        initial_count = len(self.all_jobs)
        keyword_filtered = 0
        city_filtered = 0
        scale_filtered = 0
        exp_filtered = 0
        salary_filtered = 0
        edu_filtered = 0

        for job in self.all_jobs:
            job_name = job.get('jobName', '').lower()
            job_city = job.get('cityName', '')
            job_salary = job.get('salaryDesc', '')
            job_scale = job.get('brandScaleName', '')
            job_experience = job.get('jobExperience', '')
            job_education = job.get('jobDegree', '')

            if include_keywords and not any(k in job_name for k in include_keywords):
                keyword_filtered += 1
                continue

            if any(k in job_name for k in exclude_keywords):
                keyword_filtered += 1
                continue

            if cities and job_city not in cities:
                city_filtered += 1
                continue

            if selected_scales and job_scale not in selected_scales:
                scale_filtered += 1
                continue

            if selected_experiences and job_experience not in selected_experiences:
                exp_filtered += 1
                continue

            if selected_educations and job_education not in selected_educations:
                edu_filtered += 1
                continue

            if min_salary > 0 or max_salary < float('inf'):
                salary_min, salary_max, salary_multiple = self.parse_salary(job_salary)

                if consider_multiple and salary_multiple > 1:
                    salary_min *= salary_multiple / 12
                    salary_max *= salary_multiple / 12

                if salary_max < min_salary or salary_min > max_salary:
                    salary_filtered += 1
                    continue

            filtered_jobs.append(job)

        self.change_tab("jobs")

        for job in filtered_jobs:
            job_id = job.get('encryptJobId', '')
            security_id = job.get('securityId', '')
            job_name = job.get('jobName', '')
            company = job.get('brandName', '')
            salary = job.get('salaryDesc', '')
            city = job.get('cityName', '')
            experience = job.get('jobExperience', '')
            education = job.get('jobDegree', '')
            boss_name = job.get('bossName', '')
            company_scale = job.get('brandScaleName', '')

            self.jobs_tree.insert("", tk.END, text="", values=(
                job_id, job_name, company, salary, city, experience, boss_name, security_id, company_scale, education
            ), tags=("unchecked",))

        self.log(f"筛选前总数: {initial_count}")
        if keyword_filtered > 0:
            self.log(f"关键词筛选过滤: {keyword_filtered}个")
        if city_filtered > 0:
            self.log(f"城市筛选过滤: {city_filtered}个")
        if scale_filtered > 0:
            self.log(f"公司规模筛选过滤: {scale_filtered}个")
        if exp_filtered > 0:
            self.log(f"经验要求筛选过滤: {exp_filtered}个")
        if edu_filtered > 0:
            self.log(f"学历要求筛选过滤: {edu_filtered}个")
        if salary_filtered > 0:
            self.log(f"薪资范围筛选过滤: {salary_filtered}个")

        self.log(f"筛选后剩余 {len(filtered_jobs)} 个职位")
        self.status_var.set(f"就绪 - 已加载 {len(filtered_jobs)} 个职位")

    def start_communication(self):
        selected_items = []
        for item in self.jobs_tree.get_children():
            if "checked" in self.jobs_tree.item(item, "tags"):
                values = self.jobs_tree.item(item, "values")
                job_id = values[0]
                job_name = values[1]
                security_id = values[7]
                selected_items.append((item, job_id, job_name, security_id))

        if not selected_items:
            messagebox.showinfo("提示", "请先选择要沟通的职位")
            return

        try:
            max_batch = int(self.max_batch_entry.get())
            if len(selected_items) > max_batch:
                confirm = messagebox.askyesno("提示",
                                              f"选择的职位数量 ({len(selected_items)}) 超过了设置的最大批量数 ({max_batch})，建议分批进行以避免触发反爬虫机制。\n是否仍然继续？")
                if not confirm:
                    return
        except ValueError:
            pass

        greeting = self.greeting_text.get("1.0", tk.END).strip()
        if not greeting:
            messagebox.showinfo("提示", "请输入打招呼文本")
            return

        try:
            delay = float(self.delay_entry.get())
            if delay <= 0:
                raise ValueError("间隔时间必须大于0")
        except ValueError as e:
            messagebox.showinfo("提示", f"请输入有效的间隔时间: {str(e)}")
            return

        confirm = messagebox.askyesno("确认", f"确定要向 {len(selected_items)} 个职位发送沟通请求吗？")
        if not confirm:
            return

        threading.Thread(target=self.communicate_thread,
                         args=(selected_items, greeting, delay),
                         daemon=True).start()

    def communicate_thread(self, selected_items, greeting, delay):
        self.status_var.set(f"正在沟通... (0/{len(selected_items)})")
        self.log(f"开始批量沟通，共 {len(selected_items)} 个职位")

        self.fetch_button.config(state="disabled")
        self.start_button.config(state="disabled")

        success_count = 0
        fail_count = 0
        retry_count = 0
        max_retries = 3

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Referer': 'https://www.zhipin.com/job_detail/',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.zhipin.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }

        for i, (item_id, job_id, job_name, security_id) in enumerate(selected_items):
            retry = 0
            success = False

            while not success and retry <= max_retries:
                try:
                    actual_delay = delay
                    if self.random_var.get():
                        actual_delay += random.uniform(-1, 1.5)
                        actual_delay = max(1.0, actual_delay)

                    if retry > 0:
                        actual_delay += retry * 2
                        self.log(f"第 {retry} 次重试 {job_name}，延迟 {actual_delay:.1f} 秒")

                    time.sleep(actual_delay)

                    timestamp = str(int(time.time() * 1000))

                    sec_id_encoded = urllib.parse.quote(security_id)
                    job_id_encoded = urllib.parse.quote(job_id)
                    lid_encoded = urllib.parse.quote(f"3ktqIYdhYR0.search.{i + 1}")

                    url = f"https://www.zhipin.com/wapi/zpgeek/friend/add.json?securityId={sec_id_encoded}&jobId={job_id_encoded}&lid={lid_encoded}&_={timestamp}"

                    self.log(f"发送请求: {job_name}, URL={url}")

                    response = self.session.get(url, headers=headers)

                    if response.status_code == 200:
                        data = response.json()
                        if data.get('code') == 0:
                            self.log(f"成功沟通: {job_name}")
                            success_count += 1
                            self.jobs_tree.item(item_id, tags=("sent",))
                            self.jobs_tree.item(item_id, text="✅")
                            success = True
                        else:
                            error_msg = data.get('message', '未知错误')
                            error_code = data.get('code', '未知')

                            if error_code == 121 and self.retry_var.get() and retry < max_retries:
                                retry += 1
                                retry_count += 1
                                self.log(f"请求不合法(121)错误: {job_name} - 将进行重试 {retry}/{max_retries}")
                                continue
                            else:
                                self.log(f"沟通失败: {job_name} - {error_msg}")
                                self.log(f"错误码: {error_code}, 响应: {json.dumps(data)}")
                                fail_count += 1
                                self.jobs_tree.item(item_id, tags=("failed",))
                                self.jobs_tree.item(item_id, text="❌")
                                success = True
                    else:
                        self.log(f"HTTP错误 ({response.status_code}): {job_name}")
                        self.log(f"响应内容: {response.text}")

                        if response.status_code >= 500 and self.retry_var.get() and retry < max_retries:
                            retry += 1
                            retry_count += 1
                            self.log(f"服务器错误，将进行重试 {retry}/{max_retries}")
                            continue
                        else:
                            fail_count += 1
                            self.jobs_tree.item(item_id, tags=("failed",))
                            self.jobs_tree.item(item_id, text="❌")
                            success = True

                    self.status_var.set(f"正在沟通... ({i + 1}/{len(selected_items)})")
                    self.root.update_idletasks()

                except Exception as e:
                    self.log(f"发生错误 ({job_name}): {str(e)}")

                    if self.retry_var.get() and retry < max_retries:
                        retry += 1
                        retry_count += 1
                        self.log(f"将进行重试 {retry}/{max_retries}")
                        continue
                    else:
                        fail_count += 1
                        self.jobs_tree.item(item_id, tags=("failed",))
                        self.jobs_tree.item(item_id, text="❌")
                        success = True

        self.fetch_button.config(state="normal")
        self.start_button.config(state="normal")

        self.log(f"批量沟通完成。成功: {success_count}, 失败: {fail_count}, 重试: {retry_count}")
        self.status_var.set(f"完成 - 成功: {success_count}, 失败: {fail_count}")

        messagebox.showinfo("完成", f"批量沟通完成。\n成功: {success_count}\n失败: {fail_count}\n重试: {retry_count}")


def main():
    root = tk.Tk()
    app = BossZhipinBot(root)
    root.mainloop()


if __name__ == "__main__":
    main()