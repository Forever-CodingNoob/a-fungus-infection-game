import asyncio
import socket
import random
import math
import json
from collections import deque
import sys

# Constants
MAX_ANT_MOVEMENT = 1
MAP_WIDTH = 500
MAP_HEIGHT = 300
BASE_DEF = 10
BASE_ATK = 5
BASE_INFECTION_RATE = 0.1
BASE_RADIUS = 20
ANT_GENERATION_INTERVAL = 3  # Interval in seconds
ANT_MOVEMENT_INTERVAL = 1  # Interval in seconds
UPDATE_INTERVAL = 20
ANT_MAX_N = 50

class Ant:
    def __init__(self, position, health):
        # self.ant_id = ant_id
        self.position = position
        self.health =health

    def move(self):
        # Move the ant randomly within the allowed range
        new_x = max(0, min(MAP_WIDTH - 1, self.position.x + random.randint(-MAX_ANT_MOVEMENT, MAX_ANT_MOVEMENT)))
        new_y = max(0, min(MAP_HEIGHT - 1, self.position.y + random.randint(-MAX_ANT_MOVEMENT, MAX_ANT_MOVEMENT)))
        self.position = Position(new_x, new_y)
        self.health-=1

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __eq__(self, other):
        return self.x==other.x and self.y==other.y
    def __str__(self):
        return f"{self.x} {self.y}"
    def toTuple(self):
        return (self.x, self.y)

class Tribe:
    def __init__(self, player_id, tribe_id, position):
        self.player_id = player_id
        self.tribe_id = tribe_id
        self.DEF = BASE_DEF
        self.ATK = BASE_ATK
        self.infection_probability = BASE_INFECTION_RATE
        self.radius = BASE_RADIUS
        self.position = position
        self.infection_area = set()
        # self.health = random.randint(50, 100)
        #self.positions = positions  # Queue to store positions of infected ants

        if self.position is not None:
            for x in range(self.position.x - self.radius, self.position.x + self.radius + 1):
                for y in range(self.position.y - self.radius, self.position.y + self.radius + 1):
                    if not in_field(Position(x,y)):
                        continue
                    distance = math.sqrt((self.position.x - x)**2 + (self.position.y - y)**2)
                    if distance <= self.radius:
                        self.infection_area.add((x, y))

    def __eq__(self, other):
        return (self.player_id == other.player_id) and (self.tribe_id == other.tribe_id)

    def check_dead(self):
        if self.DEF<=0 or (self.position not in self.infection_area):
            del players[self.player_id].tribes[self.tribe_id]
            print(f"Tribe {self.tribe_id} of player {self.player_id} is now dead")
            asyncio.create_task(send_notification(player, msg="tribe_dead", tid=self.tribe_id))
            # killed

    async def update_values(self):
        async with mutex:
            # Simulate the decrease of values over time
            self.DEF -= 1
            self.check_dead()

    def is_position_in_infection_area(self, x, y):
        return (x, y) in self.infection_area

    def perform_invasion(self):
        for some_player in players.values():
            for other_tribe in some_player.tribes.values():
                if other_tribe==self:
                    continue
                inter = self.infection_area.intersection(other_tribe.infection_area)
                if not inter:
                    continue
                if self.ATK>other_tribe.DEF:
                    other_tribe.infection_area.difference_update(inter)
                    other_tribe.check_dead()
                    print(f"Tribe of player {self.player_id} invades tribe of player {other_tribe.player_id} successfully")
                else:
                    self.infection_area.difference_update(inter)
                    self.check_dead()
                    print(f"Tribe of player {self.player_id} failed to invade tribe of player {other_tribe.player_id}")


# Player class with a queue to store positions and the number of tribes to create
class Player:
    def __init__(self, player_id, reader, writer):
        self.player_id = player_id
        self.reader = reader
        self.writer = writer
        self.name = "anonymous"
        self.tribes = {}
        self.tribe_count=0 # does NOT decrease when a tribe dies
        self.ant_positions = deque()  # Queue to store positions of infected ants
        self.new_tribes_to_create = 1

# Global variables
players = {}
player_counter = 0  # Counter to assign unique player IDs
ants = []
ants_count =0
mutex = asyncio.Lock()

def in_field(pos):
    return 0<= pos.x < MAP_WIDTH and 0<= pos.y < MAP_HEIGHT

async def send_message_withheader(writer, message):
    # Create a fixed-length header indicating the size of the message
    header = f"{len(message):<10}".encode('utf-8')
    writer.write(header + message.encode('utf-8'))
    await writer.drain()

async def send_message(player, _type, msg, **kwargs):
    if player.player_id not in players:
        return
    message_dict={"type":_type, "msg":msg, **kwargs}
    try:
        await send_message_withheader(player.writer, json.dumps(message_dict))
    except socket.error as e:
        print(f"Error sending {_type} to Player {player.player_id}: {e}")


async def send_notification(player, msg, **kwargs):
    await send_message(player, _type="notification", msg=msg, **kwargs)

async def send_warning(player, msg, **kwargs):
    await send_message(player, _type="warning", msg=msg, **kwargs)


def is_ant_infected(ant, tribe):
    # Check if an ant is infected by a tribe
    return ant.position.toTuple() in tribe.infection_area and random.random() < tribe.infection_probability

async def update_game_state(player, action):
    async with mutex:
        # print(f"Received command: {action} from player {player.player_id}")
        action=action.split()
        if action[0] == "create_tribe":
            if player.new_tribes_to_create > 0:
                # Store the position where the ant was infected in the queue
                ant_position = player.ant_positions.popleft();
                asyncio.create_task(send_notification(player, msg= "choose_position", x=ant_position.x, y= ant_position.y))
        elif action[0]=="choose_position":
            if len(action)<3:
                await send_warning(player, msg="argument_insufficient")
                return True
            try:
                x, y = int(action[1]), int(action[2])
            except ValueError:
                return True
            choose_position(player, x, y)
        elif action[0]=="init":
            if len(action)<2:
                await send_warning(player, msg="argument_insufficient")
                return True
            player.name = action[1]
            print(f"Player {player.player_id} has set his name to {player.name}")
        elif action[0] == 'exit':
            return False
        else:
            print(f"Command {action} not found")
    return True

def choose_position(player, x, y):
    if player.new_tribes_to_create > 0:
        # Create a new tribe with the chosen position and recorded ant positions
        pos=Position(x,y)
        if not in_field(pos):
            asyncio.create_task(send_warning(player, msg=f"position_out_of_bound"))
            return

        new_tribe = Tribe(player.player_id, tribe_id=player.tribe_count, position=pos)
        player.new_tribes_to_create -= 1
        player.tribes[new_tribe.tribe_id] = new_tribe
        player.tribe_count+=1;
        asyncio.create_task(send_notification(player, msg="tribe_created", tid=new_tribe.tribe_id))

        # invasion
        new_tribe.perform_invasion()

        print(f"Created a new tribe for player {player.player_id}({player.name})")
    else:
        asyncio.create_task(send_warning(player, msg="tribe_creation_not_available"))



async def handle_client(reader, writer):
    global player_counter
    player_id = player_counter
    player_counter += 1

    player = Player(player_id, reader, writer)
    players[player_id] = player

    print(f"Player {player_id} connected")

    try:
        while True:
            # print("try to read...")
            message = await reader.read(1024)
            if not message:
                print(f"Player {player_id} disconnected.")
                break

            message = message.decode('utf-8')
            print(f"Received from player {player.player_id}({player.name}): {message}")

            ret = await update_game_state(player, message)
            if not ret:
                print(f"Player {player_id} exiting...")
                break
            await send_game_state_all(backup=True)  # Send game state after handling the message

    except socket.error as e:
        print(f"Error receiving data from Player {player_id}: {e}")
    finally:
        del players[player_id]
        writer.close()
        await writer.wait_closed()

    # finally:
        # writer.close()
        # await writer.wait_closed()

async def send_game_state_all(backup=False):
    await send_game_state(player=None, backup=backup)

async def send_game_state(player=None, backup=False):
    game_data= await gen_game_data(backup)

    players_tmp=[player] if player is not None else players.values()

    for player_i in players_tmp:
        async with mutex:
            msg={
                "type": "data",
                "player_id": player_i.player_id,
                "new_tribes_to_create": player_i.new_tribes_to_create,
                **game_data
            }
        json_obj = json.dumps(msg)

        try:
            await send_message_withheader(player_i.writer, json_obj)
        except socket.error as e:
            print(f"Error sending game state to Player {player.player_id}: {e}")

async def gen_game_data(backup=False):
    async with mutex:
        data= {
            "map_size": {"height": MAP_HEIGHT, "width": MAP_WIDTH},
            "players": {
                i.player_id: {
                    "name": i.name,
                    "tribes": {
                        tribe.tribe_id:{
                            "DEF": tribe.DEF,
                            "ATK": tribe.ATK,
                            "infection_probability": tribe.infection_probability,
                            "radius": tribe.radius,
                            "position": {"x": tribe.position.x, "y": tribe.position.y},
                            "zone": list(tribe.infection_area)
                        }
                        for tribe in i.tribes.values()
                    }
                }
                for i in players.values()
            },
            "ants": [ant.position.toTuple() for ant in ants]
        }
    if backup:
        try:
            with open("data.json", "w") as outfile:
                json.dump(data, outfile)
        except Exception as e:
            print(f"Error writing game data to file: {e}")

    return data



async def update_tribe_values():
    while True:
        async with mutex:
            for player in players.values():
                for tribe in player.tribes.value():
                    tribe.update_values()

        await asyncio.sleep(UPDATE_INTERVAL)

async def generate_ants():
    global ants
    global ants_count
    while True:
        if ants_count<ANT_MAX_N and random.randint(0, ANT_MAX_N-1)<= ANT_MAX_N-ants_count:
            ant_health = random.randint(30,90)
            ant_position = Position(random.randint(0, MAP_WIDTH - 1), random.randint(0, MAP_HEIGHT - 1))
            new_ant = Ant(ant_position, ant_health)
            async with mutex:
                ants.append(new_ant)
                ants_count+=1
            # print(f"An ant generated at position ({ant_position.x}, {ant_position.y})")
            await send_game_state_all(backup=True)
        await asyncio.sleep(ANT_GENERATION_INTERVAL)

async def move_ants():
    global ants
    global ants_count
    while True:
        #print("getting lock...")
        async with mutex:
            for ant in ants:
                ant.move()
                # print(f"An ant moved to position ({ant.position.x}, {ant.position.y})")
                if ant.health <= 0 or not in_field(ant.position):
                    ants.remove(ant)
                    ants_count-=1
                    continue
                for player in players.values():
                    for tribe in player.tribes.values():
                        if is_ant_infected(ant, tribe):
                            # Record the position where the ant was infected
                            player.ant_positions.append(ant.position)
                            player.new_tribes_to_create += 1
                            ants_count-=1
                            print(f"An ant infected at position ({ant.position.x}, {ant.position.y})")
                            asyncio.create_task(send_notification(player, msg="ant_infected"))
        await send_game_state_all(backup=True)
        #print("move ants done")
        await asyncio.sleep(ANT_MOVEMENT_INTERVAL)
        #print("sleep done")





async def main(bind_ip='127.0.0.1', bind_port=8763):
    global loop
    server = await asyncio.start_server(
        handle_client,
        bind_ip,
        bind_port
    )

    # Start the task for generating ants
    # gen_ant_thread = threading.Thread(target=generate_ants)
    # gen_ant_thread.start()

    # Start the task for moving ants
    # move_ant_thread = threading.Thread(target=move_ants)
    # move_ant_thread.start()

    update_tribe_values_task = loop.create_task(update_tribe_values())

    # Start the asyncio task for moving and generating ants
    gen_ant_task = loop.create_task(generate_ants())
    move_ant_task = loop.create_task(move_ants())

    async with server:
        print(f'Listening on {bind_ip}:{bind_port}')
        await server.serve_forever()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python server.py <ip> <port>")
        exit(0)
    server_ip, server_port = sys.argv[1], int(sys.argv[2])
    loop = asyncio.get_event_loop()
    server_task = loop.create_task(main(bind_ip=server_ip, bind_port=server_port), name='Server')
    loop.run_forever()
