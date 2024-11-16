import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, Toplevel
import threading
import subprocess

# Function to create a custom color chooser dialog
def custom_color_chooser(title="Select Color"):
    def update_color_preview():
        # Update the color preview box with the selected color
        r = red_slider.get()
        g = green_slider.get()
        b = blue_slider.get()
        color_preview.config(bg=f"#{r:02x}{g:02x}{b:02x}")

    def confirm_color():
        # Save the selected color and close the dialog
        nonlocal selected_color
        selected_color = (red_slider.get(), green_slider.get(), blue_slider.get())  # Return BGR for OpenCV
        dialog.destroy()

    selected_color = None

    # Create a new dialog window
    dialog = Toplevel()
    dialog.title(title)
    dialog.geometry("300x300")
    dialog.resizable(False, False)

    # Sliders for Red, Green, and Blue
    red_slider = tk.Scale(dialog, from_=0, to=255, orient="horizontal", label="Red", command=lambda x: update_color_preview())
    red_slider.pack(fill="x", padx=10)

    green_slider = tk.Scale(dialog, from_=0, to=255, orient="horizontal", label="Green", command=lambda x: update_color_preview())
    green_slider.pack(fill="x", padx=10)

    blue_slider = tk.Scale(dialog, from_=0, to=255, orient="horizontal", label="Blue", command=lambda x: update_color_preview())
    blue_slider.pack(fill="x", padx=10)

    # Preview box for the selected color
    color_preview = tk.Label(dialog, text="Color Preview", bg="#000000", fg="white", height=2)
    color_preview.pack(fill="x", pady=10)

    # Buttons to confirm or cancel the selection
    confirm_button = tk.Button(dialog, text="Confirm", command=confirm_color)
    confirm_button.pack(side="left", padx=10, pady=10)

    cancel_button = tk.Button(dialog, text="Cancel", command=dialog.destroy)
    cancel_button.pack(side="right", padx=10, pady=10)

    # Wait for the dialog to close before returning the result
    dialog.transient()  # Make the dialog modal
    dialog.grab_set()
    dialog.wait_window()

    return selected_color

# Function to select a color using a color picker dialog
def select_color(title):
    color_code = custom_color_chooser(title=title)
    if color_code:  # Check if the user selected a color
        return np.array([color_code[2], color_code[1], color_code[0]], dtype=np.uint8)  # BGR for OpenCV
    return np.array([0, 0, 0], dtype=np.uint8)

# Function to interpolate between two colors based on grayscale value
def apply_gradient_color(frame, color1, color2):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    normalized_frame = gray_frame.astype(np.float32) / 255.0
    colorized_frame = np.zeros_like(frame, dtype=np.float32)

    for i in range(3):
        colorized_frame[:, :, i] = color1[i] * (1 - normalized_frame) + color2[i] * normalized_frame

    return np.clip(colorized_frame, 0, 255).astype(np.uint8)

# Function to pre-generate the colorized video and save it
def generate_colorized_video(color1, color2, video_path, output_path, progress_bar, complete_callback):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video.")
        complete_callback()  # Re-enable buttons
        return

    # Get the frame width, height, fps, and total frames
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Initialize the video writer object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    # Set up the progress bar
    progress_bar["maximum"] = total_frames
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Apply the gradient colorization to the frame
        colorized_frame = apply_gradient_color(frame, color1, color2)

        # Write the colorized frame to the output video
        out.write(colorized_frame)

        # Update progress bar
        frame_count += 1
        progress_bar["value"] = frame_count
        progress_bar.update_idletasks()

    # Release resources
    cap.release()
    out.release()
    print(f"Colorized video saved to {output_path}")
    complete_callback()  # Re-enable buttons

# Function to start video generation in a separate thread
def generate_video():
    if np.any(color1 != [0, 0, 0]) and np.any(color2 != [0, 0, 0]):  # Ensure colors are selected
        disable_buttons()
        show_progress_bar()
        threading.Thread(target=generate_colorized_video, args=(
            color1, color2, "lln.mp40001-0200.mkv", "colorized_output.avi",
            progress_bar, complete_callback
        )).start()
    else:
        print("Please select both colors before generating the video.")

# Function to run the script for the existing video
def run_script():
    disable_buttons()
    output_path = "colorized_output.avi"
    try:
        subprocess.run(["./lava_lamp.sh", output_path], check=True)
        print(f"Shell script executed successfully for {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while executing the shell script: {e}")
    enable_buttons()

# Functions to manage button states
def disable_buttons():
    generate_button.config(state="disabled")
    run_button.config(state="disabled")

def enable_buttons():
    generate_button.config(state="normal")
    run_button.config(state="normal")

# Functions to manage progress bar visibility
def show_progress_bar():
    progress_bar.pack(pady=20)

def hide_progress_bar():
    progress_bar.pack_forget()

def complete_callback():
    hide_progress_bar()
    enable_buttons()

# Create the main GUI window
root = tk.Tk()
root.title("Color Selection")
root.geometry("300x350")
root.resizable(False, False)

# Store global colors
color1 = np.array([0, 0, 0], dtype=np.uint8)
color2 = np.array([255, 255, 255], dtype=np.uint8)

# GUI Elements
label = tk.Label(root, text="Select two colors for the gradient", pady=20)
label.pack()

def set_color1():
    global color1
    color1 = select_color("Select Color 1")
    print(f"Color 1: {color1}")
    # Update color for Color 1 button
    color1_button.config(bg=f"#{color1[2]:02x}{color1[1]:02x}{color1[0]:02x}")

def set_color2():
    global color2
    color2 = select_color("Select Color 2")
    print(f"Color 2: {color2}")
    # Update color for Color 2 button
    color2_button.config(bg=f"#{color2[2]:02x}{color2[1]:02x}{color2[0]:02x}")

color1_button = tk.Button(root, text="Select Color 1", command=set_color1)
color1_button.pack(pady=10)

color2_button = tk.Button(root, text="Select Color 2", command=set_color2)
color2_button.pack(pady=10)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate")
# Initially hide the progress bar
hide_progress_bar()

generate_button = tk.Button(root, text="Generate Lava Lamp", command=generate_video)
generate_button.pack(pady=10)

run_button = tk.Button(root, text="View Lava Lamp", command=run_script)
run_button.pack(pady=10)

root.mainloop()

