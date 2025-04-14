#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import faster_whisper
from ui import sleek_ui
import sounddevice as sd
import numpy as np
import keyboard
import threading
from pynput.keyboard import Controller as PynputController
import queue
import time
import sys
import soundfile as sf # For saving debug audio

# --- Configuration ---
MODEL_SIZE = "base.en"  # Or "small.en", etc.
# --- Set this if you want to override default detection ---
MANUAL_DEVICE_INDEX = None # Example: MANUAL_DEVICE_INDEX = 0
# --- END OF MANUAL DEVICE INDEX ---
HOTKEY = "ctrl+alt+space"
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_DURATION_MS = 1000
SILENCE_THRESHOLD = 100
SILENCE_DURATION_SEC = 2

# --- Global Variables ---
is_listening = False
stop_event = threading.Event()
audio_queue = queue.Queue()
recording_thread = None
whisper_model = None
keyboard_controller = PynputController()
last_sound_time = time.time()
selected_device_index = None
selected_device_name = "Default"

# --- Functions ---

def load_model():
    """Loads the faster-whisper model."""
    global whisper_model
    print(f"Loading whisper model: {MODEL_SIZE}...")
    try:
        whisper_model = faster_whisper.WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8") # Keep int8 for now
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading whisper model: {e}")
        # (Error handling code as before)
        sys.exit(1)

def list_audio_devices():
    # (Function as before)
    print("\nAvailable Audio Devices:")
    try:
        print(sd.query_devices())
    except Exception as e:
        print(f"Could not query audio devices: {e}")
    print("--- End of Device List ---\n")


def audio_callback(indata, frames, time_info, status):
    # (Function as before)
    global last_sound_time
    if status:
        print(f"Audio callback status: {status}", file=sys.stderr)
    rms = np.sqrt(np.mean(indata**2))
    if rms > SILENCE_THRESHOLD / 1000.0:
         last_sound_time = time.time()
    audio_queue.put(indata.copy()) # indata is likely (N, 1)

def record_audio_thread():
    # (Function mostly as before)
    global is_listening, last_sound_time, selected_device_index, selected_device_name
    stream = None
    print("\nRecording started...")
    last_sound_time = time.time()

    try:
        blocksize = int(SAMPLE_RATE * BLOCK_DURATION_MS / 1000)
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32',
            device=selected_device_index,
            blocksize=blocksize,
            callback=audio_callback
        )
        stream.start()
        print(f"Stream active on device index: {selected_device_index} ('{selected_device_name}')...")

        while is_listening and not stop_event.is_set():
            time.sleep(0.1)

    except Exception as e:
        print(f"\nError during recording stream: {e}")
        # (Error handling as before)
        is_listening = False
        stop_event.set()
    finally:
        if stream:
            try:
                if stream.active:
                    stream.stop()
                stream.close()
                print("Audio stream closed.")
            except Exception as e:
                print(f"Error closing stream: {e}")
        print("Recording thread finished.")

def process_audio():
    # (Function mostly as before, with key change)
    global whisper_model, keyboard_controller
    if whisper_model is None:
        print("Model not loaded. Cannot process audio.")
        return

    print("Processing audio...")
    audio_data_list = []
    while not audio_queue.empty():
        audio_data_list.append(audio_queue.get())

    if not audio_data_list:
        print("No audio data captured in the queue.")
        return

    try:
        full_audio = np.concatenate(audio_data_list, axis=0)
        print(f"Audio duration to process: {len(full_audio) / SAMPLE_RATE:.2f} seconds")

        # (Save debug audio as before)
        try:
            # Debug audio saving removed for production use.
            pass
        except Exception as e:
            print(f"Error saving debug audio file: {e}")


        if full_audio.size == 0:
            print("Empty audio array after concatenation (no data captured?).")
            return

        # --- FIX: Ensure audio is 1D array ---
        print(f"Audio shape after concatenate: {full_audio.shape}")
        if full_audio.ndim > 1:
             print("Audio is multi-dimensional, flattening to 1D...")
             full_audio = full_audio.flatten() # Use flatten to ensure 1D
        print(f"Audio shape before transcribe: {full_audio.shape}")
        # --- END FIX ---

        # (Print audio properties as before)
        min_val, max_val = np.min(full_audio), np.max(full_audio)
        print(f"Audio properties: dtype={full_audio.dtype}, shape={full_audio.shape}, min={min_val:.4f}, max={max_val:.4f}")
        if max_val < 0.05 and min_val > -0.05 :
             print("WARNING: Audio signal range is very low. Check microphone volume/gain.")


        print("Transcribing with VAD disabled...")
        segments, info = whisper_model.transcribe(
            full_audio, # Pass the potentially flattened array
            beam_size=5,
            language="en" if ".en" in MODEL_SIZE else None,
            vad_filter=False,
        )

        # (Rest of processing and typing as before)
        print(f"Detected language: {info.language} ({(info.language_probability*100):.2f}%)")
        full_text = ""
        print("Processing segments...")
        segment_count = 0
        for segment in segments:
            segment_count += 1
            print(f"  Segment {segment_count}: {segment.start:.2f}s -> {segment.end:.2f}s, Text: '{segment.text}'")
            full_text += segment.text + " "
        trimmed_text = full_text.strip()

        if trimmed_text:
            print(f"Typing: {trimmed_text}")
            time.sleep(0.2)
            keyboard_controller.type(trimmed_text)
            print("Typing complete.")
        else:
            print(f"No text detected after processing {segment_count} segments (VAD was disabled).")
            # (Further diagnostics as before)

    except Exception as e:
        print(f"Error during transcription or typing: {e}")

    # (Clear queue as before)
    print("Clearing audio queue...")
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
        except queue.Empty:
            break
    print("Audio queue cleared.")


def start_listening():
    # (Function as before)
    global is_listening, recording_thread, stop_event, audio_queue
    if not is_listening:
        if selected_device_index is None and MANUAL_DEVICE_INDEX is None:
             print("\nWarning: No specific input device index selected. Sounddevice will use its default.")

        is_listening = True
        sleek_ui.show()
        sleek_ui.update_status("Listening...")
        stop_event.clear()
        print("Clearing queue before starting...")
        while not audio_queue.empty():
            try:
                audio_queue.get_nowait()
            except queue.Empty:
                break
        print("Queue cleared.")
        if recording_thread and recording_thread.is_alive():
             print("Waiting for previous recording thread to finish...")
             recording_thread.join(timeout=1.0)
             if recording_thread.is_alive():
                 print("Warning: Previous recording thread did not terminate cleanly.")

        recording_thread = threading.Thread(target=record_audio_thread, daemon=True)
        recording_thread.start()
        print(f"\n--- Listening activated. Press '{HOTKEY}' again to stop. ---")
    else:
        print("Already listening.")

def stop_listening():
    # (Function as before)
    global is_listening, recording_thread, stop_event
    if is_listening:
        print("\n--- Attempting to stop listening... ---")
        is_listening = False
        sleek_ui.hide()
        stop_event.set()
        if recording_thread and recording_thread.is_alive():
             print("Waiting for recording thread to exit...")
             recording_thread.join(timeout=1.5)
        if recording_thread and recording_thread.is_alive():
             print("Warning: Recording thread did not exit cleanly after stop request.")
        else:
            print("Recording thread stopped.")
        print("--- Listening deactivated. Processing... ---")
        process_audio()
    else:
        print("Was not listening.")

def toggle_listening():
    # (Function as before)
    if is_listening:
        threading.Thread(target=stop_listening, daemon=True).start()
    else:
        start_listening()

# --- Main Execution ---
import threading

def main_logic():
    global selected_device_index, selected_device_name
    print("Script starting...")
    load_model()
    list_audio_devices()

    # --- Determine the input device ---
    print("\nDetermining input device...")
    selected_device_index = None
    selected_device_name = "Not Set"

    if MANUAL_DEVICE_INDEX is not None:
        print(f"Manual device index specified: {MANUAL_DEVICE_INDEX}")
        try:
            device_info = sd.query_devices(MANUAL_DEVICE_INDEX)
            if device_info.get('max_input_channels', 0) > 0:
                selected_device_index = MANUAL_DEVICE_INDEX
                selected_device_name = device_info.get('name', f"Manual Index {MANUAL_DEVICE_INDEX}")
                print(f"Using manually specified device: {selected_device_name}")
            else:
                print(f"Warning: Manually specified device {MANUAL_DEVICE_INDEX} (...) reports 0 input channels.")
        except Exception as e:
            print(f"Error querying manually specified device {MANUAL_DEVICE_INDEX}: {e}")
            print("Falling back to system default.")

    if selected_device_index is None:
        print("Attempting to use system default input device...")
        try:
            default_devices = sd.default.device
            print(f"DEBUG: sd.default.device = {default_devices} (type: {type(default_devices)})")
            default_input_index = -1
            try:
                if isinstance(default_devices[0], int) and default_devices[0] >= 0:
                    default_input_index = default_devices[0]
                    print(f"DEBUG: Accessed default input index via sequence access: {default_input_index}")
                else:
                    print(f"DEBUG: Default input index via sequence access ({default_devices[0]}) not valid.")
            except (TypeError, IndexError, AttributeError, KeyError) as e:
                print(f"DEBUG: Could not access default device index via sequence-like access: {e}")
                default_input_index = -1

            if default_input_index >= 0:
                selected_device_index = default_input_index
                try:
                    device_info = sd.query_devices(selected_device_index)
                    selected_device_name = device_info.get('name', f"Index {selected_device_index}")
                    print(f"Successfully identified system default input device: {selected_device_name} (Index: {selected_device_index})")
                    if device_info.get('max_input_channels', 0) == 0:
                        print(f"Warning: Default device {selected_device_index} reports 0 input channels!")
                        selected_device_index = None
                        selected_device_name = "Default (No Input Channels)"
                except Exception as dev_query_e:
                    print(f"Warning: Could not query details for default input index {selected_device_index}: {dev_query_e}")
                    selected_device_name = f"Index {selected_device_index} (Query Failed)"
            else:
                print("Could not reliably determine default input device index via sequence access. Falling back.")
                selected_device_index = None
                selected_device_name = "Sounddevice Default (Auto)"
        except Exception as e:
            print(f"Error during default audio device query: {e}")
            print("Falling back to None (Sounddevice will try to pick its internal default).")
            selected_device_index = None
            selected_device_name = "Sounddevice Default (Error)"

    if selected_device_index is None:
        print("No valid input device index determined. Relying on Sounddevice's internal default selection.")
        selected_device_name = "Sounddevice Default (Final Fallback)"

    print(f"\n--- Using Microphone: {selected_device_name} (Index: {selected_device_index}) ---")
    print(f"--- Press '{HOTKEY}' to start/stop recording ---")
    print("--- Automatic silence detection via VAD is currently DISABLED for testing ---")
    print("--- Automatic stop-on-silence is also DISABLED ---")
    print("--- Press Ctrl+C in the console to exit script ---")

    try:
        keyboard.add_hotkey(HOTKEY, toggle_listening)
        print(f"Hotkey '{HOTKEY}' registered successfully.")
    except ImportError as e:
        print(f"\nError setting hotkey: {e}")
        print("This usually means you need to run the script with root/administrator privileges.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred setting the hotkey: {e}")
        sys.exit(1)

    print("\nScript ready and listening for hotkey...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Exiting script gracefully...")
    finally:
        print("Cleaning up resources...")
        try:
            keyboard.remove_hotkey(HOTKEY)
            print("Hotkey removed.")
        except Exception as e:
            print(f"Note: Could not remove hotkey (may be normal): {e}")
        if is_listening:
            print("Stopping listening as part of cleanup...")
            stop_event.set()
            is_listening = False
        if recording_thread and recording_thread.is_alive():
            print("Waiting for recording thread to finish final cleanup...")
            recording_thread.join(timeout=2.0)
        print("Script finished.")

if __name__ == "__main__":
    backend_thread = threading.Thread(target=main_logic, daemon=True)
    backend_thread.start()
    from ui import sleek_ui
    sleek_ui.run()