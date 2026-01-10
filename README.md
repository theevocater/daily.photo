# daily.photo

Used to create and update https://daily.photo

## dailyphoto
I use [uv](https://docs.astral.sh/uv/) to manage the python / dependencies. Try this out with:
```
uv sync
uv run dailyphoto --help

OR

uvx git+https://github.com/theevocater/daily.photo --help
```

## Workflow
This tool serves two purposes

* Add and maintain metadata and photos to the config
* Generate the site

### New Photos
* Queue new photos with `dailyphoto queue` to quickly add a huge batch of images starting the next day after the final
date in the config
* Add new images with a specific ordering or two specific dates using `dailyphoto new`. This gives you more control
with some cavests

### Site generation
* `dailyphoto generate` will generate the site up to and including today's date as the index. This means you can add
many images in the future but only get today's dates
