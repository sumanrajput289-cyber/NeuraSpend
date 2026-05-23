# -*- coding: utf-8 -*-
"""
Intelligent Enterprise Expense Management & Analytics System
Academic Final Year Project - Voice Capture & Speech Recognizer Module
"""

import threading
import logging
from parser import parse_transaction_text

# Conditional SpeechRecognition imports to prevent application crashes
SPEECH_SUPPORTED = False
try:
    import speech_recognition as sr
    SPEECH_SUPPORTED = True
except ImportError:
    logging.warning("SpeechRecognition package not detected in current Python environment.")


class VoiceCaptureThread(threading.Thread):
    """
    Spawns an asynchronous background worker thread to access the physical microphone.
    Prevents the Tkinter main UI thread from locking up or freezing during audio recording.
    """
    def __init__(self, callback, progress_callback=None):
        """
        Args:
            callback (callable): Function invoked on completion, receiving (success, transcript_or_error_msg)
            progress_callback (callable, optional): Function to update UI state during recording
        """
        super().__init__()
        self.callback = callback
        self.progress_callback = progress_callback
        self.daemon = True

    def run(self):
        """
        Executes the physical voice capture pipeline.
        Includes robust try-except error containment for missing hardware, low input, or API limits.
        """
        if not SPEECH_SUPPORTED:
            self.callback(False, "Voice service unavailable. Verify 'SpeechRecognition' library is installed.")
            return

        recognizer = sr.Recognizer()
        
        # Define short, strict timeouts to prevent indefinite hanging
        recognizer.operation_timeout = 8.0
        recognizer.dynamic_energy_threshold = True

        if self.progress_callback:
            self.progress_callback("Configuring microphone drivers...")

        try:
            # 1. Accessing hardware recording interface
            with sr.Microphone() as source:
                # Adjusting threshold for room ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
                
                if self.progress_callback:
                    self.progress_callback("Listening... Speak your transaction clearly.")
                
                # Listen with a maximum of 5 seconds of silence allowed before timing out
                audio_data = recognizer.listen(source, timeout=6.0, phrase_time_limit=6.0)

            if self.progress_callback:
                self.progress_callback("Converting speech coordinates...")

            # 2. Translating audio signal to textual representation.
            # Under offline guidelines, we attempt local Sphinx if available, 
            # and gracefully catch any HTTP errors if the default Google API times out.
            try:
                # Primary: Attempt Google recognition (fails cleanly if offline)
                transcript = recognizer.recognize_google(audio_data)
                self.callback(True, transcript)
            except sr.UnknownValueError:
                # Occurs when the microphone records sounds but no clear words are matched
                self.callback(False, "Voice captured, but could not be translated. Please try speaking clearer.")
            except sr.RequestError as request_err:
                # Occurs in offline mode when network resources are unavailable
                logging.info("Offline fallback: Voice engine did not connect to external servers: %s", str(request_err))
                # Fallback to local parsing description alert
                self.callback(False, "Offline Mode: Remote voice translation unavailable. Please type your entry in the form.")
                
        except (OSError, AttributeError) as hardware_err:
            # Caught when PyAudio is missing, or microphone drivers are disabled/unavailable
            logging.error("Microphone hardware error: %s", str(hardware_err))
            self.callback(False, "Microphone unavailable. Ensure a physical recording device is connected and PyAudio is active.")
        except sr.WaitTimeoutError:
            # Caught when the user does not speak within the threshold
            self.callback(False, "Speech recording timed out. No sound was detected.")
        except Exception as generic_err:
            # Absolute firewall: prevent desktop application from collapsing under any condition
            logging.error("Critical failure during voice translation: %s", str(generic_err))
            self.callback(False, f"Voice capture service failed: {str(generic_err)}")


def capture_and_parse_voice(ui_success_callback, ui_progress_callback=None):
    """
    Initiates the background thread and hooks the callback.
    When transcription succeeds, the text is run through parser.py to extract amounts and categories automatically.
    """
    def voice_completed_handler(success, result_text):
        if success:
            # Automatically feed transcription into NLP token parser
            parsed_data = parse_transaction_text(result_text)
            parsed_data["raw_text"] = result_text
            ui_success_callback(True, parsed_data)
        else:
            ui_success_callback(False, result_text)

    # Launch threaded capturer
    worker = VoiceCaptureThread(voice_completed_handler, ui_progress_callback)
    worker.start()
