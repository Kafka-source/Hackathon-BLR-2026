import requests
import json
import time
import sys

AGENT_NAME = "pixel_agent"
SERVER_URL = f"http://localhost:8080/api/v1/{AGENT_NAME}/streaming_chat"

def print_message(sender, text):
    colors = {
        "User": "\033[94m",
        "IT Agent": "\033[92m",
        "Pixel Bot": "\033[95m",
        "System": "\033[93m",
    }
    reset = "\033[0m"
    color = colors.get(sender, reset)
    print(f"\n{color}[{sender}]{reset}: {text}")

def send_to_pixel(chat_history):
    conversation_text = "\n".join([f"{msg['sender']}: {msg['text']}" for msg in chat_history])
    
    payload = {
        "user_message": {
            "text": conversation_text
        }
    }
    
    try:
        response = requests.post(SERVER_URL, json=payload, timeout=240)
        response.raise_for_status()
        
        text_resp = response.text
        lines = [line for line in text_resp.strip().split('\n') if line]
        
        if lines:
            last_msg = json.loads(lines[-1])
            final_response = last_msg.get("response", {}).get("text", "")
            if final_response:
                print_message("Pixel Bot", final_response)
                chat_history.append({"sender": "Pixel Bot", "text": final_response})
            else:
                print_message("System", f"Pixel Raw Data: {last_msg}")
    except Exception as e:
        print_message("System", f"Error communicating with Pixel: {e}")

def main():
    print_message("System", "Starting Microsoft Teams Group Chat Simulator...")
    print_message("System", "Group Members: You (User), You (IT Agent), Pixel Bot (AI)")
    print_message("System", "Commands available for IT Agent: /update-ticket, /add-note, /reassign, /resolve")
    print_message("System", "Type 'exit' to quit.\n")
    
    chat_history = []
    
    initial_context = "System: Incident INC12345 (VPN Connectivity Issue) has been created. A Teams group has been formed."
    print_message("System", "Incident INC12345 (VPN Connectivity Issue) has been created. A Teams group has been formed.")
    chat_history.append({"sender": "System", "text": initial_context})
    
    while True:
        try:
            print("\nSelect Role:")
            print("1. End User")
            print("2. IT Agent")
            role_choice = input("Enter 1 or 2 (or 'exit'): ").strip()
            
            if role_choice.lower() == 'exit':
                break
                
            if role_choice == '1':
                sender = "User"
            elif role_choice == '2':
                sender = "IT Agent"
            else:
                print("Invalid choice.")
                continue
                
            msg_text = input(f"[{sender}] Message: ").strip()
            
            if not msg_text:
                continue
                
            chat_history.append({"sender": sender, "text": msg_text})
            
            print_message("System", "Pixel is processing...")
            send_to_pixel(chat_history)
            
        except KeyboardInterrupt:
            break
            
    print("\nExiting Simulator.")

if __name__ == "__main__":
    main()
