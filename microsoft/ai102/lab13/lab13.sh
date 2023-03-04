#!/bin/bash
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate ai-102
pip install botbuilder-core
pip install asyncio
pip install aiohttp
pip install cookiecutter==1.7.0
scriptPath=$(dirname $(readlink -f $0))
bot_name=TimeBot
bot_description="A bot for our times"
pushd $scriptPath
cookiecutter --no-input https://github.com/microsoft/botbuilder-python/releases/download/Templates/echo.zip bot_name="$bot_name" bot_description="$bot_description"
cp bot.py TimeBot/bot.py
if [ ! -f BotEmulator.AppImage ]; then
    wget https://github.com/microsoft/BotFramework-Emulator/releases/download/v4.14.1/BotFramework-Emulator-4.14.1-linux-x86_64.AppImage -O BotEmulator.AppImage
    chmod +x BotEmulator.AppImage
fi
cd TimeBot
python app.py
popd