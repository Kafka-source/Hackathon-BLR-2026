import requests
import time
import sys

AGENT_NAME = "pixel_agent"
SERVER_URL = f"http://localhost:8080/api/v1/{AGENT_NAME}/streaming_chat"

def send_to_pixel(chat_history):
    conversation_text = "\n".join([f"{msg['sender']}: {msg['text']}" for msg in chat_history])
    payload = {"user_message": {"text": conversation_text}}
    
    print("=> Sending chat history to Pixel...")
    try:
        response = requests.post(SERVER_URL, json=payload, timeout=240)
        response.raise_for_status()

        text_resp = response.text
        lines = [line for line in text_resp.strip().split('\n') if line]
        
        if lines:
            import json
            last_msg = json.loads(lines[-1])
            final_response = last_msg.get("response", {}).get("text", "")
            if final_response:
                print(f"\n[Pixel Bot]: {final_response}\n")
                chat_history.append({"sender": "Pixel Bot", "text": final_response})
            else:
                print(f"\n[Pixel Bot Raw]: {last_msg}\n")
    except Exception as e:
        print(f"Error communicating with Pixel: {e}")
        sys.exit(1)

def run_test():
    print("--- STARTING PIXEL AUTO TEST ---")
    
    time.sleep(2)
    
    chat_history = [
        {"sender": "System", "text": "Incident INC9999 (VPN Issues) created."},
        {"sender": "User", "text": "Hi, I can't connect to the VPN since this morning."},
        {"sender": "IT Agent", "text": "Hello! I can help. Can you try restarting the Cisco AnyConnect client?"},
        {"sender": "User", "text": "Okay, I just restarted it. Still getting the same 'Connection failed' error."},
        {"sender": "IT Agent", "text": "Alright, let's document this. /update-ticket"}
    ]
    
    send_to_pixel(chat_history)
    
    chat_history.append({"sender": "IT Agent", "text": "I'm going to escalate this to the network team. /add-note Escalating to network team because basic restart failed."})
    send_to_pixel(chat_history)
    
    chat_history.append({"sender": "IT Agent", "text": "Network team will take it from here. /reassign to Network Team, reason: L1 troubleshooting failed."})
    send_to_pixel(chat_history)
    
    # Check the database
    print("--- CHECKING DATABASE ---")
    import json
    import os
    db_file = "../coded_tools/servicenow_mock_db.json"
    db_file_alt = "servicenow_mock_db.json"
    
    for path in [db_file, db_file_alt, "/Users/ayu/Downloads/Neurooo/coded_tools/servicenow_mock_db.json", "/Users/ayu/Downloads/Neurooo/servicenow_mock_db.json"]:
        if os.path.exists(path):
            with open(path, 'r') as f:
                db_data = json.load(f)
                print(json.dumps(db_data, indent=2))
                break
    else:
        print("Could not find database file to verify.")
        
    print("--- TEST COMPLETE ---")

if __name__ == "__main__":
    run_test()
