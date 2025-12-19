import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

from moviepy import (
    ImageSequenceClip, 
    AudioFileClip, 
    ColorClip, 
    CompositeVideoClip, 
    concatenate_videoclips,
    concatenate_audioclips
)
import math

# --- 1. PROCESSING FUNCTIONS ---

def run_conversion():
    folder = folder_path.get()
    output = save_path.get()
    audio_p = audio_path.get()
    
    # Standard 1080p Resolution
    W, H = 1920, 1080

    try:
        seconds = float(seconds_entry.get())
        img_paths = [os.path.join(folder, img) for img in os.listdir(folder) 
                     if img.lower().endswith((".png", ".jpg", ".jpeg"))]
        img_paths.sort()

        if not img_paths:
            messagebox.showerror("Error", "No images found in folder.")
            return

        # UI Updates
        progress_bar.start(10)
        status_label.config(text="Status: Rendering... (This may take a while)", fg="orange")
        btn_create.config(state="disabled")

        clips = []
        for path in img_paths:
            # Load single image as a clip
            img_clip = ImageSequenceClip([path], fps=1/seconds)
            
            # Scale image to fit within 1080p while maintaining aspect ratio
            # This prevents stretching
            img_clip = img_clip.resized(height=H) if img_clip.w/img_clip.h < W/H else img_clip.resized(width=W)
            
            # Create black background (letterboxing)
            bg = ColorClip(size=(W, H), color=(0, 0, 0), duration=seconds)
            
            # Layer the image over the black background
            final_img = CompositeVideoClip([bg, img_clip.with_position("center")])
            clips.append(final_img)

        # Combine all images into one video
        video_clip = concatenate_videoclips(clips, method="compose")

        # Attach and loop audio if selected
        if audio_p and os.path.exists(audio_p):
            audio_clip = AudioFileClip(audio_p)
            
            # Calculate how many times the song needs to repeat
            # e.g., if video is 10s and song is 3s, repeat 4 times
            n_repeats = math.ceil(video_clip.duration / audio_clip.duration)
            
            # Create a list of the same clip repeated
            repeated_audio = concatenate_audioclips([audio_clip] * n_repeats)
            
            # Trim the final audio to match the exact video length
            final_audio = repeated_audio.subclipped(0, video_clip.duration)
            
            video_clip = video_clip.with_audio(final_audio)

        # Write the file
        video_clip.write_videofile(
            output, fps=24,
            codec="libx264", 
            audio_codec="aac",
            threads=4,
            preset='ultrafast',
            logger=None
        )
        
        status_label.config(text="Status: Success!", fg="green")
        messagebox.showinfo("Success", f"Video saved to:\n{output}")
        
    except Exception as e:
        status_label.config(text="Status: Error", fg="red")
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
    finally:
        progress_bar.stop()
        btn_create.config(state="normal")

def create_slideshow_thread():
    # This prevents the GUI from freezing during the render
    thread = threading.Thread(target=run_conversion, daemon=True)
    thread.start()

# --- 2. GUI SETUP ---

root = tk.Tk()
root.title("Slideshow Maker Pro (v2.0)")
root.geometry("500x480")

folder_path, save_path, audio_path = tk.StringVar(), tk.StringVar(), tk.StringVar()

# Layout
tk.Label(root, text="1. Select Image Folder:", font=("Arial", 10, "bold")).pack(pady=(15,0))
tk.Entry(root, textvariable=folder_path, width=50).pack()
tk.Button(root, text="Browse Images", command=lambda: folder_path.set(filedialog.askdirectory())).pack(pady=5)

tk.Label(root, text="2. Background Music (Optional):", font=("Arial", 10, "bold")).pack(pady=(10,0))
tk.Entry(root, textvariable=audio_path, width=50).pack()
tk.Button(root, text="Browse Audio", command=lambda: audio_path.set(filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav")]))).pack(pady=5)

tk.Label(root, text="3. Save Video As:", font=("Arial", 10, "bold")).pack(pady=(10,0))
tk.Entry(root, textvariable=save_path, width=50).pack()
tk.Button(root, text="Set Save Name", command=lambda: save_path.set(filedialog.asksaveasfilename(defaultextension=".mp4"))).pack(pady=5)

tk.Label(root, text="Seconds per Picture:", font=("Arial", 10)).pack(pady=(10,0))
seconds_entry = tk.Entry(root, width=10)
seconds_entry.insert(0, "2")
seconds_entry.pack()

progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="indeterminate")
progress_bar.pack(pady=20)

# This button now correctly finds the function defined above
btn_create = tk.Button(root, text="GENERATE VIDEO", command=create_slideshow_thread, bg="#2ecc71", fg="white", font=("Arial", 12, "bold"))
btn_create.pack(pady=10)

status_label = tk.Label(root, text="Status: Ready", fg="blue")
status_label.pack()

root.mainloop()