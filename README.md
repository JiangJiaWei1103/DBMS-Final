# DBMS-Final
## A simple dbms for stock brokerage

### Clone the repo
* `git clone https://github.com/JiangJiaWei1103/DBMS-Final.git`
* cd into the repo.

### Setup the virtual env
* Create conda virtual env.
  * Run `conda create -n <env_name> python=3.8 -y`
* Activate virtual env.
  * Run `conda activate <env_name>`
* Install packages.
  * Run `pip install -r requirements.txt`

### Run web application
* Start server.
  * Run `uvicorn app:app --reload --port <port_num>`
