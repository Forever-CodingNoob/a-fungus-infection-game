#!/bin/env python3
import asyncio
import threading
import json
import sys
from blessed import Terminal
import random




term = Terminal()
CELL_WIDTH = 2
BG_COLOR = term.normal + term.white
META_COLOR = term.black_on_seagreen3
ANT_SYMB = "🐜"
ANT_SYMB2 = "O"
ANT_SYMB_WIDTH = 2
ANT_SYMB2_WIDTH = 1
exit_event = threading.Event()  # Event to signal exit
end = False
game_map = {}  # Dictionary to store the game map state
game_map_output = {}
ant=list()
map_size = {"height": 0, "width": 0}
new_tribes_to_create = 0
current_player_id = -1
current_player_name = ""
input_player_name = ""
cursor = (0,0)
init = False
choose_position_mode = False
show_input_name_popup = False
mutex = asyncio.Lock()



class PlayerColor:
    BGCOLOR = term.on_color_rgb(18,18,18)
    CURSOR_COLOR = term.on_red
    COLORS = [
        (252, 186, 3),
        (66, 135, 245),
        (49, 163, 212),
        (189, 151, 47),
        (214, 81, 36),
        (116, 191, 46),
        (132, 32, 186),
        (220, 7, 227),
        (12, 29, 125)
    ]
    COLORS_USED = list(range(len(COLORS)))

    @staticmethod
    def getPlayerColor(player_id):
        color = random.choice(PlayerColor.COLORS)
        PlayerColor.COLORS.remove(color)
        return color
    @staticmethod
    def returnColor(color):
        PlayerColor.COLORS.append(color)


async def send_message(writer, message):
    writer.write(message.encode('utf-8'))
    await writer.drain()

async def read_server(reader):
    global cursor, choose_position_mode, end
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
            # print(json.loads(message))
            game_data = json.loads(message)
        except json.decoder.JSONDecodeError:
            print("JSON decode error")
            continue

        if game_data['type']=="data":
            await update_terminal(game_data)
        elif game_data['type']=="notification" and game_data["msg"]=="choose_position":
            hide_cursor()
            cursor=(game_data['x'], game_data['y'])
            choose_position_mode=True
            show_cursor()
        elif game_data['type']=='notification' and game_data['msg']=='tribe_creation_succeeded':
            hide_cursor()
            choose_position_mode=False
        elif game_data['type']=='notification' and game_data['msg']=='lost':
            #print(f"{BG_COLOR}You lost (Press any key to continue...)")
            choose_position_mode=False
            end=True
            hide_cursor()



def user_input(writer):
    global choose_position_mode
    val = ''
    while not exit_event.is_set():
        val = term.inkey()
        if end:
            asyncio.run(send_message(writer, f"exit"))
            exit_event.set()
            break
        if val.is_sequence:
            if val.code==343:
                (x,y)=cursor
                asyncio.run(send_message(writer, f"choose_position {x} {y}"))
            elif val.code==259:
                # up
                move_cursor(0,-1)
            elif val.code==258:
                # down
                move_cursor(0,1)
            elif val.code==260:
                # left
                move_cursor(-1,0)
            elif val.code==261:
                move_cursor(1,0)
        elif val:
            if val.lower() == 'q':
                exit_event.set()
                break
            elif val==' ' and new_tribes_to_create>0:
                asyncio.run(send_message(writer, "create_tribe"))

    print(f'{BG_COLOR}bye!{term.normal}')

def remove_tribe(player_id, tribe_id):
    global game_map, game_map_output
    empty_cell = " " * CELL_WIDTH
    for x,y in game_map[player_id]["tribes"][tribe_id]["zone"]:
        game_map_output[y][x]=(PlayerColor.BGCOLOR, empty_cell)
    del game_map[player_id]["tribes"][tribe_id]



async def update_terminal(new_game_data):
    global game_map, game_map_output, map_size, current_player_id, init, new_tribes_to_create, current_player_name, ant
    drawn_grids = set()
    current_player_id = str(new_game_data["player_id"])
    current_player_name = new_game_data["players"][current_player_id]["name"]

    # Extract relevant data from new_game_data
    if not init:
        init=True
        map_size["height"]=int(new_game_data["map_size"]["height"])
        map_size["width"]=int(new_game_data["map_size"]["width"])
        game_map_output=[
            [(PlayerColor.BGCOLOR, " "*CELL_WIDTH) for _ in range(map_size["width"])]
            for _ in range(map_size["height"])
        ]


    new_tribes_to_create = new_game_data["new_tribes_to_create"]
    new_players = new_game_data["players"]

    # Update the game map with new data

    # Handle the case when players leave the game and tribes are deleted
    for player_id in list(game_map.keys()):
        if player_id not in new_players:
            # player is removed form game
            for tribe_id in list(game_map[player_id]["tribes"].keys()):
                remove_tribe(player_id, tribe_id)
            PlayerColor.returnColor(game_map[str(player_id)]['color'])
            del game_map[player_id]
        else:
            for tribe_id in list(game_map[player_id]["tribes"].keys()):
                if tribe_id not in new_players[player_id]["tribes"]:
                    remove_tribe(player_id, tribe_id)


    for player_id, player_data in new_players.items():

        # add new player to game_map
        if player_id not in game_map:
            game_map[player_id] = {
                "name": player_data["name"],
                "tribes": {},
                'color':  PlayerColor.getPlayerColor(player_id)
            }

        for tribe_id, tribe_data in player_data["tribes"].items():
            new_tribe_position = (int(tribe_data["position"]["x"]), int(tribe_data["position"]["y"]))
            new_tribe_zone = set([(int(pos[0]), int(pos[1])) for pos in tribe_data["zone"]])

            # add new tribe
            if tribe_id not in game_map[player_id]["tribes"]:
                game_map[player_id]["tribes"][tribe_id] = {
                    "position": tuple(),
                    "zone": set(),
                    "ATK": -1,
                    "DEF": -1
                }

            game_map[player_id]["tribes"][tribe_id]["ATK"]=int(tribe_data["ATK"])
            game_map[player_id]["tribes"][tribe_id]["DEF"]=int(tribe_data["DEF"])

            old_tribe_zone = game_map[player_id]["tribes"][tribe_id]["zone"]
            old_position = game_map[player_id]['tribes'][tribe_id]["position"]

            # Check if the cell has changed
            for x,y in old_tribe_zone.difference(new_tribe_zone).difference(drawn_grids):
                game_map_output[y][x]=(PlayerColor.BGCOLOR, " "*CELL_WIDTH)
            for x,y in (diff:=new_tribe_zone.difference(old_tribe_zone)):
                game_map_output[y][x]=(term.on_color_rgb(*game_map[player_id]['color']), " "*CELL_WIDTH)
            drawn_grids.update(diff)
            game_map[player_id]['tribes'][tribe_id]['zone'] = new_tribe_zone

            if new_tribe_position != old_position:
                if old_position!=tuple() and old_position not in drawn_grids:
                    (x,y)=old_position
                    game_map_output[y][x]=(PlayerColor.BGCOLOR, " "*CELL_WIDTH)
                (x,y)=new_tribe_position
                game_map_output[y][x]=(term.on_color_rgb(*game_map[player_id]['color']), ANT_SYMB.center(CELL_WIDTH-ANT_SYMB_WIDTH+1))
                game_map[player_id]['tribes'][tribe_id]["position"] = new_tribe_position

    for x,y in ant:
        if ANT_SYMB2 in game_map_output[y][x][1]:
            game_map_output[y][x]=(game_map_output[y][x][0]," "*CELL_WIDTH)
    ant=list()
    for x,y in new_game_data["ants"]:
        x,y=int(x), int(y)
        ant.append((x,y))
        if game_map_output[y][x][1]==" "*CELL_WIDTH:
            game_map_output[y][x]=(game_map_output[y][x][0],ANT_SYMB2.center(CELL_WIDTH-ANT_SYMB2_WIDTH+1))

    upd_screen()
    upd_metadata()

    # show cursor
    show_cursor()

    if end:
        term_size = term.height, term.width
        with term.location(0, term_size[0] // 2 - 1):
            print(term.black_on_red+"You lost".center(term_size[1]))
            print(term.black_on_red+"(Press any key to quit)".center(term_size[1]))
    if show_input_name_popup:
        await draw_popup()


def upd_screen():
    print(
        term.home+"\n".join(["".join([cell[0]+cell[1] for cell in row]) for row in game_map_output]),
        end="",
        flush=True
    )

def upd_metadata():
    with term.location(0, map_size["height"]):
        PLAYER_INFO = f"Player: {current_player_name} ({current_player_id})"
        PLAYER_INFO_WIDTH = len(PLAYER_INFO) + 5
        (R,G,B)=game_map[current_player_id]["color"]
        PLAYER_INFO_COLOR = term.on_color_rgb(R,G,B) + (term.color_rgb(255,255,255) if R+G+B<340 else term.black)
        print(
            PLAYER_INFO_COLOR + PLAYER_INFO.ljust(PLAYER_INFO_WIDTH)+META_COLOR + f"# new tribes available: {new_tribes_to_create}".rjust(map_size["width"]*CELL_WIDTH-PLAYER_INFO_WIDTH),
            end="",
            flush=True
        )

    i=1
    with term.location(0, map_size["height"]+i):
        print(
            BG_COLOR+ term.clear_eos,
            end="",
            flush=True
        )
    for tribe_id, tribe in game_map[current_player_id]["tribes"].items():
        TRIBE_INFO_WIDTH = 8
        TRIBE_INFO_TITLE_WIDTH = TRIBE_INFO_WIDTH + 5
        with term.location(0, map_size["height"]+i):
            print(
                META_COLOR+(f"Tribe {tribe_id}:").ljust(TRIBE_INFO_TITLE_WIDTH),
                end="",
                flush=True
            )
        with term.location(TRIBE_INFO_TITLE_WIDTH, map_size["height"]+i):
            print(
                META_COLOR+(f"ATK {tribe['ATK']}").ljust(TRIBE_INFO_WIDTH),
                end="",
                flush=True
            )
        with term.location(TRIBE_INFO_WIDTH+TRIBE_INFO_TITLE_WIDTH, map_size["height"]+i):
            print(
                META_COLOR+(f"DEF {tribe['DEF']}").ljust(TRIBE_INFO_WIDTH),
                end="",
                flush=True
            )
        i+=1



def move_cursor(dx, dy):
    global cursor
    hide_cursor()
    x=max(min(cursor[0]+dx, map_size["width"]-1), 0)
    y=max(min(cursor[1]+dy, map_size["height"]-1), 0)
    cursor=(x,y)
    show_cursor()

def show_cursor():
    if not choose_position_mode:
        return
    (x,y)=cursor
    with term.location(x*CELL_WIDTH,y):
        print(PlayerColor.CURSOR_COLOR+game_map_output[y][x][1], end="", flush=True)
def hide_cursor():
    (x,y)=cursor
    with term.location(x*CELL_WIDTH,y):
        print(game_map_output[y][x][0]+game_map_output[y][x][1], end="", flush=True)




async def draw_popup():
    async with mutex:
        with term.location(0, term.height // 2 - 2):
            color = term.black_on_blue
            print(color + term.bold("Enter Your Name:".center(term.width)))
            print(color + input_player_name.ljust(20, "_").center(term.width))
            print(color + "Press Enter when done.".center(term.width))

def get_user_name():
    global input_player_name

    while True:
        key = term.inkey()
        if key.is_sequence and key.code == term.KEY_ENTER:
            break
        elif key.is_sequence and key.code == term.KEY_DELETE:
            input_player_name = input_player_name[:-1]
        elif key.is_sequence and key.code == term.KEY_BACKSPACE:
            input_player_name = input_player_name[:-1]
        else:
            input_player_name += key
        color = term.black_on_blue

        asyncio.run(draw_popup())


async def main():
    global show_input_name_popup
    show_input_name_popup=True

    print(term.home + BG_COLOR + term.clear)

    server_ip, server_port = sys.argv[1], int(sys.argv[2])
    reader, writer = await asyncio.open_connection(server_ip, server_port)

    #user_input_thread = threading.Thread(target=user_input, args=(writer,))
    #user_input_thread.start()
    read_server_task = asyncio.create_task(read_server(reader))

    user_name_input_task = asyncio.to_thread(get_user_name)
    try:
        await asyncio.gather(user_name_input_task)
    except asyncio.CancelledError:
        pass
    show_input_name_popup=False
    print(term.home + BG_COLOR + term.clear)

    await send_message(writer, f"init {input_player_name}")


    user_input_task = asyncio.to_thread(user_input, writer)

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
    if len(sys.argv) != 3:
        print("Usage: python client.py <server_ip> <server_port>")
        exit(0)

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        asyncio.run(main())

