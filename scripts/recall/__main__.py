import sys
import os
from groq import Groq
from config import GROQ_API_KEY
from .tools import search_logs, search_logs_timewindow, read_file, search_code, get_current_datetime
from .system_prompt import system_prompt
from .preprocess import preprocess_user_query
from .tool_schema import tools
import json
from .preprocess import preprocess_user_query
from .tools import search_logs, search_logs_timewindow
from datetime import datetime
import logging
logging.basicConfig(level=logging.DEBUG)


def _cast_tool_arguments(tool_arguments, tool_name):
    return tool_arguments

def main():
    print("Welcome to the Recall Assistant with LLM function calling!")
    print("Ask any question about your logs or code. The LLM will decide which tools to use.")
    print("Type /exit to quit.\n")

    client = Groq(api_key=GROQ_API_KEY)
    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]
    while True:
        user_input = input("Ask: ").strip()
        if user_input == '/exit':
            break
        # Preprocess for date-based and time window log queries
        tool_name, tool_args = preprocess_user_query(user_input)
        if tool_name == 'search_logs':
            print("[AGENT] Preprocessing detected a date-based log query. Calling search_logs directly.")
            result = search_logs(tool_args["query"])
            print("[AGENT] TOOL RESULT:")
            print(json.dumps(result, indent=2) if not isinstance(result, str) else result)
            print("\n==================== LLM SUMMARIZATION ====================")
            
            # Create a simple summarization prompt
            summary_messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes user activity logs. Provide a clear, concise summary of what the user was doing based on the log entries."
                },
                {
                    "role": "user",
                    "content": f"User asked: '{user_input}'\n\nHere are the search results from their activity logs:\n\n{json.dumps(result, indent=2)}\n\nPlease provide a clear summary of their activities based on these results."
                }
            ]
            
            response2 = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=summary_messages,
            )
            print("\n-------------------- FINAL ANSWER --------------------")
            answer = response2.choices[0].message.content
            
            # Clean up any malformed tokens or truncated content
            if answer:
                # Remove any special tokens that might appear
                answer = answer.replace('<|header_start|>', '').replace('<|header_end|>', '')
                # Remove incomplete sentences at the end
                sentences = answer.split('\n')
                cleaned_sentences = []
                for sentence in sentences:
                    if sentence.strip() and not sentence.strip().endswith(','):
                        cleaned_sentences.append(sentence)
                    elif sentence.strip().endswith(',') and len(sentence.strip()) > 20:
                        # Keep longer sentences that end with comma, remove short fragments
                        cleaned_sentences.append(sentence.rstrip(','))
                answer = '\n'.join(cleaned_sentences)
            
            if not answer or answer.strip().lower() == 'none':
                if not result:
                    print("No results found for your query.")
                else:
                    print("The tool executed, but the LLM did not return a summary. Here is the raw result:")
                    print(json.dumps(result, indent=2) if not isinstance(result, str) else result)
            else:
                print(answer)
            print("----------------------------------------------------\n")
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": answer if answer else ""})
            continue
        elif tool_name == 'search_logs_timewindow':
            print("[AGENT] Preprocessing detected a time window log query. Calling search_logs_timewindow directly.")
            result = search_logs_timewindow(tool_args["since"])
            print("[AGENT] TOOL RESULT:")
            print(json.dumps(result, indent=2) if not isinstance(result, str) else result)
            print("\n==================== LLM SUMMARIZATION ====================")
            
            # Create a simple summarization prompt
            summary_messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes user activity logs. Provide a clear, concise summary of what the user was doing based on the log entries."
                },
                {
                    "role": "user",
                    "content": f"User asked: '{user_input}'\n\nHere are the search results from their activity logs:\n\n{json.dumps(result, indent=2)}\n\nPlease provide a clear summary of their activities based on these results."
                }
            ]
            
            response2 = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=summary_messages,
            )
            print("\n-------------------- FINAL ANSWER --------------------")
            answer = response2.choices[0].message.content
            
            # Clean up any malformed tokens or truncated content
            if answer:
                # Remove any special tokens that might appear
                answer = answer.replace('<|header_start|>', '').replace('<|header_end|>', '')
                # Remove incomplete sentences at the end
                sentences = answer.split('\n')
                cleaned_sentences = []
                for sentence in sentences:
                    if sentence.strip() and not sentence.strip().endswith(','):
                        cleaned_sentences.append(sentence)
                    elif sentence.strip().endswith(',') and len(sentence.strip()) > 20:
                        # Keep longer sentences that end with comma, remove short fragments
                        cleaned_sentences.append(sentence.rstrip(','))
                answer = '\n'.join(cleaned_sentences)
            
            if not answer or answer.strip().lower() == 'none':
                if not result:
                    print("No results found for your query.")
                else:
                    print("The tool executed, but the LLM did not return a summary. Here is the raw result:")
                    print(json.dumps(result, indent=2) if not isinstance(result, str) else result)
            else:
                print(answer)
            print("----------------------------------------------------\n")
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": answer if answer else ""})
            continue
        messages.append({"role": "user", "content": user_input})
        print("\n==================== LLM INVOCATION ====================")
        print(f"User: {user_input}")
        print("=======================================================\n")
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        tool_calls = getattr(response.choices[0].message, 'tool_calls', None)
        if tool_calls:
            for tool_call in tool_calls:
                print("-------------------- TOOL CALL DETECTED --------------------")
                print(f"Tool Name: {tool_call.function.name}")
                print(f"Raw Arguments: {tool_call.function.arguments}")
                print("-----------------------------------------------------------\n")
                tool_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                args = _cast_tool_arguments(args, tool_name)
                print(f"[AGENT] Executing tool: {tool_name} with arguments: {args}")
                if tool_name == "search_logs":
                    result = search_logs(args["query"])
                elif tool_name == "search_logs_timewindow":
                    from dateutil import parser as date_parser
                    since = args["since"]
                    if isinstance(since, str):
                        since = date_parser.parse(since)
                    result = search_logs_timewindow(since)
                elif tool_name == "read_file":
                    result = read_file(args["filename"])
                elif tool_name == "search_code":
                    result = search_code(args["query"])
                elif tool_name == "get_current_datetime":
                    result = get_current_datetime()
                else:
                    result = f"[ERROR] Unknown tool: {tool_name}"
                print("[AGENT] TOOL RESULT:")
                print(json.dumps(result, indent=2) if not isinstance(result, str) else result)
                print("\n==================== LLM SUMMARIZATION ====================")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(result, indent=2) if not isinstance(result, str) else result
                })
                response2 = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=messages,
                )
                print("\n-------------------- FINAL ANSWER --------------------")
                answer = response2.choices[0].message.content
                
                # Clean up any malformed tokens or truncated content
                if answer:
                    # Remove any special tokens that might appear
                    answer = answer.replace('<|header_start|>', '').replace('<|header_end|>', '')
                    # Remove incomplete sentences at the end
                    sentences = answer.split('\n')
                    cleaned_sentences = []
                    for sentence in sentences:
                        if sentence.strip() and not sentence.strip().endswith(','):
                            cleaned_sentences.append(sentence)
                        elif sentence.strip().endswith(',') and len(sentence.strip()) > 20:
                            # Keep longer sentences that end with comma, remove short fragments
                            cleaned_sentences.append(sentence.rstrip(','))
                    answer = '\n'.join(cleaned_sentences)
                
                if not answer or answer.strip().lower() == 'none':
                    if not result:
                        print("No results found for your query.")
                    else:
                        print("The tool executed, but the LLM did not return a summary. Here is the raw result:")
                        print(json.dumps(result, indent=2) if not isinstance(result, str) else result)
                else:
                    print(answer)
                print("----------------------------------------------------\n")
                messages.append({"role": "assistant", "content": answer if answer else ""})
        else:
            print("\n-------------------- FINAL ANSWER --------------------")
            answer = response.choices[0].message.content
            if not answer or answer.strip().lower() == 'none':
                print("No answer returned by the LLM.")
            else:
                print(answer)
            print("----------------------------------------------------\n")
            messages.append({"role": "assistant", "content": answer if answer else ""})

if __name__ == "__main__":
    main() 

def recall_query(user_input: str) -> str:
    logging.debug(f"recall_query called with: {user_input!r}")

    # 0) Preprocess step
    tool_name, tool_args = preprocess_user_query(user_input)
    logging.debug(f"preprocess → {tool_name}, {tool_args}")

    if tool_name == 'search_logs':
        results = search_logs(tool_args["query"])
        resp = json.dumps(results, indent=2)
        logging.debug(f"search_logs response: {resp}")
        return resp or "(no logs found)"

    if tool_name == 'search_logs_timewindow':
        since = tool_args["since"]
        if isinstance(since, str):
            since = datetime.fromisoformat(since)
        results = search_logs_timewindow(since)
        resp = json.dumps(results, indent=2)
        logging.debug(f"search_logs_timewindow response: {resp}")
        return resp or "(no logs found)"

    # 1) Full LLM + function-calling path
    client = Groq(api_key=GROQ_API_KEY)
    messages = [
        {"role": "system",  "content": system_prompt},
        {"role": "user",    "content": user_input},
    ]
    resp1 = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    msg1 = resp1.choices[0].message
    logging.debug(f"LLM first pass message: {msg1}")

    # 2) Handle function_call
    if hasattr(msg1, "function_call") and msg1.function_call:
        fc = msg1.function_call
        logging.debug(f"Function call requested: {fc.name} with args {fc.arguments}")
        args = json.loads(fc.arguments)
        args = _cast_tool_arguments(args, fc.name)

        # dispatch …
        # <same code as before to populate `result`>

        # assemble messages …
        # <same assembly code>

        resp2 = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
        )
        final = resp2.choices[0].message.content or ""
        logging.debug(f"LLM final pass content: {final!r}")
        return final or "(no summary returned)"

    # 3) No function_call → just content
    content = msg1.content or ""
    logging.debug(f"No function_call, returning content: {content!r}")
    return content or "(no content returned)"




