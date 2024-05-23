import io

import boto3
import pandas as pd
from io import BytesIO
from typing import List, Union

# S3 literals
BUCKET_NAME = "bp-authoring-files"
DATA_DIR = "data"


class TNE:
    def __init__(self, uid: str):
        self.uid = uid
        self.client = boto3.client("s3")
        self.base_prefix = f"d/{self.uid}/{DATA_DIR}"
        self.data_list = self.list_data()

    def list_data(self) -> List[str]:
        response = self.client.list_objects_v2(
            Bucket=BUCKET_NAME, Prefix=self.base_prefix
        )
        data_contents = []
        if "Contents" in response:
            for obj in response["Contents"]:
                filename = obj["Key"].split("data/")[-1]
                if obj["Size"] > 0:
                    data_contents.append(filename)

        return data_contents

    def get_object(self, key: str) -> Union[str, pd.DataFrame]:
        try:
            modified_key = f"{self.base_prefix}/{key}"
            file_content = self.client.get_object(Bucket=BUCKET_NAME, Key=modified_key)[
                "Body"
            ].read()
            if file_content:
                match key.split(".")[-1]:
                    case "txt":
                        return file_content.decode("utf-8")
                    case "csv":
                        return pd.read_csv(BytesIO(file_content), encoding="utf-8")
        except Exception:
            raise KeyError(f"No matching object key.")