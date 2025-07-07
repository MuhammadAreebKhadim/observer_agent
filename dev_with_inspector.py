# dev_with_inspector.py
import re
import shlex
import subprocess
import webbrowser
import sys

# On Windows, ensure `mcp` is on your PATH (or give full path to mcp.exe)
CMD = "mcp dev server.py"
TOKEN_RE = re.compile(r"Session token:\s*([0-9a-f]+)")

def main():
    # Launch `mcp dev server.py`, capturing its combined stdout/stderr
    # Use encoding='utf-8' with errors='replace' so stray bytes won't crash us
    p = subprocess.Popen(
        shlex.split(CMD),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1,
    )

    inspector_base = "http://127.0.0.1:6274/?MCP_PROXY_AUTH_TOKEN={}"

    try:
        # Read line by line
        for line in p.stdout:
            # Mirror the output
            sys.stdout.write(line)
            sys.stdout.flush()

            # Look for the token
            m = TOKEN_RE.search(line)
            if m:
                token = m.group(1)
                url = inspector_base.format(token)
                print(f"\n→ Opening Inspector at:\n   {url}\n")
                webbrowser.open(url)
    except KeyboardInterrupt:
        print("\nInterrupted, shutting down.")
    finally:
        p.terminate()
        p.wait()

if __name__ == "__main__":
    main()
