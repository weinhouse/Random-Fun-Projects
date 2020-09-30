### Vesync [smart outlets](http://www.vesync.com/outlets)

It's recommended to unplug a battery from it's charger within an hour or so of full charge to prolog it's life. I wanted a script to monitor my new e-bike battery and have it turn off the charger within that time frame. I found these reasonably priced [outlets](http://www.vesync.com/outlets) which also has [Python API](https://pypi.org/project/pyvesync-v2/). The goal was to see when watts output are below a certain threashold indicating that charging is complete and to shut of the smart outlet to maximize the batteries life. I wanted to have this all self contained in a Docker image to be easliy deployed anywhere. I may use this script for other power tool batteries in the future.

#### Here is how I use this script:
- vesync outlet is plugged into the wall and connected to battery charger.
- Plug charger into battery and push the button on vesync outlet turning it on.
- Cron job runs the script monitor_outlet.py every 5 minutes to see if the outlet is pushing watts.
  - once watts is above threashold, the script enters a loop and collects data every 10 minutes.
  - when the watts drop below the threashold indicating that the battery has been charged.
    - logging info is collected.
    - email containing the charging time and logging information is sent.

Any comments on process or code is always appreciated!

#### A few thoughts and tips to help you if you would like to try the same.
- Grab a vsync outlet and set it up with their app.
- Generate Docker image with included docker file, it has [vsync_v2 api](https://pypi.org/project/pyvesync-v2/). might be worth installing on your local machine and experimenting first.
  - You will need to generate a Deployment Key on GitHub and have that key in the docker directory to be copied to your image.
  - `docker build -t weinhouse/home_python_scripts:r1 .`
- monitor_outlet.py script is run via cron or other process to see if outlet is pushing watts, may want to check every 5 minutes or so
  - Edit this file with the threshold based on what the charger pulls.
  - I have 600 seconds for sleep time, but you can change this.
  - mailer module is used to mail. feel free to set up your own free sendgrid account and steal this script :-)
  - passwords are entered as environmental variables which I enter with my docker run command:
    - `docker ps | grep 'wweinhouse/home_python_scripts' > /dev/null || docker run -d --rm --name ve_sync_outlets -e sendgridKey='<Sendgrid Key>' -e vesyncPassword='<vesync pw>' -e RUN_SCRIPT='/vesync/evaluate_power.py' weinhouse/home_python_scripts:r1 /usr/local/bin/startup.sh
- Check out the Docker file you will note that the startup.sh script and deployKey(ssh-key set up as deployment key at github)
