import requests
import base64
import hashlib
import hmac
import json
import time

# p_host = "10.4.128.32:8444"
# auth_info = {"password":"ZWlzb28uY29tMTIzLg==","isRefresh":0,"email":"James.jie@aishu.cn"}

p_host = "10.4.113.43:8444"
auth_info = {"password": "ZWlzb28uY29tMTIz", "isRefresh": 0, "email": "chao@aishu.cn"}
kg_id = 4


# 在函数里实例化，不会受时效性影响
class OpenApiHeaderHandler(object):
    def __init__(self, host, payload):
        self.host = host
        self.appId = self.get_appid()
        self.timestamp = int(time.time())
        self.payload = payload
        self.appkey = self.getAppKey()
        self.header = {"appid": self.appId, "appkey": self.appkey, "timestamp": str(self.timestamp)}

    def getAppKey(self):
        _timestamp = hashlib.sha256(str(self.timestamp).encode("utf-8")).digest().hex().encode("utf-8")
        _reqParams = hashlib.sha256(self.payload.encode("utf-8")).digest().hex().encode("utf-8")
        shaStr = hmac.new(self.appId.encode("utf-8"), _timestamp + _reqParams, digestmod=hashlib.sha256).digest()
        return base64.b64encode(shaStr.hex().encode("utf-8"))

    def get_header(self):
        return self.header

    def get_appid(self):
        # return 'NWl8TVjfRwB0SdPUXw6'
        url = f"https://{self.host}/api/rbac/v1/user/appId"
        data = auth_info

        response = requests.post(url, json=data, headers={'type': 'email'}, verify=False)
        return json.loads(response.text).get("res")

class Service:
    @classmethod
    async def full_text_query_tag(cls, query, tag):
        json_data = {
            "page": 1,
            "size": 0,
            "query": f"{query}",
            "search_config": [{"tag":f"{tag}"}],
            "kg_id": kg_id,
            "matching_rule": "portion",
            "matching_num": 1
        }
        payload = json.dumps(json_data)
        url = f"https://{p_host}/api/alg-server/v1/open/graph-search/kgs/{kg_id}/full-text"
        header_handler = OpenApiHeaderHandler(p_host, payload)
        response = requests.post(url, data=payload, headers=header_handler.get_header(), verify=False)
        return json.loads(response.text)

    @classmethod
    async def get_full_text_vertex(cls, query, tag):
        res = await cls.full_text_query_tag(query, tag)
        # print(query)
        # print(tag)
        # print(res)
        if not res:
            return None
        if not res.get("res"):
            return None
        if "count" not in res.get("res"):
            return None
        if res.get("res").get("count") < 1:
            return None
        result = res.get("res").get("result")[0]
        if not result:
            return None
        if query != result.get("vertexs")[0].get("default_property"):
            return None
        temp_vertex = {}
        temp_vertex["vid"] = result.get("vertexs")[0].get("id")
        tag = result.get("tag")
        tags = [tag]
        temp_vertex["tags"] = tags
        temp_vertex["color"] = result.get("color")
        temp_vertex["alias"] = result.get("alias")
        temp_vertex["default_property"] = result.get("vertexs")[0].get("default_property")
        # if result.get("vertexs")[0].get("tags"):
        #     if result.get("vertexs")[0].get("tags")[0] == "product":
        #         plist =  result.get("vertexs")[0].get("properties")
        #         temp_V = ""
        #         for item in plist:
        #             if item.get("tag") == "product":
        #                 props = item.get("props")
        #                 for prop_item in props:
        #                     if prop_item.get("name") == "pname":
        #                         temp_V = prop_item.get("value")
        #         temp_vertex["default_property"]["n"] = "pname"
        #         temp_vertex["default_property"]["v"] = temp_V
        return temp_vertex

    @classmethod
    def cognitive_search(cls, api, json_body):
        payload = json.dumps(json_body)
        header_handler = OpenApiHeaderHandler(p_host, payload)
        response = requests.post(api, data=payload, headers=header_handler.get_header(), verify=False)
        if response.status_code != 200:
            raise Exception(response.text)
        return json.loads(response.text)
        # '''
        # "vid": "0b9f4a2a7d262d35359fb0693789ff27",
        # "tags": [
        # 	"chemical"
        # ],
        # "type": "vertex",
        # "color": "#BBD273",
        # "alias": "物质物料",
        # "default_property": {
        # 	"n": "name",
        # 	"v": "丙烯腈"
        # },
        # "icon": ""
        # '''

    @classmethod
    def assemble_node_edge_list(cls, api_path, json_body, request_type, params_list):
        gns2file = {}
        for param_info in params_list:
            entity_class = param_info["class"]
            param_name = param_info["param"]
            query = json_body[param_name]
            res = cls.quick_search(kg_id=4, query=query, entity_class=entity_class, size=10, page=1)
            if not res:
                return {}, {}, {}, {}
            if param_info["type"] == "entity":
                json_body[param_name] = res.get("vid")
            else:
                json_body[param_name] = res.get("name")
        # json_body = {list(json_body.keys())[0]: vid}
        # api访问所需要的参数，以及是vid还是name类型在qa_tag_setting_map.json中定义
        if request_type == "restful_api":
            api = f"""https://{p_host}/api/cognitive-service/v1/open/custom-search/services/{api_path}"""
        else:
            header_handler = OpenApiHeaderHandler(p_host, payload=json.dumps(json_body))
            appid = header_handler.get_appid()
            api = f"""https://{p_host}/iframe/graph?appid={appid}&operation_type=custom-search&service_id={api_path}"""
            for k, v in json_body.items():
                api += "&" + str(k) + "=" + str(v)
            return {
                "url": api,
                "request_type": request_type
            }, {}, {}, {}
        res = cls.cognitive_search(api, json_body)
        tables = res.get("res")
        entity_list = []
        edge_list = []
        edge_res = []
        vertexs = {}
        if tables:
            for table in tables:
                vertices_parsed_list = table.get("vertices_parsed_list", [])
                edges_parsed_list = table.get("edges_parsed_list", [])
                paths_parsed_list = table.get("paths_parsed_list", [])

                for vertex in vertices_parsed_list:
                    temp_vertex = {}
                    temp_vertex["vid"] = vertex.get("vid")
                    temp_vertex["alias"] = vertex.get("alias")
                    if vertex.get("default_property", {}).get("v"):
                        temp_vertex[vertex.get("default_property").get("a")] = vertex.get("default_property").get("v")
                        vertexs[vertex.get("vid")] = vertex.get("default_property").get("v")
                    for props in vertex.get("properties", []):
                        for prop in props.get("props", []):
                            if prop.get("value"):
                                temp_vertex[prop.get("alias")] = prop.get("value")
                    if temp_vertex not in edge_list:
                        entity_list.append(temp_vertex)
                for edge in edges_parsed_list:
                    temp_edge = {}
                    temp_edge["subject"] = edge.get("src_id")
                    temp_edge["object"] = edge.get("dst_id")
                    temp_edge["relation"] = edge.get("alias")
                    if temp_edge not in edge_list:
                        edge_list.append(temp_edge)
                if paths_parsed_list:
                    for vertex_line in paths_parsed_list:
                        for vertex in vertex_line.get("nodes", []):
                            temp_vertex = {}
                            temp_vertex["vid"] = vertex.get("vid")
                            # temp_vertex["tags"] = vertex.get("tags")[0]
                            temp_vertex["alias"] = vertex.get("alias")
                            if vertex.get("default_property", {}).get("v"):
                                temp_vertex[vertex.get("default_property").get("a")] = vertex.get(
                                    "default_property").get("v")
                                vertexs[vertex.get("vid")] = vertex.get("default_property").get("v")
                            for props in vertex.get("properties", []):
                                for prop in props.get("props", []):
                                    if prop.get("value"):
                                        if prop.get("name") != "before_content":
                                            temp_vertex[prop.get("alias")] = prop.get("value")

                            if temp_vertex not in entity_list:
                                entity_list.append(temp_vertex)
                            if "文档id" in temp_vertex:
                                gns2file[temp_vertex["文档id"]] = temp_vertex["名称"]
                        for edge in vertex_line.get("relationships"):
                            temp_edge = {}
                            temp_edge["subject"] = edge.get("src_id")
                            temp_edge["object"] = edge.get("dst_id")
                            temp_edge["relation"] = edge.get("alias")

                            if temp_edge not in edge_list:
                                edge_list.append(temp_edge)

            for edge_info in edge_list:
                subject = vertexs.get(edge_info.get("subject"))
                object = vertexs.get(edge_info.get("object"))
                relation = edge_info.get("relation")
                if subject and object and relation:
                    line = str(subject) + str(relation) + str(object)
                    edge_res.append(line)

        num1 = 5
        num2 = 10
        while (len(str(entity_list[:num1])) + len(str(edge_list[:num2]))) > 2400:
            num1 = int(num1 * 0.9)
            num2 = int(num2 * 0.9)
        result = {
            "entity_list": entity_list[:num1],
            "edge_list": edge_res[:num2]
        }

        return result, vertexs, tables, gns2file

    @classmethod
    # 快速搜索，根据实体名称获取对应vid
    def quick_search(cls, kg_id, query, entity_class, size=10, page=1):
        strings = "query={}&page={}&size={}&entity_classes={}".format(query, page, size, entity_class)
        header_handler = OpenApiHeaderHandler(p_host, payload=strings)
        api = "https://{}/api/alg-server/v1/open/graph-search/kgs/{}/quick-search?query={}&page={}&size={}&entity_classes={}".format(
            header_handler.host, kg_id, query, page, size, entity_class)
        response = requests.get(api, headers=header_handler.get_header(), verify=False)
        if response.status_code != 200:
            raise Exception(response.text)
        res = json.loads(response.text)
        if not res.get("res"):
            return {}
        name2vid = {}
        for line in res.get("res"):
            name2vid[line.get("default_property", {}).get("v")] = line.get("id")
        if query in name2vid:
            name = query
            vid = name2vid[name]
        else:
            vid = res.get("res")[0]["id"]
            name = res.get("res")[0]["default_property"]["v"]
        return {"vid": vid, "name": name}



def test():
    query = "丙烯腈"
    tag = "chemical"
    response = Service.get_full_text_vertex(query, tag)
    return response

def test2():
    api = "https://10.4.128.32:8444/api/cognitive-service/v1/open/custom-search/services/bbb63e1d78e148869755db9e2837bd4e"
    json_body = {"chemical_name": "丙烯腈"}
    return Service.assemble_node_edge_list(api, json_body)

def test3():
    api = "http://10.4.133.194:6475/api/builder/v1/knw/resource_exists"
    params = {'dataId': 19, 'dataType': 'kg'}
    # headers = {'Content-Type': 'application/json'}
    # headers = {'Connection': 'close'}
    response = requests.get(url=api, params=params)
    print(response.request.url)
    print(response.request.headers)
    print(response.request.body)
    return response

# print(test())


if __name__ == "__main__":
    res = Service.quick_search(kg_id=4, query="北京鼎汉检", entity_class="enterprise", size=10, page=1)
    print(res)
