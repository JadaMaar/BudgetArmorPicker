import os
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import pickle
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from functools import partial
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
import pyperclip


armor_slots = {
    26: "Helmet",
    27: "Arms",
    28: "Chest",
    29: "Legs",
    30: "Bond"
}

def OAuth():
    redirect_url = "https://www.google.com"
    base_auth_url = "https://www.bungie.net/en/OAuth/Authorize"
    token_url = "https://www.bungie.net/platform/app/oauth/token/"

    session = OAuth2Session(client_id=client_id, redirect_uri=redirect_url)

    auth_link = session.authorization_url(base_auth_url)
    print(f"Authorization link: {auth_link[0]}")

    redirect_response = input(f"Paste url link here: ")

    session.fetch_token(
        client_id=client_id,
        client_secret=client_secret,
        token_url=token_url,
        authorization_response=redirect_response
    )

    return session


def unwrap_stats(stats):
    intellect = stats["144602215"]["value"]
    resilience = stats["392767087"]["value"]
    discipline = stats["1735777505"]["value"]
    mobility = stats["2996146975"]["value"]
    strength = stats["4244567218"]["value"]

    return f"Int: {intellect}, Res: {resilience}, Disc: {discipline}, Mob: {mobility}, Strength: {strength}"

STAT_KEYS = {
    "int": "144602215",
    "res": "392767087",
    "dis": "1735777505",
    "mob": "2996146975",
    "str": "4244567218",
    "rec": "1943323491",
}

def sum_stats(pieces):
    return {k: sum(p[STAT_KEYS[k]]["value"] for p in pieces) + 2 for k in STAT_KEYS}  # +2 class item

def passes_target(stats, target_values):
    return all(stats.get(k, 0) >= target_values.get(k, 0) for k in target_values)

def process_helmet(k1, h_item, arms, chests, legs, target_values):
    h_stats = h_item["stats"]
    h_exotic = h_item["exotic"]

    results = []
    maxes = {k: 0 for k in STAT_KEYS}

    for k2, a_item in arms.items():
        if h_exotic and a_item["exotic"]:
            continue
        a_stats = a_item["stats"]
        a_exotic = a_item["exotic"]

        for k4, c_item in chests.items():
            if (h_exotic or a_exotic) and c_item["exotic"]:
                continue
            c_stats = c_item["stats"]
            c_exotic = c_item["exotic"]

            for k5, l_item in legs.items():
                if (h_exotic or a_exotic or c_exotic) and l_item["exotic"]:
                    continue
                l_stats = l_item["stats"]

                pieces = [h_stats, a_stats, c_stats, l_stats]
                stats = sum_stats(pieces)
                stats["total"] = stats["int"] + stats["res"] + stats["dis"] + stats["mob"] + stats["str"]

                if not passes_target(stats, target_values):
                    continue

                # Update max values
                for k in STAT_KEYS:
                    maxes[k] = max(maxes[k], stats[k])

                results.append({
                    **stats,
                    "helmet": k1,
                    "arms": k2,
                    "chest": k4,
                    "legs": k5,
                })

    return results, maxes

def unpack_process_helmet(args):
    return process_helmet(*args)

def calculate_combinations_parallel(guardian_class, target_values, h, a, c, l, b, print_found=True):
    helmets = h[guardian_class]
    arms = a[guardian_class]
    chests = c[guardian_class]
    legs = l[guardian_class]

    tasks = [(k1, helmets[k1], arms, chests, legs, target_values) for k1 in helmets]

    # Use tqdm for outer progress
    with Pool(cpu_count()) as pool:
        results = list(tqdm(pool.imap_unordered(unpack_process_helmet, tasks), total=len(tasks), desc="Parallel helmet combinations"))

    all_combinations = []
    max_others = {k: 0 for k in STAT_KEYS}

    for combos, maxes in results:
        if print_found:
            all_combinations.extend(combos)
        for k in STAT_KEYS:
            max_others[k] = max(max_others[k], maxes[k])

    copy_combo_string = []
    if print_found:
        all_combinations.sort(key=lambda x: x["total"])
        copy_combo_string = output_combination(all_combinations, target_values, guardian_class, h, a, c, l, print_found)
    else:
        print(f"Maximum possible values with the current targets: {max_others}")

    return max_others, copy_combo_string


def output_combination(combos, target_values: dict, guardian_class: int, h: dict, a: dict, c: dict, l: dict, print_found=True):
    copy_combo_string = []
    for i, combo in enumerate(combos):
        intellect = combo["int"]
        resilience = combo["res"]
        discipline = combo["dis"]
        mobility = combo["mob"]
        strength = combo["str"]
        recovery = combo["rec"]

        if target_values.get("int", 0) > intellect or target_values.get("res", 0) > resilience or target_values.get("dis", 0) > discipline or target_values.get("mob", 0) > mobility or target_values.get("str", 0) > strength or target_values.get("rec", 0) > recovery:
            continue

        helmet_id = combo["helmet"]
        arms_id = combo["arms"]
        legs_id = combo["legs"]
        chest_id = combo["chest"]

        if print_found:
            print(f"------------({i})-------------")
            print(f"Helmet: {unwrap_stats(h[guardian_class][helmet_id]["stats"])}, ID:{helmet_id}")
            print(f"Arms: {unwrap_stats(a[guardian_class][arms_id]["stats"])}, ID:{arms_id}")
            print(f"Chest: {unwrap_stats(c[guardian_class][chest_id]["stats"])}, ID:{chest_id}")
            print(f"Legs: {unwrap_stats(l[guardian_class][legs_id]["stats"])}, ID:{legs_id}")

            print(f"Total: {intellect + resilience + discipline + mobility + strength}, Int: {intellect}, Res: {resilience}, Dis: {discipline}, Rec: {recovery}, Mob: {mobility}, Str: {strength}")
            copy_combo_string.append(f"id:{helmet_id} or id:{arms_id} or id:{chest_id} or id:{legs_id}")
    return copy_combo_string

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv('API_KEY')
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    session = OAuth()

    # print(session.token)

    additional_headers = { 'X-API-Key': api_key }

    # Get the current user
    get_user_details_endpoint = "https://www.bungie.net/Platform/User/GetMembershipsForCurrentUser/"
    response = session.get(url=get_user_details_endpoint, headers = additional_headers)
    response_json = response.json()

    membershipId = response_json["Response"]["destinyMemberships"][0]["membershipId"]
    membershipType = response_json["Response"]["destinyMemberships"][0]["membershipType"]

    # Get the users inventory
    # we need to get: ItemStats, ProfileInventory, ItemSockets, CharacterInventory tba
    inventory_url = f"https://www.bungie.net/Platform/Destiny2/{membershipType}/Profile/{membershipId}/?components=304,102,305,201"
    response = session.get(inventory_url, headers = additional_headers)
    response_json = response.json()

    # print(response_json)
    # TODO: indentify armor by checking stats count == 6 (weapons would be 11)
    item_data: list = response_json["Response"]["profileInventory"]["data"]["items"]
    for char, value in response_json["Response"]["characterInventories"]["data"].items():
        item_data += value["items"]
    item_stats: dict = response_json["Response"]["itemComponents"]["stats"]["data"]
    item_sockets: dict = response_json["Response"]["itemComponents"]["sockets"]["data"]

    armor = {key: item for key, item in item_stats.items() if item["stats"].get('144602215')} # check if it contains the intellect hash to ensure its armor
    print(f"{len(armor)} armor pieces found")
    helmet = {2: dict(), 0: dict(), 1: dict()} # 2 warlock, 0 titan, 1 hunter
    arm = {2: dict(), 0: dict(), 1: dict()} # 2 warlock, 0 titan, 1 hunter
    chest = {2: dict(), 0: dict(), 1: dict()} # 2 warlock, 0 titan, 1 hunter
    legs = {2: dict(), 0: dict(), 1: dict()} # 2 warlock, 0 titan, 1 hunter
    bond = {2: dict(), 0: dict(), 1: dict()} # 2 warlock, 0 titan, 1 hunter

    with open('manifest.pickle', 'rb') as data:
        all_data = pickle.load(data)

    # sanitize stats aka remove stat increase mods
    for instance in armor:
        try:
            plugHash = item_sockets[instance]["sockets"][0]["plugHash"]
        except:
            continue
        if 1043342778 in all_data["DestinyInventoryItemDefinition"][plugHash]["itemCategoryHashes"]: # check if it is a subclassmod, some abilities are in this because subclasses have stats
            continue
        if plugHash not in  [1980618587, 2527938402, 369171376]: # empty mod socket, rivens curse, transcendent blessing, healing rift
            stat_mod = all_data["DestinyInventoryItemDefinition"][plugHash]
            values = stat_mod["investmentStats"][1]
            armor[instance]["stats"][str(values["statTypeHash"])]["value"] -= values["value"]
            # print(f"decreased stat of {instance} by {values["value"]}")

    # TODO: indentify armor slot
    # split armor by slot
    for item in item_data:
        valid_armor = armor.get(item.get("itemInstanceId"))
        if valid_armor:
            slot = all_data["DestinyInventoryItemDefinition"][item["itemHash"]]["itemSubType"]
            class_type = all_data["DestinyInventoryItemDefinition"][item["itemHash"]]["classType"]
            slot_name = armor_slots.get(slot)
            valid_armor["exotic"] = all_data["DestinyInventoryItemDefinition"][item["itemHash"]]["inventory"]["tierType"] == 6

            if slot_name == "Helmet":
                helmet[class_type][item["itemInstanceId"]] = valid_armor
            elif slot_name == "Arms":
                arm[class_type][item["itemInstanceId"]] = valid_armor
            elif slot_name == "Chest":
                chest[class_type][item["itemInstanceId"]] = valid_armor
            elif slot_name == "Legs":
                legs[class_type][item["itemInstanceId"]] = valid_armor
            elif slot_name == "Bond":
                bond[class_type][item["itemInstanceId"]] = valid_armor
    # print(armor)

    # TODO: do some for loops to check the stats sum of all possible combinations
    # while True:
        # current_class = input("Select which class you want to find armor for (0 Titan, 1 Hunter, 2 Warlock): \n")
    current_class = inquirer.select(
        message="Select a Class:",
        choices=[
            Choice(name="Titan", value=0),
            Choice(name="Hunter", value=1),
            Choice(name="Warlock", value=2)
        ],
        default=None,
    ).execute()

    print(f"{len(helmet[current_class]) + len(chest[current_class]) + len(arm[current_class]) + len(legs[current_class])} armor pieces found for class {current_class}")

    targets = dict()
    max_possible_stats, copy_combo_string = calculate_combinations_parallel(current_class, targets, helmet, arm, chest, legs, bond, False)


    while True:
        cmd = input("cmd: ")
        if cmd == "help":
            print("The following commands are available:")
            print("class //changes the class to the selected one")
            print("[stat] [value] //sets the desired target value")
            print("copy [index] //copies a string to search for the combination in DIM for the given index of the last search query")
        elif cmd == "class":
            current_class = inquirer.select(
                message="Select a Class:",
                choices=[
                    Choice(name="Titan", value=0),
                    Choice(name="Hunter", value=1),
                    Choice(name="Warlock", value=2)
                ],
                default=None,
            ).execute()
            max_possible_stats, _ = calculate_combinations_parallel(current_class, targets, helmet, arm, chest, legs, bond,False)
        elif cmd == "reset":
            targets = dict()
            print(f"current focus: {targets}")
            max_possible_stats, _ = calculate_combinations_parallel(current_class, targets, helmet, arm, chest, legs, bond, False)
        elif cmd.startswith(("mob", "res", "rec", "dis", "int", "str")):
            tmp_targets = dict()
            valid = True
            try:
                stat_cmd_split = cmd.split()
                stat = stat_cmd_split[0].strip()
                if stat not in ["mob", "res", "rec", "dis", "int", "str"]:
                    break
                target_value = stat_cmd_split[1]
                target_value = int(target_value)
                tmp_targets[stat] = target_value
                if target_value > max_possible_stats[stat]:
                    print(f"Given stat was higher than the max possible of {max_possible_stats[stat]}.")
                else:
                    targets[stat] = target_value
                    print(f"current focus: {targets}")
                    max_possible_stats, _ = calculate_combinations_parallel(current_class, targets, helmet, arm, chest, legs, bond, False)
            except ValueError as e:
                print("A value is required after each stat e.g. 'mob 70'")
                valid = False
                # print("Please provide a valid number!")
            except IndexError:
                print("A value is required after each stat e.g. 'mob 70'")
                valid = False
        elif cmd == "search":
            max_possible_stats, copy_combo_string = calculate_combinations_parallel(current_class, targets, helmet, arm, chest, legs, bond, True)
        elif cmd.startswith("copy"):
            try:
                cmd = cmd.split()
                index = int(cmd[1])
                pyperclip.copy(copy_combo_string[index])
                print(f"Copied '{copy_combo_string[index]}' to clipboard.")
            except Exception as e:
                print("Invalid use of the copy command.")

        elif cmd == "exit":
            break

    # TODO: profit (noone will ever see this or care ΩwΩ )



