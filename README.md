# audio_for_zumers
Self host телеграм бот для ваших знакомых зумеров которые жалуются на длинные голосовые.

Для автоустановки на винде пкм выполнить с помощью powershell setup.ps1 он всё скачает что нужно.

По умолчанию там качается маленькая модель для распознавания на русском, но можно скачать поумнее вот тут https://alphacephei.com/vosk/models архив распаковать и положить в папку чтобы был такой путь audio_for_zumers\model\am,conf,graph...

дальше просто в powershelle в папке проекта запустить venv/scripts/activate.ps1 и потом python main.py