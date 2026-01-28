# SETUP INSTRUCTIONS

### **0- Contact information**

```
caleb.n.dickson@gmail.com
```

**If you already have UV installed, skip first step**

### **1- Install UV, if not already**

```bash
brew install uv
```

_Verify installation_

```bash
uv --version
```

### **2- Create and activate virtual enviorment**

```bash
uv venv
source .venv/bin/activate
```

### **3- Download all dependencies**

```
uv pip install -r requirements.txt
```

### **4- Setting up Google Cloud Client**

```
1- Create new project
2- Enable Google Tasks API and Google Calendar API as services
3- Add yourself as a test user for the application
4- Create new credentials with OAuth 2.0 Client
5- Download the client seceret
6- Paste .json file into root directory
7- Rename to credentials.json
8- Run 'python test_google_oauth.py'
9- Successfully log in and authorize
```

### **5- Set up OLLAMA model running locally OR use openai api**

### **Default is set up for openai api call, switch on line 381 of bot.py**

```
ollama serve
ollama pull <model_name>
```

### **6- Start the discord bot**

```
source .venv/bin/activate
python bot.py
```

## Commands:

```
/help -> Returns list of
/ping -> Check if the bot is active
/add <event/task> -> Add an event or task to google calendar
/list -> List today's events and tasks
/done <item_name> -> Will mark an item as complete
/delete <item_name> -> Deletes an item from calendar / tasks
/canvas_sync -> Sync your canvas assignments to Google Tasks
```

## Example .env:

```
DISCORD_TOKEN="your_discord_token_here"
OPENAI_API_KEY="your_openai_api_key_here"
CANVAS_BASE_URL="your_canvas_base_url_here"
CANVAS_TOKEN="your_canvas_token_here"
```

## Demo Video:

![Demo](assets/demo.gif)

## Getting Data To Run:

```
DISCORD_TOKEN -> Discord developer portal when you create your bot
OPENAI_API_KEY -> OpenAI API portal when you create an API key
CANVAS_BASE_URL -> The link for your canvas home page, eg: https://<your_school>.instructure.com/
CANVAS_TOKEN -> Canvas Dashboard, Settings, Approved Integrations, New Access Token
GUILD_ID -> This is your server id, right click on your discord server then copy id
```
