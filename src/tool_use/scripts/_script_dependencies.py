SCRIPT_DEPENDENCIES = {
    "cal": [
        "anthropic",
        "google-auth-oauthlib",
        "google-auth",
        "google-api-python-client",
        "pytz",
        "tzlocal",
        "rich",
    ],
    "make-obsidian-plugin": ["rich", "inquirer"],
    "do": [
        # Add dependencies for ai_cli
    ],
    "convert": ["open-interpreter", "anthropic>=0.37.1,<0.38.0"],
}
