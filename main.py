import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
import tempfile
from moviepy import (
    ImageClip, 
    AudioFileClip, 
    concatenate_videoclips,
    CompositeVideoClip
)
from proglog import ProgressBarLogger
import imageio_ffmpeg

# --- 1. LOW-OVERHEAD LOGGER ---
class LazyLogger(ProgressBarLogger):
    def __init__(self, label, pbar, root_window):
        super().__init__()
        self.label = label
        self.pbar = pbar
        self.root = root_window
        self.last_update_time = 0
        self.update_interval = 15  # Update UI every 15 seconds

    def callback(self, **changes):
        current_time = time.time()
        
        # Only update the GUI if 15 seconds have passed
        if current_time - self.last_update_time >= self.update_interval:
            state = self.state.get('bars')
            if 't' in state:
                current = state['t']['index']
                total = state['t']['total']
                
                if total > 0:
                    percentage = (current / total) * 100
                    self.pbar['value'] = percentage
                    self.label.config(text=f"Encoding in progress... {int(percentage)}%")
                    
                    # Force a GUI refresh
                    self.root.update()
                    self.last_update_time = current_time

# --- 2. CONVERSION LOGIC ---
def run_conversion():
    folder = folder_path.get()
    output = os.path.abspath(save_path.get())
    audio_p = audio_path.get()
    
    try:
        if not folder or not output:
            messagebox.showerror("Error", "Select paths first.")
            return
        
        if os.path.exists(output):
            os.remove(output)

        seconds = float(seconds_entry.get())
        img_paths = [os.path.join(folder, f) for f in os.listdir(folder) 
                     if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        img_paths.sort()

        status_label.config(text="Status: Preparing Frames...")
        root.update()

        final_clips = []
        for path in img_paths:
            img = ImageClip(path).with_duration(seconds)
            img = img.resized(height=1080) if img.h > img.w else img.resized(width=1920)
            img = img.with_position("center")
            final_clips.append(img)

        video = concatenate_videoclips(final_clips, method="compose", bg_color=(0,0,0))

        if audio_p and os.path.exists(audio_p):
            audio = AudioFileClip(audio_p).with_duration(video.duration)
            video = video.with_audio(audio)

        # --- Adaptive estimator ---
        fps = 24
        sample_duration = min(10, video.duration)  # 10s or less if video is shorter

        # Prefer with_duration (available in MoviePy 2.x)
        try:
            sample_clip = video.with_duration(sample_duration)
        except AttributeError:
            # Fallback: wrap then apply with_duration
            sample_clip = CompositeVideoClip([video]).with_duration(sample_duration)

        tmpfile = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name

        start_time = time.time()
        sample_clip.write_videofile(
            tmpfile,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=1,
            logger=None,
            bitrate="5000k"
        )
        elapsed = time.time() - start_time

        # seconds encoded per second elapsed
        encoding_speed = sample_duration / max(elapsed, 1e-6)
        est_time = video.duration / max(encoding_speed, 1e-6)
        minutes, seconds_left = divmod(int(est_time), 60)

        # Cleanup temp file
        try:
            os.remove(tmpfile)
        except Exception:
            pass

        status_label.config(text=f"Estimated encoding time: {minutes}m {seconds_left}s")
        root.update()

        # --- Full encode (no live updates) ---
        video.write_videofile(
            output,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=1,
            logger=None,
            bitrate="5000k"
        )

        messagebox.showinfo("Success", "Video successfully created!")
        status_label.config(text="Status: Success!", fg="green")

    except Exception as e:
        messagebox.showerror("Error", f"Caught Error: {str(e)}")
    finally:
        btn_create.config(state="normal")


def start_thread():
    threading.Thread(target=run_conversion, daemon=True).start()

# --- 3. GUI ---
root = tk.Tk()
root.title("Fast Slideshow Maker")
root.geometry("450x500")

folder_path, save_path, audio_path = tk.StringVar(), tk.StringVar(), tk.StringVar()

tk.Label(root, text="Select Image Folder:").pack(pady=5)
tk.Entry(root, textvariable=folder_path, width=50).pack()
tk.Button(root, text="Browse", command=lambda: folder_path.set(filedialog.askdirectory())).pack()

tk.Label(root, text="Background Music:").pack(pady=5)
tk.Entry(root, textvariable=audio_path, width=50).pack()
tk.Button(root, text="Select", command=lambda: audio_path.set(filedialog.askopenfilename())).pack()

tk.Label(root, text="Save As:").pack(pady=5)
tk.Entry(root, textvariable=save_path, width=50).pack()
tk.Button(root, text="Browse", command=lambda: save_path.set(filedialog.asksaveasfilename(defaultextension=".mp4"))).pack()

tk.Label(root, text="Seconds per Photo:").pack(pady=5)
seconds_entry = tk.Entry(root, width=10); seconds_entry.insert(0, "2.5"); seconds_entry.pack()

progress_bar = ttk.Progressbar(root, orient="horizontal", length=350, mode="determinate")
progress_bar.pack(pady=20)

status_label = tk.Label(root, text="Status: Ready")
status_label.pack()

btn_create = tk.Button(root, text="GENERATE VIDEO", command=start_thread, bg="green", fg="white", font=("Arial", 12, "bold"))
btn_create.pack(pady=20)

root.mainloop()