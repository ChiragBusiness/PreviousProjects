FROM selenium/standalone-chrome



RUN sudo apt-get update
RUN sudo apt-get install -y python3-pip

COPY requirements.txt .
RUN pip install -r requirements.txt

ENV SE_NODE_SESSION_TIMEOUT=1800
ENV SE_SCREEN_HEIGHT=1150 
#screen height was 1150 before change
ENV SE_SCREEN_WIDTH=2048
#screen width was 2048 before
ENV SE_START_XVFB=false
ENV START_XVFB=false

RUN mkdir /home/seluser/LiquidMarketplace
RUN mkdir /home/seluser/logging
WORKDIR /home/seluser/LiquidMarketplace
COPY functions_filled_orders.py functions_main.py main.py test.py /home/seluser/LiquidMarketplace/
#COPY err.txt logs.txt  /home/seluser/logging/

#RUN sudo chown -R seluser /home/seluser/logging
#CMD sudo chown -R seluser /home/seluser/logging && /bin/bash

CMD sudo chown -R seluser /home/seluser/logging && python3 -i main.py

#ENTRYPOINT [ "/bin/sh",  "sudo", "chown", "-R", "seluser", "/home/seluser/logging"]

#RUN sudo chmod 777 /home/seluser/LiquidMarketplace  #####this does not work because when the bind mount is created it becomes root user permission, the solution is to only do chmod inside of the container 

#add -p above if we want to make parent directories aswell if they dont exist

#CMD ["sleep 5", "python3", "to_run.py"]
#CMD sleep 5

#RUN pip install selenium
#RUN pip install numpy
