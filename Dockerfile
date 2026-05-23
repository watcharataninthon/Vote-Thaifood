FROM python:3.11-slim
WORKDIR /app
COPY food_vote_server.py .
COPY food-vote.html .
EXPOSE 8080
CMD ["python3", "food_vote_server.py"]
