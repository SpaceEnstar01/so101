

| 模型        | 训练steps | 效果                         | 任务                         | 备注                                                                 |
|-------------|-----------|------------------------------|------------------------------|----------------------------------------------------------------------|
| ACT         | 50000     | 很好，几乎100%               | 抓取物品从A到B               |                                                                      |
| SmolVLA     | 80000     | 很差，很难完成一次           | 抓取物品从A到B               | (从0到1训练)，3万次--拟合                                            |
| ACT         | 80000     | 成功率80%-100%               | 抓取衣物从A到洗衣机          | 6万次部署，但是有时候部署效果差；下午部署就性能爆表，成功率接近100%；上午测试效果也非常好，也接近100% |
| SmolVLA_ba e | 60000     | 很差，可以成功抓起但是很难完成一次 | 抓取衣物从A到洗衣机          | 预训练模型，2万次--拟合                                              |
| piofast     | 30000     | 效果奇差，连抓取的动作都没有 | 抓取衣物从A到洗衣机          | 预训练模型，3万次才初现拟合，感觉训练少了；piofast模型参数巨大       |
| ACT         | 100000    | 效果非常好 几乎90%-100%      | 抓取自然衣物从洗衣篮到洗衣机 | 9-10万次拟合，last部署，3个摄像头可以依次将衣服抓取到洗衣机内部     |


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

