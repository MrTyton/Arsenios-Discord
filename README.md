Discord Bots
============

Based off of [Discord-Bots](https://github.com/sleibrock/discord-bots/) by Sleibrock, heavily modified for own purposes.


### Docs

* [AsyncIO Docs](https://docs.python.org/3.4/library/asyncio.html)
* [Discord.py API](http://discordpy.readthedocs.io/en/latest/api.html)
* [Discord Dev Portal](https://discordapp.com/developers/docs/intro)

### Introduction

Discord, the popular chat service aimed at gamers, supports a WebSocket API for sending and receiving data. From this we can create Bot users, so this project has the sole focus of creating various bots to be used with the Discord service.

In it's current state, this project has Python code wrapping around the `discord.py` library itself to aid in the development of bots, as well as bots written in Python with many different goals of doing as much as they can.

### Requirements

To run this project you will need:

* Python 3.6
* Racket 6.5 (for the `superv` manager)
* Pip for Python
* `virtualenv` installed from Pip
* Your own set of Discord credentials to use with Bots


