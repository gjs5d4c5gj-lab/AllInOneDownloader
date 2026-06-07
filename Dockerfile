# Python muhitini yuklaymiz
FROM python:3.10-slim

# Serverga FFmpeg dasturini majburlab o'rnatamiz
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Ishchi katalogni belgilaymiz
WORKDIR /app

# Kutubxonalarni ko'chirib o'rnatamiz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Hamma kodlarimizni serverga nusxalaymiz
COPY . .

# Botni ishga tushiramiz
CMD ["python", "bot.py"]
