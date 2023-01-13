from lxml import html
import requests
import re
import os

statblock = {
    "name": 0,
    "level": 0,
    "trait": "",
    "modifier": 0,
    "senses": "",
    "languages": "",
    "skills": {},
    "stats": [],
    "specialabilities": {},
    "ac": 0,
    "saves": [],
    "hp": 0,
    "health": 0,
    "immunities": 0,
    "resistances": 0,
    "weaknesses": 0,
    "defense": {},
    "speed": "",
    "offense": {},
}

actionList = {
    "Single Action": "<span class='pfactions'>1</span>",
    "Two Actions": "<span class='pfactions'>2</span>",
    "Three Actions": "<span class='pfactions'>3</span>",
    "Free Action": "<span class='pfactions'>f</span>",
    "Reaction": "<span class='pfactions'>r</span>"
}

def main():
    url = input("Enter Monster URL: ")
    os.chdir(os.path.abspath("C:/Users/jtles/Documents/Pathfinder/Dying Light Campaign"))
    #url = "https://2e.aonprd.com/Monsters.aspx?ID=432"
    page = requests.get(url, timeout=None)
    tree = html.fromstring(page.content)
    ilist = tree.xpath('//*[@id="main"]//*/text()')
    statblock["level"] = tree.xpath('//div[@id="main"]//h1[@class="title"]/span/text()')[0]
    ilist = ilist[ilist.index(statblock["level"]) - 1:]
    statblock["name"] = str(ilist[0])
    statblock["level"] = ilist[1].split()[1]
    for item in range(2, ilist.index("Source"), 2):
        statblock["trait"] += f"{ ilist[item] }, "
    statblock["trait"] = statblock["trait"].strip(", ")
    statblock["modifier"] = entrycompile(ilist, tree, "Perception")
    if len(statblock["modifier"].split(";")) < 2 or statblock["modifier"].split(";")[1] == "":
        statblock.pop("senses")
    else:
        statblock["senses"] = statblock["modifier"].split(";")[1].strip(",; ")
    statblock["modifier"] = statblock["modifier"].split(";")[0].strip(",; ")
    statblock["perception"] = f"perception {statblock['modifier']}"
    for item in ["Languages", "AC", "HP", "Immunities", "Resistances", "Weaknesses"]:
        if item not in ilist:
            statblock.pop(item.lower())
        else:
            statblock[item.lower()] = entrycompile(ilist, tree, item)
    statblock["health"] = statblock["hp"]
    statblock["armorclass"] = statblock["ac"]
    statblock["ac"] = statblock["ac"].split()[0].strip(",; ")
    statblock["hp"] = statblock["hp"].split()[0].strip(",; ")
    statblock["source"] = entrycompile(ilist, tree, "Source").split("pg.")[0].strip(",; ")
    if "Skills" in ilist:
        for i in range(ilist.index("Skills") + 2, ilist.index("Str"), 2):
            statblock["skills"][ilist[i]] = ilist[i + 1].strip().split(" ")[0].strip(",; ")
    for item in range(ilist.index("Str") + 1, ilist.index("Cha") + 2, 2):
        statblock["stats"].append(ilist[item].strip(", "))
    for item in range(ilist.index("Fort") + 1, ilist.index("Will") + 2, 2):
        statblock["saves"].append(ilist[item].strip(", "))
    statblock["speed"] = entrycompile(ilist, tree, "Speed", endsearch=tree.xpath('//span[@class="hanging-indent"][1]/b/text()')[0])

    if findnextbold(tree, "Cha") == "AC":
        statblock.pop("specialabilities")
    else:
        statblock["specialabilities"] = abilitycompiler(tree, ilist, findnextbold(tree, "Cha"), "AC")

    for item in ["HP", "Weaknesses", "Resistances", "Immunities"]:
        if item not in ilist:
            continue
        if findnextbold(tree, item) == "Speed":
            statblock.pop("defense")
            break
        if not findnextbold(tree, item) in ["Weaknesses", "Resistances", "Immunities"]:
            statblock["defense"] = abilitycompiler(tree, ilist, findnextbold(tree, item), "Speed")
            for j in ["HP", "Weaknesses", "Resistances", "Immunities"]:
                if j in statblock["defense"]:
                    statblock["defense"].pop(j)
            break

    statblock["offense"] =  getattacks(tree)
    
    if not tree.xpath('//b[contains(text(), "Spells")]/text()') == []:
        spellLists = tree.xpath('//b[contains(text(), "Spells")]/text()')
        spellLists = list(dict.fromkeys(spellLists))
        for i, spellList in enumerate(spellLists):
            statblock[f"spells{i}"] = {}
            if tree.xpath(f'((//b[text()="{spellList}"][1]/following::br[1]/preceding::b)[last()]/preceding::b)[last()]/text()')[0] == "Cantrips":
                endpoint = "Cantrips"
            else:
                endpoint = tree.xpath(f'//b[text()="{spellList}"]/following::br[1]/following::*[contains(text(), "")][1]//text()')[0]
            statblock[f"spells{i}"] = abilitycompiler(tree, ilist, spellList, endpoint)
            for key, value in statblock[f"spells{i}"].items():
                statblock[f"spells{i}"][key] = value.replace('"', "")
            if endpoint == "Cantrips":
                newlist = ilist[ilist.index(spellList):]
                newlist = newlist[newlist.index("Cantrips") + 2:]
                key = f"Cantrips {newlist[0]}"
                endpoint = tree.xpath(f'//b[text()="{spellList}"]/following::br[1]/following::*[contains(text(), "")][1]//text()')[0]
                statblock[f"spells{i}"][key] = entrycompile(newlist, tree, newlist[0], endsearch=endpoint)
            final = statblock[f"spells{i}"][spellList]
            statblock[f"spells{i}"].pop(spellList)
            for key, value in statblock[f"spells{i}"].items():
                final += f"\\n - **{key}:** {value}"
            statblock[f"spells{i}"] = {spellList: final}
            for link in tree.xpath(f'//b[text()="{spellList}"]/following::a/text()'):
                if link not in statblock[f"spells{i}"][spellList]:
                    break
                statblock[f"spells{i}"][spellList] = statblock[f"spells{i}"][spellList].replace(link, f"[[{link}]]")
            statblock[f"spells{i}"][spellList] = "\"" + statblock[f"spells{i}"][spellList] + "\""
            doublelinks = re.search("\[\[([^\]\[]+?)?\[\[([^\]\[]+?)?\]\]([^\]\[]+?)?\]\]", statblock[f"spells{i}"][spellList])
            while doublelinks:
                statblock[f"spells{i}"][spellList] = statblock[f"spells{i}"][spellList].replace(doublelinks.group(), f"[[{''.join(filter(None ,doublelinks.groups()))}]]")
                doublelinks = re.search("\[\[([^\]\[]+?)?\[\[([^\]\[]+?)?\]\]([^\]\[]+?)?\]\]", statblock[f"spells{i}"][spellList])
    if not tree.xpath('//img[@class="thumbnail"]') == []:
        getthumbnail(tree, url)
        name = statblock["name"]
        statblock["image"] = f"[[BestiaryIMG - { name }.png]]"

    makemd(url)


def makemd(url):
    finalstring = "---\nstatblock: true\ncolumnWidth: 700"
    for key, value in statblock.items():
        if type(value) == str or type(value) == int:
            finalstring += f"\n{key}: {value}"
        if type(value) == dict:
            if key == "skills":
                finalstring += f"\n{key}:"
                for key1, value1 in statblock[key].items():
                    finalstring += f"\n  - {key1}: {value1}"
            else:
                finalstring += f"\n{key}:"
                for key1, value1 in statblock[key].items():
                    finalstring += f"\n  - name: {key1}\n    desc: {value1}"
    finalstring += f"\nstats: {str(statblock['stats'])}"
    finalstring += f"\nsaves:"
    for i, item in enumerate(["Fortitude", "Reflex", "Will"]):
        finalstring += f"\n  - {item}: {statblock['saves'][i]}"
    finalstring += f"\n---\n\n[Archive Link]({url})\n\n```statblock\nmonster: {statblock['name']}\n```\n\n```encounter-table\nname: Encounter\ncreatures:\n  - {statblock['name']}\n```"
    finalstring = finalstring.replace("â", "\'")
    print(finalstring)


def getthumbnail(tree, url):
    img = tree.xpath('//img[@class="thumbnail"]/@src')[0]
    img = requests.compat.urljoin(url, img)
    name = statblock["name"]
    with open(f"z_Assets/Bestiary/BestiaryIMG - { name }.png", "wb") as f:
        f.write(requests.get(img).content)

def getattacks(tree):
    result = {}
    attackNumber = 1
    attackList = tree.xpath('//span[@class="hanging-indent"][1]//text()')
    while not attackList == []:
        key = attackList[0]
        while key in result:
            i = 2
            key = key + str(i)
        value = ""
        for item in attackList[1:]:
            if value == "" and item.strip(",; ") == "":
                continue
            value += item
        value = abilityformatter(tree, f'//span[@class="hanging-indent"][{attackNumber}]/b[1]', value.strip(",; "))
        if ( not tree.xpath(f'//span[@class="hanging-indent"][{attackNumber}]/b[1]//*') == []) and str(tree.xpath(f'//span[@class="hanging-indent"][{attackNumber}]/b[1]//*')).split()[1] == "span":
            value = actionList[tree.xpath(f'//span[@class="hanging-indent"][{attackNumber}]/span[1]/@aria-label')[0]] + " " + value
        if str(tree.xpath(f'//span[@class="hanging-indent"][{attackNumber}]/b[1]/following::*[1]')).split()[1] == "span":
            if not tree.xpath(f'//span[@class="hanging-indent"][{attackNumber}]/b[1]/following::span[1]//@aria-label') == []:
                value = actionList[tree.xpath(f'//span[@class="hanging-indent"][{attackNumber}]/b[1]/following::span[1]//@aria-label')[0]] + " " + value
        for link in tree.xpath(f'//span[@class="hanging-indent"][{attackNumber}]/b[1]/following::a//text()'):
            if link not in value:
                break
            if re.match("\+\d+/\+\d+", link):
                continue
            value = value.replace(link.split()[0].strip(",; "), f"[[{link.split()[0].strip(',; ')}]]")
        doublelinks = re.search("\[\[([^\]\[]+?)?\[\[([^\]\[]+?)?\]\]([^\]\[]+?)?\]\]", value)
        while doublelinks:
            value = value.replace(doublelinks.group(), f"[[{''.join(filter(None ,doublelinks.groups()))}]]")
            doublelinks = re.search("\[\[([^\]\[]+?)?\[\[([^\]\[]+?)?\]\]([^\]\[]+?)?\]\]", value)
        diceattacks = re.compile("(\+\d+) \[(\+\d+)/(\+\d+)\]")
        rollvalues = diceattacks.search(value)
        if rollvalues:
            value = value.replace(rollvalues.group(), f"`dice: 1d20{rollvalues.groups()[0]}` {rollvalues.groups()[0]} [`dice: 1d20{rollvalues.groups()[1]}` {rollvalues.groups()[1]} / `dice: 1d20{rollvalues.groups()[2]}` {rollvalues.groups()[2]}]")
        value = "\"" + value.strip(",;\n ") + "\""
        attackNumber += 1
        attackList = tree.xpath(f'//span[@class="hanging-indent"][{attackNumber}]//text()')
        result[key] = value
    return result

def abilitycompiler(tree, ilist, startsearch, endsearch):
    result = {}
    newlist = ilist[ilist.index(startsearch):]
    newlist = newlist[0:newlist.index(endsearch)]
    buffer = 1
    entries = []
    entries.append(newlist[0])
    while True:
        entry = findnextbold(tree, startsearch, buffer=buffer, skipkeywords=False)
        if entry not in newlist:
            break
        else:
            if entry.strip(",; ") not in ["Trigger", "Effect", "Damage", "Saving Throw", "Critical Success", "Success", "Failure", "Critical Failure", "Frequency", "Constant"]:
                entries.append(entry)
        buffer += 1
    for i, entry in enumerate(entries):
        if i + 1 < len(entries):
            entrylist = newlist[newlist.index(entry):newlist.index(entries[i+1])]
        else:
            entrylist = newlist[newlist.index(entry):]
        key = entrylist[0].strip(",; ")
        value = ""
        for j in entrylist[1:]:
            if value == "" and j.strip(",; ") == "":
                continue
            else:
                value += j
        value = abilityformatter(tree, f'//b[text()="{entrylist[0]}"]', value.strip(",;\n "))
        if ( not tree.xpath(f'//*[text()="{ entrylist[0] }"]//*') == []) and str(tree.xpath(f'//*[text()="{ entrylist[0] }"]//*')).split()[1] == "span":
            value = actionList[tree.xpath(f'//*[text()="{ entrylist[0] }"]/span[1]/@aria-label')[0]] + " " + value
        if str(tree.xpath(f'//*[text()="{ entrylist[0] }"]/following::*[1]')).split()[1] == "span":
            value = actionList[tree.xpath(f'//*[text()="{ entrylist[0] }"]/following::span[1]/@aria-label')[0]] + " " + value
        if value == "":
            value = "Per Core Rules"
        value = "\"" + value + "\""
        result[key] = value
    return result

def abilityformatter(tree, path, value):
    boldlist = set()
    buffer = 1
    while True:
        bold = tree.xpath(f"{path}/following::b[{buffer}]/text()")
        if bold == []:
            break
        else:
            bold = bold[0]
        if bold in value:
            boldlist.add(bold)
            buffer += 1
        else:
            break
    for item in boldlist:
        if item in ["Critical Success", "Critical Failure"]:
            continue
        if item in ["Failure", "Success"]:
            replacement = f"\\n - **{item}**"
        else:
            replacement = f"**{item}**"
        value = value.replace(item, replacement)
    for item in ["Success", "Failure"]:
        value = value.replace(f"Critical \\n - **{item}**", f"\\n - Critical {item}")
    value = value.replace("\'", "'")

    attackdice = re.compile(" ?(\d+d\d+(?: ?\+ ?\d+)?) ")
    dicelist = attackdice.findall(value)
    dicelist = list(dict.fromkeys(dicelist))
    for replacement in dicelist:
        value = value.replace(replacement, f"`dice: {replacement}` ({replacement})")
    return value

def entrycompile(ilist, tree, search, endsearch=""):
    value = ""
    startsearch = ilist.index(search) + 1
    ilist = ilist[startsearch:]
    if endsearch == "":
        endsearch = ilist.index(findnextbold(tree, search))
    else:
        endsearch = ilist.index(endsearch)
    newlist = ilist[0:endsearch]
    for item in newlist:
        if value == "" and item.strip(", ") == "":
            continue
        value += item
    return value.strip(",; ")

def findnextbold(tree, search, buffer=1, skipkeywords=True):
    nextbold = search
    if skipkeywords:
        while nextbold in [search, "Trigger", "Effect", "Damage", "Saving Throw", "Critical Success", "Success", "Failure", "Critical Failure", "Frequency", "Constant"]:
            nextbold = tree.xpath(f'//*[text()="{ search }"]//following::b[{buffer}]//text()')[0]
            buffer += 1
    else:
        nextbold = tree.xpath(f'//*[text()="{ search }"]//following::b[{buffer}]//text()')[0]
    return nextbold

if __name__ == "__main__":
    main()