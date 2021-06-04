# Import packages
from sqlalchemy import Column, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from db import Base

# Relation schema definitions (converted from existing database - order.sqlite3)
class Bank(Base):
    __tablename__ = 'Bank'

    BankNum = Column(Text, primary_key=True)
    Name = Column(Text, nullable=False)
    Address = Column(Text)
    Phone = Column(Text, nullable=False)


class Client(Base):
    __tablename__ = 'Client'

    SSN = Column(Text, primary_key=True)
    Name = Column(Text, nullable=False)
    Birthday = Column(Text)
    Phone = Column(Text)
    Occupation = Column(Text)
    SetAccNo = Column(ForeignKey('SettlementAccount.AccNum'), nullable=False)
    SecAccNo = Column(ForeignKey('SecurityAccount.AccNum'), nullable=False)

    SecurityAccount = relationship('SecurityAccount', primaryjoin='Client.SecAccNo == SecurityAccount.AccNum')
    SettlementAccount = relationship('SettlementAccount')


class SecurityAccount(Base):
    __tablename__ = 'SecurityAccount'

    AccNum = Column(Text, primary_key=True)
    ForeignTransaction = Column(Integer, nullable=False)
    ElectronicTransaction = Column(Integer, nullable=False)
    ManagerSSN = Column(ForeignKey('Client.SSN'))
    ManageStartDate = Column(Text, nullable=False)

    Client = relationship('Client', primaryjoin='SecurityAccount.ManagerSSN == Client.SSN')


class Ordering(Base):
    __tablename__ = 'Ordering'

    Number = Column(Text, primary_key=True)
    StockTicker = Column(Text, nullable=False)
    Date = Column(Text, nullable=False)
    Price = Column(Float, nullable=False)
    Volume = Column(Integer, nullable=False)
    Type = Column(Text, nullable=False)
    SecAccNo = Column(ForeignKey('SecurityAccount.AccNum'), nullable=False)

    SecurityAccount = relationship('SecurityAccount')


class SettlementAccount(Base):
    __tablename__ = 'SettlementAccount'

    AccNum = Column(Text, primary_key=True)
    AccName = Column(Text, nullable=False)
    Balance = Column(Integer, nullable=False)
    Type = Column(Text, nullable=False)
    BankNo = Column(ForeignKey('Bank.BankNum'), nullable=False)
    SignDate = Column(Text, nullable=False)

    Bank = relationship('Bank')