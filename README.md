KanColle Bridge is (will be) a smart little Python app for your Ubuntu that can help you with a bunch of stuff related to your beloved shipdaughters.

# Current capabilities

* Record stats about sorties and constructs

## Indicator features 
* Track time of expeditions, constructions and repairs
* Alert with notification when time something is completed
* Display fleets with name, ships and eta to return from expedition when applicable
* Display your admiral name, rank and level
* Allows you to launch the window mode
* Allows you to close the app completely

## Window mode features
* Display current bucket and flamethrower count
* Display current/max ship and equipment count

### The fleets tab shows:
* Type and name of ship
* Equipment (name of equipment shown in tooltip on hover)
* HP, fuel, ammo and fatigue (colors adjusted to game, exact values shown on hover)
* Level and XP (details on hover)
* Average level and air superiority power of the fleet, and also whether it's high speed or not

### The shipdaughter list:
* Shows all the basic stats of the ships
* Shows the possible upgrades for each stat

# Features to come

* Quest tracking
* Optional tracking for individual shipdaughters
* Display the stats collected in an useful manner
* Easy internationalization (at this point everything displayed is in Japanese)
* Other stuff you suggest

# Initial setup and such

Edit kconfig.py and set theServer to your server's IP (the default is Brunei). After this just launch kcbridge.py from the terminal (it will ask for admin rights -- required for catching KC traffic), and launch/reload KanColle. If everything goes well, by the time your office shows up, the indicator menu will have everything loaded.

## About traffic

Bridge does not make any kind of requests. It does not send any data to the KC servers or any other computer. It does not alter any of the data received by KanColle either. It only displays useful bits of info and collects certain stats for internal use.

## Requirements

The Python version default in the latest version of Ubuntu (currently 2.7.5). I haven't installed any additional libraries (as far as I remember). It might work on other versions and systems as well, no idea.

## Bugs etc

If the app seems unresponsive, just quit and restart it. (Though at this point it shouldn't really hang or crash.)

Be sure to tell me about bugs you encounter.
