FROM python:3.10

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt && \
    groupadd user -g 1000 && \
    useradd -m user -u 1000 -g 1000

WORKDIR /usr/src/app

COPY . .

RUN chown -R user:user .

USER user

CMD ["python", "main.py", "-c", "config.yml"]
