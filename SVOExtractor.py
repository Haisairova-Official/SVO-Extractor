import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# 主题颜色定义
COLOR_BG = "#1e1e1e" 
COLOR_CARD = "#2d2d2d" 
COLOR_ACCENT = "#00adb5"
COLOR_TEXT = "#eeeeee"
COLOR_TEXT_DIM = "#b0b0b0" 
COLOR_SUCCESS = "#4caf50"  

class SVO_Extractor_Aki:
    def __init__(self, root):
        self.root = root
        self.root.title("SVO Extractor | AkiACG Resource Tools")
        self.root.geometry("700x550")
        self.root.configure(bg=COLOR_BG)

        # 设置字体
        self.font_main = ("Microsoft YaHei", 10)
        self.font_bold = ("Microsoft YaHei", 10, "bold")

        self.svo_dir = tk.StringVar()
        self.output_dir = tk.StringVar()

        self.setup_ui()

    def setup_ui(self):
        # 顶部 Header 装饰
        header = tk.Frame(self.root, bg=COLOR_ACCENT, height=50)
        header.pack(fill="x", side="top")
        tk.Label(header, text="SVO EXTRACTOR", bg=COLOR_ACCENT, fg="white", 
                 font=("Consolas", 16, "bold")).pack(pady=10)

        # 主容器
        main_frame = tk.Frame(self.root, bg=COLOR_BG, padx=30, pady=20)
        main_frame.pack(fill="both", expand=True)

        # 路径选择区域
        self.create_path_row(main_frame, "扫描目录 (SVO Path):", self.svo_dir, self.browse_svo)
        self.create_path_row(main_frame, "输出目录 (Export Path):", self.output_dir, self.browse_output)

        # 进度条样式
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Aki.Horizontal.TProgressbar", thickness=10, background=COLOR_ACCENT, 
                        troughcolor=COLOR_CARD, borderwidth=0)
        
        tk.Label(main_frame, text="任务进度:", bg=COLOR_BG, fg=COLOR_TEXT_DIM, font=self.font_main).pack(anchor="w", pady=(15, 5))
        self.progress = ttk.Progressbar(main_frame, style="Aki.Horizontal.TProgressbar", 
                                        orient="horizontal", mode="determinate")
        self.progress.pack(fill="x")

        # 控制台日志
        tk.Label(main_frame, text="运行日志:", bg=COLOR_BG, fg=COLOR_TEXT_DIM, font=self.font_main).pack(anchor="w", pady=(15, 5))
        self.log_text = tk.Text(main_frame, bg=COLOR_CARD, fg=COLOR_TEXT, borderwidth=0, 
                                padx=10, pady=10, font=("Consolas", 9), insertbackground="white")
        self.log_text.pack(fill="both", expand=True)

        # 底部按钮
        btn_run = tk.Button(self.root, text="START EXTRACTION", bg=COLOR_ACCENT, fg="white",
                           activebackground="#008c94", activeforeground="white",
                           font=self.font_bold, relief="flat", height=2, cursor="hand2",
                           command=self.start_extraction)
        btn_run.pack(fill="x", side="bottom", padx=30, pady=20)

    def create_path_row(self, parent, label_text, var, command):
        tk.Label(parent, text=label_text, bg=COLOR_BG, fg=COLOR_TEXT, font=self.font_main).pack(anchor="w", pady=(10, 2))
        row = tk.Frame(parent, bg=COLOR_BG)
        row.pack(fill="x")
        entry = tk.Entry(row, textvariable=var, bg=COLOR_CARD, fg=COLOR_TEXT, 
                         insertbackground="white", borderwidth=0, font=self.font_main)
        entry.pack(side="left", fill="x", expand=True, ipady=5)
        btn = tk.Button(row, text="BROWSE", bg="#444444", fg="white", relief="flat", 
                        padx=15, font=("Arial", 8, "bold"), command=command, cursor="hand2")
        btn.pack(side="right", padx=(5, 0))

    # --- 逻辑部分 ---
    def browse_svo(self):
        path = filedialog.askdirectory()
        if path: self.svo_dir.set(path)

    def browse_output(self):
        path = filedialog.askdirectory()
        if path: self.output_dir.set(path)

    def log(self, message, color=COLOR_TEXT):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"> {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.root.update()

    def start_extraction(self):
        input_path = self.svo_dir.get()
        out_base = self.output_dir.get()

        if not input_path or not out_base:
            messagebox.showwarning("AkiACG Tool", "路径不能为空！")
            return

        svo_files = []
        for root, dirs, files in os.walk(input_path): # 支持递归子目录
            for f in files:
                if f.lower().endswith(".svo"):
                    svo_files.append(os.path.join(root, f))

        if not svo_files:
            self.log("未发现 .svo 文件", "#ff5555")
            return

        self.progress["maximum"] = len(svo_files)
        self.log(f"开始任务: 发现 {len(svo_files)} 个文件")
        
        for idx, svo_path in enumerate(svo_files):
            filename = os.path.basename(svo_path)
            self.log(f"Processing: {filename}")
            self.extract_logic(svo_path, out_base)
            self.progress["value"] = idx + 1
            
        self.log("DONE! 提取任务完成", COLOR_SUCCESS)
        messagebox.showinfo("AkiACG.Tool.SVO.Extractor", "所有贴图已成功导出！")

    def extract_logic(self, svo_path, out_base):
        try:
            with open(svo_path, "rb") as f:
                data = f.read()
            matches = [m.start() for m in re.finditer(b'DDS ', data)]
            if not matches: return

            folder_name = os.path.basename(svo_path).replace(".", "_")
            save_path = os.path.join(out_base, folder_name)
            os.makedirs(save_path, exist_ok=True)

            for i in range(len(matches)):
                start = matches[i]
                end = matches[i+1] if i+1 < len(matches) else len(data)
                with open(os.path.join(save_path, f"tex_{i:03d}.dds"), "wb") as out_f:
                    out_f.write(data[start:end])
        except Exception as e:
            self.log(f"Error at {os.path.basename(svo_path)}: {str(e)}")

if __name__ == "__main__":
    app_root = tk.Tk()
    SVO_Extractor_Aki(app_root)
    app_root.mainloop()

# Present by AkiACG.com
# Version 1.0.0
