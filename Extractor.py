import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# --- 配置常量 ---
COLOR_BG = "#1e1e1e"
COLOR_CARD = "#2d2d2d"
COLOR_ACCENT = "#00adb5"
COLOR_TEXT = "#eeeeee"
COLOR_TEXT_DIM = "#b0b0b0"
COLOR_SUCCESS = "#4caf50"

class Extractor:
    def __init__(self, root):
        self.root = root
        self.root.title("AkiACG All-in-One TeaGFX Extractor")
        self.root.geometry("750x850")
        self.root.configure(bg=COLOR_BG)

        self.font_main = ("Microsoft YaHei", 10)
        self.font_bold = ("Microsoft YaHei", 10, "bold")

        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()

        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg=COLOR_ACCENT, height=60)
        header.pack(fill="x", side="top")
        tk.Label(header, text="TEAGFX RESOURCE EXTRACTOR", bg=COLOR_ACCENT, fg="white", 
                 font=("Consolas", 14, "bold")).pack(pady=15)

        # Main Container
        main_frame = tk.Frame(self.root, bg=COLOR_BG, padx=30, pady=10)
        main_frame.pack(fill="both", expand=True)

        self.create_path_row(main_frame, "输入目录 (SVO/AFB Path):", self.input_dir, self.browse_input)
        self.create_path_row(main_frame, "输出目录 (Export Path):", self.output_dir, self.browse_output)

        # Progress
        tk.Label(main_frame, text="任务进度:", bg=COLOR_BG, fg=COLOR_TEXT_DIM, font=self.font_main).pack(anchor="w", pady=(15, 5))
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Aki.Horizontal.TProgressbar", thickness=10, background=COLOR_ACCENT, troughcolor=COLOR_CARD, borderwidth=0)
        self.progress = ttk.Progressbar(main_frame, style="Aki.Horizontal.TProgressbar", orient="horizontal", mode="determinate")
        self.progress.pack(fill="x")

        # Console
        tk.Label(main_frame, text="运行日志:", bg=COLOR_BG, fg=COLOR_TEXT_DIM, font=self.font_main).pack(anchor="w", pady=(15, 5))
        self.log_text = tk.Text(main_frame, bg=COLOR_CARD, fg=COLOR_TEXT, borderwidth=0, padx=10, pady=10, 
                                font=("Consolas", 9), insertbackground="white", height=12)
        self.log_text.pack(fill="both", expand=True)

        # Footer Button
        btn_run = tk.Button(self.root, text="START MULTI-EXTRACTION", bg=COLOR_ACCENT, fg="white",
                           font=self.font_bold, relief="flat", height=2, cursor="hand2",
                           command=self.start_extraction)
        btn_run.pack(fill="x", side="bottom", padx=30, pady=20)

    def create_path_row(self, parent, label_text, var, command):
        tk.Label(parent, text=label_text, bg=COLOR_BG, fg=COLOR_TEXT, font=self.font_main).pack(anchor="w", pady=(10, 2))
        row = tk.Frame(parent, bg=COLOR_BG)
        row.pack(fill="x")
        tk.Entry(row, textvariable=var, bg=COLOR_CARD, fg=COLOR_TEXT, insertbackground="white", 
                 borderwidth=0, font=self.font_main).pack(side="left", fill="x", expand=True, ipady=5)
        tk.Button(row, text="BROWSE", bg="#444444", fg="white", relief="flat", padx=15, 
                  font=("Arial", 8, "bold"), command=command, cursor="hand2").pack(side="right", padx=(5, 0))

    def browse_input(self):
        path = filedialog.askdirectory()
        if path: self.input_dir.set(path)

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
        in_path, out_base = self.input_dir.get(), self.output_dir.get()
        if not in_path or not out_base:
            messagebox.showwarning("Warning", "请选择输入和输出路径！")
            return

        files = []
        for root, _, fs in os.walk(in_path):
            for f in fs:
                if f.lower().endswith((".svo", ".afb")):
                    files.append(os.path.join(root, f))

        if not files:
            self.log("未发现可处理的 .svo 或 .afb 文件", "#ff5555")
            return

        self.progress["value"] = 0
        self.progress["maximum"] = len(files)
        
        for idx, fpath in enumerate(files):
            ext = os.path.splitext(fpath)[1].lower()
            self.log(f"正在处理 [{ext.upper()}]: {os.path.basename(fpath)}")
            
            if ext == ".afb":
                self.extract_afb_logic(fpath, out_base)
            else:
                self.extract_svo_logic(fpath, out_base)
                
            self.progress["value"] = idx + 1
            
        self.log("所有任务已完成！", COLOR_SUCCESS)
        messagebox.showinfo("Success", "提取完成！")

    def extract_svo_logic(self, svo_path, out_base):
        """传统的 SVO 提取逻辑：按序号命名"""
        try:
            with open(svo_path, "rb") as f:
                data = f.read()
            matches = [m.start() for m in re.finditer(b'DDS ', data)]
            if not matches: return

            save_path = os.path.join(out_base, os.path.basename(svo_path).replace(".", "_"))
            os.makedirs(save_path, exist_ok=True)

            for i, start in enumerate(matches):
                end = matches[i+1] if i+1 < len(matches) else len(data)
                with open(os.path.join(save_path, f"tex_{i:03d}.dds"), "wb") as out_f:
                    out_f.write(data[start:end])
        except Exception as e:
            self.log(f"SVO Error: {str(e)}")

    def extract_afb_logic(self, afb_path, out_base):
        """增强的 AFB 提取逻辑：支持原文件名还原"""
        try:
            with open(afb_path, "rb") as f:
                data = f.read()

            # 1. 尝试提取所有 .dds 结尾的文件名字符串
            # 匹配规则：非打印字符后的 [字母数字_-].dds
            found_names = re.findall(rb'[\w\-\.]+\.dds', data, re.IGNORECASE)
            # 转为字符串并去重（保持顺序）
            clean_names = []
            for name in found_names:
                name_str = name.decode('utf-8', errors='ignore')
                if name_str not in clean_names:
                    clean_names.append(name_str)

            # 2. 定位 DDS 数据块
            matches = [m.start() for m in re.finditer(b'DDS ', data)]
            if not matches: return

            save_path = os.path.join(out_base, os.path.basename(afb_path).replace(".", "_"))
            os.makedirs(save_path, exist_ok=True)

            # 3. 提取数据
            for i, start in enumerate(matches):
                # 确定结束点：下一个 DDS 或 POF 标记，或文件末尾
                end = len(data)
                next_dds = matches[i+1] if i+1 < len(matches) else len(data)
                
                # 检查两个 DDS 之间是否有 POF 标记
                chunk = data[start:next_dds]
                pof_match = re.search(b'POF', chunk)
                if pof_match:
                    end = start + pof_match.start()
                else:
                    end = next_dds

                # 命名逻辑：如果有对应原名则使用原名，否则用序号
                if i < len(clean_names):
                    filename = clean_names[i]
                else:
                    filename = f"unknown_{i:03d}.dds"

                with open(os.path.join(save_path, filename), "wb") as out_f:
                    out_f.write(data[start:end])
                    
            self.log(f"成功从 AFB 提取了 {len(matches)} 个贴图")

        except Exception as e:
            self.log(f"AFB Error: {str(e)}")
if __name__ == "__main__":
    import ctypes
    
    # --- 新增 DPI 自适应代码 ---
    try:
        # 告诉 Windows 该程序支持 DPI 感知
        # 针对 Windows 10/11
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            # 针对旧版 Windows (7/8)
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass # 如果非 Windows 系统则跳过

    app_root = tk.Tk()
    Extractor(app_root)
    app_root.mainloop()
