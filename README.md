
### The purpose of this repository is to document and share my personal development journey.  
### Through open-source collaboration and transparent technical sharing, supporting technical innovation. 


English version:

| Model       | Training Steps | Performance                     | Data | Task                           | Notes                                                                 |
|-------------|----------------|---------------------------------|------|--------------------------------|----------------------------------------------------------------------|
| ACT         | 50000          | Very good, almost 100%          | 50x2 | Pick objects from A to B       |                                                                      |
| SmolVLA     | 80000          | Very poor, hard to complete once | 50x2 | Pick objects from A to B       | Trained from scratch, 30k steps for fitting                         |
| ACT         | 80000          | Success rate 80%-100%           | 50x2 | Pick clothes from A to washing machine | 60k deployments, sometimes performance drops<br>Afternoon deployments nearly 100%<br>Morning tests also very good, close to 100% |
| SmolVLA_base | 60000         | Poor, can pick but rarely complete | 50x2 | Pick clothes from A to washing machine | Pretrained model, 20k steps fitting                                  |
| pi0fast     | 30000          | Very poor, cannot even pick      | 50x2 | Pick clothes from A to washing machine | Pretrained, 30k steps for initial fitting; model parameters huge     |
| ACT         | 100000         | Excellent, almost 90%-100%      | 62x3 | Pick natural clothes from laundry basket to washing machine | 90-100k steps fitting, last deployment, 3 cameras<br>Can sequentially pick clothes into washing machine; arm movement is natural |
| pi0fast     | 80000          | Very poor, HF pi0 model seems problematic | 62x3 | Pick natural clothes from laundry basket to washing machine | Deployed after ACT_100k with 90% success; many factors excluded; pi0fast last deployment = arm almost frozen;<br>40000 steps deployment also very poor |






## Demo 视频

点击观看 Demo 1:(https://www.youtube.com/shorts/5soQiujo6fU) 

点击观看 Demo 2:(https://www.youtube.com/shorts/BxUSwnyWUZQ)

 

点击缩略图跳转到 YouTube：

[![Demo 1](https://www.youtube.com/shorts/5soQiujo6fU/0.jpg)](https://www.youtube.com/shorts/5soQiujo6fU) 





[![Demo 2](https://www.youtube.com/shorts/BxUSwnyWUZQ/0.jpg)](https://www.youtube.com/shorts/BxUSwnyWUZQ)




## so101 Leader Teleoperate so101 Followwer: Data Collection, Training, and Deployment

##### here is the information I will add later




## so101 Teleoperate piper: Data Collection, Training, and Deployment



### practical experiments 



 
### Hardware Setup and Check  

#### Check USB interfaces  
Run the following commands to check USB interfaces, mainly for **so101_leader arm** (based on my actual test):  

```bash
ls -l /dev/ttyACM*
sudo chmod +666 /dev/ttyACM*
```

---

#### Piper Interface Setup  

Navigate to the Piper SDK directory:  

```bash
cd /home/paris/X/piper/piper_sdk
```

Find all CAN ports:  

```bash
bash find_all_can_port.sh
```

Activate CAN port:  

```bash
bash can_activate.sh can0 1000000
```

Set video device permissions:  

```bash
sudo chmod 666 /dev/video*
```

---

#### Verify Camera Devices  

List available video devices:  

```bash
ls -l /dev/video*
```

Check camera index with `ffplay`:  

```bash
ffplay -f v4l2 -input_format mjpeg -video_size 640x480 -framerate 30 -i /dev/video0
```








