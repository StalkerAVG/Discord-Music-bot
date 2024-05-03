# Discord Music Bot

This is a music bot for Discord that plays songs from YouTube in a Discord voice channel.

## Features

- Play a song or add it to the queue.
- Skip the currently playing song or multiple songs based on vote.
- Show the current song queue.
- Actions done by interacting with emoji's:
- Pause or resume the currently playing song.
- Adjust the volume of the bot's audio source.

## Commands

- `%play <song>`: Play a song or add it to the queue. If the bot is already playing a song, the new song will be added to the queue.
- `%skip`: Skip the currently playing song. This command starts a vote, and if at least 80% of the users in the voice channel vote to skip, the song will be skipped.
- `%queue`: Show the current song queue.
- `%leave`: Make the bot leave the voice channel.

## Reactions

- '🔉': Decrease the volume of the bot's audio source.
- '🔊': Increase the volume of the bot's audio source.
- '⏩': Stop the currently playing song.
- '⏪': Try to play the last song in the queue.
- '⏯': Pause or resume the currently playing song.

## Installation

1. Clone this repository.
2. Install the required dependencies.
3. Run the bot.

