from django.core.cache import cache
from django.http import Http404
from models import *
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.conf import settings
import os
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page


@never_cache
def index(request):
    games = cache.get('games')
    if not games:
        games = Game.objects.all().order_by('name')
        cache.set('games', games, 60*60*24)

    for game in games:
        modes = GameMode.objects.filter(game=game).order_by('name')
        for mode in modes:
            maps = Map.objects.filter(game=game, gameMode=mode).order_by('name')
            setattr(mode, 'maps', maps)
        setattr(game, 'modes', modes)

    return render(request, 'tacsketch/tac.html', {'games': games})


@cache_page(60*60*24*3)  # Cache for 3 days
def icons(request):

    response_data = {}

    for folder in os.listdir(settings.ICONS_ROOT):
        if os.path.isdir(settings.ICONS_ROOT + "/" + folder):

            image_list = []

            for file in os.listdir(settings.ICONS_ROOT + "/" + folder):
                if os.path.isfile(settings.ICONS_ROOT + "/" + folder + "/" + file):

                    if file.find("_b.png") != -1 or file.find("_b.jpg") != -1:

                        filename = file
                        thumbnail = file.replace("_b.", "_t.")

                        if request.is_secure():
                            scheme = 'https://'
                        else:
                            scheme = 'http://'
                        start_uri = scheme + request.get_host()
                        containsNumbers = False
                        vocals = "aeiouy"
                        nameList = file[0:len(file)-6].split("_")
                        newNameList = []

                        for name in nameList:
                            for i in name:
                                if i.isdigit():
                                    containsNumbers = True
                                    break
                            if containsNumbers or ("counter" in folder.lower() and len(name) <= 3):
                                name = name.upper()
                            elif "-" in name:
                                names = name.split("-")
                                for i in range(len(names)):
                                    names[i] = names[i].title()
                                name = "-".join(names)
                            else:
                                hasVocals = False
                                for i in name:
                                    if i in vocals:
                                        hasVocals = True
                                        break
                                if hasVocals:
                                    name = name.title()
                                else:
                                    name = name.upper()
                            containsNumbers = False
                            newNameList.append(name)

                        name = " ".join(newNameList)

                        image_data = {
                            'name': name,
                            'thumbnail': start_uri + "/static/icons/" + folder + "/" + thumbnail,
                            'image': start_uri + "/static/icons/" + folder + "/" + filename
                        }
                        image_list.append(image_data)

            game_name = folder.replace("_", " ").title()
            response_data[game_name] = image_list

    return HttpResponse(json.dumps(response_data, sort_keys=True), content_type="application/json")


@csrf_exempt
def save_tac(request):
    if request.method == "POST":
        user = request.user
        name = request.POST['name']
        gameMap = request.POST['map']
        fabricData = request.POST['fabric']
        linesData = request.POST['lines']

        try:
            map = Map.objects.get(id = int(gameMap))
            obj = TacSave.add_object(name, user, map, fabricData,linesData)
            return HttpResponse("True")
        except:
            return HttpResponse("False")

    else:
        raise Http404


def load_tac_list(request):
    try:
        response_data = {}

        tacs = TacSave.objects.filter(user = request.user).order_by('datetime')
        for tac in tacs:
            response_data[tac.id] = {'id':tac.id, 'name':tac.name, 'mapID': tac.gameMap.id, 'mapURI': str(tac.gameMap.image), 'mapName': tac.gameMap.name, 'gameName': tac.gameMap.game.name, 'datetime': str(tac.datetime), 'fabric': tac.fabricData, 'lines': tac.linesData}

        return HttpResponse(json.dumps(response_data), content_type="application/json")
    except:
        return HttpResponse("False")


@csrf_exempt
def delete_tac(request):
    try:
        id = request.POST['id']
        obj = TacSave.objects.get(id=id)
        if obj.user == request.user:
            obj.delete()
            return HttpResponse('True')
    except:
        pass

    return HttpResponse('False')


