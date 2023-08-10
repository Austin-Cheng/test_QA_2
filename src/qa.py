import ast
import os
import json
import re
from prompt_manager.prompt import PromptHandler
from llm_api.openai_client import oa_client
from service import Service

class QA:
    def _load_json(self, name):
        json_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except FileNotFoundError:
            print('File not found')
        except json.JSONDecodeError:
            print('Invalid JSON format')
        finally:
            f.close()
    def _chat_func(self):
        if PromptHandler.gpt_model == "chatgpt":
            return oa_client.chatgpt
        else:
            return oa_client.chat
    # 判断操作类型：qa、画布
    async def judge_ops_type(self, query):
        data = self._load_json('ops_type.json')
        message = PromptHandler.get_ops_type_prompt(data, query)
        result = await self._chat_func()(message)
        # print("op type: ", result)
        return result
    
    # 判断画布类型：
    async def judge_canvas_ops(self, query):
        data = self._load_json('canvas_ops.json')
        message = PromptHandler.get_canvas_ops_prompt(data, query)
        result = await self._chat_func()(message)
        return result

    # 判断qa操作类型
    async def judge_qa_ops_type(self, query):
        data = self._load_json('qa_ops.json')
        message = PromptHandler.get_qa_ops_prompt(data, query)
        # print(message)
        result = await self._chat_func()(message)
        # print(result)
        return result

    # 根据操作类型、槽位、query来填槽：
    # 填充参数：跟query和参数list返回列表["param1":"str1 ", "param2":""...]}
    async def slot_filling(self, query, qa_op):
        data = self._load_json('qa_ops.json')
        if qa_op not in data:
            return []
        param_list = data.get(qa_op).get("param_list")
        message = PromptHandler.get_qa_slot_prompt(query, param_list)
        result = await self._chat_func()(message)
        return result

    def _key_in_list(self, dstlist, key):
        for item in dstlist:
            if key in item:
                return True
        return False

    async def get_slot_value_dict(self, query, qa_op, res):
        data = self._load_json('qa_ops.json')
        param_list = data.get(qa_op).get("param_list")
        slot_list = res
        result = {}
        for slot_body in slot_list:
            for key in slot_body.keys():
                if self._key_in_list(param_list,key):
                    slot_value = slot_body.get(key).get("slot_value")
                    if slot_value in query:
                        result[key] = slot_value
        return result

    # 根据原有信息和返回的子图来组织答案
    async def get_answer_by_sub_graph(self, query, res):
        message = PromptHandler.get_qa_answer_explain_prompt(query, res)
        result = await self._chat_func()(message)
        return result

    async def get_qa_resp(self, query):
        # ops_type_str = await self.judge_ops_type(query)
        # ops_type_list = ast.literal_eval(ops_type_str)
        default_url = "https://anyshare.aishu.cn/anyshare/zh-cn/foxitreader?_tb=none&gns="
        ops_type_list = ["<knowledge_graph_qa>"]
        response_q = {}
        response_c = ""
        if ops_type_list:
            # 图谱问答
            if "<knowledge_graph_qa>" == ops_type_list[0]:
                # 判断qa的操作类型
                qa_ops_type = await self.judge_qa_ops_type(query)
                qa_type = ast.literal_eval(qa_ops_type)
                if qa_type[0] == 'ambiguity':
                    return {"qa": {"chat": {"answer": "很抱歉，没能理解您的问题。输入明确的问题，可以更好的帮您查询。"}}}
                if qa_type[0] == "interrogative_function":
                    answer = """您好，我是ChatKG，一款基于大模型的知识图谱智能助手。集成大模型提强大的自然语言理解和生成能力，帮助您快速实现对非结构化文本的知识抽取，以及知识图谱数据的高效获取。比如：
1、帮助您快速获取所文本、文档中包含的三元组信息，并更新到当前知识图谱中；
2、帮助您高效地获取图谱信息，并提供一定程度的整合、分析以及对比等功能。
其他功能，请您期待后续升级。"""
                    return {"qa": {"chat": {"answer": answer}}}
                # 填槽
                slot_str = await self.slot_filling(query,qa_type[0])

                # 获取服务配置信息
                qa_tag_setting_map = self._load_json("qa_tag_setting_map.json")
                server = qa_tag_setting_map.get("server")
                host = server.get("host")
                settings = qa_tag_setting_map.get("settings")
                api_path = settings.get(qa_type[0]).get("api_path")
                # 请求方式，restful_api为restful_api请求，否则为PC端网页嵌入请求
                request_type = settings.get(qa_type[0]).get("request_type", "restful_api")
                # 参数
                param_list = settings.get(qa_type[0]).get("param_list")
                slot_json = json.loads(slot_str)
                result = await self.get_slot_value_dict(query,qa_type[0],slot_json)

                # 请求服务
                res_q, vertexs, res, gns2file = Service.assemble_node_edge_list(api_path, result, request_type, param_list)
                if not res:
                    return {"qa": {"chat": {"answer": "很抱歉，没有查询到您搜索的信息。"}}}
                if request_type != "restful_api":
                    return res_q
                try:
                    result_qa = await self.get_answer_by_sub_graph(query, res_q)
                except Exception as e:
                    print(repr(e))
                    return {"qa": {"chat": {"answer": "很抱歉，你查询的信息过多，超出LLMs处理范围。"}}}

                # print("result_qa: ", result_qa)
                r_json = ast.literal_eval(result_qa)
                answer = r_json.get("answer")
                reference = {}
                file2url = {}
                # 返回格式处理
                if vertexs:
                    idx = 1
                    source = ""
                    vertexs_sorted = sorted(vertexs.items(), key=lambda x: len(x[1]), reverse=True)
                    for vertex_info in vertexs_sorted:
                        vid, name = vertex_info
                        flag = "[<" + str(idx) + ">]"
                        answer = answer.replace(name, flag)
                        url = ""
                        for gns, file in gns2file.items():
                            if name == file:
                                url = default_url + str(gns[6:]) + "&name=" + str(file)
                                type = file.split(".")[-1]
                                file2url[file] = url
                                source += "[" + str(idx) + "] " + str(name) + "\n"
                                name = "".join(file.split(".")[:-1])
                        idx += 1

                        if url:
                            reference[flag] = {"vid": vid, "name": name, "url": url, "type": "." + str(type)}
                        else:
                            reference[flag] = {"vid": vid, "name": name}
                    # if source:
                    #     answer += "\n" + source

                for line in re.findall(r"\d{1,2}、", answer):
                    if line.startswith("\n"):
                        line = re.sub("\n", "", line)
                    answer = answer.replace(line, str("\n") + line, 1)
                #     else:
                #         answer = answer.replace(line, str("\n") + line)
                r_json["answer"] = answer.strip()
                r_json["reference"] = reference

                response_q = {
                    "chat":r_json,
                    "table":res,
                    "request_type": request_type,
                    "service_id": api_path
                }
            # 画布操作
            if "<canvas_ops>" == ops_type_list[0]:
                canvas_ops = await self.judge_canvas_ops(query)
                # print("c: ",canvas_ops)
                co1 = json.loads(canvas_ops)
                if co1:
                    co = co1[0]
                    response_c = {
                        "ops":co
                    }
            response = {
                "qa":response_q,
                "canvas":response_c
            }

            return response

async def main():

    
    query = """
    层次布局
    """
    qa = QA()
    return await qa.get_qa_resp(query)
    # return await qa.judge_canvas_ops(data_info)
if __name__ == "__main__":
    import asyncio
    print(asyncio.run(main()))
