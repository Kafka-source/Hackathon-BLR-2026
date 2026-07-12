import json
import os
import asyncio
import requests
from datetime import datetime
from typing import Any, Dict, Union
from neuro_san.interfaces.coded_tool import CodedTool


SNOW_USER = "" # SNOW Service Account username
SNOW_PWD = "" # SNOW Service Account password
SNOW_BASE_URL = "https://dev183600.service-now.com/api/global/teams_bot_triage"
SNOW_TABLE_API = "https://dev183600.service-now.com/api/now/table/incident"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

TICKET_CACHE = {}

class CreateTicketTool(CodedTool):
    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        url = f"{SNOW_BASE_URL}/ticket"
        payload = {
            "short_description": args.get("description", "No description provided"),
            "assignment_group": args.get("assignment_group", "L1 Support"),
            "question": args.get("question", "General Issue"),
            "impact": args.get("impact", "1"),
            "severity": args.get("severity", "1"),
            "caller_name": args.get("user", "Unknown User")
        }
        response = requests.post(url, auth=(SNOW_USER, SNOW_PWD), headers=HEADERS, json=payload)
        if response.status_code != 200 and response.status_code != 201:
            return {"status": "error", "message": f"API Error: {response.status_code}", "details": response.text}
        data = response.json()
        result_data = data.get("result", data) 
        incident_number = result_data.get("number") or result_data.get("incident_number")
        sys_id = result_data.get("sys_id")
        if incident_number and sys_id:
            TICKET_CACHE[incident_number] = sys_id
 
        return {
            "status": "success", 
            "ticket_id": incident_number, 
            "sys_id": sys_id,
            "message": f"Successfully created new ticket {incident_number}.",
            "raw_response": data
        }
 
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Union[dict[str, Any], str]:
        return await asyncio.to_thread(self.invoke, args, sly_data)
 
 
class UpdateTicketTool(CodedTool):
    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        incident_number = args.get("ticket_id")
        description = args.get("description")
        sys_id = args.get("sys_id") or TICKET_CACHE.get(incident_number)
 
        if not sys_id:
            return {"status": "error", "message": "sys_id not found. Cannot update without sys_id."}

        url = f"{SNOW_TABLE_API}/{sys_id}"
        payload = {"description": description}
        response = requests.put(url, auth=(SNOW_USER, SNOW_PWD), headers=HEADERS, json=payload)
        if response.status_code == 200:
            return {"status": "success", "message": f"Successfully updated ticket {incident_number}."}
        return {"status": "error", "message": response.text}
 
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Union[dict[str, Any], str]:
        return await asyncio.to_thread(self.invoke, args, sly_data)
 
 
class AddNoteTool(CodedTool):
    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        incident_number = args.get("ticket_id")
        note = args.get("note")
        sys_id = args.get("sys_id") or TICKET_CACHE.get(incident_number)
 
        if not sys_id:
            return {"status": "error", "message": f"Missing sys_id for ticket {incident_number}. Ensure it was created in this session."}
 
        url = f"{SNOW_BASE_URL}/ticket/{sys_id}/note"
        payload = {"note": note}
        response = requests.post(url, auth=(SNOW_USER, SNOW_PWD), headers=HEADERS, json=payload)
        if response.status_code in (200, 201):
            return {"status": "success", "message": f"Successfully added note to ticket {incident_number}."}
        return {"status": "error", "message": f"Failed to add note: {response.text}"}
 
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Union[dict[str, Any], str]:
        return await asyncio.to_thread(self.invoke, args, sly_data)
 
 
class ReassignTicketTool(CodedTool):
    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        incident_number = args.get("ticket_id")
        new_group = args.get("new_assignment_group")
        url = f"{SNOW_BASE_URL}/reassign"
        payload = {
            "incident_number": incident_number,
            "new_assignment_group": new_group
        }
        response = requests.put(url, auth=(SNOW_USER, SNOW_PWD), headers=HEADERS, json=payload)
        if response.status_code == 200:
            return {"status": "success", "message": f"Successfully reassigned ticket {incident_number} to {new_group}."}
        return {"status": "error", "message": f"Failed to reassign: {response.text}"}
 
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Union[dict[str, Any], str]:
        return await asyncio.to_thread(self.invoke, args, sly_data)
 
 
class ResolveTicketTool(CodedTool):
    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        incident_number = args.get("ticket_id")
        notes = args.get("resolution_notes", "Resolved by bot.")
        sys_id = args.get("sys_id") or TICKET_CACHE.get(incident_number)
 
        if not sys_id:
            return {"status": "error", "message": "sys_id not found for resolution."}
 
        url = f"{SNOW_TABLE_API}/{sys_id}"
        payload = {
            "state": "6",
            "close_notes": notes
        }
        response = requests.put(url, auth=(SNOW_USER, SNOW_PWD), headers=HEADERS, json=payload)
        if response.status_code == 200:
            return {"status": "success", "message": f"Successfully resolved ticket {incident_number}."}
        return {"status": "error", "message": response.text}
 
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Union[dict[str, Any], str]:
        return await asyncio.to_thread(self.invoke, args, sly_data)
 
 
class GetTicketStatusTool(CodedTool):
    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        incident_number = args.get("ticket_id")
        url = f"{SNOW_TABLE_API}?sysparm_query=number={incident_number}&sysparm_limit=1"
        response = requests.get(url, auth=(SNOW_USER, SNOW_PWD), headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            if data.get("result"):
                return {"status": "success", "ticket": data["result"][0]}
            return {"status": "error", "message": f"Ticket {incident_number} not found."}
        return {"status": "error", "message": response.text}
 
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Union[dict[str, Any], str]:
        return await asyncio.to_thread(self.invoke, args, sly_data)