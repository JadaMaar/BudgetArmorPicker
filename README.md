# BudgetArmorPicker

A small python script to calculate Destiny 2armor combination stats up to 200 to prepare sets for the Edge of Fate expansion.

## Setup
1. Create a new App in the Bungie Application Portal: https://www.bungie.net/en/Application
2. Set OAuth Client Type to  `Confidential`
3. Set the Redirect URL to https://www.google.com (any other works but need to be adjusted in the script)
4. Check the Scope `Read your Destiny 2 information (Vault, Inventory, and Vendors), as well as Destiny 1 Vault and Inventory data.`
5. Create a ``.env`` File and insert `API_KEY`, `CLIENT_ID` and `CLIENT_SECRET`. It should look like the following:
```
API_KEY=9f3ec71622ab44aea97e9aec96555e50
CLIENT_ID=12345
CLIENT_SECRET=RkOMORlGLC7qQK3Lydz8ytcJK1hgEIut-dHbqtm1Vo8
```

## Usage
1. Start the script
2. Click on the Authorization Link. This will send you to https://www.google.com/?code=MYAUTHCODE
3. Copy the entire URL into the console
4. Select the initial class for which you want to find armor

Commands:
- `<stat> <value>` Sets the desired value for a given stat without the use of any stat mods.
  - `<stat>` can be `mob`, `res`, `rec`, `dis`, `int`, `str`
  - `<value>` can not be higher than the highest possible value
- `reset` Sets the desired value for each stat to 0
- `search` Prints all armor combinations that satisfy the selected stats sorted by their total stats
- `copy <index>` Copies a string to search for the entire set using DIM
  - `<index>` Number shown above each result when using search. Always applies to the latest search query
- `class` Switches the class you want to find armor for
- `exit` Exits the program :)