# start with a base image
FROM python:3.11

# Set a neutral working directory. This is a common best practice.
WORKDIR /app

# Copy only the requirements file first to leverage Docker's layer caching.
# This layer will only be rebuilt if requirements.txt changes.
COPY requirements*.txt ./

# Installing the necessary dependencies
RUN pip install --upgrade pip && pip install -r requirements-dev.txt

# Now, copy the rest of the application code.
# This layer will be rebuilt whenever your source code changes.
COPY . .

# Exposing Application Port
EXPOSE 8000 

# Running the startup command
CMD ["uvicorn", "src:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
