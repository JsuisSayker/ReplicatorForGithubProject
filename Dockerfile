FROM python:alpine3.20 as python

WORKDIR /app

RUN python -m venv .venv
RUN source .venv/bin/activate

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

COPY ./.env /app/.env
COPY ./replicate_jira_ticket_to_github_project.py /app/replicate_jira_ticket_to_github_project.py

CMD ["/app/replicate_jira_ticket_to_github_project.py"]