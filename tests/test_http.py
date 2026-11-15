import asyncio
import unittest

from websockets import connect
from websockets.server import serve

from wisp.server.http import HeadRequestProtocol, request_handler


async def websocket_handler(websocket):
  await websocket.wait_closed()


class HealthCheckMethodTests(unittest.IsolatedAsyncioTestCase):
  async def test_get_and_head_health_checks(self):
    async with serve(
      websocket_handler,
      "127.0.0.1",
      0,
      process_request=request_handler,
      create_protocol=HeadRequestProtocol,
    ) as server:
      port = server.sockets[0].getsockname()[1]

      async def request(method):
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(
          f"{method} /health HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n".encode()
        )
        await writer.drain()
        response = await reader.read()
        writer.close()
        await writer.wait_closed()
        return response

      get_response = await request("GET")
      self.assertTrue(get_response.startswith(b"HTTP/1.1 200 OK\r\n"))
      self.assertTrue(get_response.endswith(b"\r\n\r\nOK"))

      head_response = await request("HEAD")
      self.assertTrue(head_response.startswith(b"HTTP/1.1 200 OK\r\n"))
      headers, body = head_response.split(b"\r\n\r\n", 1)
      self.assertIn(b"Content-Length: 2", headers)
      self.assertEqual(body, b"")

      async with connect(f"ws://127.0.0.1:{port}/"):
        pass
