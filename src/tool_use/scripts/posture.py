import os
import time
import sys
import json
import cv2
import numpy as np
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
from rich.text import Text
from datetime import datetime
from collections import deque
import statistics
from PIL import Image
from pydantic import BaseModel
from enum import Enum
from typing import List
from llama_index.core.bridge.pydantic import BaseModel
from llama_index.core.tools import FunctionTool
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage
from transformers import AutoModelForCausalLM, AutoTokenizer
from ..config_manager import config_manager

console = Console()



class Moondream:
    MODEL_ID = "vikhyatk/moondream2"
    REVISION = "2024-08-26"
    
    def __init__(self):
        print("Loading Moondream2 model...")
        self.model = AutoModelForCausalLM.from_pretrained(
            self.MODEL_ID,
            trust_remote_code=True,
            revision=self.REVISION
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.MODEL_ID,
            revision=self.REVISION
        )
        print("Moondream2 model loaded successfully!")
            
    def analyze_posture(self, image):
            start_total = time.time()
            
            # Time image encoding
            start_encode = time.time()
            encoded_image = self.model.encode_image(image)
            encode_time = time.time() - start_encode
            print(f"Image encoding took {encode_time:.2f} seconds")
            
            # Check for focus
            start_focus = time.time()
            focus_answer = self.model.answer_question(
                encoded_image,
                "Look at this webcam image. Please provide several sentences that describe if there is a person there, and if so, if they are focused/distracted, or if they are slouching.",
                self.tokenizer
            )
            focus_time = time.time() - start_focus
            print(f"Focus analysis took {focus_time:.2f} seconds")
            
            # # Check for slouching
            # start_posture = time.time()
            # posture_answer = self.model.answer_question(
            #     encoded_image,
            #     "Is the person slouching or showing poor posture? Answer with just Yes or No.",
            #     self.tokenizer
            # )
            
            total_time = time.time() - start_total
            print(f"\nTotal analysis time: {total_time:.2f} seconds")
            print(f"Results: Focus: {focus_answer}\n")

            return focus_answer.lower().strip() 

class AnalysisResults(BaseModel):
    """Results of analyzing the description of a webcam image"""
    present: bool
    focused: bool
    slouching: bool
    distracted: bool

llm = Ollama(model="llama3.1:latest", request_timeout=120.0)
sllm = llm.as_structured_llm(AnalysisResults)

def extractDataFromMoondream(text: str) -> str:
    prompt = f""" 
    Determine the following information from the provided text:
        1. Human is present
        2. Human is focused on work
        3. Human is not slouching
        4. Human is not distracted
        
        {text}
    """
    try:
        response = sllm.chat([ChatMessage(role="user", content=prompt)])
        
        # Create a dictionary with the analysis results
        analysis = {
            "present": False,
            "focused": False,
            "slouching": False,
            "distracted": False
        }
        
        # Parse the response content
        if hasattr(response.message, 'content'):
            content = response.message.content
            if isinstance(content, str):
                try:
                    # Try to parse it as JSON first
                    analysis = json.loads(content)
                except json.JSONDecodeError:
                    # If it's not JSON, try to parse the text response
                    analysis["present"] = "present: true" in content.lower()
                    analysis["focused"] = "focused: true" in content.lower()
                    analysis["slouching"] = "slouching: true" in content.lower()
                    analysis["distracted"] = "distracted: true" in content.lower()
            elif isinstance(content, dict):
                analysis = content
        
        # Convert the analysis to a JSON string
        return json.dumps(analysis)
        
    except Exception as e:
        print(f"Error in extractDataFromMoondream: {e}")
        # Return a default response if there's an error
        return json.dumps({
            "present": False,
            "focused": False,
            "slouching": False,
            "distracted": False
        })
        
        
class WebcamHandler:
    def __init__(
        self, 
        capture_interval=10, 
        save_images=False, 
        save_directory="captured_images",
        resize_factor=0.5,
        jpeg_quality=85
    ):
        self.capture_interval = capture_interval
        self.save_images = save_images
        self.save_directory = save_directory
        self.resize_factor = resize_factor
        self.jpeg_quality = jpeg_quality
        
        if save_images:
            os.makedirs(save_directory, exist_ok=True)
        
        self.camera = None
        self.initialize_camera()

    def initialize_camera(self):
        """Initialize the webcam with proper error handling"""
        # Try to open the camera
        self.camera = cv2.VideoCapture(0)
        
        if not self.camera.isOpened():
            if sys.platform == "darwin":  # macOS
                print("Camera access denied. Attempting to fix...")
                print("Please grant camera permissions in System Preferences -> Security & Privacy -> Camera")
                print("You might need to run: 'tccutil reset Camera' in Terminal with admin privileges")
                
                try:
                    subprocess.run(['tccutil', 'reset', 'Camera'], check=True)
                    print("Camera permissions reset. Please run the program again.")
                except subprocess.CalledProcessError:
                    print("Failed to reset camera permissions automatically.")
                except FileNotFoundError:
                    print("Could not find tccutil. Please reset permissions manually.")
                
            else:  # Other platforms
                print("Could not open webcam. Please check if:")
                print("1. Your webcam is connected")
                print("2. It's not being used by another application")
                print("3. You have granted necessary permissions")
            
            raise RuntimeError("Could not open webcam. Please check permissions and try again.")

        # Test capture to ensure camera is working
        ret, _ = self.camera.read()
        if not ret:
            self.camera.release()
            raise RuntimeError("Camera opened but failed to capture. Please check if it's being used by another application.")

    def capture_frame(self):
        """Capture a frame from webcam and return as PIL Image"""
        if self.camera is None or not self.camera.isOpened():
            self.initialize_camera()

        ret, frame = self.camera.read()
        if not ret:
            print("Failed to capture frame. Attempting to reinitialize camera...")
            if self.camera is not None:
                self.camera.release()
            self.initialize_camera()
            ret, frame = self.camera.read()
            if not ret:
                raise RuntimeError("Failed to capture frame even after reinitializing camera")

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        image = Image.fromarray(rgb_frame)
        
        # Resize based on resize_factor
        width, height = image.size
        new_width = int(width * self.resize_factor)
        new_height = int(height * self.resize_factor)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        if self.save_images:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.save_directory, f"frame_{timestamp}.jpg")
            image.save(save_path, "JPEG", quality=self.jpeg_quality)
            return image, save_path
        
        return image, None

    def process_saved_image(self, image_path: str):
        """Process a saved image (e.g., move it to an archive folder or delete it)"""
        if os.path.exists(image_path):
            # For now, we'll just delete the temporary image
            # You could modify this to move it to an archive folder instead
            os.remove(image_path)

    def __del__(self):
        if self.camera is not None:
            self.camera.release()
        

class ProductivityCoach:
    def __init__(
        self, 
        capture_interval=10,
        save_images=False,
        resize_factor=0.5,
        jpeg_quality=85,
    ):
        # Initialize with a fancy loading display
        with console.status("[bold green]Initializing Productivity Coach...", spinner="dots"):
            self.moondream = Moondream()
            self.webcam = WebcamHandler(
                capture_interval=capture_interval,
                save_images=save_images,
                resize_factor=resize_factor,
                jpeg_quality=jpeg_quality
            )
            self.capture_interval = capture_interval
            
            # Stats tracking
            self.stats = {
                "total_frames": 0,
                "focused_frames": 0,
                "slouching_frames": 0,
                "distracted_frames": 0,
                "start_time": datetime.now(),
                "focus_history": deque(maxlen=50),  # Keep last 50 readings
            }

    def generate_layout(self) -> Layout:
        layout = Layout()
        
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="stats"),
            Layout(name="current_status"),
        )
        
        return layout

    def make_stats_panel(self) -> Panel:
        duration = datetime.now() - self.stats["start_time"]
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        # Calculate percentages
        total = max(1, self.stats["total_frames"])
        focus_rate = (self.stats["focused_frames"] / total) * 100
        slouch_rate = (self.stats["slouching_frames"] / total) * 100
        distraction_rate = (self.stats["distracted_frames"] / total) * 100
        
        # Calculate recent focus trend
        recent_focus = list(self.stats["focus_history"])
        trend = "→"
        if len(recent_focus) > 5:
            recent_avg = statistics.mean(recent_focus[-5:])
            older_avg = statistics.mean(recent_focus[-10:-5])
            if recent_avg > older_avg + 0.1:
                trend = "↑"
            elif recent_avg < older_avg - 0.1:
                trend = "↓"

        stats_table = Table(show_header=False, box=None)
        stats_table.add_row("Session Duration:", f"{hours:02d}:{minutes:02d}")
        stats_table.add_row("Total Frames:", str(self.stats["total_frames"]))
        stats_table.add_row("Focus Rate:", f"{focus_rate:.1f}% {trend}")
        stats_table.add_row("Slouching Rate:", f"{slouch_rate:.1f}%")
        stats_table.add_row("Distraction Rate:", f"{distraction_rate:.1f}%")
        
        return Panel(stats_table, title="[bold]Session Statistics", border_style="blue")

    def make_status_panel(self, status_data) -> Panel:
        status_text = Text()
        
        # Focus Status
        if status_data["focused"]:
            status_text.append("🎯 Focused\n", style="bold green")
        else:
            status_text.append("😶‍🌫️ Distracted\n", style="bold red")
            
        # Posture Status
        if status_data["slouching"]:
            status_text.append("🪑 Poor Posture\n", style="bold red")
        else:
            status_text.append("👍 Good Posture\n", style="bold green")
            
        # Presence Status
        if status_data["present"]:
            status_text.append("👤 Present\n", style="bold green")
        else:
            status_text.append("❓ Not Detected\n", style="bold yellow")
            
        return Panel(status_text, title="[bold]Current Status", border_style="green")

    def update_stats(self, status_str: str):
        # Parse the JSON string into a dictionary
        try:
            status = json.loads(status_str)
        except json.JSONDecodeError:
            console.print("[bold red]Error parsing status data[/]")
            return

        self.stats["total_frames"] += 1
        if status.get("focused", False):
            self.stats["focused_frames"] += 1
        if status.get("slouching", False):
            self.stats["slouching_frames"] += 1
        if status.get("distracted", False):
            self.stats["distracted_frames"] += 1
            
        # Update focus history (1 for focused, 0 for not)
        self.stats["focus_history"].append(1 if status.get("focused", False) else 0)

    def run(self):
        layout = self.generate_layout()
        
        # Header and footer
        layout["header"].update(Panel(
            "[bold blue]Productivity Coach[/] - Press Ctrl+C to exit",
            style="bold white on blue"
        ))
        layout["footer"].update(Panel(
            f"Capturing every {self.capture_interval}s • Image Size: {self.webcam.resize_factor*100:.0f}% • JPEG Quality: {self.webcam.jpeg_quality}",
            style="bold white on blue"
        ))
        
        # Initialize the panels with default content
        layout["stats"].update(self.make_stats_panel())
        layout["current_status"].update(self.make_status_panel({
            "present": False,
            "focused": False,
            "slouching": False,
            "distracted": False
        }))
        
        with Live(layout, refresh_per_second=1, screen=True):
            try:
                while True:
                    # Capture and analyze frame
                    image, temp_path = self.webcam.capture_frame()
                    results = self.moondream.analyze_posture(image)
                    status_str = extractDataFromMoondream(results)
                    
                    try:
                        status_data = json.loads(status_str)
                        # Update stats
                        self.update_stats(status_str)
                        
                        # Update panels
                        layout["stats"].update(self.make_stats_panel())
                        layout["current_status"].update(self.make_status_panel(status_data))
                    except json.JSONDecodeError:
                        console.print("[bold red]Error parsing status data[/]")
                    
                    # Process saved image
                    if temp_path:
                        self.webcam.process_saved_image(temp_path)
                    
                    time.sleep(self.capture_interval)
                    
            except KeyboardInterrupt:
                console.print("\n[bold red]Stopping Productivity Coach...[/]")

def main(args=None):
    tool_config = config_manager.get_tool_config("posture")
    max_retries = 3
    retry_delay = 5
    capture_interval = tool_config.get("capture_interval", 10)
    save_images = tool_config.get("save_images", False)
    
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} of {max_retries} to start Productivity Coach...")
            coach = ProductivityCoach(capture_interval=capture_interval, save_images=save_images)
            coach.run()
            break
        except RuntimeError as e:
            print(f"\nError: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("\nFailed to initialize after multiple attempts.")
                print("Please ensure your webcam is connected and permissions are granted.")
                if sys.platform == "darwin":
                    print("\nOn macOS, try these steps:")
                    print("1. Open System Preferences")
                    print("2. Go to Security & Privacy -> Privacy -> Camera")
                    print("3. Ensure your terminal/IDE has camera permissions")
                    print("4. Run 'tccutil reset Camera' in Terminal with admin privileges")
                sys.exit(1)

if __name__ == "__main__":
    main()