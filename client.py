import asyncio
import threading
import json

async def send_message(writer, message):
    writer.write(message.encode('utf-8'))
    await writer.drain()

async def read_server(reader):
    while True:
        data = await reader.read(1024)
        if not data:
            break
        print("Received from server:")
        print(json.loads(data.decode('utf-8')))

def user_input(writer):
    while True:
        cc = input("Enter command:")
        asyncio.run(send_message(writer, cc))
        if cc == 'exit':
            break

async def main():
    reader, writer = await asyncio.open_connection('127.0.0.1', 8763)

    user_input_thread = threading.Thread(target=user_input, args=(writer,))
    user_input_thread.start()

    try:
        await read_server(reader)
    except asyncio.CancelledError:
        pass
    finally:
        writer.close()
        await writer.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())

