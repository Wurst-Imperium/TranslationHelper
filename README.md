# TranslationHelper

A tool to help me review pending Wurst Client translations. Not sure if anyone else will find this useful. Maybe some translators will want to analyze their own translations before submitting them. But if you do, please note running all the OpenAI stuff is not free. Analyzing a full translation with the default settings costs about $0.16. You will get a more accurate estimate for each analysis when you run the script.

## Features

- Google-translates the translation back to English, so I can review translations in languages I don't speak. (I used to do this manually for every string, so this is a huge time saver.)

- Uses ChatGPT to quickly highlight strings where the reverse translation differs from the original. (Not perfect, but it helps.)

- Uses ChatGPT to find mentions of Minecraft blocks, items, etc. Then checks those against Minecraft's official translations to find inconsistencies. (I used to not do this at all since it would take too long to do manually.)

- Checks for common mistakes like untranslated strings, miscapitalized Wurst features, and issues with the color codes.

- Highlights names and color codes so it's easier to spot issues with them.

- Includes a "bookmark" (red outline around a row), which can be moved up and down with the arrow keys and keeps its position when the page is reloaded. This helps me keep track of where I left off when I take a break from reviewing a translation.

## Installation

Be warned that this is an internal tool, so not much effort was put into making it beginner-friendly. You will need command line experience, a Python installation, an OpenAI API key, a Wurst Client installation, and knowledge of how to use Wurst's WikiDataExport feature. The installation steps are as follows:

1. Clone this repository.

2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   (I use Python 3.10, but it should work with newer versions too.)

3. Create a wiki data export in Wurst (open Navigator and search "WikiDataExport") and either put it in the root directory of this project or set the `WURST_FOLDER` environment variable to the path of your Wurst folder.

## Usage

```bash
python make_table.py
```

And then open `table.html` in your browser.

If you want to analyze a translation that isn't a pull request yet, save it as `pending.json` in the root directory of this project and create a file called `pending_lang.txt` with the language code (e.g. `en_us`) in it. Then run the script.
