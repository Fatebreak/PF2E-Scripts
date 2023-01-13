from lxml import html
import requests
import re
import os

class monster:
    statblock = {
    "name": 0,
    "level": 0,
    "trait": "",
    "perception": 0,
    "senses": "",
    "languages": "",
    "skills": {},
    "stats": [],
    "specialabilities": {},
    "ac": 0,
    "saves": [],
    "hp": 0,
    "immunities": 0,
    "resistances": 0,
    "weaknesses": 0,
    "defense": {},
    "speed": "",
    "offense": {},
}