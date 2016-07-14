FROM python:3.5.2

RUN apt-get update && apt-get install cron -y && pip install configobj influxdb python-nest pytz

VOLUME /config

# Add our crontab file
ADD ./config/crontab /etc/cron.d/crontab
ADD ./config/nest_push.py /src/nest_push.py

# Use the crontab file
RUN chmod 0644 /etc/cron.d/crontab && chmod +x /src/nest_push.py && touch /var/log/cron.log

# Start cron
CMD cron && tail -f /var/log/cron.log
#CMD ["python", "/src/nest_push.py"]