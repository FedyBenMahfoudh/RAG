# mini-rag

This is a minimal implementation of the RAG model for question answering.


## Requirements

- Python 3.8 or later


### (Optional) Setup you command line interface for better readability

```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```

### (Optional) Run Ollama Local LLM Server using Colab + Ngrok

- Check the [notebook](https://colab.research.google.com/drive/1k4YdxuJDSWEgkIhRhYqxB45ZCf-Dhito?usp=sharing)

## Steps to run
#### 1) Install Python using MiniConda

1) Download and install MiniConda from [here](https://docs.anaconda.com/free/miniconda/#quick-command-line-install)
2) Create a new environment using the following command:

```bash
$ conda create -n rag python=3.10
```
3) Activate the environment:
```bash
$ conda activate rag
```

### 2) Install the required packages

```bash
$ pip install -r requirements.txt
```

### 3) Setup the environment variables

```bash
$ cp .env.example .env
```

Set your environment variables in the `.env` file. Like `OPENAI_API_KEY` value.

## 4) Run Docker Compose Services

```bash
$ cd docker
$ cp .env.example .env
```

- update `.env` with your credentials



```bash
$ cd docker
$ sudo docker compose up -d
```

## 5) Run the FastAPI server

```bash
$ uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

## 6) TEST THE ENDPOINTS POSTMAN Collection

Download the POSTMAN collection from [RAG.postman_collection.json]
