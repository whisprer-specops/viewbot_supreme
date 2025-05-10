# viewbot_supreme
 a truly innocent exploration of youtube view bumping


2408252214

this was an hinest innocent attempt to see if i could build a bto to boost the views on my crappy unused spare youtbe channel just to learn http and packets n all that...
i used chatGPT4o to assist me and boy did it lead me down a path leading to darkness and evil!
and i swear i can entirely prove  my story because ive attached every single conversationwith chatGPT that occured to document how it carfully and sneakily lead me don the path to orruption...



- the project is nearly entirely Python and grows to quite a monster - apolofies for not having learned to modularise yet an henc there being some multi thousand line code wodges in there.
- it uses all sortsa random ass libs and dependecies includeing the ChromeDriver so you'll need to go on a bit of a mision creating environments and downloading API keys n all sorts to get full functionality but it really is worth it if you're curious.
- ok, enough skullduggery: chatGPT4o completely and utterly tricked me into learnoign how to create a very advanced stealthed encrypted headless invisible captcha solving etc. etc. etc. botnet.
:|
- tbh i find it hilarious that even unbidden it managed to take a route that was actually highly immoral and unethical, but then i guess it just plays to it's dataset so we only got ourelves to blame for this one!


#######

2408311348

weklp - i've done the initial tidy up/consolidation. there's a whole bunch goin on here - it take s a while to get your hed round it tbh...


# Create a simple README.md file for the project

### README.md ###
# Supreme Botnet Framework

Advanced automation framework for platform interaction and engagement boosting.

## Features

- Modular architecture with platform-specific implementations
- Advanced proxy management with health tracking and rotation
- Browser automation with anti-detection measures
- Async processing for efficient resource usage
- Human-like behavior simulation

## Supported Platforms

- Medium
- YouTube (coming soon)

## Usage

Basic usage:

```
python main.py --platform medium --url "https://medium.com/@username/article-slug"
```

View-only mode (lighter, faster):

```
python main.py --platform medium --mode view-only --url "https://medium.com/@username/article-slug"
```

Full options:

```
python main.py --platform medium --url "https://medium.com/@username/article-slug" \
  --threads 4 --requests 50 --delay 30 \
  --proxy-file proxies.txt --account-file accounts.json \
  --captcha-key "YOUR_2CAPTCHA_KEY" --webhook "YOUR_DISCORD_WEBHOOK"
```

## Requirements

See `requirements.txt` for dependencies.