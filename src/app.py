import os
import traceback

import uvicorn
from fastapi import FastAPI, File, UploadFile
from extraction import Extraction
from qa import QA
from pydantic import BaseModel

api = FastAPI()


class Query(BaseModel):
    query: str


@api.post("/api/chat_kg/v1/upload_file/")
async def create_upload_file(file: UploadFile = File(...)):
    with open(file.filename, "wb") as buffer:
        buffer.write(await file.read())
    try:
        ex = Extraction()
        fl = ex._chunk(file.filename)
        print("text chunk:", len(fl))
    except Exception as e:
        print("ERROR in file chunk:{}".format(e))
        traceback.print_exc()
        if "type error, it's not .docx .pdf .txt" in str(e):
            return {"res": {"entity_list": [], "edge_list": []}, "ans": "抱歉未能解析文档信息。仅支持docx，pdf，txt文件。"}
        return {"res": {"entity_list": [],"edge_list": []}, "ans": "抱歉未能解析文档信息。"}
    try:
        # res = await ex.extract_event_llm(fl)
        res = await ex.extract_llm(fl, 'relation')
    except Exception as e:
        print("ERROR in llm extract:{}".format(e))
        traceback.print_exc()
        return {"res": {"entity_list": [], "edge_list": []}, "ans": "抱歉未能抽取文档信息。请上传其他文件或稍后重试。"}

    return res


@api.post("/api/chat_kg/v1/qa/")
async def create_qa(query: Query):
    qa = QA()
    res = {}
    if query.query:
        res = await qa.get_qa_resp(query.query)
        return {"res":res}
    else:
        return {"error_code":"400"}



# async def test_extraction():
#     ex = Extraction()
#     # fl=ex._chunk('price.pdf')
#     fl = """光伏电池产量大涨：4 月份光伏电池产量 39.92GW，同比增长 69.1%5 月 16 日，国家统计局发布了 2023 年 4 月份规模以上工业生产主要数据。其
# 中，4 月份光伏电池产量 3992 万千瓦，同比增长 69.1%；1-4 月光伏电池累计
# 产量 14435 万千瓦，同比增长 56.7%。
# 发电量方面，今年 4 月份光伏发电量 231 亿千瓦时，同比下降 3.3%。1-4 月累
# 计发电量 846 亿千瓦时，同比增长 7.5%"""
#     res = await ex.extract_event_llm(fl)
#     print(res)

# async def test_qa():
#     qa = QA()
#     res = await qa.get_qa_resp("浙江爱科新材料有限公司竞争对手是")
#     print(res)

# async def main():
#     await test_extraction()

#     # await test_qa()

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())

if __name__ == "__main__":
    uvicorn.run(app="app:api", host="0.0.0.0", port=8000, reload=True)
