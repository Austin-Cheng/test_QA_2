import json


class PromptTemplate:
  
  @classmethod
  def get_entity_tag_template(cls):
      recognize_item = "实体"
      item_type_name = "entity_type"
      example = '''[{'<chemical>': {'desc': '化学品'}}, {'<reaction>': {'desc': '反应'}}]'''
      all_include_response_example = """[<chemical>,<reaction>]"""
      return (recognize_item, item_type_name, example, all_include_response_example)

  @classmethod
  def get_event_tag_template(cls):
      recognize_item = "事件"
      item_type_name = "event_type"
      example =  '''[
                      {
                        "<price_increase>": {
                          "desc": "价格上涨"
                        }
                      },
                      {
                        "<price_decrease>": {
                          "desc": "价格下降"
                        }
                      }
                  ]'''
      # all_include_response_example = """[<price_increase>,<price_decrease>]"""
      all_include_response_example = example
      return (recognize_item, item_type_name, example, all_include_response_example)

  @classmethod
  def get_relation_tag_template(cls):
      recognize_item = "关系"
      item_type_name = "relation_type"
      example = '''[
        {
            "<product_of>": {
              "desc": "生产产品",
              "subject": {
                "type": "<enterprise>",
                "desc": "企业"
              },
              "object": {
                "type": "<product>",
                "desc": "产品"
              }

        }
      }
      ]'''
      all_include_response_example = """[<product_of>]"""
      return (recognize_item, item_type_name, example, all_include_response_example)

  @classmethod
  def get_event_extraction_template(cls):
      event_type_example = """
        {
            "<price_increase>": {
              "desc": "价格上涨",
              "roles": ["<chemical>","<from_price>","<to_price>","<time>"]
            }
        }
      """
      return_example = """
        {
          "event_type":"<price_increase>",
          "event_title":"xxxxx",
          "roles":[{"<chemical>":"xxx"},{"<from_price>":"xxx"},{"<to_price>":"xxx"},{"<time>":"xxx"}]
        }
      """
      return (event_type_example, return_example)

  @classmethod
  def get_entity_extraction_template(cls):
      event_type_example = """
         {'<product>': {'desc': '产品'}}
      """
      return_example = """
        {
          "entity_type":"<product>",
          "entity_name":"xxxxx"
        }
      """
      return (event_type_example, return_example)

  @classmethod
  def get_entity_extraction_response_format(cls, entity_json):
      # entity_json = json.loads(entity_json)
      entity_type = list(entity_json.keys())[0]

      return_example = {
        #   "entity_type": entity_type,
        #   "entity_name": "the text of entity extracted from text"
        # }
          entity_type: "the text of entity extracted from text"
      }
      return_example = json.dumps(return_example, ensure_ascii=False, indent=4, separators=[',',':'])

      return return_example

  @classmethod
  def get_relation_extraction_template(cls):
      event_type_example = """
      {
        "<product_of>": {
          "desc": "生产产品",
          "subject": {
            "type": "<enterprise>",
            "desc": "企业"
          },
          "object": {
            "type": "<product>",
            "desc": "产品"
          }

        }
      }
      """
      return_example = """
        {
          "relation_type":"<product_of>",
          "relation_name":"xxxxx",
          "subject":{"<enterprise>":"xxx"},
          "object": {"<product>":"xxx"}
        }
      """
      return (event_type_example, return_example)

  @classmethod
  def get_relation_extraction_response_format(cls, relation_json):
      # relation_json = json.loads(relation_json)
      relation_type = list(relation_json.keys())[0]
      subj_type = relation_json[relation_type]['subject']['type']
      obj_type = relation_json[relation_type]['object']['type']

      return_example = {
      #   "relation_type":relation_type,
      #   "relation_name":"the relation text extracted from text",
      #   "subject":{subj_type:"the subject of the relation"},
      #   "object": {obj_type:"the object of the relation"}
      # }

          relation_type: {
              "subject": "the subject text of the relation",
              "object": "the object text of the relation"
          }
      }
      return_example = json.dumps(return_example, ensure_ascii=False, indent=4, separators=[',',':'])

      return return_example

  @classmethod
  def proc_relation_type_format(cls, relation_json):
      # relation_json = json.loads(relation_json)
      relation_type = list(relation_json.keys())[0]
      subj_type = relation_json[relation_type]['subject']['desc']
      obj_type = relation_json[relation_type]['object']['desc']

      return_example = {
            relation_type:relation_json[relation_type]['desc'],
            "subject":subj_type,
            "object": obj_type
      }
      return return_example

  @classmethod
  def get_ops_type_template(cls):
      ops_type_example = """{
          "ops_type":[
              {
                  "<canvas_ops>": {
                    "desc": "画布操作，包括改变布局、颜色、样式等；例如布局有自由布局、层次布局、树形布局等"
                  }
              },
              {
                  "<knowledge_graph_qa>": {
                    "desc": "图谱QA，根据图谱数据回答用户问题"
                  }
              }
          ]
        }"""
      return_example = """[<canvas_ops>,<knowledge_graph_qa>]"""
      return (ops_type_example, return_example)
  
  @classmethod
  def get_canvas_ops_type_template(cls):
    ops_type_example = """{
      "<freedom_layout>":{"name":"自由布局","desc":"自由布局"},
      "<tree_layout>":{"name":"树状布局", "desc":"树状布局"},
      "<cascade_layout>":{"name":"层次布局", "desc":"层次布局"}
    }"""
    return_example = """["<freedom_layout>","<tree_layout>","<cascade_layout>"]"""
    return (ops_type_example, return_example)

  @classmethod
  def get_qa_ops_template(cls):
      qa_ops_example = """{
        "<2_hop_find_neihbors>":{
            "name":"物质物料二度下游邻居",
            "desc":"物质物料二度下游邻居",
            "param_list":["chemical_name"]
        },
        "<2_hop_find_neihbors_enterprise>":{
            "name":"企业二度下游邻居",
            "desc":"企业二度下游邻居",
            "param_list":["enterprise_name"]
        }
      }"""
      return_example = """["<2_hop_find_neihbors>"]"""
      return (qa_ops_example, return_example)

  @classmethod
  def get_qa_slot_template(cls):
      ops_example = """{
        "name":"企业二度下游邻居",
        "desc":"企业二度下游邻居",
        "param_list":[{"enterprise_name":{"desc":"企业名称","slot_value":""}},{"product":{"desc":"产品","slot_value":""}]
      }"""
      query_example = """华为的竞品公司的手机类型"""
      return_example = """
        [{"enterprise_name":{"desc":"企业名称","slot_value":"华为"}},{"product":{"desc":"产品","slot_value":"手机"}]
      """
      return (ops_example, query_example, return_example)