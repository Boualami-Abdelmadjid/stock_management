FROM harbor.cicd.rain.co.za/docker.io/library/python:3.11.4-slim


# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
# Dont compile
ENV PYTHONDONTWRITEBYTECODE 1
# Streaming output
ENV PYTHONUNBUFFERED 1
# dump tracebacks
ENV PYTHONFAULTHANDLER 1

WORKDIR /app

COPY app/requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app .

# Create and switch to a new user
# UID should be defined explicitly
# otherwise kubernetes returns error with runAsNonRoot set to true
RUN useradd --create-home --home-dir /app --uid 1989 stockmanagementpoc && \
    mkdir /home/.stockmanagementpoc && \
    chown stockmanagementpoc:stockmanagementpoc /home/.stockmanagementpoc

USER 1989


RUN python manage.py collectstatic -v 3 --noinput && \
    python manage.py migrate

CMD [ "python3", "manage.py", "runserver", "0.0.0.0:8000"]
