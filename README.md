# An unnamed fungus infection game
## Introduction & Rules
This is a game about Ophiocordyceps unilateralis, aka zombie-ant fungus, infecting ants.  The game never stops (and so does the server) so that players can join the game as long as the server does not terminate unexpectedly. 
The field (aka map) of the game consists of 500x300 grids. The size of field may be altered by the server owner (aka game host) before the game starts.
Each player control some tribes of a distinct subspecies of Ophiocordyceps unilateralis, which takes over some ant's corpse on the map.
Each ant's corpse is at the fixed position (represented by $(x_i, y_i)$, occupied by a player (i.e., a tribe of a subspecies of zombie-ant fungus) and spans an "infection zone", which might infect the ants passing by at some rate (the probability of infection of an ant passing by is defined as a value stored by the corresponding corpse). Note that the infection zone must be a circle if there is no other infection zone around.
In particular, each corpse (or, tribe of zombie-ant fungus) embodies the following values:
1. The infection probability of the infection zone created by the tribe.
2. Defense value (DEF): This is related to how long the corpse the its infection zone could last the on the field and whether a tribe owned by this subspecies (or, player) can successfully thwart the invasion of other tribes of zombie-ant fungus nearby, controlled by other players,  contending for area (i.e., grids) on the field that is both covered by the infection zone of this corpse and in the "circle" of the infection zone that is about the be created by the invading (aka attacking) tribe. If the ATK of the invading tribe is higher than the DEF of that of this tribe, which is the invaded tribe, the area mention above will then be taken over by the invading tribe and hence the invaded tribe will "lose" this area of its infection zone; otherwise, the invading tribe cannot take over this area and nothing happens. That is, a tribe loses a portion of its infection zone whenever some other tribe with a ATK higher than host's DEF creates its infection zone that covers that portion of field.
3. Attack value (ATK): This is related to whether a tribe owned by the player can successfully invade other tribe of other players to claim the area where its infection zone yet to be created should cover when the tribe is newly created, as described above.
4. Radius of the infection zone (a circle).

Note that when the grid where the corpse is located (i.e., the grid at position $(x_i, y_i)$) is taken over by a tribe of some other player as a result of invasion, the corpse  and the corresponding tribe are eliminated from the game field, meaning that the player has lost this tribe. Meanwhile, the grid  where the corpse was previously located is now in the infection zone of the invading tribe.

Also, each subspecies of zombie-ant fungus, which corresponds to a player, embodies the following values:
1. Base-DEF: the initial DEF of a newly created tribe owned by the player.
2. Base-ATK: the initial ATK of a newly created tribe owned by the player.
3. Base infection probability of the infection zone created by any tribe of the player.

Note that the DEF, ATK, and infection probability of the infection zone of each tribe will decrease by some rate, which should also be able to be altered by the host of the game before the game starts. Besides, each corpse of will eventually "dies" and be eliminated from the field due to microbial and scavenger attack. As a result, the corresponding tribe and infection zone will also be eliminated. As the DEF of a tribe is strongly related to how likely the tribe can successfully defend attacks from microbial and scavenger,  at any time in the game,  if the DEF of a tribe reaches 0, then its corpse dies and it is thus eliminated, including its infection zone.

When an ant is infected a subspecies of zombie-ant fungus  when passing by an infection zone of one of its tribes at some position (aka grid),  the corresponding player that owns the subspecies can then decide to control where the infected ant should take "the death bite" and then create a new tribe of the subspecies owned by the player. In particular, the player is responsible for choosing a position (aka grid) on the field to create a tribe, and then the server will create a tribe for the player, where the tribe has DEF=Base-DEF, ATK=Base-ATK, infection probability = base infection probability, and the newly created tribe will create its infection zone immediately, during which invasion might take place.

## Run the game server (NO installation required)
1. Get `server.py` in your Linux environment with [Python3](https://www.python.org/downloads/) installed:
    + from Github repo (here!)
    + from [workstation](https://www.csie.ntu.edu.tw/~b11902015/bio-game/server.py)
2. Acquire execution permission: `chmod u+x <path_to_client.py>`
3. Run `server.py` directly: `<path_to_server.py> <bind_ip> <bind_port>`
    + e.g. `./server.py 0.0.0.0 48763`

## Run the game client (NO installation required)
1. Get `client.py` in your Linux environment with [Python3](https://www.python.org/downloads/) installed:
    + from Github repo (here!)
    + from [workstation](https://www.csie.ntu.edu.tw/~b11902015/bio-game/client.py)
2. Acquire execution permission: `chmod u+x <path_to_client.py>`
3. Run `client.py`: `python <path_to_client.py> <server_ip_or_domainname> <server_port>` 
    + e.g. `python client.py ws2.csie.ntu.edu.tw 48763`

