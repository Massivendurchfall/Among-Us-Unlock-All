import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import json
import os
import sys
import zipfile
import threading
from datetime import datetime
from packaging import version


class AUnlockerUpdaterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AUnlocker Auto-Updater")
        self.root.geometry("700x650")
        self.root.resizable(False, False)

        self.repo_owner = "astra1dev"
        self.repo_name = "AUnlocker"
        self.api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        self.config_file = "aunlocker_config.json"
        self.platform = tk.StringVar()
        self.among_us_path = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.status_text = tk.StringVar(value="Ready")
        self.current_release_data = None
        self.download_speed = tk.StringVar(value="")

        self.load_config()
        self.setup_gui()
        self.root.after(500, self.initial_check)

    def setup_gui(self):
        title_frame = tk.Frame(self.root, bg="#2b2b2b")
        title_frame.pack(fill="x", pady=(0, 20))

        title_label = tk.Label(
            title_frame,
            text="🎮 AUnlocker Auto-Updater",
            font=("Arial", 18, "bold"),
            bg="#2b2b2b",
            fg="white",
            pady=10
        )
        title_label.pack()

        made_by_label = tk.Label(
            title_frame,
            text="Made by Massivendurchfall",
            font=("Arial", 10, "italic"),
            bg="#2b2b2b",
            fg="#888888",
            pady=5
        )
        made_by_label.pack()

        main_frame = tk.Frame(self.root, padx=30, pady=10)
        main_frame.pack(fill="both", expand=True)

        platform_frame = tk.LabelFrame(
            main_frame,
            text="Select Platform",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=15
        )
        platform_frame.pack(fill="x", pady=(0, 15))

        tk.Radiobutton(
            platform_frame,
            text="Steam / Itch.io",
            variable=self.platform,
            value="Steam_Itch",
            font=("Arial", 10),
            command=self.on_platform_change
        ).pack(anchor="w", pady=3)

        tk.Radiobutton(
            platform_frame,
            text="Microsoft Store / Epic Games / Xbox App",
            variable=self.platform,
            value="EpicGames_MicrosoftStore_XboxApp",
            font=("Arial", 10),
            command=self.on_platform_change
        ).pack(anchor="w", pady=3)

        path_frame = tk.LabelFrame(
            main_frame,
            text="Among Us Installation Path",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=15
        )
        path_frame.pack(fill="x", pady=(0, 15))

        path_container = tk.Frame(path_frame)
        path_container.pack(fill="x")

        self.path_entry = tk.Entry(
            path_container,
            textvariable=self.among_us_path,
            font=("Arial", 10),
            state="readonly"
        )
        self.path_entry.pack(side="left", fill="x", expand=True)

        tk.Button(
            path_container,
            text="📁 Browse",
            font=("Arial", 10),
            command=self.browse_among_us_path,
            padx=10
        ).pack(side="right", padx=(10, 0))

        self.path_hint = tk.Label(
            path_frame,
            text="",
            font=("Arial", 9),
            fg="gray"
        )
        self.path_hint.pack(anchor="w", pady=(5, 0))

        status_frame = tk.LabelFrame(
            main_frame,
            text="Update Status",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=15
        )
        status_frame.pack(fill="both", expand=True, pady=(0, 15))

        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_text,
            font=("Arial", 10),
            justify="left",
            anchor="w"
        )
        self.status_label.pack(fill="x", pady=(0, 10))

        self.version_label = tk.Label(
            status_frame,
            text="",
            font=("Arial", 10),
            justify="left",
            anchor="w"
        )
        self.version_label.pack(fill="x", pady=(0, 10))

        self.download_label = tk.Label(
            status_frame,
            text="",
            font=("Arial", 10),
            justify="left",
            anchor="w"
        )
        self.download_label.pack(fill="x", pady=(0, 5))

        download_info_frame = tk.Frame(status_frame)
        download_info_frame.pack(fill="x", pady=(0, 10))

        self.speed_label = tk.Label(
            download_info_frame,
            textvariable=self.download_speed,
            font=("Arial", 9),
            fg="#2196F3"
        )
        self.speed_label.pack(side="left")

        self.eta_label = tk.Label(
            download_info_frame,
            text="",
            font=("Arial", 9),
            fg="#666"
        )
        self.eta_label.pack(side="right")

        self.progress_bar = ttk.Progressbar(
            status_frame,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(fill="x", pady=(0, 5))

        self.progress_label = tk.Label(
            status_frame,
            text="",
            font=("Arial", 9)
        )
        self.progress_label.pack()

        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x")

        self.download_button = tk.Button(
            button_frame,
            text="⬇️ Download Newest Update",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10,
            command=self.download_newest_update,
            state="disabled"
        )
        self.download_button.pack(side="left", expand=True, fill="x", padx=(0, 5))

        tk.Button(
            button_frame,
            text="❌ Exit",
            font=("Arial", 12, "bold"),
            bg="#f44336",
            fg="white",
            padx=20,
            pady=10,
            command=self.root.quit
        ).pack(side="right", expand=True, fill="x", padx=(5, 0))

        if hasattr(self, 'saved_platform') and self.saved_platform:
            self.platform.set(self.saved_platform)
            self.on_platform_change()

    def on_platform_change(self):
        platform = self.platform.get()

        if platform == "Steam_Itch":
            self.path_hint.config(
                text="Select folder where Among Us.exe is located (e.g. Steam/steamapps/common/Among Us)")
        elif platform == "EpicGames_MicrosoftStore_XboxApp":
            self.path_hint.config(text="Select folder where Among Us.exe is located (e.g. WindowsApps/...)")

        if self.among_us_path.get() and platform:
            self.download_button.config(state="normal")

    def browse_among_us_path(self):
        if not self.platform.get():
            messagebox.showwarning("Select Platform", "Please select your platform first!")
            return

        folder = filedialog.askdirectory(
            title="Select Among Us installation folder (where Among Us.exe is located)"
        )

        if folder:
            exe_path = os.path.join(folder, "Among Us.exe")
            if os.path.exists(exe_path):
                self.among_us_path.set(folder)
                self.status_text.set("✅ Among Us path found!")
                self.save_config()
                self.download_button.config(state="normal")
            else:
                messagebox.showerror(
                    "Wrong Folder",
                    "Among Us.exe not found!\n\n"
                    "Please select the folder where Among Us.exe is located."
                )

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.saved_platform = config.get("platform", "")
                    self.saved_path = config.get("among_us_path", "")
                    self.saved_version = config.get("version", None)

                    if self.saved_path:
                        self.among_us_path.set(self.saved_path)

                    if self.saved_version:
                        self.version_label.config(text=f"Installed version: {self.saved_version}")
            except:
                pass

    def save_config(self):
        config = {
            "platform": self.platform.get(),
            "among_us_path": self.among_us_path.get(),
            "version": getattr(self, 'saved_version', None),
            "last_updated": datetime.now().isoformat()
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def initial_check(self):
        if self.platform.get() and self.among_us_path.get():
            thread = threading.Thread(target=self.check_version_on_start)
            thread.daemon = True
            thread.start()

    def check_version_on_start(self):
        self.status_text.set("🔍 Checking version...")
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()

            release_data = response.json()
            latest_version = release_data['tag_name']
            current_version = getattr(self, 'saved_version', None)

            if current_version:
                try:
                    latest_clean = latest_version.lstrip('v')
                    current_clean = current_version.lstrip('v')

                    if version.parse(latest_clean) > version.parse(current_clean):
                        self.status_text.set(f"🆕 Update available: {latest_version}")
                    else:
                        self.status_text.set(f"✅ Up to date (Version {current_version})")
                except:
                    if latest_version != current_version:
                        self.status_text.set(f"🆕 Update available: {latest_version}")
                    else:
                        self.status_text.set(f"✅ Up to date (Version {current_version})")
            else:
                self.status_text.set("Ready to download")

        except:
            self.status_text.set("Ready")

    def download_newest_update(self):
        if not self.platform.get():
            messagebox.showwarning("Select Platform", "Please select your platform first!")
            return

        if not self.among_us_path.get():
            messagebox.showwarning("Select Path", "Please select Among Us installation path first!")
            return

        self.download_button.config(state="disabled")
        thread = threading.Thread(target=self.check_and_download)
        thread.daemon = True
        thread.start()

    def check_and_download(self):
        self.status_text.set("🔍 Checking for newest update...")
        self.progress_var.set(0)
        self.download_label.config(text="")
        self.download_speed.set("")
        self.eta_label.config(text="")

        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()

            release_data = response.json()
            latest_version = release_data['tag_name']

            current_version = getattr(self, 'saved_version', None)

            if current_version:
                try:
                    latest_clean = latest_version.lstrip('v')
                    current_clean = current_version.lstrip('v')

                    if version.parse(latest_clean) <= version.parse(current_clean):
                        self.status_text.set(f"✅ Already up to date (Version {current_version})")
                        self.download_button.config(state="normal")
                        return
                except:
                    if latest_version == current_version:
                        self.status_text.set(f"✅ Already up to date (Version {current_version})")
                        self.download_button.config(state="normal")
                        return

            self.status_text.set(f"🆕 Downloading version {latest_version}...")
            self.download_and_install(release_data)

        except requests.exceptions.Timeout:
            self.status_text.set("❌ Connection timeout")
            self.download_button.config(state="normal")
        except requests.exceptions.ConnectionError:
            self.status_text.set("❌ No internet connection")
            self.download_button.config(state="normal")
        except Exception as e:
            self.status_text.set(f"❌ Error: {str(e)}")
            self.download_button.config(state="normal")

    def download_and_install(self, release_data):
        platform = self.platform.get()
        version_tag = release_data['tag_name']
        assets = release_data.get('assets', [])

        target_file = None
        for asset in assets:
            asset_name = asset['name']
            if asset_name.endswith('.zip'):
                if platform == "Steam_Itch" and "Steam" in asset_name:
                    target_file = asset
                    break
                elif platform == "EpicGames_MicrosoftStore_XboxApp" and (
                        "Microsoft" in asset_name or "Epic" in asset_name):
                    target_file = asset
                    break

        if not target_file:
            self.status_text.set("❌ No matching file found for your platform")
            self.download_button.config(state="normal")
            return

        download_url = target_file['browser_download_url']
        file_name = target_file['name']
        file_size = target_file['size']

        self.download_label.config(text=f"📥 {file_name} ({file_size / 1024 / 1024:.1f} MB)")
        self.status_text.set("📥 Downloading...")

        try:
            import time
            start_time = time.time()
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            temp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_update.zip")

            with open(temp_file, 'wb') as f:
                downloaded = 0
                total_size = int(response.headers.get('content-length', 0))
                chunk_size = 8192

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self.progress_var.set(progress)
                            self.progress_label.config(text=f"{progress:.1f}%")

                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                speed = downloaded / elapsed_time
                                speed_mb = speed / 1024 / 1024
                                self.download_speed.set(f"Speed: {speed_mb:.2f} MB/s")

                                remaining = total_size - downloaded
                                if speed > 0:
                                    eta = remaining / speed
                                    eta_min = int(eta // 60)
                                    eta_sec = int(eta % 60)
                                    if eta_min > 0:
                                        self.eta_label.config(text=f"ETA: {eta_min}m {eta_sec}s")
                                    else:
                                        self.eta_label.config(text=f"ETA: {eta_sec}s")

                            self.root.update_idletasks()

            self.status_text.set("📦 Installing update...")
            self.progress_var.set(100)

            among_us_folder = self.among_us_path.get()

            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                zip_ref.extractall(among_us_folder)

            os.remove(temp_file)

            self.saved_version = version_tag
            self.save_config()

            self.version_label.config(text=f"Installed version: {version_tag}")
            self.status_text.set(f"✅ Update successfully installed!")
            self.progress_label.config(text="100% - Complete")
            self.download_speed.set("")
            self.eta_label.config(text="")

            messagebox.showinfo(
                "Update Successful!",
                f"AUnlocker has been updated to version {version_tag}!\n\n"
                f"Installed in: {among_us_folder}"
            )

        except Exception as e:
            self.status_text.set(f"❌ Error: {str(e)}")
            messagebox.showerror("Update Error", f"Failed to update:\n{str(e)}")
        finally:
            self.download_button.config(state="normal")


def main():
    try:
        import packaging
    except ImportError:
        root = tk.Tk()
        root.withdraw()

        result = messagebox.askyesno(
            "Install Packages",
            "Required packages (packaging, requests) are not installed.\n\n"
            "Install them now?"
        )

        if result:
            import subprocess
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "packaging", "requests"])
                messagebox.showinfo("Success", "Packages installed. Please restart the program.")
            except:
                messagebox.showerror("Failed", "Please install manually:\npip install packaging requests")

        root.destroy()
        sys.exit(0)

    root = tk.Tk()
    app = AUnlockerUpdaterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
