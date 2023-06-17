# Secret Sauce AI chatbot
## Description
A fun project to learn about and use AI chatbots with LLMS. This project covers:
- `text_generation_api`: A simple flask API to generate text with Hugging Face encoder-decoder models and decoder only models. It currently only works with CPU, but will probably be updated to also work with GPU. It includes an SQLite database to store the generated text, the model used, the input prompt, optional pre-prompt, and an optional vote from the user of the response. 
- `telegram_bot`: A telegram bot that uses the `text_generation_api` to generate text and send it to the user. It also allows the user to vote on the generated text.
- `slack_bot`: (WIP) A slack bot made with FastAPI that uses the `text_generation_api` to generate text and send it to the user. It also allows the user to vote on the generated text.
- `docker-compose.yml`: A docker-compose file to run the `text_generation_api` and the `telegram_bot` together. WIP to include the `slack_bot` as well.

## Usage
### `docker-compose.yml`
#### Setup
1. Add your environment variables to the `docker-compose.yml` file:
- `CHECKPOINT`: the model/checkpoint from Hugging Face to use for text generation. I have found that `MBZUAI/LaMini-GPT-124M` works pretty well. I wish I could run the larger `MBZUAI/LaMini-GPT-774M` model, but it is too large for my CPU to run in a reasonable amount of time.
- `PREPROMPT`: the pre-prompt to use for the text generation. It is optional and can be left empty. I have found better results with decoder only models when using a prompt. This doesn't seem to be the case with encoder-decoder models.
- `TEXT_GENERATION_HOST`:`text_generation_api` should be used for docker-compose.
- `PORT`: the port of`text_generation_api` to use.
- `TELEGRAM_BOT_TOKEN`: the token of the telegram bot to use.
2. Run `docker-compose up` to start the `text_generation_api` and the `telegram_bot` together.
3. Test the API with `curl -X POST -H "Content-Type: application/json" -d '{"input_prompt": "Please let me know your thoughts on the given place and why you think it deserves to be visited: \n\"Barcelona, Spain\""}' http://localhost:5000/generate_text` or by sending a message to the telegram bot.
### `text_generation_api`
#### Setup
You can either run it with Python or with Docker.
##### Python
1. Install the requirements with `pip install -r requirements.txt`
2. Set up a `config.toml` file in `chat_ai/config/` or use environment variables.

Example `config.toml` for `text_generation_api`:

```
checkpoint = "MBZUAI/LaMini-GPT-124M"
preprompt = "Below is an instruction that describes a task. Write a response that appropriately completes the request. \n\n### Instruction:\n{instruction}\n\n### Response:\n"
text_generation_host = "127.0.0.1"
port = "5000"
```
3. Run the API with from the `text_generation_api` with `python run_inference_api.py`


4. Test the API with `curl -X POST -H "Content-Type: application/json" -d '{"input_prompt": "Please let me know your thoughts on the given place and why you think it deserves to be visited: \n\"Barcelona, Spain\""}' http://localhost:5000/generate_text`

##### Docker
1. Build the docker image with `docker build -t text_generation_api .` or pull it from Docker Hub with `docker pull bartmoss/text_generation_api`
2. Run the docker image with `docker run -p 5000:5000 text_generation_api` you can pass the environment variables as well with `-e` or `--env-file`.

Example environment variables for `text_generation_api`:

```
CHECKPOINT=MBZUAI/LaMini-GPT-124M
PREPROMPT=Below is an instruction that describes a task. Write a response that appropriately completes the request. \n\n### Instruction:\n{instruction}\n\n### Response:\n
TEXT_GENERATION_HOST="127.0.0.1"
PORT="5000"
```
3. Test the API with `curl -X POST -H "Content-Type: application/json" -d '{"input_prompt": "Please let me know your thoughts on the given place and why you think it deserves to be visited: \n\"Barcelona, Spain\""}' http://localhost:5000/generate_text`

### `telegram_bot`
#### Setup
##### Python
1. Install the requirements with `pip install -r requirements.txt`
2. Set up a `config.toml` file in `chat_ai/config/` or use environment variables.

Example `config.toml` for `telegram_bot`:

```
text_generation_host = "127.0.0.1"
port = "5000"
telegram_bot_token = "token"
```
3. Run the API with from the `telegram_bot` with `python telegram_bot.py`

##### Docker
1. Build the docker image with `docker build -t telegram_bot .` or pull it from Docker Hub with `docker pull bartmoss/telegram_bot`
2. Run the docker image with `docker run telegram_bot` you can pass the environment variables as well with `-e` or `--env-file`.

Example environment variables for `telegram_bot`:

```
TEXT_GENERATION_HOST="127.0.01"
PORT="5000"
TELEGRAM_BOT_TOKEN="token"
```

### `slack_bot`
The slack bot is still a work in progress. It hasn't been dockerized yet and still requires implementation of the voting system. Creating and setting up a slack bot can be tricky.

You will need to get a token for your slack bot. Slack also requires a pretty good amount of set up for their API. You can find more information [here](https://api.slack.com/). It can be a bit confusing with permissions and scopes. Once you have that set up, you will need to do the following:
1. You will need to publically connect your server to slack, you can use ngrok for example: `ngrok http port_number`
2. Run the slack bot, you will need to run FastAPI, for example you can use uvicorn: `uvicorn slack_bot:app --port port_number --reload`
3. Copy the ngrok URL and paste it into the slack bot settings in event subscriptions: `https://<ngrok_url>/slack/events`, verify and save the settings.

It will work both for channels you invite the bot to and direct messages.

## LLMs and experiments
### License warning
This repo's code is licensed under the Apache2 license, but some models used are licensed under the [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) license or may have other licenses. Please make sure you are allowed to use the models for your use case. 

### Pipeline
We use the Hugging Face `pipeline` with either `text2text-generation` or `text-generation` to generate text. The `text2text-generation` pipeline is used for encoder-decoder models and the `text-generation` pipeline is used for decoder only models. 

### Models
#### Decoder only models
I have been mostly experimenting with models from [MBZUAI NLP LaMini-LM](https://github.com/mbzuai-nlp/lamini-lm). I have found that the [LaMini-GPT-124M](https://huggingface.co/MBZUAI/LaMini-GPT-124M) model works pretty well. Likewise, I wish I could run the larger [LaMini-GPT-774M](https://huggingface.co/MBZUAI/LaMini-GPT-774M) model, but it is too large for my CPU to run in a reasonable amount of time.

#### Encoder-decoder models
I have also tried the encoder-decoder [LaMini-Flan-T5-783M](https://huggingface.co/MBZUAI/LaMini-Flan-T5-783M) model, but it didn't work as well as the decoder only models. There may have been an issue when they trained this model, as the max tokens for output seems to be limited to 128 tokens. I have tried to change this, but I haven't been able to get it to work. I tested the same `pipeline` with [flan-t5-base](https://huggingface.co/google/flan-t5-base), and it worked fine up to 512 tokens. Perhaps when they fine-tuned the model, they set the max output tokens to 128 instead of 512. This issue can impact results. I would love to see this model retrained with a larger max output tokens and benchmark this model again.


### Benchmarking
I am currently collecting data from myself and friends to use as a benchmark for the models. This data represents a vast number of tasks an LLM should be able to perform. I am currently collecting data for the following tasks:
- Open Question Answering (OpenQA)
- Text generation (NLG)
- Text classification (NLU)

A user can vote on the quality of the output from the LLM. 

## Next steps
* Test more models
* Finish slack bot
* Onnx support, add script to convert models to onnx, and benchmark onnx models.
* GPU support
* fine-tune models on custom data

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. 
