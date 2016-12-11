docker stop bsnp-code-tester
docker rm bsnp-code-tester
docker run --name=bsnp-code-tester -p 8000:8000 -d bsnp-code-tester
