import openai
from typing import List
OPENAI_API_KEY = "5cc0b8aef94b47db86c5b8c7f61ab9f2"
OPENAI_ENDPOINT  = "https://anyshare-demo-chatgpt.openai.azure.com/"
OPENAI_API_VERSION  = "2023-03-15-preview"
OPENAI_API_TYPE  = "azure"
openai.api_type = OPENAI_API_TYPE
openai.api_base = OPENAI_ENDPOINT
openai.api_version = OPENAI_API_VERSION
openai.api_key = OPENAI_API_KEY


class OpenAIClient:

    def __init__(self):
        pass
    
    async def chat(self, prompt, model="asdavinci003", temperature=0, max_tokens=800, n=1, frequency_penalty=0, presence_penalty=0, stop=None):
        response = openai.Completion.create(
            engine=model,
            prompt=prompt,
            max_tokens=max_tokens,
            n=n,
            stop=stop,
            temperature=temperature,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )

        return response.choices[0].text.strip()
    ''' model="aschatgpt35"'''
    async def chatgpt(self, messages, model="aschatgpt35", temperature=0, max_tokens=800, top_p=0.95, frequency_penalty=0, presence_penalty=0, stop=None):
        response = openai.ChatCompletion.create(
            engine=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop=stop
        )

        return response.choices[0].message.content.strip()
    
    async def generate_text(self, prompt, model, temperature=0.5, max_tokens=100):
        response = openai.Completion.create(
            engine=model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].text.strip()

    async def generate_embedding(self, text, model) -> List[float]:
        text = text.replace("\n", " ")
        # 使用openai调用模型生成向量
        response = openai.Embedding.create(input = [text], engine=model)
        return response['data'][0]['embedding']
    


oa_client = OpenAIClient()


# text = """
# 请使用中文回答，生成下面文本的摘要：Azure Search  \nblobdatabase企业知识 (来自内部 pdf文件)1.选择 Azure 门户左侧菜单上的“创建资源”。 此时会显示“新建”窗口。  \n2.选择“网络”，然后在“特色”列表中选择“应用程序网关” 。  \n3. 在“基本信息”选项卡上，输入这些值作为以下应用程序网关设置：  \n•资源组：选择“新建”，创建一个新的。  \n•应用程序网关名称 ：输入 myAppGateway 作为应用程序网关的名称。  \n•层：选择“ WAF V2” 。  \n•WAF 策略：选择新建，键入新策略的名称，然后选择 确定。这会创建具有托管核心规则集  \n(CRS) 的基本 WAF 策略。  \n4. 设置前端选项卡 ：选择 ”公共”  \n5. 设置后端选项卡：选择 ”不包含目标的后端池 ” （后续步骤再配置目标 )  \n6. 设置“配置”选项卡”创建应用程序网关 (Application Gateway)创建Azure API 管理 (APIM)  \n1.在Azure 门户菜单中，选择“创建资源”。 还可以在 Azure“主页”上选择“创建资源”。  \n2.在“创建资源”页上，选择“集成” >“API 管理”。  \n3.在“创建 API 管理”页中，输入设置  \n4.选择“查看 + 创建”。  \n5.导入和发布 API (后续步骤 )  \n6.包含你的 API (后续步骤 )创建应用程序服务 (App Service) : 前端UI应用  \n1.在Azure门户中搜索框中键入“应用服务”。 在“服务”下选择“应用程序服务”  \n2.在“应用服务”页面中，请选择“ + 创建”。  \n3.在“基本信息”选项卡中的“项目详细信息”下，确保选择了正确的订阅，然后选  \n择“新建”来新建资源组。  \n4.设置“实例信息”选项卡：  \n•在“名称”下，为 Web 应用键入全局唯一名称。  \n•在“发布”下，选择“代码”。  \n•在“运行时堆栈”下，选择“ .NET 6 (LTS)” 。
# """

# model_id = "your-model-id"
# model_name = "your-model-name"
# model_language = "your-model-language"
async def main():
    message = [
    {
        "role": "system",
        "content": "You are a poet."
    },
    {
        "role": "user",
        "content": "写一首赞美祖国的诗"
    }
]
    res = await OpenAIClient().generate_embedding("写一首赞美祖国的诗", model="astextada002")
    print(res)
if __name__== "__main__":
    import asyncio
    asyncio.run(main())
