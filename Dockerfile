FROM python:3.10-slim

# Install system-level dependencies
RUN apt-get update && apt-get install -y tesseract-ocr libtesseract-dev

# Set up the Python environment
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# Command to run the application using Uvicorn
CMD ["uvicorn", "niftys:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]