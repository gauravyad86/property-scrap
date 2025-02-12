FROM python:3.10

WORKDIR /home/user/app

RUN apt-get update && apt-get install -y wget unzip curl \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 libnspr4 libnss3 libx11-xcb1 \
    libxcomposite1 libxdamage1 libxrandr2 xdg-utils libgbm1 chromium-driver

RUN wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome.deb || apt-get install -f -y \
    && apt-get install -y google-chrome-stable \
    && rm google-chrome.deb

RUN chmod +x /usr/bin/google-chrome-stable && chmod +x /usr/bin/chromedriver

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt 

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
