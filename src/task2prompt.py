#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/7/1 9:49
# @Author  : Jay.zhu
# @File    : task2prompt.py.py
import json


class TaskPrompt(object):
    def __init__(self):
        pass

    def _default_prompt(self, query, graph_info):
        schema = {"answer": "xxxx：1、xxxx;2、xxx等等;\n详细信息请查阅图谱数据。"}
        self.task2prompt = {
            "interrogative_function": {
                "name": "功能介绍",
                "prompt": ""
            },
            "competitive_enterprise": {
                "name": "竞品公司",
                "prompt": f"""若两个公司有共同的生产产品，则属于竞品公司。请根据图谱数据回答用户问题，并严格按照json报文回复。
                图谱数据：```{graph_info}```
                用户问题：```{query}```;
                请严格按照{schema}格式处理，直接以json报文回复。,
                """
            },
            "scope_of_enterprise": {
                "name": "企业经营范围",
                "prompt": f"""企业经营范围是企业从事的行业，生产产品、服务内容等。请根据图谱数据回答用户问题。
                图谱数据：```{graph_info},其中entity_list表示实体信息,edge_list表示实体之间的关系。```
                用户问题：```{query}```;
                请严格按照json报文回复,答案放在报文的"answer"字段里,如果没有答案，则直接回复，['很抱歉，图谱中未查询到该信息。']。如果可以分点论述时，请按以下格式组织答案:
                1、...；2、...等；详细信息请查阅图谱数据。"""
            },
            "industry_chain": {
                "name": "产业链",
                "prompt": f"""产业链是某个产业行业内包含的产品，以及生产这些产品的公司之间链路关系。请根据图谱数据回答用户问题。
                图谱数据：```{graph_info},其中entity_list表示实体信息,edge_list表示实体之间的关系。```
                用户问题：```{query}```;
                请严格按照json报文回复,答案放在报文的"answer"字段里,如果没有答案，则直接回复，['很抱歉，图谱中未查询到该信息。']。如果可以分点论述时，请按以下格式组织答案:
                1、...；2、...等；详细信息请查阅图谱数据。"""
            },
            "enterprise_details": {
                "name": "企业详情信息",
                "prompt": f"""企业详细信息是该公司相关产品、经营范围、所属行业、地理位置、时间等信息。请根据图谱数据回答用户问题。
                图谱数据：```{graph_info},其中entity_list表示实体信息,edge_list表示实体之间的关系。```
                用户问题：```{query}```;
                请严格按照json报文回复,答案放在报文的"answer"字段里,如果没有答案，则直接回复，['很抱歉，图谱中未查询到该信息。']。如果可以分点论述时，请按以下格式组织答案:
                1、...；2、...等；详细信息请查阅图谱数据。"""
            },
            "corporate_relations": {
                "name": "企业关系",
                "prompt": f"""企业关系是两家企业之间的关联关系，比如经营范围、所属行业、所在区域等之间的相同点和差异点。请根据图谱数据回答用户问题。
                图谱数据：```{graph_info},其中entity_list表示实体信息,edge_list表示实体之间的关系。```
                用户问题：```{query}```;
                请严格按照json报文回复,答案放在报文的"answer"字段里,如果没有答案，则直接回复，['很抱歉，图谱中未查询到该信息。']。请按以下格式组织答案，从不同角度进行分析:
                1、...；2、...等；详细信息请查阅图谱数据。"""
            },
            "enterprise_comparison_report": {
                "name": "企业对比报告",
                "prompt": f"""企业对比是两家企业之间的关联关系，比如经营范围、所属行业、所在区域等之间的相同点和差异点。请根据图谱数据回答用户问题。
                图谱数据：```{graph_info},其中entity_list表示实体信息,edge_list表示实体之间的关系。```
                用户问题：```{query}```;
                请严格按照json报文回复,答案放在报文的"answer"字段里,如果没有答案，则直接回复，['很抱歉，图谱中未查询到该信息。']。请按以下格式组织答案，从不同角度进行分析:
                1、...；2、...等；详细信息请查阅图谱数据。"""
            },
            "enterprise_investment": {
                "name": "企业投资查询",
                "prompt": f"""企业投资是该企业投资的公司或者被其他公司投资。请根据图谱数据回答用户问题。
                图谱数据：```{graph_info},其中entity_list表示实体信息,edge_list表示实体之间的关系。```
                用户问题：```{query}```;
                请严格按照json报文回复,答案放在报文的"answer"字段里,如果没有答案，则直接回复，['很抱歉，图谱中未查询到该信息。']。请按以下格式组织答案，从不同角度进行分析:
                1、...；2、...等；详细信息请查阅图谱数据。"""
            },
            "corporate_product_public_opinion": {
                "name": "企业产品舆情查询",
                "prompt": f"""企业舆情是该企业某个产品相关的新闻、报道以及最近发生的等信息。请根据图谱数据回答用户问题。
                图谱数据：```{graph_info}```
                用户问题：```{query}```;
                请严格按照{schema}格式处理，直接以json报文回复。"""
            },
            "default": {
                "name": "默认",
                "prompt": f"""我需要你做一些信息整合，根据图谱数据回答用户问题。
                图谱数据：```{graph_info},其中entity_list表示实体信息,edge_list表示实体之间的关系。```
                用户问题：```{query}```;
                请严格按照json报文回复,答案放在报文的"answer"字段里,如果没有答案，则直接回复，['很抱歉，图谱中未查询到该信息。']。若可以分点论述，请按以下格式组织答案，从不同角度进行分析:
                1、...；2、...等；详细信息请查阅图谱数据。"""
            }
        }

    def get_prompt(self, query, graph_info, task_name):
        self._default_prompt(query, graph_info)
        if task_name not in self.task2prompt:
            task_name = "default"
        return self.task2prompt.get(task_name).get("prompt")


task_prompt = TaskPrompt()

