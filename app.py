# Import packages
from db import SessionLocal, engine
from sqlalchemy.orm import Session
from fastapi import status, FastAPI, Request, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.responses import RedirectResponse

from models import Base, Bank, Client, Ordering, SecurityAccount, SettlementAccount
from utils import obj2dict

# pydantic data model definitions
class SqlCmdReq(BaseModel):
	SqlCmd: str

class ClientReq(BaseModel):
	SSN: str
	Name: str
	Birthday: str
	Phone: str
	Occupation: str
	SetAccNo: str
	SecAccNo: str

class BalanceReq(BaseModel):
	AccNum: str
	Balance: int

class ManagedClientsReq(BaseModel):
	ManagerSSN: str
	Clients: str

class OrderingClientsReq(BaseModel):
	StockTicker: str
	Ordered: str

class StatisticsReq(BaseModel):
	StockTicker: str

class PopularStocksReq(BaseModel):
	Month: str
	CountThreshold: str

class DeleteClientReq(BaseModel):
	SSN: str

# Function definitions
def get_db():
	try:
		db = SessionLocal()
		yield db
	finally:
		db.close()

def get_query_results(sql_cmd, db):
	query_results = db.execute(sql_cmd)

	return {
		"msg": "Query success",
		"attributes": query_results.keys(),
		"relation": query_results.fetchall()
	}

# Configuration
app = FastAPI()
Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")

# Router definitions
@app.get("/")
def index(req: Request, db: Session=Depends(get_db)):
	# Query the whole table when loading the home page
	clients = db.query(Client).all()
	clients = obj2dict(clients)

	return templates.TemplateResponse("panel.html", {
			"request": req,
			"attributes": Client.__table__.columns.keys(),
			"relation": clients
		})

@app.get("/render-table/{rel_name}")
def panel(rel_name: str, db: Session=Depends(get_db)):
	# Query the whole table based on the specified relation name
	if rel_name == "client":
		model = Client
	elif rel_name == "bank":
		model = Bank
	elif rel_name == "ordering":
		model = Ordering
	elif rel_name == "sec-acc":
		model = SecurityAccount
	elif rel_name == "set-acc":
		model = SettlementAccount
	
	query_results = db.query(model).all()
	query_results = obj2dict(query_results)

	return {
		"state": "success",
		"attributes": model.__table__.columns.keys(),
		"relation": query_results
	}

@app.post("/sql-cli")
def sql_cli(sql_cmd_req: SqlCmdReq, db: Session=Depends(get_db)):
	# Handle CLI SQL commands
	cmd = sql_cmd_req.SqlCmd
	if cmd.startswith("INSERT") or cmd.startswith("insert"):
		# Scenario - inserting new client  
		target_table = "Client"
	elif cmd.startswith("UPDATE") or cmd.startswith("udpate"):
		# Scenario - updating balance in the specified settlement account 
		target_table = "SettlementAccount"
	elif cmd.startswith("DELETE") or cmd.startswith("delete"):
		# Scenario - deleting the client wanting to terminate the contract
		target_table = "Client"
	else:
		return get_query_results(cmd, db)

	db.execute(cmd)
	db.commit()
	return get_query_results(f"SELECT * FROM {target_table}", db)

@app.post("/client")
def create_client(client_req: ClientReq, db: Session=Depends(get_db)):
	# Create a new client (INSERT).
	client = Client()
	client.SSN = client_req.SSN
	client.Name = client_req.Name
	client.Birthday = client_req.Birthday
	client.Phone = client_req.Phone
	client.Occupation = client_req.Occupation
	client.SetAccNo = client_req.SetAccNo
	client.SecAccNo = client_req.SecAccNo
	db.add(client)
	db.commit()

	return get_query_results("SELECT * FROM Client", db)

@app.delete("/client")
def delete_client(delete_client_req: DeleteClientReq, db: Session=Depends(get_db)):
	# Delete the client terminating the contract with the brokerage (DELETE).
	SSN = delete_client_req.SSN
	db.execute(f"""DELETE FROM Client
				   WHERE SSN=\"{SSN}\";""")
	db.commit()

	return get_query_results("SELECT * FROM Client", db)

@app.put("/acc/balance")
def update_balance(balance_req: BalanceReq, db: Session=Depends(get_db)):
	# Update balance value in the specific settlement account (UPDATE).
	AccNum = balance_req.AccNum
	Balance = balance_req.Balance
	db.query(SettlementAccount).filter(
		SettlementAccount.AccNum==AccNum
	).update({
			"Balance": Balance 
		})
	db.commit()

	return get_query_results("SELECT * FROM SettlementAccount", db)

@app.post("/search-clients")
def get_managed_clients(managed_clients_req: ManagedClientsReq, db: Session=Depends(get_db)):
	# Search for the clients managed by the specified security specialist,
	# or those not (IN/NOT IN).
	ManagerSSN = managed_clients_req.ManagerSSN
	Clients = managed_clients_req.Clients   # Whether to get clients under management or those out of management
	managed = "" if Clients == "Yes" else "NOT"	

	# SQL command
	cmd = f"""SELECT * 
		      FROM Client 
			  WHERE Client.SecAccNo {managed} IN (
				  SELECT AccNum 
				  FROM SecurityAccount
				  WHERE ManagerSSN=\"{ManagerSSN}\"
			  );"""

	return get_query_results(cmd, db)

@app.post("/search-ordering-clients")
def get_ordering_clients(ordering_clients_req: OrderingClientsReq, db: Session=Depends(get_db)):
	# Search for the clients having ordered the specified stock,
	# or those not (EXISTS/NOT EXISTS).
	StockTicker = ordering_clients_req.StockTicker
	Ordered = ordering_clients_req.Ordered   # Whether to get clients who have ordered this stock or those haven't
	ordered = "" if Ordered == "Yes" else "NOT"

	# SQL command
	cmd = f"""SELECT * 
		      FROM Client 
			  WHERE {ordered} EXISTS (
				  SELECT * 
				  FROM Ordering
				  WHERE Client.SecAccNo=Ordering.SecAccNo
				  AND StockTicker={StockTicker}
			  );"""

	return get_query_results(cmd, db)

@app.post("/get-ordering-statistics")
def get_ordering_statistics(statistics_req: StatisticsReq, db: Session=Depends(get_db)):
	# Calculate and return the statistics of the specified stock 
	# (COUNT, SUM, MAX, MIN, AVG).
	StockTicker = statistics_req.StockTicker

	# SQL command
	cmd = f"""SELECT COUNT(*) AS TotalOrdering,
					 SUM(Volume) AS TotalVolume,
					 MAX(Volume) AS MaxVolume,
					 MIN(Volume) AS MinVolume,
					 AVG(Volume) AS AvgVolume
		      FROM Ordering
			  WHERE StockTicker={StockTicker};"""
	
	return get_query_results(cmd, db)

@app.post("/get-popular-stocks")
def get_popular_stocks(popular_stocks_req: PopularStocksReq, db: Session=Depends(get_db)):
	# Get the popular stock whose ordering count greater than the specified threshold 
	# in the specified month (HAVING). 
	Month = popular_stocks_req.Month
	CountThreshold = popular_stocks_req.CountThreshold

	# SQL command
	cmd = f"""SELECT StockTicker, COUNT(*) AS OrderingCount
			  FROM Ordering
			  WHERE Date LIKE \'20210{Month}%\'
			  GROUP BY StockTicker
			  HAVING COUNT(*) > {CountThreshold};"""
	
	return get_query_results(cmd, db)