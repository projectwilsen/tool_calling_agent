# Tools
from pydantic.v1 import BaseModel, Field, validator
from langchain_core.tools import StructuredTool, ToolException

import json
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

rapid_api_key = os.getenv("RAPID_API_KEY")

class SearchInput(BaseModel):
    stock: str = Field(description="Stock ticker to search for, should only contain up to 4 characters")

    @validator('stock')
    def validate_stock(cls, v):
        if not v.isalpha() or len(v) > 4:
            raise ToolException('Stock ticker should only contain up to 4 alphabetic characters')
        return v

def get_company_profile(stock:str) -> str:
    """Get detail profile such as company name, sector name, primary name, number of employees of a stock"""

    api_key = rapid_api_key
    url = "https://seeking-alpha.p.rapidapi.com/symbols/get-profile"

    querystring = {"symbols":stock.lower()}

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "seeking-alpha.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    
    if response.status_code == 200:
        data = response.json()
        result = json.dumps(data)
    else:
        raise ToolException(f"No data for {stock}")
    
    return result

def get_competitors(stock:str) -> str:
    """Get peers or competitors of a stock"""

    api_key = rapid_api_key
    url = "https://seeking-alpha.p.rapidapi.com/symbols/get-peers"

    querystring = {"symbol":stock.lower()}

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "seeking-alpha.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    
    if response.status_code == 200:
        data = response.json()
        result = json.dumps(data)
    else:
        raise ToolException(f"No data for {stock}")
    
    return result


get_company_profile_tool = StructuredTool.from_function(
    func=get_company_profile,
    args_schema= SearchInput,
    handle_tool_error=True, # add this
)

get_competitors_tool = StructuredTool.from_function(
    func=get_competitors,
    args_schema= SearchInput,
    handle_tool_error=True, # add this
)
