docker build -t yorkregistry.azurecr.io/aisummarizer:latest .

 docker run -p 5000:5000 yorkregistry.azurecr.io/aisummarizer:latest
 docker push yorkregistry.azurecr.io/aisummarizer