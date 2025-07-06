tools = [
    {
        "type": "function",
        "function": {
            "name": "search_logs",
            "description": "Search all logs for a keyword or date (e.g., '2024-07-05').",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The keyword, phrase, or date to search for in logs."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_logs_timewindow",
            "description": "Search all logs for entries in a time window (e.g., last 3 hours).",
            "parameters": {
                "type": "object",
                "properties": {
                    "since": {"type": "string", "description": "ISO datetime string for the start of the window."}
                },
                "required": ["since"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read and return the content of a file (log or code).",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The path to the file to read."}
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search all code files for a keyword or pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The keyword or regex pattern to search for in code files."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "Get the current date and time.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
] 