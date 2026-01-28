# SETUP INSTRUCTIONS

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

### **4- Set up OLLAMA model running locally**

```
ollama serve
```

### **5- Start the discord bot**

```
source .venv/bin/activate
python bot.py
```
