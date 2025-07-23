import customtkinter as ctk
import speech_recognition as sr
import logging
import traceback
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from nlp_processor import NLPProcessor
from task_manager import TaskManager
from constants import ThemeColors, UIConfig, StatusEmojis, THEME_PRESETS

class AnimatedButton(ctk.CTkButton):
    """Custom animated button with hover effects"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hover_color = kwargs.get("hover_color", ThemeColors.PRIMARY_HOVER)
        self.default_color = kwargs.get("fg_color", ThemeColors.PRIMARY)
        
        # Bind hover events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event=None):
        """Handle mouse enter event"""
        self.configure(fg_color=self.hover_color)
    
    def _on_leave(self, event=None):
        """Handle mouse leave event"""
        self.configure(fg_color=self.default_color)
    
    def _clicked(self, event=None):
        """Override the default click handler"""
        if self._command is not None:  # Changed from self.command to self._command
            self._command()
        self._on_leave()

class MessageBubble(ctk.CTkFrame):
    """Enhanced message bubble with animations and rich formatting"""
    def __init__(
        self, 
        master: Any, 
        message: str, 
        is_user: bool = False, 
        **kwargs
    ):
        super().__init__(master, **kwargs)

        # Configure bubble appearance
        self.configure(
            fg_color=ThemeColors.USER_MSG_BG if is_user else ThemeColors.BOT_MSG_BG,
            corner_radius=UIConfig.CORNERS["message"]
        )

        # Message container
        self.message_container = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.message_container.pack(fill="both", expand=True)

        # Message label with improved typography
        self.message = ctk.CTkLabel(
            self.message_container,
            text=message,
            text_color=ThemeColors.USER_MSG_TEXT if is_user else ThemeColors.BOT_MSG_TEXT,
            font=(UIConfig.FONTS["messages"], UIConfig.FONT_SIZES["medium"]),
            wraplength=500,
            justify="left"
        )
        self.message.pack(padx=UIConfig.PADDING["medium"], 
                         pady=UIConfig.PADDING["small"])

        # Timestamp with subtle styling
        self.timestamp = ctk.CTkLabel(
            self.message_container,
            text=datetime.now().strftime("%H:%M"),
            text_color=ThemeColors.USER_MSG_TEXT if is_user else ThemeColors.BOT_MSG_TEXT,
            font=(UIConfig.FONTS["main"], UIConfig.FONT_SIZES["tiny"]),
            fg_color="transparent"
        )
        self.timestamp.pack(padx=UIConfig.PADDING["small"], 
                          pady=(0, UIConfig.PADDING["small"]), 
                          anchor="e")
                          
class VISA4DGui(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk):
        super().__init__(master)
        self.master = master
        self.master.title("VISA4D: Voice-Integrated Scheduling Assistant")
        self.master.geometry("1000x700")
        
        # Initialize speech recognition
        try:
            self.recognizer = sr.Recognizer()
            # Test microphone availability
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.speech_recognition_available = True
        except Exception as e:
            logging.error(f"Speech recognition initialization error: {str(e)}")
            self.speech_recognition_available = False
        
        # Apply theme
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        
        # Initialize components
        self.nlp_processor = NLPProcessor()
        self.task_manager = TaskManager()  # Initialize without credentials initially
        
        # GUI state
        self.state: Dict[str, Any] = {
            'awaiting_confirmation': False,
            'confirmation_task': None,
            'confirmation_date': None,
            'command_type': None,
            'recording': False,
            'theme': 'light',
            'authenticated': False
        }

        self._init_gui_components()
        self._apply_theme(self.state['theme'])
        self.pack(fill="both", expand=True)
        
        # Show authentication prompt after initializing GUI
        self.after(500, self.prompt_authentication)

    def _init_gui_components(self):
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header area
        self.header = self._setup_header()
        self.header.grid(row=0, column=0, padx=UIConfig.PADDING["medium"], 
                        pady=UIConfig.PADDING["medium"], sticky="ew")

        # Chat area with improved styling
        self.chat_frame = self._setup_chat_frame()
        self.chat_frame.grid(row=1, column=0, padx=UIConfig.PADDING["medium"], 
                           pady=(0, UIConfig.PADDING["medium"]), sticky="nsew")

        # Input area with modern design
        self.input_frame = self._setup_input_area()
        self.input_frame.grid(row=2, column=0, padx=UIConfig.PADDING["medium"], 
                            pady=UIConfig.PADDING["medium"], sticky="ew")

        # Status bar with subtle design
        self.status_bar = self._setup_status_bar()
        self.status_bar.grid(row=3, column=0, padx=UIConfig.PADDING["medium"], 
                           pady=(0, UIConfig.PADDING["medium"]), sticky="ew")

        # Welcome message
        self.display_message("👋 Welcome to VISA4D! How can I help you today?", is_user=False)

    def _setup_header(self) -> ctk.CTkFrame:
        header = ctk.CTkFrame(self, fg_color="transparent")
        
        # Title with custom font
        title = ctk.CTkLabel(
            header,
            text="VISA4D Assistant",
            font=(UIConfig.FONTS["headers"], UIConfig.FONT_SIZES["xlarge"]),
            text_color=ThemeColors.PRIMARY
        )
        title.pack(side="left", padx=UIConfig.PADDING["medium"])
        
        # Authentication status indicator
        self.auth_status = ctk.CTkLabel(
            header,
            text="🔒 Not Connected",
            font=(UIConfig.FONTS["main"], UIConfig.FONT_SIZES["small"]),
            text_color="#F39C12"  # Yellow/orange for warning
        )
        self.auth_status.pack(side="left", padx=UIConfig.PADDING["medium"])
        
        # Authentication button
        self.auth_button = AnimatedButton(
            header,
            text="Connect",
            width=80,
            command=self.prompt_authentication,
            font=(UIConfig.FONTS["main"], UIConfig.FONT_SIZES["small"])
        )
        self.auth_button.pack(side="right", padx=UIConfig.PADDING["small"])
        
        # Theme switcher
        theme_button = AnimatedButton(
            header,
            text="🌓",
            width=40,
            command=self._toggle_theme,
            font=(UIConfig.FONTS["main"], UIConfig.FONT_SIZES["large"])
        )
        theme_button.pack(side="right", padx=UIConfig.PADDING["medium"])
        
        return header

    def _setup_chat_frame(self) -> ctk.CTkScrollableFrame:
        return ctk.CTkScrollableFrame(
            self,
            corner_radius=UIConfig.CORNERS["large"],
            fg_color=THEME_PRESETS[self.state['theme']]['secondary_bg']
        )

    def _setup_input_area(self) -> ctk.CTkFrame:
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        # Modern text input
        self.input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your message here...",
            height=45,
            font=(UIConfig.FONTS["main"], UIConfig.FONT_SIZES["medium"]),
            corner_radius=UIConfig.CORNERS["medium"]
        )
        self.input_entry.pack(side="left", fill="x", expand=True, 
                            padx=(0, UIConfig.PADDING["medium"]))
        self.input_entry.bind("<Return>", self.on_enter)

        # Voice input button with animation
        self.speak_button = AnimatedButton(
            input_frame,
            text=StatusEmojis.MIC,
            width=45,
            height=45,
            corner_radius=UIConfig.CORNERS["medium"],
            command=self.prompt_recording,
            font=(UIConfig.FONTS["main"], UIConfig.FONT_SIZES["large"])
        )
        self.speak_button.pack(side="left", padx=UIConfig.PADDING["small"])

        # Send button with animation
        self.send_button = AnimatedButton(
            input_frame,
            text=StatusEmojis.SEND,
            width=45,
            height=45,
            corner_radius=UIConfig.CORNERS["medium"],
            command=self.on_type_button_click,
            font=(UIConfig.FONTS["main"], UIConfig.FONT_SIZES["large"])
        )
        self.send_button.pack(side="left")

        return input_frame

    def _setup_status_bar(self) -> ctk.CTkLabel:
        return ctk.CTkLabel(
            self,
            text="Ready",
            font=(UIConfig.FONTS["main"], UIConfig.FONT_SIZES["small"]),
            anchor="w",
            fg_color="transparent"
        )

    def prompt_authentication(self):
        """Show authentication dialog using standard Tkinter to avoid CustomTkinter scaling issues"""
        import tkinter as tk
        from tkinter import ttk
        
        # Create a standard Tkinter dialog instead
        auth_dialog = tk.Toplevel(self)
        auth_dialog.title("Connect to Navisworks")
        auth_dialog.geometry("400x200")
        auth_dialog.resizable(False, False)
        
        # Make dialog modal using standard Tkinter
        auth_dialog.transient(self.winfo_toplevel())
        auth_dialog.grab_set()
        
        # Style the Tkinter dialog to look similar to CustomTkinter
        style = ttk.Style()
        style.configure("TFrame", background="#2a2a2a")
        style.configure("TLabel", background="#2a2a2a", foreground="white", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))
        
        # Dark theme for the dialog
        auth_dialog.configure(bg="#2a2a2a")
        
        # Center the dialog
        auth_dialog.update_idletasks()
        width = auth_dialog.winfo_width()
        height = auth_dialog.winfo_height()
        x = (auth_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (auth_dialog.winfo_screenheight() // 2) - (height // 2)
        auth_dialog.geometry(f"+{x}+{y}")
        
        # Create a frame to hold the content
        main_frame = ttk.Frame(auth_dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Dialog content
        header_label = ttk.Label(
            main_frame, 
            text="Connect to Navisworks API",
            font=("Segoe UI", 14, "bold"),
            foreground="white"
        )
        header_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        # Client ID
        id_label = ttk.Label(
            main_frame,
            text="Client ID:",
            foreground="white"
        )
        id_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        client_id_entry = ttk.Entry(main_frame, width=30)
        client_id_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Client Secret
        secret_label = ttk.Label(
            main_frame,
            text="Client Secret:",
            foreground="white"
        )
        secret_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        client_secret_entry = ttk.Entry(main_frame, width=30, show="•")
        client_secret_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # Status message
        status_var = tk.StringVar()
        status_label = ttk.Label(
            main_frame,
            textvariable=status_var,
            foreground="#F39C12"  # Yellow/orange for warning
        )
        status_label.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Connect button
        def on_connect():
            client_id = client_id_entry.get().strip()
            client_secret = client_secret_entry.get().strip()
            
            if not client_id or not client_secret:
                status_var.set("Please enter both Client ID and Client Secret")
                return
            
            status_var.set("Connecting...")
            auth_dialog.update()
            
            # Authenticate with Navisworks API
            success = self.authenticate(client_id, client_secret)
            
            if success:
                status_var.set("Connected successfully!")
                # Change status label color to green
                status_label.configure(foreground="#27AE60")
                auth_dialog.after(1000, auth_dialog.destroy)
            else:
                status_var.set("Authentication failed. Please check your credentials.")
        
        connect_button = ttk.Button(
            button_frame,
            text="Connect",
            command=on_connect
        )
        connect_button.pack(side="left", padx=5)
        
        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=auth_dialog.destroy
        )
        cancel_button.pack(side="left", padx=5)
        
        # Set focus to the client ID entry
        client_id_entry.focus_set()
        
        # Set focus to first entry
        client_id_entry.focus_set()

    def authenticate(self, client_id: str, client_secret: str) -> bool:
        """Authenticate with the Navisworks API"""
        try:
            # Initialize a new TaskManager with credentials if not already created
            if not hasattr(self, 'task_manager') or self.task_manager is None:
                self.task_manager = TaskManager(client_id, client_secret)
            
            # Authenticate with the API
            success = self.task_manager.authenticate(client_id, client_secret)
            
            # Update UI based on authentication result
            if success:
                self.state['authenticated'] = True
                self.auth_status.configure(
                    text="🔓 Connected",
                    text_color="#27AE60"  # Green color for success
                )
                self.auth_button.configure(text="Reconnect")
                self.display_message("✅ Connected to Navisworks successfully!", is_user=False)
            else:
                self.state['authenticated'] = False
                self.auth_status.configure(
                    text="🔒 Not Connected",
                    text_color="#F39C12"  # Yellow/orange for warning
                )
                self.display_message("❌ Failed to connect to Navisworks API. Please check your credentials and try again.", is_user=False)
            
            return success
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            self.state['authenticated'] = False
            self.auth_status.configure(
                text="🔒 Error Connecting",
                text_color="#E74C3C"  # Red color for error
            )
            self.display_message(f"❌ Error connecting to Navisworks API: {str(e)}", is_user=False)
            return False

    def check_authenticated(self) -> bool:
        """Check if authenticated and prompt if not"""
        if not self.state.get('authenticated', False):
            self.display_message(
                "⚠️ You need to connect to Navisworks first before performing this action.",
                is_user=False
            )
            self.prompt_authentication()
            return False
        return True

    def _toggle_theme(self):
        self.state['theme'] = 'dark' if self.state['theme'] == 'light' else 'light'
        self._apply_theme(self.state['theme'])

    def _apply_theme(self, theme_name: str):
        theme = THEME_PRESETS[theme_name]
        self.configure(fg_color=theme["bg_color"])
        self.chat_frame.configure(fg_color=theme["secondary_bg"])
        ctk.set_appearance_mode(theme_name)

    def display_message(self, message: str, is_user: bool = False):
        message_bubble = MessageBubble(
            self.chat_frame,
            message,
            is_user=is_user
        )
        message_bubble.pack(
            fill="x",
            padx=UIConfig.PADDING["medium"],
            pady=UIConfig.PADDING["small"],
            anchor="e" if is_user else "w"
        )
        
        # Auto scroll to bottom
        self.after(100, self.chat_frame._parent_canvas.yview_moveto, 1.0)

    # Modified to check authentication before processing commands
    def on_enter(self, event=None):
        try:
            command = self.input_entry.get().strip()
            if command:
                self.display_message(command, is_user=True)
                
                # Check if command is related to authentication
                if "connect" in command.lower() or "login" in command.lower() or "authenticate" in command.lower():
                    self.prompt_authentication()
                else:
                    # For other commands, check authentication status
                    if not self.check_authenticated() and "help" not in command.lower():
                        # Skip NLP processing if not authenticated
                        pass
                    else:
                        self.nlp_processor.process_command(command, self)
                
                self.input_entry.delete(0, 'end')
        except Exception as e:
            logging.error(f"Error in on_enter: {str(e)}\n{traceback.format_exc()}")
            self.display_message(
                f"{StatusEmojis.ERROR} An error occurred while processing your command. Please try again.",
                is_user=False
            )
    
    def on_type_button_click(self):
        self.on_enter()
        
    def prompt_recording(self):
        """Handle recording button click"""
        if not self.speech_recognition_available:
            self.display_message(
                f"{StatusEmojis.ERROR} Speech recognition is not available. Please check your microphone.",
                is_user=False
            )
            return

        try:
            if not self.state['recording']:
                # Start recording
                self.state['recording'] = True
                self.speak_button.configure(text=StatusEmojis.RECORDING)
                self.status_bar.configure(text="Recording started...")
                
                # Start recording in a separate thread
                threading.Thread(target=self.start_recording, daemon=True).start()
            else:
                # Stop recording
                self.state['recording'] = False
                self.speak_button.configure(text=StatusEmojis.MIC)
                self.status_bar.configure(text="Recording stopped")
        except Exception as e:
            logging.error(f"Error in prompt_recording: {str(e)}\n{traceback.format_exc()}")
            self.display_message(
                f"{StatusEmojis.ERROR} An error occurred with the recording system. Please try typing instead.",
                is_user=False
            )
            self._reset_recording_state()

    def start_recording(self):
        """Handle the actual recording process"""
        try:
            with sr.Microphone() as source:
                # Update GUI from main thread
                self.after(0, lambda: self.status_bar.configure(text="Calibrating microphone..."))
                
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Update status
                self.after(0, lambda: self.status_bar.configure(text="Listening for your command..."))
                
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=15)
                
                # Process audio
                self.after(0, lambda: self.status_bar.configure(text="Processing your command..."))
                
                # Convert speech to text
                text = self.recognizer.recognize_google(audio)
                
                # Update GUI with results
                self.after(0, lambda: self.display_message(text, is_user=True))
                
                # Check authentication before processing voice commands
                def process_voice_command():
                    if "connect" in text.lower() or "login" in text.lower() or "authenticate" in text.lower():
                        self.prompt_authentication()
                    elif not self.check_authenticated() and "help" not in text.lower():
                        # Skip NLP processing if not authenticated
                        pass
                    else:
                        self.nlp_processor.process_command(text, self)
                
                self.after(0, process_voice_command)
                
        except sr.WaitTimeoutError:
            self.after(0, lambda: self.display_message(
                "No speech detected. Please try again.",
                is_user=False
            ))
        except sr.RequestError:
            self.after(0, lambda: self.display_message(
                "Could not connect to the speech recognition service. Please check your internet connection.",
                is_user=False
            ))
        except sr.UnknownValueError:
            self.after(0, lambda: self.display_message(
                "Sorry, I couldn't understand what you said. Please try again.",
                is_user=False
            ))
        except Exception as e:
            logging.error(f"Error in start_recording: {str(e)}\n{traceback.format_exc()}")
            self.after(0, lambda: self.display_message(
                "An error occurred during recording. Please try again.",
                is_user=False
            ))
        finally:
            self._reset_recording_state()

    def _reset_recording_state(self):
        """Reset the recording state and update UI"""
        self.state['recording'] = False
        self.after(0, lambda: self.speak_button.configure(text=StatusEmojis.MIC))
        self.after(0, lambda: self.status_bar.configure(text="Ready"))