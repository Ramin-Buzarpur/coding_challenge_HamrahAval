"""A throwaway node used only for trying the client by hand.

It is not part of the solution - the task says the cluster API is out of
scope - but it makes the retry and rollback behaviour easy to see.

    python dev/fake_node.py 8001

FAILURE_RATE (0..1) makes the node answer 500 from time to time, which is
roughly what the task describes as an unstable API.
"""

import json
import os
import random
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

GROUPS = set()
FAILURE_RATE = float(os.getenv("FAILURE_RATE", "0.3"))


class Handler(BaseHTTPRequestHandler):
    def _reply(self, status, body=None):
        payload = json.dumps(body).encode() if body is not None else b""

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def _unstable(self):
        if random.random() < FAILURE_RATE:
            self._reply(500, {"error": "something went wrong"})
            return True

        return False

    def do_POST(self):
        if self._unstable():
            return

        group_id = self._body().get("groupId")

        if group_id in GROUPS:
            return self._reply(400, {"error": "already exists"})

        GROUPS.add(group_id)
        self._reply(201)

    def do_DELETE(self):
        if self._unstable():
            return

        group_id = self._body().get("groupId")

        if group_id not in GROUPS:
            return self._reply(404, {"error": "not found"})

        GROUPS.discard(group_id)
        self._reply(200)

    def do_GET(self):
        group_id = self.path.strip("/").split("/")[-1]

        if group_id not in GROUPS:
            return self._reply(404, {"error": "not found"})

        self._reply(200, {"groupId": group_id})

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[node:{self.server.server_address[1]}] {fmt % args}\n")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
