Law of the West C64 NTSC

Partially disassembled and commented

When I first played this game, I was fascinated by its branching dialogue system and the many possible outcomes of each conversation.

I often wondered:

	* How is the final score calculated?
	* What triggers all six robbery scenes?
	* How could I explore every dialogue option and consequence without replaying the game hundreds of times?
	
Back then, the answers were out of reach. Today, they are at hand.

To uncover them, I partially disassembled the game, focusing on its scoring and dialogue systems. 

Start with the "Overview" file.

Here's a list of files and directories, and their purpose:

diagrams/						A directory containing diagrams and tables that aid to visualize how Rapidlok works
dump-dialogue/					A directory containing Python scripts that can dump the dialogue from the game
Overview						A general overview of the game findings: including the scoring, dialogue and outcome system
Rapidlok overview				A more detailed file focusing on Rapidlok
(files starting with 01 to 09)	A stage by stage disassembly of the Rapidlok loader
10-computer-intro-screen		A partial disassembly of the intro screen
11-computer-main-code			A partial disassembly of the main game
full-dialogue-dump				A full dump of every possible dialogue for every character, including scores and outcomes
routine map						A routine map of the main game
sector map						A map of the disk sectors
