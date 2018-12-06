========== CRAWLING HOWTO ===========

1.  Start Docker Engine
On windows, run "Docker Quickstart Terminal" as Administrator

2a. Build docker
open Windows PowerShell as Administrator, run these commands:
> cd D:\crawler
> docker build -t crawling .

2b. Start Crawler Service
You need to create folder "shared/logs" & "/shared/data" in C:\Users
Then on Windows PowerShell (as Administrator), run command:
> docker run -v "/c/Users/shared/logs:/app/logs" -v "/c/Users/shared/data:/app/data" --rm -d -p 6800:6800 -p 9000:9000 crawling

3. Run Crawling Jobs
After crawler service is running, you can then run crawling job using http clients tools such as curl or Postman.
please refer to README.pdf to see example how to run crawling job.

4. Stop Crawler
Still on Windows PowerShell (as Administrator), run command:
> docker ps -a  // get container_id
> docker container stop {container_id}
