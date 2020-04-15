### [rosetta@home](https://en.wikipedia.org/wiki/Rosetta@home)

One can help with covid research processing by joining a project named [rosetta@home](http://boinc.bakerlab.org/rosetta/) PART OF THE UW INSTITUTE FOR PROTEIN DESIGN (University of Washington) https://www.bakerlab.org/

I heard about this project while reading an article about setting it up on a Rasperry pi. I've been experimenting with pi's to do home automation type work in my off grid solr shed and figured it would be a good place to run my node. Although my little pi 3 (Model B Rev 1.2) hasn't much processing power, it seemed as though it would be an interesting project to try and figured that every little bit helps. following are the steps I went through:

- Article described running via a gui, I wanted to run headless using ubuntu server for [Raspberry Pi](https://ubuntu.com/download/raspberry-pi)
- Boinc a project sponsored at http://boinc.berkeley.edu
  - Set up account
  - Install my nodes [software](https://boinc.berkeley.edu/wiki/User_manual). For headless setup there is a "boinccmd" command line tool.
- rosetta@home a project sponsered at http://boinc.bakerlab.org/rosetta/
  - Set up account
  - join the rosetta@home project (in my case using command line tool)
    - In your case, you may want to to with the GUI version which seems pretty straight forward.
- There are several monitoring tools, I'm planning on trying https://www.boincstats.com/
  - Set up account
  - Spent a bit of time checking it out while waiting for a project.

#### Learnings:
This has so far been in interesting project. If you would like to try, might be easier to just download the GUI application and start contributing.

### Followup:
HaHaHa, 5 days later and I've been sent some tasks. Sooooo cool not sure if this is actually helping with the Covid-19 effort, but fun to see that my little pi is able to contribute. There were 3 completed, 2 failed and 3 running tasks. The pi is a quad core and the project is using 3 of the 4 as I type. I went to the shed and the heat sink on the cpu seems a bit warm, but I don't really have anything at this point to compare. Anyway even more entertaining was to get my certificate and see that I contributed 520 Cobblestones. After a bit of readding I somewhat understand what that is :-)
![Certificate](https://github.com/weinhouse/Random-Fun-Projects/blob/master/images/certificate.png)

below I have some free flowing notes for myself which might come in handy for you.
```
Imaging tool on my linux box was crashing back to good old dd:
dd if=ubuntu-18.04.4-preinstalled-server-arm64+raspi3.img of=/dev/sdd bs=32M

Client runs as a service:
systemctl status boinc-client -l

boinccmd command line tool:
--project_attach URL auth
    boinccmd --project_attach http://boinc.bakerlab.org/rosetta/ <my authentication>
boinccmd --get_project_status
boinccmd --get_state
boinccmd --project http://boinc.bakerlab.org/rosetta/ detach_when_done
boinccmd --join_acct_mgr -- Seems broken, may be useful, possibly check into it some day.

boinc binary to start daemon and some other stuff boinc --help
```
