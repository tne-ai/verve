import json
import yaml
import boto3
import pandas as pd
from PIL import Image
from io import BytesIO
from docx import Document
from pptx import Presentation
from typing import Dict, List, Optional, Union

from reportlab.platypus import SimpleDocTemplate

# S3 literals
DATA_DIR = "Data"
LATEST = "LATEST"


class TNE:
    def __init__(
        self,
        uid: str = "",
        bucket_name: str = "bp-authoring-files",
        project: Optional[str] = None,
        version: Optional[str] = LATEST,
    ):
        self.uid = uid
        self.bucket_name = bucket_name
        self.client = boto3.client("s3")
        if project:
            self.base_prefix = f"projects/{project}--{version}/{DATA_DIR}"
        else:
            self.base_prefix = f"d/{self.uid}/{DATA_DIR}"
        self.data_list = self.list_data()

    def list_data(self) -> List[str]:
        response = self.client.list_objects_v2(
            Bucket=self.bucket_name, Prefix=self.base_prefix
        )
        data_contents = []
        if "Contents" in response:
            for obj in response["Contents"]:
                filename = obj["Key"].split("data/")[-1]
                if obj["Size"] > 0:
                    data_contents.append(filename)

        return data_contents

    def get_object(self, key: str) -> Union[str, pd.DataFrame, Image.Image, Dict, Document, Presentation]:
        try:
            file_content = self.get_object_bytes(key)
            if file_content:
                match key.split(".")[-1]:
                    case "txt" | "md" | "out":
                        return file_content.decode("utf-8")
                    case "csv":
                        return pd.read_csv(BytesIO(file_content), encoding="utf-8")
                    case "xlsx":
                        return pd.read_excel(
                            BytesIO(file_content), sheet_name=None, engine="openpyxl"
                        )
                    case "jpg" | "jpeg" | "png":
                        return Image.open(BytesIO(file_content))
                    case "json":
                        return json.loads(file_content.decode("utf-8"))
                    case "yaml" | "yml":
                        return yaml.safe_load(file_content.decode("utf-8"))
                    case "docx":
                        docx_buffer = BytesIO(file_content)
                        return Document(docx_buffer)
                    case "pptx":
                        pptx_buffer = BytesIO(file_content)
                        return Presentation(pptx_buffer)
                    case _:
                        raise ValueError(
                            f"Unsupported file extension: {key.split('.')[-1]}. Use method get_object_bytes() to access this object."
                        )

        except IOError as io:
            raise io
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise e


    def get_object_bytes(self, key: str) -> bytes:
        try:
            modified_key = f"{self.base_prefix}/{key}"
            file_content = self.client.get_object(
                Bucket=self.bucket_name, Key=modified_key
            )["Body"].read()
            return file_content
        except Exception as e:
            raise IOError(f"Error pulling object from S3: {e}")

    def upload_object(self, key: str, data: Union[str, pd.DataFrame, Image, Dict]):
        try:
            modified_key = f"{self.base_prefix}/{key}"

            # Handling different data types
            match key.split(".")[-1]:
                case "txt" | "md" | "out":
                    file_content = data.encode("utf-8") if isinstance(data, str) else str(data).encode("utf-8")
                case "csv":
                    if isinstance(data, pd.DataFrame):
                        csv_buffer = BytesIO()
                        data.to_csv(csv_buffer, index=False)
                        file_content = csv_buffer.getvalue()
                    else:
                        raise ValueError(f"Expected a DataFrame for CSV upload, got {type(data)}.")
                case "xlsx":
                    if isinstance(data, pd.DataFrame) or isinstance(data, dict):
                        excel_buffer = BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                            if isinstance(data, pd.DataFrame):
                                data.to_excel(writer, index=False, sheet_name="Sheet1")
                            else:
                                for sheet_name, df in data.items():
                                    if isinstance(df, pd.DataFrame):
                                        df.to_excel(writer, index=False, sheet_name=sheet_name)
                        file_content = excel_buffer.getvalue()
                    else:
                        raise ValueError(f"Expected a DataFrame or a dictionary of DataFrames for XLSX upload, got {type(data)}.")
                case "jpg" | "jpeg" | "png":
                    if isinstance(data, Image.Image):
                        img_buffer = BytesIO()
                        data.save(img_buffer, format=data.format if data.format else "PNG")
                        file_content = img_buffer.getvalue()
                    else:
                        raise ValueError(f"Expected a PIL Image for image upload, got {type(data)}.")
                case "json":
                    file_content = json.dumps(data).encode("utf-8") if isinstance(data, (dict, list)) else str(data).encode("utf-8")
                case "yaml" | "yml":
                    file_content = yaml.safe_dump(data).encode("utf-8") if isinstance(data, (dict, list)) else str(data).encode("utf-8")
                case "docx":
                    try:
                        docx_buffer = BytesIO()
                        data.save(docx_buffer)
                        file_content = docx_buffer.getvalue()
                    except AttributeError:
                        raise ValueError(f"Expected a python-docx Document for DOCX upload, got {type(data)}.")
                case "pptx":
                    try:
                        pptx_buffer = BytesIO()
                        data.save(pptx_buffer)
                        file_content = pptx_buffer.getvalue()
                    except AttributeError:
                        raise ValueError(f"Expected a python-pptx Presentation for PPTX upload, got {type(data)}.")
                case "pdf":
                    file_content = data.getvalue()
                case _:
                    raise ValueError(f"Unsupported file extension: {key.split('.')[-1]}. Cannot determine how to upload this object.")

            # Upload the object to S3
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=modified_key,
                Body=file_content
            )

        except ValueError as ve:
            raise ve
        except Exception as e:
            raise IOError(f"Error uploading object to S3: {e}")

