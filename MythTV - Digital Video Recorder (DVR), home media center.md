#### The Goal:
This project is so I can run a server version of [MythTV](https://www.mythtv.org/detail/mythtv) and be able to connect to it from a pi that I plan to use as a media player connected to my livingroom TV. I've so far tested this by running server version as a docker image on a computer in my equipment closet connected to my TV Antena. I was able to install MythTV Client on my working PC (Ubuntu 18.04) and it seems to work well.

##### MythTV: (original installation December 2019)
##### version: (mythbackend version:  [v29.1])
##### docker image/repo: https://hub.docker.com/r/apnar/mythtv-backend
##### github repo: https://github.com/apnar/docker-image-mythtv-backend
##### Host: Ubuntu 18.04 Desktop version running on NUC

#### Outline of the project (client/server model)
 - Uses --net in `docker run` command not sure if I want to change this or not depending on the host it's running on, but it works as is.
 - Had to add arguments in `docker run` command to recognize my TV card.
 - To add additional space on the NUC Host, symbolic link to an external hard drive to hold files on the host (/home/larryw/mythtv/mythrecordings)
 - mythtv-frontend (client) installed on working personal computer via package manager.
  - Docker author states that it was updated to v29. My Ubuntu client connected, but I tried from a Mac with older client version and it would not connect.
 - **Image author states there is no security built in to run on secure network, possibly change this to be more secure/public**

The following run command names the container, set network to the host, give the host a name, map the TV tuner device, map the database to volumes on the host for persistence:
```
docker run -d --name mythtv --net=host -h mythtv.local --device=/dev/vbi0:/dev/vbi0 --device=/dev/dvb:/dev/dvb -v /home/larryw/mythtv/mythdb:/var/lib/mysql -v /home/larryw/mythtv/mythrecordings:/mnt/recordings -v /etc/localtime:/etc/localtime:ro apnar/mythtv-backend
```
#### ToDo
  - Look into removing --net command in the future to eliminate contention with other services on host?
  - Test with Windows/Mac to get a version of MythTV that can work with more clients.
    - Possibly clone an image that works for me into my own docker repo.
  - Move forward on TV Project to get a client connected to Livingroom TV.
