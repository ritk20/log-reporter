from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
import re
import base64
import json



# ---------- Utility Functions ----------

# parser_log_file_from_content should start correctly
def parser_log_file_from_content(content: str):
    log_pattern = re.compile(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(?P<level>\w+)\s+(?P<module>[\w:]+(?:\{[^\}]+\})?):\s+(?P<message>.*?)(?=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z|$)',
        re.DOTALL
    )

    matches = log_pattern.findall(content)
    parsed_logs = []
    for match in matches:
        parsed_logs.append({
            'timestamp': match[0],  # e.g., 2025-04-25T14:11:19.206712Z
            'level': match[1],      # e.g., INFO
            'module': match[2],     # e.g., attestation::api::handlers::req_issue_token
            'message': match[3].strip()
        })

    return parsed_logs

def extract_field(text, field):
    match = re.search(rf'{field}="([^"]+)"', text)
    return match.group(1) if match else None

def transaction_detail(text):
    match=re.search(r'ResDetails type="([^"]+)" Operation="([^"]+)">',text)
    return (match.group(1),match.group(2)) if match else (None,None)
    

def extract_msg_id(text):
    return extract_field(text, "msgId")

def extract_result(text):
    match = re.search(r'<Resp reqMsgId="[^"]+" result="([^"]+)"', text)
    return match.group(1) if match else None

def extract_result_2(text):
    match = re.search(r'<Resp reqMsgId="[^"]+" result="[^"]+" errCode="([^"]+)"', text)
    return match.group(1) if match else "No error"

def extract_result_3(text):
    match = re.search(r'<Resp reqMsgId="[^"]+" result="[^"]+" errCode="[^"]+" msg="([^"]+)"', text)
    return match.group(1) if match else "No error"

def extract_amount(text):
    match = re.search(r'<Amount value="([^"]+)" curr="([^"]+)">', text)
    return f"{match.group(1)} {match.group(2)}" if match else None

def is_request(msg): return '<ReqDetails' in msg
def is_response(msg): return '<ResDetails' in msg

def extract_attr_value(text, attr_name):
    match = re.search(rf'name="{attr_name}" value="([^"]+)"', text)
    return match.group(1) if match else None

def extract_tokens_from_msg(text):
    matches = re.findall(r'<Detail name="tag" value="([^"]+)"', text)
    return [decode_details(match) for match in matches] if matches else []
def extract_tag_value(text,tag):
    match=re.search(rf"{tag}[6>]*>(.*?)</{tag}>",text)
    return match.group(1) if match else None
def decode_details(encoded_data):
    if not encoded_data:
        return None
    decoded_bytes = base64.b64decode(encoded_data)
    return json.loads(decoded_bytes.decode('utf-8'))

def extract_token_details(token, is_response):
    if is_response:
        return {
            "id": token.get("id", ""),
            "serialNo": token.get("serialNo", ""),
            "value": token.get("value", ""),
            "currency": token.get("tag", {}).get("currency", ""),
            "creationTimestamp": token.get("tag", {}).get("creationTimestamp", ""),
            "issuerSignature": token.get("tag", {}).get("issuerSignature", ""),
            "ownerAddress": token.get("tag", {}).get("ownerAddress", "")
        }
    else:
        input_list=[]
        output_list=[]
        for input_item in token.get("inputs", []):
            input_details={
                "id": input_item.get("id", ""),
                "serialNo": input_item.get("serialNo", ""),
                "value": input_item.get("value", ""),
                "currency": input_item.get("tag", {}).get("currency", ""),
                "creationTimestamp": input_item.get("tag", {}).get("creationTimestamp", ""),
                "issuerSignature": input_item.get("tag", {}).get("issuerSignature", ""),
                "ownerAddress": input_item.get("tag", {}).get("ownerAddress", "")
            }
            input_list.append(input_details)
        for output_item in token.get("outputs", []):
            output_det={
                "value": output_item.get("value", ""),
                "OutputIndex": output_item.get("outputIndex", "")
            }
            output_list.append(output_det)
        return (input_list, output_list)
def combine_logs(logs):
    transaction = {}
    indx=1
    indx_2=1
    for log in logs:
        msg = log['message']
        msg_id = extract_msg_id(msg)
        if not msg_id:
            continue
        if msg_id not  in transaction:
            transaction[indx]={"Msg_id":msg_id}

        if is_request(msg):
            tokens_data = extract_tokens_from_msg(msg)
            input_list, output_list = extract_token_details(tokens_data[0], False) if tokens_data else ([], [])
            tot_am=0
            input_amt_list=[]
            for i in input_list:
                am=i.get("value")
                input_amt_list.append(float(am))
                tot_am=tot_am+float(am)
            output_amt_list=[]
            for  i in output_list:
                am=i.get("value")
                output_amt_list.append(float(am))
            token_id=[]
            for i in input_list:
                am=i.get("id")
                
                token_id.append(am)
          
           
            transaction[indx].update({
                "Msg_id": msg_id,
                "Request_timestamp": log["timestamp"],
                "SenderOrgId": extract_attr_value(msg, "senderOrgId"),
                "ReceiverOrgId": extract_attr_value(msg, "receiverOrgId"),
                "Transaction_Id": extract_attr_value(msg, "transactionId"),
                "Amount": extract_amount(msg),
                "Req_Tot_Amount": tot_am,
                "Req_input_amt_list": input_amt_list,
                "Output_amt_list": output_amt_list,
                "Inputs": input_list,
                "Outputs": output_list,
                "Token_id_before_response": token_id
            })
            
            indx=indx+1

        elif is_response(msg):
            tokens_data = extract_tokens_from_msg(msg)
            token_details_list = [extract_token_details(token, True) for token in tokens_data]
            tot_am=0
            
            input_amt_list =[]
            for i in  token_details_list:
                am=i.get("value")
                input_amt_list.append(float(am))
                tot_am=tot_am+float(am)
            token_id=[]
            for i in token_details_list:
                am=i.get("id")
                token_id.append(am)
            type_value ,operation_value= transaction_detail(msg)
         

            transaction[indx_2].update({
                "Response_timestamp": log["timestamp"],
                "Type_Of_Transaction": type_value,
                "Operation": operation_value,
                "Responsetotamount": tot_am,
                "Resptokens": token_details_list,
                "Result_of_Transaction": extract_result(msg),
                "ErrorCode": extract_result_2(msg),
                "ErrorMsg": extract_result_3(msg),
                "Input_amt_lists": input_amt_list,
                "Token_id_after_transaction": token_id
            })
            indx_2=indx_2+1

    df = pd.DataFrame(transaction.values())

    # Parse timestamps with the correct format
    df["Request_timestamp"] = pd.to_datetime(df["Request_timestamp"], utc=True)
    df["Response_timestamp"] = pd.to_datetime(df["Response_timestamp"], utc=True)

    # Log any invalid timestamps for debugging
    # if df["Request_timestamp"].isna().any():
    #     print("Invalid Request_timestamps found:", df[df["Request_timestamp"].isna()][["Msg_id", "Request_timestamp"]])
    # if df["Response_timestamp"].isna().any():
    #     print("Invalid Response_timestamps found:", df[df["Response_timestamp"].isna()][["Msg_id", "Response_timestamp"]])

    # Replace NaT values with None for MongoDB compatibility
    df["Request_timestamp"] = df["Request_timestamp"].where(df["Request_timestamp"].notna(), None)
    df["Response_timestamp"] = df["Response_timestamp"].where(df["Response_timestamp"].notna(), None)

    # Calculate time differences, only for valid timestamps
    mask = df["Request_timestamp"].notna() & df["Response_timestamp"].notna()
    df["Time_to_Transaction_secs"] = pd.Series(dtype='float64')  # Initialize with empty series
    df.loc[mask, "Time_to_Transaction_secs"] = (
        df.loc[mask, "Response_timestamp"] - df.loc[mask, "Request_timestamp"]
    ).dt.total_seconds() * 1000

    # Fill missing values with 0
    df["Time_to_Transaction_secs"] = df["Time_to_Transaction_secs"].fillna(0)

    # df["Time_to_Transaction"] = df["Time_to_Transaction"].fillna(0) 
    # df.drop(columns=["Time_to_Transaction"], inplace=True, errors='ignore')

    # Convert success/failure to binary
    df["Result_of_Transaction"] = df["Result_of_Transaction"].replace({'SUCCESS': 1, 'FAILURE': 0})

    # Additional computed fields
    df["input_amount"] = df["Req_Tot_Amount"].astype(float)
    df["NumberOfInputs"] = df["Req_input_amt_list"].apply(lambda x: len(x) if isinstance(x, list) else 0)
    df["NumberOfOutputs"] = df["Output_amt_list"].apply(lambda x: len(x) if isinstance(x, list) else 0)
    df["Token_id_after_transaction"] = df["Token_id_after_transaction"].apply(lambda x: eval(x) if isinstance(x, str) else x)
    df["Token_id_before_transaction"] = df["Token_id_before_response"].apply(lambda x: eval(x) if isinstance(x, str) else x)

    # Drop unnecessary columns
    df = df.drop(columns=["SenderOrgId", "ReceiverOrgId"], errors='ignore')
    df.dropna()
    return df

# ------------------- FastAPI Endpoint -------------------
# --- Ma

# ------------------- FastAPI Endpoint -------------------