"""
Bloomberg Trading Challenge - Localhost Dashboard Server
Provides local HTTP service on http://localhost:8000 with automatic background script execution:
  - Serves index.html with dual Current Holdings & Wishlist views
  - API endpoint /api/sync triggers Bloomberg data sync & dashboard regeneration automatically
  - API endpoint /api/wishlist saves and updates team wishlist items to wishlist.json
  - API endpoint /api/status provides live Bloomberg port handshake diagnostics
"""

import os
import sys
import json
import socket
import argparse
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def check_bloomberg_port(host="127.0.0.1", port=8194, timeout=0.4):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        bb_exe = r"C:\blp\DAPI\bbcomm.exe"
        if os.path.exists(bb_exe):
            try:
                import subprocess, time
                subprocess.Popen([bb_exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1.5)
                with socket.create_connection((host, port), timeout=timeout):
                    return True
            except Exception:
                pass
        return False

def run_sync_scripts():
    """Runs data sync and regenerates web dashboard."""
    output = {"messages": []}
    
    # Check if Bloomberg is active
    is_bb_active = check_bloomberg_port()
    output["bloomberg_connected"] = is_bb_active
    
    import subprocess
    if is_bb_active:
        try:
            output["messages"].append("Connecting to Bloomberg BLPAPI at 127.0.0.1:8194...")
            subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "sync_remote_excel.py")], capture_output=True, text=True, check=True)
            output["messages"].append("Live Bloomberg quotes updated successfully.")
        except Exception as e:
            output["messages"].append(f"Bloomberg sync notice: {str(e)}")
    else:
        output["messages"].append("Bloomberg daemon offline; utilizing cached market quotes.")

    try:
        subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "generate_web_dashboard.py")], capture_output=True, text=True, check=True)
        output["messages"].append("Web dashboard regenerated successfully.")
        output["success"] = True
    except Exception as e:
        output["messages"].append(f"Dashboard generation error: {str(e)}")
        output["success"] = False

    return output

class DashboardRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SCRIPT_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            is_bb = check_bloomberg_port()
            resp = {
                "bloomberg_port_8194": is_bb,
                "status": "online" if is_bb else "cached",
                "timestamp": str(os.path.getmtime(os.path.join(SCRIPT_DIR, "index.html")) if os.path.exists(os.path.join(SCRIPT_DIR, "index.html")) else "")
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        elif path == "/api/sync":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            res = run_sync_scripts()
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        elif path == "/api/wishlist":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            w_path = os.path.join(SCRIPT_DIR, "wishlist.json")
            data = []
            if os.path.exists(w_path):
                try:
                    with open(w_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = []
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        elif path == "/api/holdings":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            h_path = os.path.join(SCRIPT_DIR, "current_holdings.json")
            data = []
            if os.path.exists(h_path):
                try:
                    with open(h_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = []
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # Default: serve static files (index.html, etc.)
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/sync":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            res = run_sync_scripts()
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        elif path == "/api/wishlist":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            w_path = os.path.join(SCRIPT_DIR, "wishlist.json")
            
            try:
                payload = json.loads(body.decode("utf-8"))
                # Action: add or delete or replace
                action = payload.get("action", "add")
                item = payload.get("item", {})
                
                current = []
                if os.path.exists(w_path):
                    try:
                        with open(w_path, "r", encoding="utf-8") as f:
                            current = json.load(f)
                    except Exception:
                        current = []

                if action == "add":
                    sym = item.get("symbol", "").upper().strip()
                    if sym:
                        # Remove if already exists, then prepend
                        current = [x for x in current if x.get("symbol") != sym]
                        current.insert(0, item)
                elif action == "delete":
                    sym = item.get("symbol", "").upper().strip()
                    current = [x for x in current if x.get("symbol") != sym]
                elif action == "replace":
                    current = payload.get("items", [])

                with open(w_path, "w", encoding="utf-8") as f:
                    json.dump(current, f, indent=2)

                # Regenerate dashboard with updated wishlist
                try:
                    import generate_web_dashboard
                    generate_web_dashboard.generate_dashboard()
                except Exception:
                    pass

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "count": len(current)}).encode("utf-8"))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
                return

        return super().do_POST()

def main():
    parser = argparse.ArgumentParser(description="Bloomberg Dashboard Localhost Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--open", action="store_true", help="Open browser automatically after server start")
    args = parser.parse_args()

    port = args.port
    
    # 1. Regenerate dashboard on startup so it has fresh data
    print("[Bloomberg Dashboard] Initializing dashboard and checking feeds...")
    try:
        import generate_web_dashboard
        generate_web_dashboard.generate_dashboard()
    except Exception as e:
        print(f"[Warning] Could not regenerate on start: {e}")

    server_address = ("127.0.0.1", port)
    try:
        httpd = HTTPServer(server_address, DashboardRequestHandler)
    except OSError as e:
        if "already in use" in str(e).lower() or e.errno == 10048:
            print(f"[Notice] Port {port} is already active. Opening existing server.")
            if args.open:
                webbrowser.open(f"http://localhost:{port}")
            sys.exit(0)
        raise

    url = f"http://localhost:{port}"
    print(f"========================================================")
    print(f" Dallas College Bloomberg Trading Terminal Running Live")
    print(f" Localhost URL: {url}")
    print(f" Automatic API sync available via /api/sync")
    print(f"========================================================")

    if args.open:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Server] Shutting down localhost server gracefully.")
        httpd.server_close()

if __name__ == "__main__":
    main()
