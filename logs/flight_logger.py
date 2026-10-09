import logging
import pandas as pd
from datetime import datetime

class FlightLogger:
    def __init__(self):
        self.logs = []
    
    def log(self, level, module, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append({
            "Timestamp": timestamp,
            "Level": level,
            "Module": module,
            "Message": message
        })
        
    def get_logs_df(self):
        return pd.DataFrame(self.logs)

# Global instance for the dashboard to access
flight_logger = FlightLogger()

# Custom logging handler to redirect standard Python logs to our FlightLogger
class DashboardLogHandler(logging.Handler):
    def emit(self, record):
        flight_logger.log(record.levelname, record.module, record.getMessage())

dashboard_handler = DashboardLogHandler()
logging.getLogger().addHandler(dashboard_handler)
logging.getLogger().setLevel(logging.INFO)
