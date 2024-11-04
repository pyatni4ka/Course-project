# utils.py

import hashlib
import asyncio
import websockets
from typing import List

connected_students: List[str] = []

def encrypt_password(password: str) -> str:
    salt = "your_salt_here"
    return hashlib.sha256((salt + password).encode()).hexdigest()

async def start_websocket_server():
    async with websockets.serve(handle_student_connection, "localhost", 5678):
        await asyncio.Future()  # Run indefinitely

async def handle_student_connection(websocket, path):
    student_info = await websocket.recv()
    connected_students.append(student_info)
    try:
        while True:
            await websocket.send("Heartbeat")
            await asyncio.sleep(5)
    except websockets.ConnectionClosed:
        connected_students.remove(student_info)

def student_monitor() -> List[str]:
    return connected_students.copy()

