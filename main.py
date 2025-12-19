import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from moviepy.editor import ImageSequenceClip, AudioFileClip, afx

def create_slideshow_thread():
    thread = threading.Thread(target=run_conversion)
    thread.start()

def run_conversion():
    folder = folder_path.get()
    output = save_path.get()
    audio_p = audio_path.get()
    
    try:
        seconds = float(seconds_entry.get())
        images = [os.path.join(folder, img) for img in os.listdir(folder) 
                  if img.lower().endswith((".png", ".jpg", ".jpeg"))]
        images.sort()

        if not images:
            messagebox.showerror("Error", "No images found.")
            return

        progress_bar.start(10) 
        status_label.config(text="Status: Rendering Video...", fg="orange")
        btn_create.config(state="disabled")

        # Create video clip
        video_clip = ImageSequenceClip(images, fps=1/seconds)

        # Add Audio if selected
        if audio_p and os.path.exists(audio_p):
            audio_clip = AudioFileClip(audio_p)
            # Loop audio if shorter than video, or trim if longer
            audio_clip = afx.audio_loop(audio_clip, duration=video_clip.duration)
            video_clip = video_clip.set_audio(audio_clip)

        video_clip.write_videofile(output, codec="libx264", audio_codec="aac")
        
        status_label.config(text="Status: Finished!", fg="green")
        messagebox.showinfo("Success", "Video Created Successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
    finally:
        progress_bar.stop()
        btn_create.config(state="normal")

# --- GUI Setup ---
root = tk.Tk()
root.title("Slideshow Maker Pro")
root.geometry("500x450")

folder_path, save_path, audio_path = tk.StringVar(), tk.StringVar(), tk.StringVar()

# UI Elements
tk.Label(root, text="1. Image Folder:").pack(pady=(10,0))
tk.Entry(root, textvariable=folder_path, width=50).pack()
tk.Button(root, text="Browse Images", command=lambda: folder_path.set(filedialog.askdirectory())).pack()

tk.Label(root, text="2. Background Music (Optional):").pack(pady=(10,0))
tk.Entry(root, textvariable=audio_path, width=50).pack()
tk.Button(root, text="Browse Audio", command=lambda: audio_path.set(filedialog.askopenfilename(filetypes=[("Audio files", "*.mp3 *.wav")]))).pack()

tk.Label(root, text="3. Save Video As:").pack(pady=(10,0))
tk.Entry(root, textvariable=save_path, width=50).pack()
tk.Button(root, text="Set Destination", command=lambda: save_path.set(filedialog.asksaveasfilename(defaultextension=".mp4"))).pack()

tk.Label(root, text="Seconds per Picture:").pack()
seconds_entry = tk.Entry(root, width=10); seconds_entry.insert(0, "2"); seconds_entry.pack()

progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="indeterminate")
progress_bar.pack(pady=10)

btn_create = tk.Button(root, text="GENERATE VIDEO", command=create_slideshow_thread, bg="#2ecc71", fg="white", font=("Arial", 12, "bold"))
btn_create.pack(pady=10)

status_label = tk.Label(root, text="Status: Ready", fg="blue"); status_label.pack()

root.mainloop()
