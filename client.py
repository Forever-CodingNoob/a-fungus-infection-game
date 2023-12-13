import asyncio
import threading
import json
import sys

exit_event = threading.Event()  # Event to signal exit

async def send_message(writer, message):
    writer.write(message.encode('utf-8'))
    await writer.drain()

async def read_server(reader):
    while not exit_event.is_set():
        try:
            # Read the fixed-length header
            data = await reader.readexactly(10)
            message_size = int(data.decode('utf-8').strip())

            # Read the message
            data = await reader.readexactly(message_size)
        except asyncio.IncompleteReadError as e:
            # print(f"imcomplete read error: {str(e)}")
            break

        if exit_event.is_set():
            break
        message = data.decode('utf-8')

        try:
            print(json.loads(message))
        except json.decoder.JSONDecodeError:
            print("JSON decode error")

def user_input(writer):
    while True:
        cc = input("Enter command:")
        asyncio.run(send_message(writer, cc))
        if cc == 'exit':
            exit_event.set()  # Signal the exit event
            break

async def main():
    if len(sys.argv) != 3:
        print("Usage: python client.py <server_ip> <server_port>")
        return

    server_ip, server_port = sys.argv[1], int(sys.argv[2])
    reader, writer = await asyncio.open_connection(server_ip, server_port)

    #user_input_thread = threading.Thread(target=user_input, args=(writer,))
    #user_input_thread.start()
    user_input_task = asyncio.to_thread(user_input, writer)
    read_server_task = asyncio.create_task(read_server(reader))

    try:
        #await read_server(reader)
        await asyncio.gather(
            user_input_task,
            read_server_task
        )
    except asyncio.CancelledError:
        pass
    finally:
        writer.close()
        await writer.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())

