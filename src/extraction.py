import ast
import asyncio
import json
import os
import re
import time
import traceback

import openai

from llm_api.openai_client import oa_client
from prompt_manager.prompt import PromptHandler
from service import Service
from file_process import FileProcess
import uuid



class Extraction:
    def __init__(self) -> None:
        pass
    # 文件->分段：前端获得文件对象，处理，分段；return list;
    def _chat_func(self):
        # if PromptHandler.gpt_model == "chatgpt":
        return oa_client.chatgpt
        # else:
        # return oa_client.chat
    def _chunk(self, doc_path)->list:
        return FileProcess.passage_parse(doc_path).get("passages")
    #  llm api 判断包含类型：填充prompt 解析报文；
    def _load_type(self):
        json_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'types.json')
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                entity_type = data.get('entity_type', [])
                event_type = data.get('event_type', [])
                relation_type = data.get('relation_type', [])
                return (entity_type, event_type, relation_type)
        except FileNotFoundError:
            print('File not found')
        except json.JSONDecodeError:
            print('Invalid JSON format')
        finally:
            f.close()

    async def _find_item_tag(self, input, type):
        '''
        从types.json文件读取实体或事件类型，大模型返回input包含的tag列表：type指定“entity”，“event”或“relation”
        '''
        item_types = self._load_type()
        message = PromptHandler.get_extraction_tag_prompt(input,type,item_types)
        # print("message:", message)
        result=await self._chat_func()(message)
        print("chat result:", result)
        return result

    def _find_body_from_list(self, tag, body_list):
        # print(tag)
        for body in body_list:
            if tag in body:
                return body
        return {}

    def _get_item_body(self, tag, type):
        item_types = self._load_type()
        if type=='entity':
            return self._find_body_from_list(tag,item_types[0])
        if type=='event':
            return self._find_body_from_list(tag,item_types[1])
        if type=='relation':
            return self._find_body_from_list(tag,item_types[2])

    def _get_type2alias(self):
        item_types = self._load_type()
        type2alias = {'entity':{},'event':{},'relation':{}}
        for dic in item_types[0]:
            type_name = list(dic.keys())[0]
            type2alias['entity'][type_name[1:-1]] = dic[type_name]['desc']
        for dic in item_types[1]:
            type_name = list(dic.keys())[0]
            type2alias['event'][type_name[1:-1]] = dic[type_name]['desc']
        for dic in item_types[2]:
            type_name = list(dic.keys())[0]
            type2alias['relation'][type_name[1:-1]] = dic[type_name]['desc']
        return type2alias

    # llm api 获取对应类型的值，找到对应的schema解析，抽取；
    async def _extract(self,event_json,input_text, extract_type='event'):
        # if isinstance(event_json, list):
        #     messages = []
        #     for ej in event_json:
        #         message = PromptHandler.get_extraction_prompt(ej, input_text, extract_type)
        #         messages.append(message)
        #     tasks = [asyncio.create_task(self._chat_func()(message, max_tokens=2000))
        #              for message in messages]
        #     res = await asyncio.wait(tasks)
        #     result = [x.result() for x in res[0]]
        # else:
        message = PromptHandler.get_extraction_prompt(event_json,input_text, extract_type)
        # print("message:", message)
        result=await self._chat_func()(message, max_tokens=2000)
        return result
    

    def _get_entity_list(self):
        """types.json中实体列表tag"""
        item_type_list = self._load_type()
        keys = []
        for entity_type in item_type_list[0]:
            for key in entity_type.keys():
                keys.append(key)
        return keys
    
    def _get_role_list (self,data):
        """获取事件中的论元列表, 关系的头尾实体类型，实体的类型"""

        # data = ast.literal_eval(event)
        roles = []
        entity_types = []

        if isinstance(data, dict):
            roles = data.get("roles",[])
        if isinstance(data, list):
            for d in data:
                subject = d.get('subject', None)
                object = d.get('object', None)
                if subject is not None:
                    roles.append(subject)
                if object is not None:
                    roles.append(object)
                et = d.get('entity_type', None)
                if et:
                    entity_types.append(et)
        keys = []
        for entity_type in roles:
            for key in entity_type.keys():
                keys.append(key)
        keys += entity_types
        return keys

    def _entity_role_mapping(self, entity_list, role_list):
        """获取types.json中的实体列表与事件论元中的论元列表的交集，即事件的相关实体，作为参考点"""
        return list(set(entity_list) & set(role_list))

    def _get_related_entities(self, response):
        #大模型返回的报文中找到相关论元
        roles = self._get_role_list(response)
        #types.json中实体列表tag
        entities = self._get_entity_list()
        #找到事件相关实体作为参考点
        return self._entity_role_mapping(entities, roles)
        
    def _get_entity_body_list(self,entities, response):
        if entities and response:
            response_json = json.loads(response) 
            res = []
            for entity in entities:
                for entity_body in response_json.get("roles"):
                    if entity in entity_body:
                        res.append(entity_body)   
            return res
        return []

    # 通过mapping.json在schema.json里拿到tags：
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
    # 根据tag获得shcema映射表
    def _get_mapping (self, type_json):
        data = self._load_json('mapping.json')
        if data and type_json:
            for key in type_json.keys():
                if key in data:
                    return {key:data.get(key)}
        return None

    # 根据tag-id映射表，获取schema节点json
    def _get_schema (self, mapping_json):
        if not mapping_json:
            return None
        data_tag = next(iter(mapping_json.keys()))
        data_type = next(iter(mapping_json.get(data_tag)))
        schema_json = self._load_json('schema.json')
        
        edges = schema_json.get("res").get("edges")
        entities = schema_json.get("res").get("entity")
        if edges and (data_type == 'edge_id'):
            edge_id = mapping_json.get(data_tag).get(data_type)
            for edge in edges:
                if edge_id == edge.get("edge_id"):
                    return edge
        if entities and (data_type == 'entity_id'):
            entity_id = mapping_json.get(data_tag).get(data_type)
            for entity in entities:
                if entity_id == entity.get("entity_id"):
                    return entity
        return None
    
    #组装full-text搜索的query与tag
    def _get_query_tag(self, entity_info, schema_element):
        query = entity_info.get(next(iter(entity_info.keys())))
        tag = schema_element.get("name")
        return query,tag

    def get_graph_otl(self):
        with open('graph_otl.json', 'r', encoding='utf8')as f:
            graph_otl = json.load(f)
        dic = {'entity':{}, 'relation':{}}
        for entities in graph_otl['entity']:
            dic['entity'][entities['name']] = entities
        for edge in graph_otl['edge']:
            dic['relation'][edge['name']] = edge
        return dic

    def _add_new_node(self, entity_type, entity_name, entity2uuid, entity_list, graph_otl, types2alias):
        ent_tag_name = entity_type + '__' + entity_name
        if ent_tag_name not in entity2uuid:
            random_uuid1 = uuid.uuid4().hex

            subject_node = {
                "vid": random_uuid1,
                "tags": [
                    entity_type
                ],
                "color": "#C64F58",  # graph_otl['entity'].get(entity_type, {}).get('colour',"#C64F58"),
                "alias": types2alias['entity'][entity_type],
                "default_property": {
                    "n": "name",
                    "v": entity_name
                }
            }
            entity_list.append(subject_node)
            entity2uuid[ent_tag_name] = random_uuid1
        return entity_list, entity2uuid

    async def _gen_node(self, entity_type, entity_name, graph_otl, types2alias):
        try:
            vertex = await Service.get_full_text_vertex(entity_name, entity_type)
        except Exception as e:
            print("Full text search graph error:{}".format(e))
            traceback.print_exc()
            vertex = None
        if vertex is None:
            random_uuid1 = uuid.uuid4().hex
            vertex = {
                "vid": random_uuid1,
                "tags": [
                    entity_type
                ],
                "color": "#C64F58",  # graph_otl['entity'].get(entity_type, {}).get('colour',"#C64F58"),
                "alias": types2alias['entity'][entity_type],
                "default_property": {
                    "n": "name",
                    "v": entity_name
                }
            }
        return vertex

    def _gen_edge(self, relation_type, src_id, dst_id, entity2uuid, graph_otl, types2alias):
        edge_class = relation_type
        src_id = entity2uuid[src_id]
        dst_id = entity2uuid[dst_id]
        edge_id = f"{edge_class}:\"{src_id}\"->\"{dst_id}\""
        edge = {
            "src_id": src_id,
            "dst_id": dst_id,
            "edge_class": edge_class,
            "edge_id": edge_id,
            "type": "edge",
            "color": "#BBD273",  # graph_otl['relation'].get(edge_class, {}).get('colour', "#BBD273"),
            "alias": types2alias['relation'][edge_class]
        }
        return edge

    def _add_new_edge(self, relation_type, src_id, dst_id, edge_set, edge_list, graph_otl, types2alias):
        edge_class = relation_type
        edge_id = f"{edge_class}:\"{src_id}\"->\"{dst_id}\""
        if edge_id not in edge_set:
            edge = {
                "src_id": src_id,
                "dst_id": dst_id,
                "edge_class": edge_class,
                "edge_id": edge_id,
                "type": "edge",
                "color": "#BBD273",  # graph_otl['relation'].get(edge_class, {}).get('colour', "#BBD273"),
                "alias": types2alias['relation'][edge_class]
            }
            edge_list.append(edge)
            edge_set.add(edge_id)
        return edge_list, edge_set

    # 返回前端，根据实体类、实体获得参考位置、写入数据到画布图谱；
    async def extract_event_llm(self, input_texts):
        entity_list = []
        edge_list = []
        for input_text in input_texts:
            event_tag = await self._find_item_tag(input_text, "event")
            # print('event_tag:', event_tag)
            if not event_tag:
                etags = []
            else:
                etags = ast.literal_eval(event_tag)
            for etag in etags:
                event_list = []
                for key in etag.keys():
                    event_list.append(key)
                etag_item = ""
                if not event_list:
                    continue
                etag_item = event_list[0]
                print('etag_item:', etag_item)
                if not etag_item:
                    continue
                event_body = self._get_item_body(etag_item,"event")
                if not event_body:
                    continue
                print('event_body:', event_body)
                result = await self._extract(event_body, input_text)
                """
{
  "event_type": "<technology>",
  "event_title": "产品技术",
  "roles": [
    {
      "<product>": "产品"
    },
    {
      "<technology_type>": "工程开发"
    }
  ]
}
                
                """
                if not result:
                    return None
                print('result:', result)
                result_json = ast.literal_eval(result)
                related_entities = self._get_related_entities(result_json)
                print('related_entites:', related_entities)
                entity_body_list = self._get_entity_body_list(related_entities,result)
                print('entity_body_list', entity_body_list)
                mapping_info = self._get_mapping(entity_body_list[0])
                print('mapping info:', mapping_info)
                schema = self._get_schema(mapping_info)
                print('schema:', schema)
                query,tag = self._get_query_tag(entity_body_list[0], schema)
                print('query={}, tag={}'.format(query, tag))
                """
                related_entites: ['<product>']
entity_body_list [{'<product>': '产品'}]
mapping info: {'<product>': {'entity_id': 21}}
schema: {'alias': '产品', 'color': '#5889C4', 'entity_id': 21, 'icon': '', 'name': 'product', 'x': 844.5098357275501, 'y': 456.9959954275668}
query=产品, tag=product
                """
                # print(tag)
                # print(query)
                # 生成一个随机的UUID
                random_uuid = uuid.uuid4().hex
                vertex = await Service.get_full_text_vertex(query, tag)
                # 情报点边固定
                information = {
                    "vid":random_uuid,
                    "tags": [
                        "information"
                    ],
                    "color": "#C64F58",
                    "alias": "情报",
                    "default_property": {
                        "n": "name",
                        "v": json.loads(result).get("event_title")
                    }
                }
                src_node = vertex.get("tags")[0]
                dst_node = information.get("tags")[0]
                edge_class = f"{src_node}_2_{dst_node}"
                vid = vertex.get("vid")
                edge_id = f"{edge_class}:\"{vid}\"->\"{random_uuid}\""
                edge = {
                    "src_id":vertex.get("vid"),
                    "dst_id":information.get("vid"),
                    "edge_class": edge_class,
                    "edge_id":edge_id,
                    "type": "edge",
                    "color": "#BBD273",
                    "alias": "情报"
                }

                entity_list.append(vertex)
                entity_list.append(information)
                edge_list.append(edge)
        res_dict = {
            "entity_list": entity_list,
            "edge_list":edge_list
        }
        return {"res": res_dict, "ans": "抽取完成。"}

    async def req_openai(self, input_text, extract_type):
        event_tag = await self._find_item_tag(input_text, extract_type)
        event_list = re.findall(r'(?<={")<.+?>(?=":)', event_tag) + re.findall(r"(?<={')<.+?>(?=':)", event_tag)
        event_list = list(set(event_list))
        print("event_list:", event_list)
        if not event_list:
            return '[]'
        event_list = list(set(event_list))
        event_bodys = []
        for etag_item in event_list:
            event_body = self._get_item_body(etag_item, extract_type)
            if event_body:
                event_bodys.append(event_body)
        # print('event_bodys:', event_bodys)
        # start_time = time.time()
        # results = await self._extract(event_bodys, input_text, extract_type)
        # result_json = []
        # for x in results:
        #     print(x)
        #     x = ast.literal_eval(x)
        #     result_json += x
        # end_time = time.time()
        # print(json.dumps(result_json, ensure_ascii=False, indent=4, separators=[',',':']))
        # print('async extract spend:', end_time-start_time)
        # start_time = time.time()
        # for event_body in event_bodys:
        #     result = await self._extract(event_body, input_text, extract_type)
        #     if not result:
        #         continue
        #     print('result:', result)
        #     result_json = ast.literal_eval(result)
        # end_time = time.time()
        # print('for xunhuan extract spend:', end_time - start_time)
        # start_time = time.time()
        result = await self._extract(event_bodys, input_text, extract_type)
        if not result:
            return '[]'
        print('result:', result)

        # end_time = time.time()
        # print('List extract spend:', end_time - start_time)
        return result

    async def extract_llm(self, input_texts, extract_type):
        entity_list = []
        edge_list = []
        entity2uuid = {}
        node_set = set()
        edge_set = set()

        graph_ent_types = self._get_entity_list()
        graph_otl = self.get_graph_otl()
        types2alias = self._get_type2alias()
        graph_ent_types = [x[1:-1] for x in graph_ent_types]
        tasks = [asyncio.create_task(self.req_openai(input_text, extract_type))
                 for input_text in input_texts]
        try:
            res = await asyncio.wait(tasks)
            results = [x.result() for x in res[0]]
        except Exception as e:
            traceback.print_exc()
            if isinstance(e, openai.error.APIError):
                return {"res": {"entity_list": [], "edge_list": []}, "ans": "抱歉未能抽取文档信息。大模型API服务错误，请稍后重试。"}
            else:
                return {"res": {"entity_list": [], "edge_list": []}, "ans": "抱歉未能抽取文档信息。请求大模型API失败，请稍后重试。"}

        result_json = []
        for result in results:
            try:
                result_json += ast.literal_eval(result)
            except Exception as e:
                print("LLM抽取返回结果格式错误：{}.返回结果:{}".format(e, result))

        # 图谱中有的实体类型
        # start_time = time.time()
        if extract_type == 'entity':
            entitys = []
            for res in result_json:
                entity_type = list(res.keys())[0][1:-1]
                entity_name = list(res.values())[0]
                entity_tag_name = entity_type + '__' + entity_name
                # entity_tag_name = res['entity_type'][1:-1] + '__' + res['entity_name']
                if entity_type in graph_ent_types and entity_name and entity_tag_name not in node_set:
                    entitys.append((entity_type, entity_name))
                    node_set.add(entity_tag_name)
            tasks = [asyncio.create_task(self._gen_node(e[0], e[1], graph_otl, types2alias))
                     for e in entitys]
            res = await asyncio.wait(tasks)
            ent_res = [x.result() for x in res[0]]
            entity_list += ent_res
            for e in ent_res:
                entity2uuid[e['tags'][0] + '__' + e['default_property']['v']] = e.get('vid')

        elif extract_type == 'relation':
            entitys = []
            relations = []
            for res in result_json:
                item_type = ''
                for key in res.keys():
                    if key not in ['subject','object']:
                        item_type = key
                if not item_type.startswith('<') or not item_type.endswith('>'):
                    print("抽取返回格式不对：{}".format(res))
                    continue
                relation_body = self._get_item_body(item_type, extract_type)
                if not relation_body:
                    print("抽取返回格式不对：{}".format(res))
                    continue
                sub_tag = relation_body[item_type]['subject']['type'][1:-1]
                obj_tag = relation_body[item_type]['object']['type'][1:-1]
                sub_val = res[item_type]['subject']
                if isinstance(sub_val, dict):
                    sub_val = sub_val.get('desc', '')
                obj_val = res[item_type]['object']
                if isinstance(obj_val, dict):
                    obj_val = obj_val.get('desc', '')

                subj_tag_name = str(sub_tag) + '__' + str(sub_val)
                obj_tag_name = str(obj_tag) + '__' + str(obj_val)
                if sub_tag in graph_ent_types and sub_val and subj_tag_name not in node_set:
                    entitys.append((sub_tag, sub_val))
                    node_set.add(subj_tag_name)

                if obj_tag in graph_ent_types and obj_val and obj_tag_name not in node_set:
                    entitys.append((obj_tag, obj_val))
                    node_set.add(obj_tag_name)

                if sub_tag in graph_ent_types and sub_val and obj_tag in graph_ent_types and obj_val:
                    # relation_type = res['relation_type'][1:-1]
                    relation_type = item_type[1:-1]
                    edge_name = f"{relation_type}:\"{subj_tag_name}\"->\"{obj_tag_name}\""
                    if edge_name not in edge_set:
                        relations.append((relation_type, subj_tag_name, obj_tag_name))
                        edge_set.add(edge_name)
            if entitys:
                tasks = [asyncio.create_task(self._gen_node(e[0], e[1],  graph_otl, types2alias))
                         for e in entitys]
                res = await asyncio.wait(tasks)
                ent_res = [x.result() for x in res[0]]
                entity_list += ent_res
                for e in ent_res:
                    entity2uuid[e['tags'][0] + '__' + e['default_property']['v']] = e.get('vid')

            edge_list += [self._gen_edge(e[0], e[1], e[2], entity2uuid, graph_otl, types2alias) for e in relations]

        # end_time = time.time()
        # print('subgraph process spend', end_time-start_time)
        res_dict = {
            "entity_list": entity_list,
            "edge_list": edge_list
        }
        print(json.dumps(res_dict, indent=4, separators=[',',':'], ensure_ascii=False))
        print('entity num:', len(entity_list))

        return {"res": res_dict, "ans": "抽取完成。"}

# async def main():
#     data_info = """
#     近期（5.1~5.12）丙烯腈市场行情小幅上涨。据生意社数据监测，截至5月12日丙烯腈市场散水价格在9862元/吨，较月初的9662元/吨上涨了0.52%。目前丙烯腈市场出罐自提价格在9700~10000元/吨之间。原料价格弱势下跌丙烯腈成本面小幅下行，需求面刚需支撑，加之部分企业装置停车、降负小幅提振市场气氛，丙烯腈行情小幅上涨。
#     """
   
#     ex = Extraction()
#     fl=ex._chunk('price.pdf')
#     return await ex.extract_event_llm(fl)

# if __name__ == "__main__":
#     import asyncio
#     print(asyncio.run(main()))
   