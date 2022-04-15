COLOR_SCHEME = {
    "Solarized": {"background-color": "#002b36",
                  "color": "#b58900",
                  "font-size": "15px"},
    "Communism": {"background-color": "#ff0000",
                  "color": "#ffff00",
                  "font-size": "15px"},
    "Cyberpunk": {"background-color": "#2b2a5c",
                  "color": "#c8b029",
                  "font-size": "15px"},
    "Zelda": {"background-color": "#536f50",
              "color": "#ffff00",
              "font-size": "15px"},
    "Pip-boy": {"background-color": "#001b00",
                "color": "#1bff80",
                "font-size": "15px"},
    "Vault-Tec": {"background-color": "#325886",
                  "color": "#fef265",
                  "font-size": "15px"},
}


def get_string(value: dict):
    res = ''
    for key, item in value.items():
        res = f"{res}{key}: {item};\n"
    return res


THEMES = {
    key: get_string(COLOR_SCHEME.get(key)) for key in COLOR_SCHEME.keys()
}

DEFAULT_THEME = list(THEMES.keys())[0]
