from pydantic import BaseModel, Field
from typing import Optional, List

class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = 'driver'
    email: Optional[str] = None
    phone: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class Telemetry(BaseModel):
    time_s: int
    pack_voltage: float
    pack_current: float
    soc: float
    soh: float
    cell_temp_max: float
    cell_temp_min: float
    coolant_temp: float
    motor_rpm: float
    motor_torque: float
    inverter_temp: float
    speed_kph: float
    dtc_codes: Optional[List[str]] = Field(default_factory=list)

class TicketCreate(BaseModel):
    title: str
    description: Optional[str] = None
    telemetry_snapshot: Optional[dict] = None
    priority: str = 'normal'
    vehicle_id: Optional[str] = None

class TicketOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    created_at: float
    priority: str
    vehicle_id: Optional[str]
    status: str
    assigned_to: Optional[int]
    telemetry_snapshot: Optional[dict]