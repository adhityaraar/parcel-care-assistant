"""
ADK tool: Append a localized timestamp to user-provided text.

This module exposes a single tool that takes a short summary string,
appends the current date & time in the timezone and
adds a standard disclaimer. 
"""

import datetime
from zoneinfo import ZoneInfo

from google.adk.tools import FunctionTool

def current_datetime(summary: str) -> dict:
   """Appends the current date, time, and a disclaimer to a summary."""
   disclaimer = "Disclaimer: Information provided is for demonstration purposes only..."
   try:
       tz = ZoneInfo("Asia/Jakarta")
       now = datetime.datetime.now(tz)
       formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S %Z%z")
       report = (f'Summary of your content: {summary}.\n\nTime of summary: {formatted_datetime} \n\n{disclaimer}')
       return {"status": "success", "report": report}
   except Exception as e:
       return {"status": "error", "message": str(e)}
   

get_current_datetime_tool = FunctionTool(current_datetime)