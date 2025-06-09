import os
from celery import Celery
from celery.schedules import crontab # For periodic tasks

# It's crucial that the broker URL is correctly configured for Docker networking
# 'rabbitmq' will be the hostname of the RabbitMQ service in docker-compose
broker_url = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")
# Using Redis as a result backend is common, 'redis' for docker-compose service hostname
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery(
    "worker", # Can be any name
    broker=broker_url,
    backend=result_backend,
    include=["app.tasks"] # List of modules to import tasks from
)

# Optional Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],  # Ignore other content
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Example: Add a periodic task (Celery Beat schedule)
    # beat_schedule={
    # 'fetch-emails-every-5-minutes': {
    # 'task': 'app.tasks.periodic_fetch_all_emails',
    # 'schedule': crontab(minute='*/5'), # Run every 5 minutes
    #    },
    # }
)

# To run Celery Beat, you would typically run 'celery -A app.core.celery_config beat -l info'
# To run a worker, 'celery -A app.core.celery_config worker -l info'

# For Celery Beat with default scheduler using the schedule above:
# celery_app.conf.beat_schedule = {
# 'fetch-emails-every-5-minutes': {
# 'task': 'app.tasks.periodic_fetch_all_emails', # Make sure this task name is correct
# 'schedule': crontab(minute='*/5'),
# # 'args': (16, 16) # Example arguments for the task
#    },
# }
