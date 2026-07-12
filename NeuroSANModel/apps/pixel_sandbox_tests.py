import requests
import json
import time
import asyncio
import random

API_URL = "http://localhost:8080/api/v1/pixel_agent/streaming_chat"

SCENARIOS = [
    "I need access to the finance shared folder. I've never had it before.",
    "My VPN is disconnecting every 5 minutes today, it worked fine yesterday.",
    "Don't create a ticket for this, just tell me how to reset my password.",
    "Assign this to the L2 network team IMMEDIATELY, my internet is down.",
    "I need Adobe Acrobat Pro installed on my new laptop.",
    "My laptop is super slow when I open Excel, please help.",
    "I lost access to the shared mailbox for HR, I was able to see it yesterday.",
    "I need a new wireless mouse, mine broke.",
    "Outlook is saying disconnected.",
    "I'm getting an error when I try to log into the CRM system."
]

USERS = ["Alice_Finance", "Bob_Engineering", "Charlie_HR", "Dave_Sales", "Eve_Marketing"]

async def run_scenario(idx, scenario, user):
    payload = {
        "user_message": f"User: {scenario}",
        "chat_context": {},
        "metadata": {"user": user}
    }
    try:
        response = await asyncio.to_thread(
            requests.post,
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            lines = [line for line in response.text.strip().split('\n') if line]
            if lines:
                last_msg = json.loads(lines[-1])
                return f"SCENARIO {idx} ({user}): {scenario}\nBOT RESPONSE:\n{last_msg.get('text', '')}\n"
    except Exception as e:
        return f"SCENARIO {idx} ({user}): ERROR {e}\n"
    return f"SCENARIO {idx} ({user}): FAILED\n"

async def main():
    print("Running Sandbox Edge Cases...")
    results = []
    
    tasks = []
    for i, scenario in enumerate(SCENARIOS):
        user = random.choice(USERS)
        tasks.append(run_scenario(i+1, scenario, user))
        
    completed = await asyncio.gather(*tasks)
    
    with open("sandbox_results.txt", "w") as f:
        f.write("\n==============================\n".join(completed))
    print("Tests completed! Saved to sandbox_results.txt")

if __name__ == "__main__":
    asyncio.run(main())
