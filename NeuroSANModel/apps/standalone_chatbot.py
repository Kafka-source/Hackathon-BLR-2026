import requests
import json
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Standalone CLI Chatbot for Neuro-San")
    parser.add_argument("--agent", default="pixel_agent", help="Name of the agent to chat with (e.g., pixel_agent, basic/coding_assistant)")
    parser.add_argument("--port", default=8080, type=int, help="Port the NeuroSan server is running on")
    args = parser.parse_args()

    url = f"http://localhost:{args.port}/api/v1/{args.agent}/streaming_chat"
    
    print(f"\n=======================================================")
    print(f"  Neuro-San Standalone Chatbot CLI - {args.agent}")
    print(f"=======================================================")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    chat_context = {}

    while True:
        try:
            user_input = input("\033[94mYou: \033[0m").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("Ending session. Goodbye!")
                break

            payload = {
                "user_message": {"text": user_input},
                "chat_context": chat_context,
                "metadata": {"source": "standalone_cli"}
            }

            response = requests.post(url, json=payload, stream=True)
            
            if response.status_code != 200:
                print(f"\033[91mError: Server returned status {response.status_code}\033[0m")
                print(response.text)
                continue

            print("\033[92mAgent:\033[0m ", end="", flush=True)
            
            last_msg = None
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    try:
                        last_msg = json.loads(decoded)
                    except json.JSONDecodeError:
                        pass
            
            if last_msg:
                final_text = last_msg.get("response", {}).get("text", "")
                
                if "chat_context" in last_msg.get("response", {}):
                    chat_context = last_msg["response"]["chat_context"]
                elif "chat_context" in last_msg:
                    chat_context = last_msg["chat_context"]

                print(f"{final_text}\n")
            else:
                print("\033[91mNo valid response received.\033[0m\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)
        except requests.exceptions.ConnectionError:
            print(f"\033[91mError: Could not connect to {url}. Is the Neuro-San server running?\033[0m\n")
            sys.exit(1)
        except Exception as e:
            print(f"\033[91mUnexpected error: {e}\033[0m\n")

if __name__ == "__main__":
    main()
