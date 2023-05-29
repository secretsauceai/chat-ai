FROM python:3.10-slim-buster

RUN mkdir /text_generation_api
WORKDIR /text_generation_api

RUN pip install --upgrade pip

RUN pip install --no-cache-dir torch torchvision torchaudio -f https://download.pytorch.org/whl/cpu/torch_stable.html

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./run_inference_api.py .

CMD ["python", "run_inference_api.py"]
