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

### **3- Set up OLLAMA model running locally**

```
# Install Ollama from https://ollama.ai
# Then run:
ollama serve

# In another terminal, pull a model:
ollama pull llama2  # or neural-chat, mistral, etc.
```
