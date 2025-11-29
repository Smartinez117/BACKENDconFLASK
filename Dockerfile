FROM python:3.13.3
WORKDIR /app
COPY . /app
RUN pip install uv
RUN uv sync
EXPOSE 80
CMD ["uv", "run", "python", "./app.py"]
